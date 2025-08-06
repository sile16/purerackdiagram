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

try:
    import jsonurl_py as jsonurl
except ImportError:
    # For older commits that don't have jsonurl_py
    jsonurl = None
    
try:
    from test_one_offs import more_tests
except ImportError:
    # For older commits that don't have test_one_offs
    more_tests = []
import subprocess
import datetime
import shutil


logger = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
logger.addHandler(ch)
logger.setLevel(logging.WARN)

save_dir = 'test_results/'


def get_file_hash(file_path):
    """Get SHA256 hash of a file"""
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def manage_file_history(test_key, source_file_path, git_state):
    """
    Manage file history with deduplication and 3-generation history.
    
    Args:
        test_key: The test key/name
        source_file_path: Path to the newly generated file
        git_state: Current git state
        
    Returns:
        dict: Information about file placement and deduplication
    """
    if not os.path.exists(source_file_path):
        return {'status': 'error', 'message': 'Source file not found'}
    
    # Get file extension
    file_ext = os.path.splitext(source_file_path)[1]
    
    # Calculate hash of the new file
    new_hash = get_file_hash(source_file_path)
    
    # Create git-state directory structure
    git_dir = os.path.join(save_dir, git_state)
    if not os.path.exists(git_dir):
        os.makedirs(git_dir)
    
    # Look for existing files with the same hash across all git states
    existing_file = None
    duplicate_info = {'is_duplicate': False, 'original_path': None, 'original_git_state': None}
    
    # Search all git state directories for duplicates
    for state_dir in os.listdir(save_dir):
        state_path = os.path.join(save_dir, state_dir)
        if not os.path.isdir(state_path):
            continue
            
        # Look for files with the same test_key
        potential_matches = []
        for filename in os.listdir(state_path):
            if filename.startswith(test_key) and filename.endswith(file_ext):
                potential_matches.append(os.path.join(state_path, filename))
        
        # Check hashes of potential matches
        for match_path in potential_matches:
            try:
                if get_file_hash(match_path) == new_hash:
                    existing_file = match_path
                    duplicate_info = {
                        'is_duplicate': True,
                        'original_path': match_path,
                        'original_git_state': state_dir
                    }
                    break
            except (IOError, OSError):
                continue
                
        if existing_file:
            break
    
    final_path = os.path.join(git_dir, f"{test_key}{file_ext}")
    
    if existing_file and duplicate_info['is_duplicate']:
        # File is a duplicate - create a symlink instead of copying
        if not os.path.exists(final_path):
            try:
                # Create relative symlink
                rel_path = os.path.relpath(existing_file, git_dir)
                os.symlink(rel_path, final_path)
                logger.info(f"Created symlink for duplicate: {test_key} -> {duplicate_info['original_git_state']}")
            except OSError:
                # Fallback to copy if symlinks not supported
                shutil.copy2(existing_file, final_path)
                logger.info(f"Copied duplicate (symlink failed): {test_key} -> {duplicate_info['original_git_state']}")
        
        return {
            'status': 'duplicate',
            'final_path': final_path,
            'hash': new_hash,
            'duplicate_info': duplicate_info
        }
    else:
        # File is unique - copy it and manage history
        shutil.copy2(source_file_path, final_path)
        
        # Manage 3-generation history for this test across all git states
        manage_test_history(test_key, file_ext)
        
        return {
            'status': 'unique',
            'final_path': final_path,
            'hash': new_hash,
            'duplicate_info': duplicate_info
        }


def manage_test_history(test_key, file_ext):
    """
    Keep only the last 3 generations of a specific test across all git states.
    This helps prevent disk space from growing infinitely.
    """
    # Find all instances of this test across git states
    test_instances = []
    
    for state_dir in os.listdir(save_dir):
        state_path = os.path.join(save_dir, state_dir)
        if not os.path.isdir(state_path):
            continue
            
        for filename in os.listdir(state_path):
            if filename.startswith(test_key) and filename.endswith(file_ext):
                file_path = os.path.join(state_path, filename)
                try:
                    stat = os.stat(file_path)
                    test_instances.append({
                        'path': file_path,
                        'git_state': state_dir,
                        'mtime': stat.st_mtime,
                        'is_symlink': os.path.islink(file_path)
                    })
                except (IOError, OSError):
                    continue
    
    # Sort by modification time (newest first)
    test_instances.sort(key=lambda x: x['mtime'], reverse=True)
    
    # Keep only the 3 most recent, delete the rest
    instances_to_delete = test_instances[3:]  # Everything after the first 3
    
    for instance in instances_to_delete:
        try:
            if instance['is_symlink']:
                os.unlink(instance['path'])  # Remove symlink
            else:
                os.remove(instance['path'])  # Remove actual file
            logger.info(f"Removed old test instance: {instance['path']}")
        except (IOError, OSError) as e:
            logger.warning(f"Failed to remove old test instance {instance['path']}: {e}")


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


def get_git_state():
    """Get current git commit hash or 'head' if there are uncommitted changes."""
    try:
        # Check if there are any uncommitted changes
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        has_changes = bool(result.stdout.strip())
        
        # Get current commit hash
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        commit_hash = result.stdout.strip()
        
        if has_changes:
            return 'head'
        else:
            return commit_hash
    except subprocess.CalledProcessError:
        # Not a git repo or git not available
        return f'nogit_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'


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


def test_lambda(params, outputfile, git_state=None):
    """
    Run lambda test and save output files.
    
    Args:
        params: Test parameters
        outputfile: Base path for output file (without extension)
        git_state: Git commit hash or 'head' (if None, will be determined)
    """
    if git_state is None:
        git_state = get_git_state()
    
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
        
        # Save the response content to the appropriate file
        #if content_type == 'image/png':
        #    ext = '.png'
        #elif content_type == 'application/vnd.ms-visio.stencil':
        #    ext = '.vssx'
        #elif content_type == 'application/json':
        #    ext = '.json'
        #else:
        #    ext = ''
        
        #with open(outputfile + ext, 'wb') as outfile:
        #    outfile.write(response.content)

    
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
            if 'image' in obj and obj['image'] is not None:
                # Replace image data with SHA256 hash
                if obj.get('image_type') == 'link' or obj['image'].startswith(('http://', 'https://')):
                    # Image is a URL - download and hash the content
                    logger.info(f"Downloading image from URL: {obj['image']}")
                    obj['image'] = download_and_hash_image(obj['image'])
                else:
                    # Image is base64 data - decode and hash
                    h = hashlib.sha256()
                    try:
                        decoded_image = base64.b64decode(obj['image'])
                    except (TypeError, ValueError) as e:
                        logger.error(f"Failed to decode image data: {e}")
                        decoded_image = b''
                    h.update(decoded_image)
                    obj['image'] = h.hexdigest()
            else:
                if 'json_only' not in params['queryStringParameters'] and results['statusCode'] == 200:
                    # If no image data, just use the original body
                    print("No image data found in JSON response")

            results['body'] = obj

            with open(outputfile + '.json', 'w',  encoding='utf-8') as outfile:
                json.dump(obj, outfile, indent=4, ensure_ascii=False)
            #del results['body']

    return results


def create_test_image_original(item, count, total):
    """Original function, kept for reference"""
    
    folder = "test_results"
    file_name = f"{item['model']}"
    for n in ['face', 'bezel', 'mezz', 'fm_label', 'dp_label', 'addoncards', 'ports', 'csize', 'datapacks',  
    'no_of_chassis', 'no_of_blades', 'efm', 'direction', 'drive_size', 'no_of_drives_per_blade', 'vssx', 'json', 'chassis_gen' ]:
        if n in item:
            if n == 'datapacks':
                file_name += f"_{str(item[n]).replace('/', '-')}"
            else:
                file_name += f"_{n}-{item[n]}"
    

# Now define the new create_test_image function
# Global set to track all generated keys for duplicate detection
_generated_keys = {}  # Change to dict to store both key and item
_duplicate_keys = []

def create_test_image(item, count, total, git_state=None):
    """
    Create test image with git-state based directory structure.
    
    Args:
        item: Test parameters
        count: Current test number
        total: Total number of tests
        git_state: Git commit hash or 'head' (if None, will be determined)
    """
    if git_state is None:
        git_state = get_git_state()
    
    # Create git-state based subdirectory
    folder = os.path.join("test_results", git_state)
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Build the complete file_name first to compute its hash
    file_name_parts = [item['model']]
    for n in ['face', 'bezel', 'mezz', 'fm_label', 'dp_label', 'addoncards', 'ports', 'csize', 'datapacks',  
    'no_of_chassis', 'no_of_blades', 'efm', 'direction', 'drive_size', 'no_of_drives_per_blade', 'vssx', 'json', 
    'chassis_gen', 'json_only', 'datapacksv2', 'bladesv2', 'protocol', 'chassis', 'dc_power', 'individual',
    'jsononly', 'pci0', 'pci1', 'pci2', 'pci3', 'pci4', 'pci5', 'local_delay', 'chassi_gen', 
    'blades', 'dfm_label' ]:
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
                if isinstance(value, bool):
                    file_name_parts.append(f"_{n}-bool_{value}")
                elif isinstance(value, str):
                    file_name_parts.append(f"_{n}-str_{value}")
                else:
                    file_name_parts.append(f"_{n}-{type(value).__name__}_{value}")
    
    # Join all parts to create the base filename
    file_name_base = ''.join(file_name_parts)
    
    # Add a hash of the case-sensitive filename to handle case-insensitive filesystems
    # This ensures fa-c70r4b and fa-C70R4b create different files
    case_hash = hashlib.md5(file_name_base.encode()).hexdigest()[:6]
    file_name = f"{file_name_base}_{case_hash}"
    
    # Check filename length against OS limits
    # Most filesystems support 255 bytes for filename, but we need to account for:
    # - The folder path length
    # - The file extension (.png, .json, etc.)
    # - Safety margin
    max_filename_length = 255  # Common filesystem limit
    folder = os.path.join("test_results", git_state)
    extension = ".json"  # Longest extension we use
    full_path_est = os.path.join(folder, file_name + extension)
    
    if len(file_name) > max_filename_length - len(extension) - 10:  # 10 byte safety margin
        logger.warning(f"Filename approaching OS limit ({len(file_name)} chars): {file_name[:50]}...")
        # Truncate and add hash to ensure uniqueness
        truncate_at = max_filename_length - len(extension) - 20  # Leave room for hash
        file_name_hash = hashlib.sha256(file_name.encode('utf-8')).hexdigest()[:8]
        file_name = file_name[:truncate_at] + "_" + file_name_hash
        logger.info(f"Truncated to: {file_name}")
    
    # Check for duplicate keys and compare with json_diff
    if file_name in _generated_keys:
        # Use json_diff to check if items are truly identical
        original_item = _generated_keys[file_name]
        diff = jsondiff.diff(original_item, item)
        
        if not diff:
            # Truly identical - this is a real duplicate
            print(f"TRUE DUPLICATE DETECTED: {file_name}")
            print(f"  Items are identical: {item}")
            _duplicate_keys.append((file_name, original_item, item, "identical"))
        else:
            # Different items with same key - key generation needs improvement
            print(f"KEY CONFLICT DETECTED: {file_name}")
            print(f"  Original item: {original_item}")
            print(f"  Current item:  {item}")
            print(f"  Differences:   {diff}")
            _duplicate_keys.append((file_name, original_item, item, "different"))
    else:
        # Store a deep copy to prevent modification by lambda function
        _generated_keys[file_name] = copy.deepcopy(item)

    try:
        results = test_lambda({"queryStringParameters":item}, os.path.join(folder, file_name), git_state)

        h = hashlib.sha256()
        content_type = results['headers'].get("Content-Type")
        status_code = results['statusCode']

        # Check for error responses (4xx, 5xx)
        if 400 <= status_code < 600:
            print(f"{count} of {total}   {file_name} - ERROR {status_code}")
            
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
                    return({file_name: {
                        "status": status_code,
                        "error_type": error_type,
                        "error_msg": error_msg,
                        "path": f"{git_state}/{file_name}",
                        "git_state": git_state
                    }})
                except json.JSONDecodeError:
                    print(f"  Failed to parse error JSON")
                    return({file_name: {
                        "status": status_code,
                        "error": "Failed to parse error JSON",
                        "path": f"{git_state}/{file_name}",
                        "git_state": git_state
                    }})
        
        # For successful responses or errors that aren't in JSON format
        print(f"{count} of {total}   {file_name} - Status: {status_code}")
        
        # Prepare result with path information
        result_data = {
            'path': f"{git_state}/{file_name}",
            'git_state': git_state
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
        
        return({file_name: result_data})

    except Exception as ex_unknown:
        print(f"Caught exception in image: {file_name}")
        traceback.print_exc()
        return({file_name: {
            "status": 500,
            "error": str(ex_unknown),
            "traceback": traceback.format_exc(),
            "path": f"{git_state}/{file_name}",
            "git_state": git_state
        }})

#    if "fa-er1-f" in item['model'] :
#        pass

    # Original implementation replaced by the new create_test_image function above

    


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
    
    #return count
        
        




        
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

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Get git state - use override if provided, otherwise default to "head"
    if hasattr(args, 'git_state') and args.git_state:
        git_state = args.git_state
        print(f"Using specified git state: {git_state}")
    else:
        git_state = "head"
        print(f"Using default git state: {git_state}")

    # Create amultiprocessing pool
    pool = Pool(processes=args.t)
    futures = []
    total_count = 0

    all_items = list(get_all_tests())
    if args.limit is not None:
        all_items = all_items[:args.limit]
    count = 0
    for item in all_items:
        futures.append(pool.apply_async(create_test_image, args=(item, count, len(all_items), git_state)))
        count += 1

    pool.close()
    pool.join()

    results = {}

    for f in futures:
        result = f.get()
        results.update(result)

    # Create git-state subdirectory and save results there
    git_dir = f"test_results/{git_state}/"
    os.makedirs(git_dir, exist_ok=True)
    output_filename = f"{git_dir}test_results_{git_state}.json"
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
        
        # Save detailed report
        with open("duplicate_keys_report.json", "w") as f:
            json.dump({
                "total_issues": len(_duplicate_keys),
                "true_duplicates": len(true_duplicates),
                "key_conflicts": len(key_conflicts),
                "true_duplicate_details": [
                    {"key": key, "params": original} for key, original, duplicate in true_duplicates
                ],
                "key_conflict_details": [
                    {
                        "key": key, 
                        "original": original, 
                        "duplicate": duplicate,
                        "differences": jsondiff.diff(original, duplicate)
                    } for key, original, duplicate in key_conflicts
                ]
            }, f, indent=4, ensure_ascii=False)
        print(f"\nDetailed report saved to duplicate_keys_report.json")
    
    print(f"Total unique keys generated: {len(_generated_keys)}")
    print(f"Total tests processed: {len(results)}")
    
    # Count duplicates for final summary
    true_dup_count = len([x for x in _duplicate_keys if len(x) == 4 and x[3] == "identical"])
    key_conflict_count = len(_duplicate_keys) - true_dup_count
    print(f"Issues found: {len(_duplicate_keys)} (True duplicates: {true_dup_count}, Key conflicts: {key_conflict_count})")

    with open("test_validation.json") as f:
        validation = json.load(f)

    errors = 0
    warnings = 0
    json_only_to_original = 0
    json_to_image_compare_count = 0
    for key, result_value in results.items():
        # Extract actual data/hash from new structure
        if isinstance(result_value, dict) and 'data' in result_value:
            result_compare = result_value['data']
        elif isinstance(result_value, dict) and 'hash' in result_value:
            result_compare = result_value['hash']
        elif isinstance(result_value, dict) and 'status' in result_value:
            # Error case
            result_compare = result_value
        else:
            result_compare = result_value
            
        if key not in validation:
            warnings += 1
            print("WARNING missing key:{}".format(key))
        elif 'vssx' in key:
            pass # always different because unique key
        elif 'json_only' in key:

            # Now lets compare to 
            
            ignore_keys = ['execution_duration']
                
            diff = True
            try:
                res_json = result_compare.copy() if isinstance(result_compare, dict) else result_compare
                val_json = validation[key].copy() if isinstance(validation[key], dict) else validation[key]
                for k in ignore_keys:
                    if k in res_json:
                        del res_json[k]
                    if k in val_json:
                        del val_json[k]
                diff = jsondiff.diff(val_json, res_json)
            except Exception as ex:
                pass
            
            if diff:
                errors += 1
                print("Error JSON Only Changed!!:{}".format(key))
                print(str(diff)[:100])

            
            original_json_key = key.replace("_json_only-True", "_json-True")

            if original_json_key not in validation:
                original_json_key = key.replace("_json_only-True", "")
                if original_json_key not in validation:
                    continue
            
            

            
            val_json = validation[original_json_key]
            if type(val_json) is str:
                continue # it's a hash value for an image not json
            json_only_to_original += 1

            ignore_keys = ['execution_duration', 'image', "image_mib", "params", "json_only", "json", "image_type"]
            
            for k in ignore_keys:
                if k in res_json:
                    del res_json[k]
                if k in val_json:
                    del val_json[k]

            

            diff = True
            diff = jsondiff.diff(val_json, res_json)
            if diff:
                errors += 1
                print("Error JSON_Only, vs JSON difference!!:{}".format(original_json_key))
                print(str(diff)[:100])


        elif 'json' in key:
            # use jsondiff to compare the two
            # load the two strings into json objects, results
            # compare json

            ignore_keys = [ 'execution_duration']
            
            diff = True
            try:
                res_json = result_compare.copy() if isinstance(result_compare, dict) else result_compare
                val_json = validation[key].copy() if isinstance(validation[key], dict) else validation[key]
                if isinstance(res_json, dict) and isinstance(val_json, dict):
                    for k in ignore_keys:
                        if k in res_json:
                            del res_json[k]
                        if k in val_json:
                            del val_json[k]
                diff = jsondiff.diff(val_json, res_json)
            except Exception as ex:
                pass

            if diff:
                # Check if this is a known non-deterministic case
                if 'individual-str_True' in key:
                    # JSON responses for individual mode may have non-deterministic metadata
                    print(f"Warning: Skipping non-deterministic individual mode JSON: {key}")
                    warnings += 1
                else:
                    errors += 1
                    print("Error JSON Changed!!:{}".format(key))
                    print(str(diff)[:100])
            
            # Compare JSON image hash with PNG image hash
            if isinstance(result_compare, dict) and 'image' in result_compare:
                # Get the non-JSON key by removing _json-True
                png_key = key.replace("_json-bool_True", "").replace("_json-str_True", "")
                if png_key == key:
                    print("Warning: PNG key not found for JSON key: {}".format(key))
                    continue
                
                if png_key in results:
                    # Extract PNG hash from result structure
                    png_result = results[png_key]
                    if isinstance(png_result, dict) and 'hash' in png_result:
                        png_hash = png_result['hash']
                    else:
                        png_hash = png_result
                    
                    json_image_hash = result_compare['image']

                    json_to_image_compare_count +=1
                    
                    if png_hash != json_image_hash:
                        errors += 1
                        print(f"Error: Image hash mismatch between JSON and PNG for {key}")
                        print(f"  JSON image hash: {json_image_hash}")
                        print(f"  PNG image hash:  {png_hash}")
            
            
        
        elif result_compare != validation[key]:
            # Check if this is a known non-deterministic case
            if 'individual-str_True' in key:
                # ZIP files with individual mode are non-deterministic due to timestamps
                print(f"Warning: Skipping non-deterministic ZIP file: {key}")
                warnings += 1
            else:
                errors += 1
                # Get the actual path from result_value if available
                if isinstance(result_value, dict) and 'path' in result_value:
                    file_path = os.path.join(save_dir, result_value['path'])
                else:
                    file_path = os.path.join(save_dir, git_state, key) + '.png'
                print(f"Error Image Changed!!: {key} (file://{os.path.abspath(file_path)})")
    print("Test Complete {} Errors Found {} Warning".format(errors, warnings))
    print("JSON Only to Original: {}".format(json_only_to_original))
    print("JSON to Image Compare Count: {}".format(json_to_image_compare_count))


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
    parser.add_argument('--limit', type=int, help="limit the total number of tests to run", default=None)
    parser.add_argument('--git-state', dest='git_state', type=str, 
                        help="Override git state (e.g., commit hash like '9fc053a')")
    main(parser.parse_args())
