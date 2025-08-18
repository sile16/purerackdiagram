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


# Initialize logger with default WARN level (will be updated by setup_logging)
logger = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
logger.addHandler(ch)
logger.setLevel(logging.WARN)

def setup_logging(debug_level):
    """Setup logging based on debug level argument"""
    # Map string levels to logging constants
    level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'warn': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    # Convert to lowercase and get logging level
    level = level_map.get(debug_level.lower(), logging.WARNING)
    
    # Update existing logger and handler
    logger.setLevel(level)
    ch.setLevel(level)
    
    # Set format based on level
    if level <= logging.DEBUG:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    ch.setFormatter(formatter)
    
    logger.info(f"Logging level set to: {debug_level.upper()}")


def clear_image_cache():
    """Clear the global image cache to prevent state leakage between tests"""
    from purerackdiagram.utils import cache
    cache_size_before = len(cache)
    cache.clear()
    logger.debug(f"Cleared image cache: {cache_size_before} items -> {len(cache)} items")

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

def download_image(url):
    """Download image content from URL and return raw bytes."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.content
    except requests.RequestException as e:
        logger.error(f"Failed to download image from {url}: {e}")
        return None
    
def hash_image(image_data):
    """Hash the raw image bytes and return SHA256 hash."""
    if image_data is None:
        # Return hash of empty bytes as fallback
        h = hashlib.sha256()
        h.update(b'')
        return h.hexdigest()
    
    h = hashlib.sha256()
    h.update(image_data)
    return h.hexdigest()
    
def download_and_hash_image(url):
    """Download image content from URL and return SHA256 hash of raw bytes."""
    image_content = download_image(url)
    return hash_image(image_content)
        


def test_lambda(params, outputfile ):
    """
    Run lambda test and save output files.
    
    Args:
        params: Test parameters
        outputfile: Base path for output file (without extension)
        git_state: Git commit hash or 'head' (if None, will be determined)
    """

    
    results = lambdaentry.handler(params, None)
    results['json'] = False  # Not a JSON response
    results['params'] = params['queryStringParameters'].copy()  # Copy original parameters

    # If statusCode is 302, follow the redirect
    if results['statusCode'] == 302:
        location = results['headers']['Location']
        response = requests.get(location)
        content_type = response.headers.get('Content-Type')
        logger.info(f"Redirected to {location} with content type {content_type}")
        
        # Update the body and headers of the results to hide the redirect
        results['body'] = base64.b64encode(response.content).decode('utf-8')
        results['headers']['Content-Type'] = content_type
        results['statusCode'] = response.status_code  # Update status code to OK


    image_type = "file"
    file_extension = ".png"  # Default to PNG for image files
    full_file_path = outputfile
    if results['headers'].get("Content-Type") == 'image/png':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            image_type = "png"
            full_file_path += file_extension
            with open(full_file_path, 'wb') as outfile:
                outfile.write(img_str)
            
            #hash image
            
            results['hash'] = hash_image(img_str)  # Add hash to results
            results['image_type'] = image_type  # Add image type to results
            

    elif results['headers'].get("Content-Type") == 'application/vnd.ms-visio.stencil':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            file_extension = '.vssx'  # Set extension for VSSX files
            full_file_path += file_extension
            with open(full_file_path, 'wb') as outfile:
                outfile.write(img_str)

    elif results['headers'].get("Content-Type") == 'application/zip':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            file_extension = '.zip'  # Set extension for ZIP files
            full_file_path += file_extension
            with open(full_file_path, 'wb') as outfile:
                outfile.write(img_str)

    elif results['headers'].get("Content-Type") == 'application/json':
        obj = json.loads(results['body'])
        
        # Create a modified version with hashed image for both disk storage and results
        result_obj = obj.copy()
        image_type = result_obj['image_type']
        results['json'] = True
        
        if result_obj.get('image_type') == 'link' or str(result_obj.get('image','')).startswith(('http://', 'https://')):
            # Image is a URL - download and hash the content
            logger.info(f"Downloading image from URL: {result_obj['image']}")
            img_bytes = download_image(result_obj['image'])
            result_obj['image'] = base64.b64encode(img_bytes).decode('utf-8')  # Store base64 encoded image
            
            
            result_obj['image_type'] = "png"  # Remove raw image data
            image_type = "png"  # Set image type to json


        if image_type == "png":
            img_bytes = base64.b64decode(result_obj['image'].encode('utf-8'))
            results['hash'] = hash_image(img_bytes)  # Add hash of image

        # Save the hashed version to disk with correct extension
        jo = ""
        file_extension = '.json'
        if image_type == "json_only":
            file_extension = '.json'
            jo = "_jo"

        # check if file exists and create unique name if needed:
        full_file_path +=  jo + file_extension
        original_path = full_file_path
        counter = 1
        while os.path.exists(full_file_path):
            logger.warning(f"File already exists: {original_path}")
            # Create new filename with counter
            base_path = original_path.rsplit('.', 1)[0]  # Remove extension
            extension = original_path.rsplit('.', 1)[1] if '.' in original_path else ''
            full_file_path = f"{base_path}_dup{counter}.{extension}" if extension else f"{base_path}_dup{counter}"
            counter += 1
        
        if full_file_path != original_path:
            logger.info(f"Writing to unique filename: {full_file_path}")
            
        with open(full_file_path, 'w',  encoding='utf-8') as outfile:
            json.dump(result_obj, outfile, indent=4, ensure_ascii=False)

        results['body'] = result_obj  # Use the modified version with hash for results

    results['image_type'] = image_type  # Add image type to results
    results['key'] = outputfile
    results['file_extension'] = file_extension  # Add file extension to results
    results['path'] = full_file_path  # Add path to results
    category = results.get('image_type')
    if image_type == "json_only":
        category = "json_only"
    elif results['json']:
        category = "json"
    else:
        category = results['image_type']  # Default to image type
    results['category'] = category  # Add category to results
    return results


# Now define the new create_test_image function
# Global set to track all generated keys for duplicate detection
_generated_keys = {}  # Change to dict to store both key and item
_duplicate_keys = []

def encode_jsonurl_to_filename(s):
    return (
        s.replace('~', '~~')
         .replace('%', '~p')
         .replace(':', '~c')
         .replace('/', '~s')
    )

def create_test_image(item, count, total, save_dir):
    """
    Create test image with git-state based directory structure.
    
    Args:
        item: Test parameters
        count: Current test number
        total: Total number of tests
        save_dir: Directory name for saving results
    """

    import hashlib  # Import needed for multiprocessing
    
    # Create git-state based subdirectory
    clear_image_cache() 
    folder = os.path.join("test_results", save_dir)
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    file_name_parts = ['t']
    for n in item:
        n = str(n).lower()
        # Skip json and json_only parameters in filename generation
        if n in ['json', 'json_only']:
            continue
        value = item[n]

        if n == 'datapacks':
            value = f"_{str(item[n]).replace('/', '-')}"
        elif n == 'datapacksv2' or n == 'bladesv2':
            value = encode_jsonurl_to_filename(str(item[n]))
     
        file_name_parts.append(f"_{n}-{value}")
    
    # Join all parts to create the base filename
    file_name_base = ''.join(file_name_parts)
    
    # Add a hash of the case-sensitive filename to handle case-insensitive filesystems
    # This ensures fa-c70r4b and fa-C70R4b create different files
    case_hash = hashlib.md5(file_name_base.encode()).hexdigest()[:10]
    # Check filename length against OS limits
    max_filename_length = 150  # Common filesystem limit

    # Create the full filename with extension - this will be our result key
    key = file_name_base[:(max_filename_length - 10)] + f"_{case_hash}"
    
    try:
        # Use base filename (without extension) for the actual file output
        results = test_lambda({"queryStringParameters":item}, os.path.join(folder, key))

        status_code = results.get('statusCode', 999999)  # Default to 200 if not set
        # For successful responses or errors that aren't in JSON format
        print(f"{count} of {total}   {key} - Status: {status_code}")

        return(results)

    except Exception as ex_unknown:
        print(f"Caught exception in image: {key}")
        traceback.print_exc()
        return({
            "status": 500,
            "error": str(ex_unknown),
            "traceback": traceback.format_exc(),
            "path": f"{save_dir}/{key}",
            "params": item,
            "key": key,
            "category": "other",
        })

    


def get_all_tests():
    models = global_config['pci_config_lookup']
    dps = ['45/45-31/63-45-24.0', '3/127-24.0-45']

    valid_chassis_dps = list(global_config['chassis_dp_size_lookup'].keys())
    valid_shelf_dps = list(global_config['shelf_dp_size_lookup'].keys())

    # get the keys of diction csize_lookup
    csizes = list(global_config['csize_lookup'].keys())


    count = 0

    for test in more_tests:
        #if not test['queryStringParameters'].get('json'):
        #    continue
        json_test = test['queryStringParameters']
        yield json_test
        count += 1

        if 'json' not in json_test:
            json_test = json_test.copy()
            json_test['json'] = "True"
            yield json_test

        if 'json_only' not in json_test:
            #json onlytest
            json_test = json_test.copy()
            json_test['json_only'] = "True"
            yield json_test

        
    for json_test in [None,"json","json_only"]:
        for cg in ['1', '2']:
            for model in ['x50r4', 'c50r4', 'c20', 'c50r4b', 'x50r4b', 'er1', 'er1b']:
                    params = {"model": f"fa-{model}",
                                "datapacks": "0",
                                "face": "front",
                                'chassi_gen': cg,
                                "fm_label": "True",
                                "dp_label": "True"}
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
                            "fm_label": "True",
                            "dp_label": "True",
                            "csize": '984'}
                if json_test is not None:
                    params[json_test] = "True"
                
                yield params
            else:
                for dp in dps:
                    count += 1
                    params = {"model": model,
                                "fm_label": "True",
                                "dp_label": "True",
                                "datapacks": dp}
                    if json_test is not None:
                        params[json_test] = "True"
                    
                    yield params

            # The bezel.
            params = {"model": model,
                        "fm_label": "True",
                        "dp_label": "True",
                        "bezel": "True",
                        "datapacks": '366'}
            if json_test is not None:
                params[json_test] = "True"
            
            yield params

        for csize in csizes:
            count += 1
            params = {"model": 'fa-c60',
                        "fm_label": "True",
                        "dp_label": "True",
                        "csize": csize}
            if json_test is not None:
                params[json_test] = "True"
            
            yield params
        
        #Test all Datapacks on the front.
        for dp in valid_chassis_dps:
            count += 1
            params = {"model": "fa-x70r1",
                        "fm_label": "True",
                        "dp_label": "True",
                        "datapacks": dp}
            if json_test is not None:
                params[json_test] = "True"
            
            yield params

        for dp in valid_shelf_dps:
            count += 1
            params = {"model": "fa-x70r4",
                        "fm_label": "True",
                        "dp_label": "True",
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
                            "ports": "True"}
                if json_test is not None:
                    params[json_test] = "True"
                
                count += 1
                yield params

            else:
                params = {"model": model,
                            "datapacks": "63-24.0-45",
                            "addoncards": '4fc',
                            "face": "back",
                            "ports": "True"}
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
                            "ports": "True"}
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
                                "ports": "True"}
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
        head_dir = os.path.join("test_results", save_dir)
        if os.path.exists(head_dir):
            print(f"Automatically clearing head directory: {head_dir}")
            shutil.rmtree(head_dir)
        if os.path.exists(results_json_file):
            print(f"Automatically removing head results file: {results_json_file}")
            os.remove(results_json_file)
    else:
        # Ask user for confirmation before deleting other git-state directories
        state_dir = os.path.join("test_results", save_dir)
        if os.path.exists(state_dir) or os.path.exists(results_json_file):
            print(f"Directory {state_dir} or results file {results_json_file} already exists.")
            response = input(f"Do you want to overwrite the existing data for git-state '{git_state}'? (y/N): ")
            if response.lower() in ['y', 'yes']:
                if os.path.exists(state_dir):
                    print(f"Removing directory: {state_dir}")
                    shutil.rmtree(state_dir)
                if os.path.exists(results_json_file):
                    print(f"Removing results file: {results_json_file}")
                    os.remove(results_json_file)
            else:
                print("Aborting test run to avoid overwriting existing data.")
                return

    # Create amultiprocessing pool
    pool = Pool(processes=args.t)
    futures = []
    total_count = 0

    all_items = list(get_all_tests())

    #applly filter
    if args.filter:
        filter_text = args.filter.lower()
        all_items = [item for item in all_items if filter_text in json.dumps(item).lower()]
        print(f"Filtered {len(all_items)} items matching '{filter_text}'")
    
    
    if args.limit is not None:
        all_items = all_items[:args.limit]

    count = 0
    
    for item in all_items:
        futures.append(pool.apply_async(create_test_image, args=(item, count, len(all_items), save_dir)))
        count += 1

    pool.close()
    pool.join()

    results = {"png":{}, "json": {}, "json_only": {}, "other": {}, "file": {}}
    duplicate = 0
    duplicate_errors = 0
    key_count = 0

    json_only_errors = 0
    json_keys_matched = 0

    def compare_json_only_to_json(json_only_obj, json_obj):
        nonlocal json_only_errors, json_keys_matched
        try:
            with open(json_only_obj['path'], 'r', encoding='utf-8') as f:
                json_only_data = json.load(f)
            with open(json_obj['path'], 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            if isinstance(json_only_data, dict) and isinstance(json_data, dict):
                # Compare excluding specific keys (including path which can vary between output types)
                ignore_keys = ['execution_duration', 'image', 'image_mib', 'params', 'json_only', 'json', 'image_type', 'path', 'hash']
                
                json_only_filtered = {k: v for k, v in json_only_data.items() if k not in ignore_keys}
                json_filtered = {k: v for k, v in json_data.items() if k not in ignore_keys}
                
                diff = jsondiff.diff(json_only_filtered, json_filtered)
                if diff:
                    json_only_errors += 1
                    print(f"  ERROR: JSON vs JSON_only mismatch for {key[:50]}...")
                    print(f"    Differences: {str(diff)[:100]}")
                    return diff
                else:
                    json_keys_matched += 1
                    return diff

        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  WARNING: Could not compare {key}: {e}")
            print(f"    Paths: {json_only_obj['path']} vs {json_obj['path']}")




    for f in futures:
        result = f.get()
        category = result['category']
        key = result['key']
        
        if key in results[category]:
            if 'hash' in result and 'hash' in results[category][key]:
                if results[category][key]['hash'] != result['hash']:
                    # If the key already exists but hashes differ, it's a duplicate
                    duplicate_errors += 1
                    print(f"ERROR Duplicate key found: {key} with different hashes")
                else:
                    duplicate += 1
                    #print(f"Info Duplicate key found: {key} with identical hashes")
            elif ('hash' in result and 'hash' not in results[category][key]) or \
                     ('hash' not in result and 'hash' in results[category][key]):
                     print(f"ERROR: Duplicate key found without hash comparison: {key}")
                     
            else:
                diff = compare_json_only_to_json(result, results[category][key])
                if diff:
                    print(f"ERROR: Duplicate key found with differences: {key}")
                    duplicate_errors += 1
                else:
                    duplicate += 1
                    print(f"Info Duplicate key found with no differences: {key}")

        else:
            results[category][key] = result
            key_count += 1

    

    # Create git-state subdirectory and save results there
    
    output_filename = os.path.join("test_results", f"test_{git_state}.json")
    with open(output_filename, "w") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print(f"Results saved to: {output_filename}")
    
    print(f"Total unique keys generated: {key_count}")
    print(f"Total duplicate keys processed: {duplicate + duplicate_errors}")
    
    # Count duplicates for final summary
    
    print(f"Duplicate ERORRs found: {duplicate_errors}")

    # ============================================
    # SELF-COMPARISON VALIDATION
    # ============================================
    print("\n=== SELF-COMPARISON VALIDATION ===")
    
    json_to_binary_comparisons = 0
    json_to_binary_errors = 0
    

    def compare_json_to_png(json_obj, png_obj):
        nonlocal json_to_binary_errors, json_to_binary_comparisons
        if json_obj['statusCode'] != 200:
            if json_obj['statusCode'] != png_obj['statusCode']:
                print(f"ERROR: Status code mismatch for key {json_obj['key']}")
                json_to_binary_errors += 1
                return
            
        elif json_obj['hash'] != png_obj['hash']:
            print(f"ERROR: Hash mismatch for key {json_obj['key']}")
            json_to_binary_errors += 1
            return
        json_to_binary_comparisons += 1

    
    # 1. Compare JSON image hash with binary image hash
    print("\nComparing JSON vs Binary image hashes...")
    processed_keys = set()  # Track processed keys to avoid duplicates
    for key in results['json']:
        if key in results['png']:
            compare_json_to_png(results['json'][key], results['png'][key])
            processed_keys.add(key)
    
    for key in results['png']:
        if key not in processed_keys and key in results['json']:
            compare_json_to_png(results['json'][key], results['png'][key])
            processed_keys.add(key)
    
    # 2. Compare json vs json_only (excluding image fields)
    print("\nComparing JSON vs JSON_only outputs...")
    
        
    processed_keys = set()
    for key in results['json']:
        if key in results['json_only']:
            compare_json_only_to_json(results['json_only'][key], results['json'][key])
            processed_keys.add(key)
        #else:
        #    print(f"  WARNING: JSON key {key} not found in JSON_only results")
    
    for key in results['json_only']:
        if key not in processed_keys:
            if key in results['json']:
                compare_json_only_to_json(results['json_only'][key], results['json'][key])
            #else:
            #    print(f"  WARNING: JSON_only key {key} not found in JSON results")

    
    
    
    print(f"\n=== SELF-COMPARISON SUMMARY ===")
    
    print(f"JSON to Binary comparisons: {json_to_binary_comparisons}")
    print(f"JSON to JSON_only comparisons: {json_keys_matched}")

    print(f"JSON to Binary errors: {json_to_binary_errors}")
    print(f"JSON to JSON_only errors: {json_only_errors}")
    
    print(f"\n=== TEST COMPLETE ===")
    print(f"For external validation against previous runs, use:")
    print(f"  python test_compare.py {output_filename} --validation test_validation.json")


def main(args):
    if args.testtype == 'all':
        test_all(args)
    else:
        all_items = list(get_all_tests())
        print(f"Running single test at index {args.index} of {len(all_items)}")    
        create_test_image(all_items[args.index], 0, 1, '')
        
        


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('testtype', choices=['all', 'lambda'], default='all',
                        nargs='?',
                        help="Test all options, or test through lamdba entry")
    parser.add_argument('-t', type=int, help="number of threads", default=8)
    parser.add_argument('-i', '--index', type=int, help="Index of the test to run (0-based)", default=0)
    parser.add_argument('--limit', type=int, help="limit the total number of tests to run")
    parser.add_argument('--git-state', dest='git_state', type=str, 
                        help="Override git state (e.g., commit hash like '9fc053a')")
    parser.add_argument('--debug-level', dest='debug_level', type=str, default='warning',
                        choices=['debug', 'info', 'warning', 'warn', 'error', 'critical'],
                        help="Set logging level (default: warning)")
    parser.add_argument('--filter', dest='filter', type=str, 
                        help="Filter tests by key name - only run tests whose key contains this text")
    
    args = parser.parse_args()
    
    # Setup logging based on debug level argument
    setup_logging(args.debug_level)
    
    main(args)
