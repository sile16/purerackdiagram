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

import lambdaentry
from purerackdiagram.utils import global_config

import jsonurl_py as jsonurl
from test_one_offs import more_tests


logger = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
logger.addHandler(ch)
logger.setLevel(logging.WARN)

save_dir = 'test_results/'


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


def test_lambda(params, outputfile):
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

def create_test_image(item, count, total):
    folder = "test_results"
    file_name = f"{item['model']}"
    for n in ['face', 'bezel', 'mezz', 'fm_label', 'dp_label', 'addoncards', 'ports', 'csize', 'datapacks',  
    'no_of_chassis', 'no_of_blades', 'efm', 'direction', 'drive_size', 'no_of_drives_per_blade', 'vssx', 'json', 
    'chassis_gen', 'json_only', 'datapacksv2', 'bladesv2', 'protocol', 'chassis', 'dc_power', 'individual',
    'jsononly', 'pci0', 'pci1', 'pci2', 'pci3', 'pci4', 'pci5', 'local_delay', 'chassi_gen', 
    'blades', 'dfm_label' ]:
        if n in item:
            if n == 'datapacks':
                file_name += f"_{str(item[n]).replace('/', '-')}"
            elif n == 'datapacksv2' or n == 'bladesv2':
                #sha256 hash the datapacksv2 value
                h = hashlib.sha256()
                h.update(item[n].encode('utf-8'))
                file_name += f"_{n}-{h.hexdigest()[:8]}"
            else:
                # Normalize boolean and numeric values for consistent keys
                value = item[n]
                if isinstance(value, bool):
                    # Convert boolean to string with type prefix
                    value = f"bool_{str(value)}"
                elif isinstance(value, str) and value.lower() in ['true', 'false']:
                    # String representations of boolean values
                    value = f"str_{value.lower().capitalize()}"
                elif isinstance(value, str) and value in ['TRUE', 'FALSE']:
                    # All caps string representations  
                    value = f"str_{value.lower().capitalize()}"
                elif value == 'True' or value == 'False':
                    # Exact string literals
                    value = f"str_{value}"
                else:
                    # All other values - include type info for better differentiation
                    value = f"{type(value).__name__}_{str(value)}"
                file_name += f"_{n}-{value}"
    
    # Check filename length against OS limits
    # Most filesystems support 255 bytes for filename, but we need to account for:
    # - The folder path length
    # - The file extension (.png, .json, etc.)
    # - Safety margin
    max_filename_length = 255  # Common filesystem limit
    folder = "test_results"
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
        _generated_keys[file_name] = item

    try:
        results = test_lambda({"queryStringParameters":item}, os.path.join(folder, file_name))

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
                        "error_msg": error_msg
                    }})
                except json.JSONDecodeError:
                    print(f"  Failed to parse error JSON")
                    return({file_name: {
                        "status": status_code,
                        "error": "Failed to parse error JSON"
                    }})
        
        # For successful responses or errors that aren't in JSON format
        print(f"{count} of {total}   {file_name} - Status: {status_code}")
        if content_type == 'application/json':
            return({file_name: results['body']})
        else:
            # For other content types (PNG, VSSX, ZIP), decode base64 and hash raw bytes
            decoded_body = base64.b64decode(results['body'].encode('utf-8'))
            h.update(decoded_body)
            return({file_name: h.hexdigest()})

    except Exception as ex_unknown:
        print(f"Caught exception in image: {file_name}")
        traceback.print_exc()
        return({file_name: {
            "status": 500,
            "error": str(ex_unknown),
            "traceback": traceback.format_exc()
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

    # Create amultiprocessing pool
    pool = Pool(processes=args.t)
    futures = []
    total_count = 0

    all_items = list(get_all_tests())
    if args.limit is not None:
        all_items = all_items[:args.limit]
    count = 0
    for item in all_items:
        futures.append(pool.apply_async(create_test_image, args=(item, count, len(all_items), )))
        count += 1

    pool.close()
    pool.join()

    results = {}

    for f in futures:
        result = f.get()
        results.update(result)

    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
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
    for key,_ in results.items():
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
                res_json = results[key].copy() if isinstance(results[key], dict) else results[key]
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

            ignore_keys = ['image_size', 'execution_duration', 'image', "image_mib", "params", "json_only", "json", "image_type"]
            
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
                res_json = results[key].copy() if isinstance(results[key], dict) else results[key]
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
            if isinstance(results[key], dict) and 'image' in results[key]:
                # Get the non-JSON key by removing _json-True
                png_key = key.replace("_json-bool_True", "").replace("_json-str_True", "")
                if png_key == key:
                    print("Warning: PNG key not found for JSON key: {}".format(key))
                    continue
                
                if png_key in validation:
                    # The PNG result should be a hash string
                    png_hash = results[png_key]
                    json_image_hash = results[key]['image']

                    json_to_image_compare_count +=1
                    
                    if png_hash != json_image_hash:
                        errors += 1
                        print(f"Error: Image hash mismatch between JSON and PNG for {key}")
                        print(f"  JSON image hash: {json_image_hash}")
                        print(f"  PNG image hash:  {png_hash}")
            
            
        
        elif results[key] != validation[key]:
            # Check if this is a known non-deterministic case
            if 'individual-str_True' in key:
                # ZIP files with individual mode are non-deterministic due to timestamps
                print(f"Warning: Skipping non-deterministic ZIP file: {key}")
                warnings += 1
            else:
                errors += 1
                print(f"Error Image Changed!!: {key} (file://{os.path.abspath(os.path.join(save_dir, key))}.png)")
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
    main(parser.parse_args())
