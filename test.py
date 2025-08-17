from pprint import pprint
import logging
import base64
from multiprocessing import Pool
import hashlib
import json
import traceback
import os
import requests
import jsondiff
import copy

import lambdaentry
from purerackdiagram.utils import global_config
import jsonurl_py as jsonurl
from test_one_offs import more_tests
import subprocess
import datetime
import shutil


logger = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
logger.addHandler(ch)
logger.setLevel(logging.WARN)

def get_file_hash(file_path):
    """Get SHA256 hash of a file"""
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def filter_result_data(data):
    """Filter out keys that should not be used for comparisons"""
    if not isinstance(data, dict):
        return data
    
    # Keys to always ignore in comparisons
    always_ignore = {'execution_duration'}
    
    # Create filtered copy
    filtered = {k: v for k, v in data.items() if k not in always_ignore}
    
    # For JSON-based tests, also ignore these keys when they exist
    if 'image_type' in filtered:
        image_type = filtered.get('image_type')
        if image_type in ['json', 'json_only']:
            json_ignore = {'image_mib'}
            filtered = {k: v for k, v in filtered.items() if k not in json_ignore}
    
    return filtered


def download_and_hash_image(url):
    """Download image content from URL and return SHA256 hash of raw bytes."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # Hash the raw bytes
        h = hashlib.sha256()
        h.update(response.content)
        return h.hexdigest()
    except requests.RequestException as e:
        logger.error(f"Failed to download image from {url}: {e}")
        # Return hash of empty bytes as fallback
        h = hashlib.sha256()
        h.update(b'')
        return h.hexdigest()


def test_lambda(params, outputfile ):
    """
    Run lambda test and save output files.
    
    Args:
        params: Test parameters
        outputfile: Base path for output file (without extension)
        git_state: Git commit hash or 'head' (if None, will be determined)
    """

    
    results = lambdaentry.handler(params, None)
    
    # Check for error status codes (4xx)
    if 400 <= results['statusCode'] < 500:
        if results['headers'].get("Content-Type") == 'application/json':
            # Parse the JSON response to inspect error message
            try:
                if type(results['body']) is str:
                    error_data = json.loads(results['body'])
                else:
                    error_data = results['body']

                error_msg = error_data.get('error', 'Unknown error')
                error_type = error_data.get('error_type', 'Unknown')
                logger.info(f"Error response ({results['statusCode']}): {error_type} - {error_msg}")
                
            except json.JSONDecodeError:
                logger.error("Failed to parse error JSON response")
        elif results['headers'].get("Content-Type") == 'image/png':
            # If it's an image error message, we can't inspect it directly
            logger.info(f"Error response ({results['statusCode']}) as image")

    # If statusCode is 302, follow the redirect
    if results['statusCode'] == 302:
        location = results['headers']['Location']
        response = requests.get(location)
        content_type = response.headers.get('Content-Type')
        logger.info(f"Redirected to {location} with content type {content_type}")
        
        # Update the body and headers of the results to hide the redirect
        results['body'] = base64.b64encode(response.content).decode('utf-8')
        results['headers']['Content-Type'] = content_type
        results['statusCode'] = 200  # Update status code to OK

    
    if results['headers'].get("Content-Type") == 'image/png':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            with open(outputfile + '.png', 'wb') as outfile:
                outfile.write(img_str)

    elif results['headers'].get("Content-Type") == 'application/vnd.ms-visio.stencil':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            with open(outputfile + '.vssx', 'wb') as outfile:
                outfile.write(img_str)

    elif results['headers'].get("Content-Type") == 'application/zip':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            with open(outputfile + '.zip', 'wb') as outfile:
                outfile.write(img_str)

    elif results['headers'].get("Content-Type") == 'application/json':
        if 'body' in results:
            
            obj = json.loads(results['body'])
            
            # Save the original object to file WITHOUT modifying the image
            with open(outputfile + '.json', 'w',  encoding='utf-8') as outfile:
                json.dump(obj, outfile, indent=4, ensure_ascii=False)
            
            # Now create a modified version for the results data structure
            # This modified version will have the hash instead of the full image
            result_obj = obj.copy()
            if 'image' in result_obj and result_obj['image'] is not None:
                # Replace image data with SHA256 hash in the result object only
                if result_obj.get('image_type') == 'link' or result_obj['image'].startswith(('http://', 'https://')):
                    # Image is a URL - download and hash the content
                    logger.info(f"Downloading image from URL: {result_obj['image']}")
                    result_obj['image'] = download_and_hash_image(result_obj['image'])
                else:
                    # Image is base64 data - decode and hash
                    h = hashlib.sha256()
                    try:
                        decoded_image = base64.b64decode(result_obj['image'])
                    except (TypeError, ValueError) as e:
                        logger.error(f"Failed to decode image data: {e}")
                        decoded_image = b''
                    h.update(decoded_image)
                    result_obj['image'] = h.hexdigest()
            else:
                if 'json_only' not in params['queryStringParameters'] and results['statusCode'] == 200:
                    # If no image data, just use the original body
                    print("No image data found in JSON response")

            results['body'] = result_obj  # Use the modified version with hash for results

    return results


# Now define the new create_test_image function
# Global set to track all generated keys for duplicate detection
_generated_keys = {}  # Change to dict to store both key and item
_duplicate_keys = []

def create_test_image(item, count, total, save_dir):
    """
    Create test image with git-state based directory structure.
    
    Args:
        item: Test parameters
        count: Current test number
        total: Total number of tests
        save_dir: Directory name for saving results
    """

    
    # Create git-state based subdirectory
    folder = os.path.join("test_results", save_dir)
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Extract json/json_only parameters to determine output type
    json_param = item.get('json')
    json_only_param = item.get('json_only')
    
    # Determine output type based on parameter priority
    if json_only_param:  # json_only takes precedence
        output_type = 'json_only'
        file_extension = '.json_only'
    elif json_param:
        output_type = 'json'
        file_extension = '.json'
    else:
        output_type = 'png'
        file_extension = '.png'
    
    # Build filename WITHOUT json/json_only parameters (so hash is same for all variants)
    file_name_parts = [item['model']]
    for n in ['face', 'bezel', 'mezz', 'fm_label', 'dp_label', 'addoncards', 'ports', 'csize', 'datapacks',  
    'no_of_chassis', 'no_of_blades', 'efm', 'direction', 'drive_size', 'no_of_drives_per_blade', 'vssx',
    'chassis_gen', 'datapacksv2', 'bladesv2', 'protocol', 'chassis', 'dc_power', 'individual',
    'jsononly', 'pci0', 'pci1', 'pci2', 'pci3', 'pci4', 'pci5', 'local_delay', 'chassi_gen', 
    'blades', 'dfm_label' ]:
        # Skip json and json_only parameters in filename generation
        if n in ['json', 'json_only']:
            continue
            
        if n in item:
            if n == 'datapacks':
                file_name_parts.append(f"_{str(item[n]).replace('/', '-')}")
            elif n == 'datapacksv2' or n == 'bladesv2':
                #sha256 hash the datapacksv2 value
                h = hashlib.sha256()
                h.update(item[n].encode('utf-8'))
                file_name_parts.append(f"_{n}-{h.hexdigest()[:8]}")
            else:
                # Include type information to differentiate between bool True vs string "True"
                value = item[n]
                file_name_parts.append(f"_{n}-{type(value).__name__}_{value}")
    
    # Join all parts to create the base filename
    file_name_base = ''.join(file_name_parts)
    
    # Add a hash of the case-sensitive filename to handle case-insensitive filesystems
    # This ensures fa-c70r4b and fa-C70R4b create different files
    case_hash = hashlib.md5(file_name_base.encode()).hexdigest()[:6]
    base_file_name = f"{file_name_base}_{case_hash}"
    
    # Create the full filename with extension - this will be our result key
    full_file_name = base_file_name + file_extension
    
    # Check filename length against OS limits
    max_filename_length = 255  # Common filesystem limit
    
    if len(full_file_name) > max_filename_length - 10:  # 10 byte safety margin
        logger.warning(f"Filename approaching OS limit ({len(full_file_name)} chars): {full_file_name[:50]}...")
        # Truncate base name and add hash to ensure uniqueness
        truncate_at = max_filename_length - len(file_extension) - 20  # Leave room for hash and extension
        file_name_hash = hashlib.sha256(base_file_name.encode('utf-8')).hexdigest()[:8]
        base_file_name = base_file_name[:truncate_at] + "_" + file_name_hash
        full_file_name = base_file_name + file_extension
        logger.info(f"Truncated to: {full_file_name}")
    
    # Check for duplicate keys and compare with json_diff
    if full_file_name in _generated_keys:
        # Use json_diff to check if items are truly identical
        original_item = _generated_keys[full_file_name]
        diff = jsondiff.diff(original_item, item)
        
        if not diff:
            # Truly identical - this is a real duplicate
            print(f"TRUE DUPLICATE DETECTED: {full_file_name}")
            print(f"  Items are identical: {item}")
            _duplicate_keys.append((full_file_name, original_item, item, "identical"))
        else:
            # Different items with same key - key generation needs improvement
            print(f"KEY CONFLICT DETECTED: {full_file_name}")
            print(f"  Original item: {original_item}")
            print(f"  Current item:  {item}")
            print(f"  Differences:   {diff}")
            _duplicate_keys.append((full_file_name, original_item, item, "different"))
    else:
        # Store a deep copy to prevent modification by lambda function
        _generated_keys[full_file_name] = copy.deepcopy(item)

    try:
        # Use base filename (without extension) for the actual file output
        results = test_lambda({"queryStringParameters":item}, os.path.join(folder, base_file_name))

        h = hashlib.sha256()
        content_type = results['headers'].get("Content-Type")
        status_code = results['statusCode']

        # Check for error responses (4xx, 5xx)
        if 400 <= status_code < 600:
            print(f"{count} of {total}   {full_file_name} - ERROR {status_code}")
            
            # For JSON errors, we can examine the detailed message
            if content_type == 'application/json' and 'body' in results:
                try:
                    if type(results['body']) is str:
                        # If body is a string, decode it
                        error_data = json.loads(results['body'])
                    else:
                        error_data = results['body']
                    error_msg = error_data.get('error', 'Unknown error')
                    error_type = error_data.get('error_type', 'Unknown')
                    
                    # Return error details for validation and testing
                    return({full_file_name: {
                        "status": status_code,
                        "error_type": error_type,
                        "error_msg": error_msg,
                        "path": f"{save_dir}/{base_file_name}",
            
                    }})
                except json.JSONDecodeError:
                    print(f"  Failed to parse error JSON")
                    return({full_file_name: {
                        "status": status_code,
                        "error": "Failed to parse error JSON",
                        "path": f"{save_dir}/{base_file_name}",
 
                    }})
        
        # For successful responses or errors that aren't in JSON format
        print(f"{count} of {total}   {full_file_name} - Status: {status_code}")
        
        # Prepare result with path information
        result_data = {
            'path': f"{save_dir}/{base_file_name}",

        }
        
        if content_type == 'application/json':
            result_data['data'] = filter_result_data(results['body'])
        else:
            # For other content types (PNG, VSSX, ZIP), decode base64 and hash raw bytes
            decoded_body = base64.b64decode(results['body'].encode('utf-8'))
            h.update(decoded_body)
            result_data['hash'] = h.hexdigest()
            
            # Determine file extension based on content type
            if content_type == 'image/png':
                result_data['path'] += '.png'
            elif content_type == 'application/vnd.ms-visio.stencil':
                result_data['path'] += '.vssx'
            elif content_type == 'application/zip':
                result_data['path'] += '.zip'
        
        return({full_file_name: result_data})

    except Exception as ex_unknown:
        print(f"Caught exception in image: {full_file_name}")
        traceback.print_exc()
        return({full_file_name: {
            "status": 500,
            "error": str(ex_unknown),
            "traceback": traceback.format_exc(),
            "path": f"{save_dir}/{base_file_name}",
        }})

    


def get_all_tests():
    models = global_config['pci_config_lookup']
    dps = ['45/45-31/63-45-24.0', '3/127-24.0-45']

    valid_chassis_dps = list(global_config['chassis_dp_size_lookup'].keys())
    #valid_chassis_dps += list(global_config['qlc_chassis_dp_size_lookup'].keys())
    valid_shelf_dps = list(global_config['shelf_dp_size_lookup'].keys())
    #valid_shelf_dps += list(global_config['qlc_shelf_dp_size_lookup'].keys())

    # get the keys of diction csize_lookup
    csizes = list(global_config['csize_lookup'].keys())
    #csizes = ['964', '984']
    #global_config.csize_lookup

    count = 0

    for test in more_tests:
        #if not test['queryStringParameters'].get('json'):
        #    continue
        json_test = test['queryStringParameters']
        yield json_test
        count += 1

        if 'json' not in json_test:
            json_test = json_test.copy()
            json_test['json'] = True
            yield json_test

        if 'json_only' not in json_test:
            #json onlytest
            json_test = json_test.copy()
            json_test['json_only'] = True
            yield json_test

        
    for json_test in [None,"json","json_only"]:
        for cg in ['1', '2']:
            for model in ['x50r4', 'c50r4', 'c20', 'c50r4b', 'x50r4b', 'er1', 'er1b']:
                    params = {"model": f"fa-{model}",
                                "datapacks": "0",
                                "face": "front",
                                'chassi_gen': cg,
                                "fm_label": True,
                                "dp_label": True}
                    if json_test is not None:
                        params[json_test] = "True"
                    
                    yield params
        
        
        # Test all Models with a front data pack and shelf.
        
        for model in models:
            #continue
            #model = model.split('-')[0] + '-' + model.split('-')[1]
            if 'c' in model or 'e' in model:
                count += 1
                params = {"model": model,
                            "fm_label": True,
                            "dp_label": True,
                            "csize": '984'}
                if json_test is not None:
                    params[json_test] = "True"
                
                yield params
            else:
                for dp in dps:
                    count += 1
                    params = {"model": model,
                                "fm_label": True,
                                "dp_label": True,
                                "datapacks": dp}
                    if json_test is not None:
                        params[json_test] = "True"
                    
                    yield params

            # The bezel.
            params = {"model": model,
                        "fm_label": True,
                        "dp_label": True,
                        "bezel": True,
                        "datapacks": '366'}
            if json_test is not None:
                params[json_test] = "True"
            
            yield params

        for csize in csizes:
            count += 1
            params = {"model": 'fa-c60',
                        "fm_label": True,
                        "dp_label": True,
                        "csize": csize}
            if json_test is not None:
                params[json_test] = "True"
            
            yield params
        
        #Test all Datapacks on the front.
        for dp in valid_chassis_dps:
            count += 1
            params = {"model": "fa-x70r1",
                        "fm_label": True,
                        "dp_label": True,
                        "datapacks": dp}
            if json_test is not None:
                params[json_test] = "True"
            
            yield params

        for dp in valid_shelf_dps:
            count += 1
            params = {"model": "fa-x70r4",
                        "fm_label": True,
                        "dp_label": True,
                        "datapacks": f"63-{dp}"}
            if json_test is not None:
                params[json_test] = "True"
            
            yield params
                

        # back:
        addon_cards = global_config['pci_valid_cards']

        #every model and shelf back view.
        for model in models:
            #continue
            #model = model.split('-')[0] + '-' + model.split('-')[1]
            
            if 'c' in model or 'e' in model:
                params = {"model": model,
                            "addoncards": '4fc',
                            "face": "back",
                            "csize": '984',
                            "ports": True}
                if json_test is not None:
                    params[json_test] = "True"
                
                count += 1
                yield params

            else:
                params = {"model": model,
                            "datapacks": "63-24.0-45",
                            "addoncards": '4fc',
                            "face": "back",
                            "ports": True}
                if json_test is not None:
                    params[json_test] = "True"
                
                count += 1
                yield params

            # every model with each card.
            for card in addon_cards:
                params = {"model": model,
                            "datapacks": "366",
                            "addoncards": f"{card},{card},{card}",
                            "face": "back",
                            "ports": True}
                if json_test is not None:
                    params[json_test] = "True"
                count += 1
                yield params



        

        for blades in [10, 15, 30]:
            for dfms in [2, 4]:
                for size in [24.0, 48.2]:
                    for face in ['front', 'back']:
                        params = {"model": "fb-s200",
                                "no_of_blades": blades,
                                "face": face,
                                "no_of_drives_per_blade": dfms,
                                "drive_size": size,
                                "ports": True}
                        if json_test is not None:
                            params[json_test] = "True"
                        
                        count += 1
                        yield params
                        params = {"model": "fb-e",
                                "no_of_blades": blades,
                                "face": face,
                                "no_of_drives_per_blade": dfms,
                                "drive_size": size,
                                "ports": "TRUE"}
                        if json_test is not None:
                            params[json_test] = "True"
                        
                        count += 1
                        yield params

        



def test_all(args):


    git_state = "head"
    if hasattr(args, 'git_state') and args.git_state:
        git_state = args.git_state
    print(f"Using specified git state: {git_state}")

    save_dir = git_state
    
    # Handle directory cleanup based on git-state
    results_json_file = os.path.join("test_results", f"test_results_{git_state}.json")
    
    if git_state == "head":
        # Automatically delete head directory contents and JSON file
        if os.path.exists(save_dir):
            print(f"Automatically clearing head directory: {save_dir}")
            shutil.rmtree(save_dir)
        if os.path.exists(results_json_file):
            print(f"Automatically removing head results file: {results_json_file}")
            os.remove(results_json_file)
    else:
        # Ask user for confirmation before deleting other git-state directories
        if os.path.exists(save_dir) or os.path.exists(results_json_file):
            print(f"Directory {save_dir} or results file {results_json_file} already exists.")
            response = input(f"Do you want to overwrite the existing data for git-state '{git_state}'? (y/N): ")
            if response.lower() in ['y', 'yes']:
                if os.path.exists(save_dir):
                    print(f"Removing directory: {save_dir}")
                    shutil.rmtree(save_dir)
                if os.path.exists(results_json_file):
                    print(f"Removing results file: {results_json_file}")
                    os.remove(results_json_file)
            else:
                print("Aborting test run to avoid overwriting existing data.")
                return

    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    # Create amultiprocessing pool
    pool = Pool(processes=args.t)
    futures = []
    total_count = 0

    all_items = list(get_all_tests())
    if args.limit is not None:
        all_items = all_items[:args.limit]
    count = 0
    for item in all_items:
        futures.append(pool.apply_async(create_test_image, args=(item, count, len(all_items), save_dir)))
        count += 1

    pool.close()
    pool.join()

    results = {}

    for f in futures:
        result = f.get()
        results.update(result)

    # Create git-state subdirectory and save results there
    
    output_filename = os.path.join("test_results", f"test_results_{git_state}.json")
    with open(output_filename, "w") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print(f"Results saved to: {output_filename}")
    
    # Report duplicate keys with categorization
    if _duplicate_keys:
        # Separate true duplicates from key conflicts
        true_duplicates = []
        key_conflicts = []
        
        for entry in _duplicate_keys:
            if len(entry) == 4:  # New format with type
                key, original, duplicate, dup_type = entry
                if dup_type == "identical":
                    true_duplicates.append((key, original, duplicate))
                else:
                    key_conflicts.append((key, original, duplicate))
            else:  # Old format - assume it's a conflict
                key_conflicts.append(entry)
        
        print(f"\n=== DUPLICATE ANALYSIS SUMMARY ===")
        print(f"Total issues found: {len(_duplicate_keys)}")
        print(f"True duplicates (identical tests): {len(true_duplicates)}")
        print(f"Key conflicts (different tests, same key): {len(key_conflicts)}")
        
        if true_duplicates:
            print(f"\n=== TRUE DUPLICATES (Test Generation Issues) ===")
            for i, (key, original, duplicate) in enumerate(true_duplicates[:10]):  # Show first 10
                print(f"{i+1}. Key: {key}")
                print(f"   Test params: {original}")
        
        if key_conflicts:
            print(f"\n=== KEY CONFLICTS (Key Generation Issues) ===")
            for i, (key, original, duplicate) in enumerate(key_conflicts[:5]):  # Show first 5
                print(f"{i+1}. Key: {key}")
                print(f"   Original: {original}")
                print(f"   Current:  {duplicate}")
                print(f"   Diff:     {jsondiff.diff(original, duplicate)}")
        
     
        
    
    print(f"Total unique keys generated: {len(_generated_keys)}")
    print(f"Total tests processed: {len(results)}")
    
    # Count duplicates for final summary
    true_dup_count = len([x for x in _duplicate_keys if len(x) == 4 and x[3] == "identical"])
    key_conflict_count = len(_duplicate_keys) - true_dup_count
    print(f"Issues found: {len(_duplicate_keys)} (True duplicates: {true_dup_count}, Key conflicts: {key_conflict_count})")

    # ============================================
    # SELF-COMPARISON VALIDATION
    # ============================================
    print("\n=== SELF-COMPARISON VALIDATION ===")
    self_comparison_errors = 0
    json_to_binary_comparisons = 0
    json_to_json_only_comparisons = 0
    
    # 1. Compare JSON image hash with binary image hash
    print("\nComparing JSON vs Binary image hashes...")
    for key in results:
        if key.endswith('.json') and 'vssx' not in key:
            json_result = results[key]
            if isinstance(json_result, dict) and 'data' in json_result:
                json_data = json_result['data']
                if isinstance(json_data, dict) and 'image' in json_data:
                    # Get base key by removing extension
                    base_key = key.rsplit('.', 1)[0]
                    png_key = base_key + '.png'
                    
                    if png_key in results:
                        png_result = results[png_key]
                        if isinstance(png_result, dict) and 'hash' in png_result:
                            json_to_binary_comparisons += 1
                            json_image_hash = json_data['image']
                            png_hash = png_result['hash']
                            if json_image_hash != png_hash:
                                self_comparison_errors += 1
                                print(f"  ERROR: Image hash mismatch for {key[:50]}...")
                                print(f"    JSON hash: {json_image_hash}")
                                print(f"    PNG hash:  {png_hash}")
    
    print(f"  Compared {json_to_binary_comparisons} JSON/Binary pairs, {self_comparison_errors} errors")
    
    # 2. Compare json vs json_only (excluding image fields)
    print("\nComparing JSON vs JSON_only outputs...")
    json_only_errors = 0
    for key in results:
        if key.endswith('.json_only') and 'vssx' not in key:
            json_only_result = results[key]
            # Find corresponding json key - same base with .json extension
            base_key = key.rsplit('.', 1)[0]
            json_key = base_key + '.json'
            
            if json_key in results:
                json_to_json_only_comparisons += 1
                
                # Extract data from both results
                json_only_data = json_only_result.get('data', json_only_result) if isinstance(json_only_result, dict) else json_only_result
                json_data = results[json_key].get('data', results[json_key]) if isinstance(results[json_key], dict) else results[json_key]
                
                if isinstance(json_only_data, dict) and isinstance(json_data, dict):
                    # Compare excluding specific keys (including path which can vary between output types)
                    ignore_keys = ['execution_duration', 'image', 'image_mib', 'params', 'json_only', 'json', 'image_type', 'path']
                    
                    json_only_filtered = {k: v for k, v in json_only_data.items() if k not in ignore_keys}
                    json_filtered = {k: v for k, v in json_data.items() if k not in ignore_keys}
                    
                    diff = jsondiff.diff(json_only_filtered, json_filtered)
                    if diff:
                        json_only_errors += 1
                        print(f"  ERROR: JSON vs JSON_only mismatch for {key[:50]}...")
                        print(f"    Differences: {str(diff)[:100]}")
    
    print(f"  Compared {json_to_json_only_comparisons} JSON/JSON_only pairs, {json_only_errors} errors")
    self_comparison_errors += json_only_errors
    
    print(f"\n=== SELF-COMPARISON SUMMARY ===")
    print(f"Total self-comparison errors: {self_comparison_errors}")
    print(f"JSON to Binary comparisons: {json_to_binary_comparisons}")
    print(f"JSON to JSON_only comparisons: {json_to_json_only_comparisons}")
    
    print(f"\n=== TEST COMPLETE ===")
    print(f"For external validation against previous runs, use:")
    print(f"  python test_compare.py {output_filename} --validation test_validation.json")


def main(args):
    if args.testtype == 'all':
        test_all(args)
    else:
        test_lambda(more_tests[0], 'tmp')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('testtype', choices=['all', 'lambda'], default='all',
                        nargs='?',
                        help="Test all options, or test through lamdba entry")
    parser.add_argument('-t', type=int, help="number of threads", default=8)
    parser.add_argument('--limit', type=int, help="limit the total number of tests to run")
    parser.add_argument('--git-state', dest='git_state', type=str, 
                        help="Override git state (e.g., commit hash like '9fc053a')")
    main(parser.parse_args())
