#!/usr/bin/env python3

import json
import jsondiff
import argparse
import os
import base64
from datetime import datetime
import hashlib
from collections import defaultdict

def extract_result_data(result_value):
    """Extract actual data/hash from result structure"""
    if isinstance(result_value, dict) and 'data' in result_value:
        return result_value['data']
    elif isinstance(result_value, dict) and 'hash' in result_value:
        return result_value['hash']
    elif isinstance(result_value, dict) and 'status' in result_value:
        # Error case
        return result_value
    else:
        return result_value

def get_image_data_url(file_path):
    """Convert image file to data URL for embedding in HTML"""
    if not os.path.exists(file_path):
        return None
    
    # Check file size - if too large, return path instead
    file_size = os.path.getsize(file_path)
    if file_size > 500000:  # 500KB limit for embedding
        # Return relative path for direct file reference
        return file_path
    
    # Determine MIME type based on extension
    ext = os.path.splitext(file_path)[1].lower()
    mime_type = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg', 
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml'
    }.get(ext, 'image/png')
    
    try:
        with open(file_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f"data:{mime_type};base64,{encoded}"
    except Exception:
        return None

def get_file_paths_for_comparison(key, results, validation, input_file, validation_file):
    """Get the actual file paths for both result and validation files"""
    result_path = None
    validation_path = None
    
    # For result file
    if key in results and isinstance(results[key], dict) and 'path' in results[key]:
        # The path field contains the path
        result_path = results[key]['path']
        # Ensure it has the correct format
        if not result_path.startswith('test_results/'):
            # If it starts with just the git state (like "head/..."), add test_results prefix
            result_path = os.path.join('test_results', result_path)
        # If path doesn't have an extension, add it based on the key
        if not any(result_path.endswith(ext) for ext in ['.png', '.json', '.vssx']):
            if '.png' in key and '.json' not in key:
                result_path = result_path + '.png'
            elif '.json_only' in key:
                result_path = result_path + '.json'  
            elif '.json' in key:
                result_path = result_path + '.json'
            elif '.vssx' in key:
                result_path = result_path + '.vssx'
            else:
                result_path = result_path + '.png'
    
    # For validation file
    if key in validation and isinstance(validation[key], dict) and 'path' in validation[key]:
        # The path field contains the path
        validation_path = validation[key]['path']
        # Ensure it has the correct format
        if not validation_path.startswith('test_results/'):
            # If it starts with just the git state (like "9fc053a/..."), add test_results prefix
            validation_path = os.path.join('test_results', validation_path)
        # If path doesn't have an extension, add it based on the key
        if not any(validation_path.endswith(ext) for ext in ['.png', '.json', '.vssx']):
            if '.png' in key and '.json' not in key:
                validation_path = validation_path + '.png'
            elif '.json_only' in key:
                validation_path = validation_path + '.json'
            elif '.json' in key:
                validation_path = validation_path + '.json'
            elif '.vssx' in key:
                validation_path = validation_path + '.vssx'
            else:
                validation_path = validation_path + '.png'
    
    return result_path, validation_path

def categorize_key(key):
    """Categorize a key by its type"""
    if '.json_only' in key:
        return 'json_only'
    elif '.json' in key:
        return 'json'
    elif '.png' in key:
        return 'image'
    elif '.vssx' in key:
        return 'vssx'
    else:
        return 'image'  # Default to image for hash comparisons

def group_errors_by_diff(errors):
    """Group errors by their diff pattern"""
    grouped = defaultdict(list)
    
    for error in errors:
        if 'diff' in error:
            # Create a key from the diff for grouping
            try:
                diff_str = json.dumps(error['diff'], sort_keys=True)
            except (TypeError, ValueError):
                # If JSON serialization fails, use string representation
                diff_str = str(error['diff'])
            grouped[diff_str].append(error)
        else:
            # Non-diff errors go in their own group
            grouped['_no_diff_' + str(error.get('message', ''))].append(error)
    
    return grouped

def sort_ports_list(data):
    """Sort ports list in data if it exists, recursively handling nested structures"""
    if isinstance(data, dict):
        # Check if this dict has a ports list
        if 'ports' in data and isinstance(data['ports'], list):
            def port_key(port):
                return (port['loc'][0], port['loc'][1])
            
            # Sort the ports list
            data['ports'] = sorted(data['ports'], key=port_key)
        
        # Recursively check all nested dictionaries
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                data[key] = sort_ports_list(value)
    
    elif isinstance(data, list):
        # Handle lists that might contain dicts with ports
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                data[i] = sort_ports_list(item)
    
    return data

def compare_results(input_file, validation_file, output_html=None):
    """Compare two test result JSON files and generate HTML report"""
    
    # Load JSON files
    with open(input_file, 'r') as f:
        results = json.load(f)
    
    with open(validation_file, 'r') as f:
        validation = json.load(f)
    
    # Determine output filename if not specified
    if output_html is None:
        input_name = os.path.splitext(os.path.basename(input_file))[0]
        validation_name = os.path.splitext(os.path.basename(validation_file))[0]
        output_html = f"compare_{input_name}_vs_{validation_name}.html"
    
    # Compare results - now grouped by type
    errors_by_type = {
        'json_only': [],
        'json': [],
        'image': [],
        'other': []
    }
    warnings = []
    matches = []
    
    all_keys = set(results.keys()) | set(validation.keys())
    
    for key in all_keys:
        result_value = results.get(key)
        validation_value = validation.get(key)
        
        if key not in results:
            warnings.append({
                'key': key,
                'type': 'missing_in_results',
                'message': f'Key exists in validation but not in results',
                'category': categorize_key(key)
            })
            continue
            
        if key not in validation:
            warnings.append({
                'key': key,
                'type': 'missing_in_validation', 
                'message': f'Key exists in results but not in validation',
                'category': categorize_key(key)
            })
            continue
        
        # Skip VSSX files (always different due to unique keys)
        if 'vssx' in key:
            continue
        
        # Determine category
        category = categorize_key(key)
        
        # Extract comparable data
        result_compare = extract_result_data(result_value)
        validation_compare = extract_result_data(validation_value)
        
        # Get file paths for both sides
        result_path, validation_path = get_file_paths_for_comparison(key, results, validation, input_file, validation_file)
        
        # Compare based on key type
        if 'json_only' in key or 'json' in key:
            # JSON comparison - ignore path field since it's test folder specific
            ignore_keys = ['execution_duration', 'image', 'image_mib', 'params', 'json_only', 'json', 'image_type', 'path']
            
            try:
                res_json = result_compare.copy() if isinstance(result_compare, dict) else result_compare
                val_json = validation_compare.copy() if isinstance(validation_compare, dict) else validation_compare
                
                if isinstance(res_json, dict) and isinstance(val_json, dict):
                    for k in ignore_keys:
                        res_json.pop(k, None)
                        val_json.pop(k, None)
                    
                    # Sort ports list before comparison to ensure consistent ordering
                    res_json = sort_ports_list(res_json)
                    val_json = sort_ports_list(val_json)
                
                diff = jsondiff.diff(val_json, res_json)
                
                if diff:
                    # Check for non-deterministic cases
                    if 'individual-str_True' in key:
                        warnings.append({
                            'key': key,
                            'type': 'non_deterministic',
                            'message': 'Non-deterministic individual mode',
                            'diff': diff,
                            'category': category
                        })
                    else:
                        error_entry = {
                            'key': key,
                            'type': 'json_diff',
                            'message': 'JSON content differs',
                            'diff': diff,
                            'result_data': res_json,
                            'validation_data': val_json,
                            'result_path': result_path,
                            'validation_path': validation_path
                        }
                        
                        if category == 'json_only':
                            errors_by_type['json_only'].append(error_entry)
                        elif category == 'json':
                            errors_by_type['json'].append(error_entry)
                        else:
                            errors_by_type['other'].append(error_entry)
                else:
                    matches.append({'key': key, 'type': 'json_match', 'category': category})
                    
            except Exception as ex:
                error_entry = {
                    'key': key,
                    'type': 'comparison_error',
                    'message': f'Error comparing JSON: {str(ex)}',
                    'result_data': result_compare,
                    'validation_data': validation_compare,
                    'result_path': result_path,
                    'validation_path': validation_path
                }
                errors_by_type['other'].append(error_entry)
        else:
            # Hash/binary comparison (images)
            if result_compare != validation_compare:
                # Check for non-deterministic cases
                if 'individual-str_True' in key:
                    warnings.append({
                        'key': key,
                        'type': 'non_deterministic',
                        'message': 'Non-deterministic ZIP file with timestamps',
                        'category': category
                    })
                else:
                    error_entry = {
                        'key': key,
                        'type': 'hash_diff',
                        'message': 'Image/binary content differs',
                        'result_hash': result_compare,
                        'validation_hash': validation_compare,
                        'has_images': True,
                        'result_path': result_path,
                        'validation_path': validation_path
                    }
                    errors_by_type['image'].append(error_entry)
            else:
                matches.append({'key': key, 'type': 'hash_match', 'category': category})
    
    # Generate HTML report
    generate_html_report(results, validation, errors_by_type, warnings, matches, output_html, input_file, validation_file)
    
    # Calculate total errors
    total_errors = sum(len(errors) for errors in errors_by_type.values())
    
    return total_errors, len(warnings), len(matches)

def generate_html_report(results, validation, errors_by_type, warnings, matches, output_file, input_file, validation_file):
    """Generate HTML report with embedded images and comparisons grouped by type"""
    
    # Calculate totals
    total_errors = sum(len(errors) for errors in errors_by_type.values())
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Comparison Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        
        .summary {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex: 1;
            text-align: center;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        
        .summary-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .summary-card.errors {{
            border-left: 4px solid #e74c3c;
        }}
        
        .summary-card.warnings {{
            border-left: 4px solid #f39c12;
        }}
        
        .summary-card.matches {{
            border-left: 4px solid #27ae60;
        }}
        
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .summary-card .number {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .errors .number {{ color: #e74c3c; }}
        .warnings .number {{ color: #f39c12; }}
        .matches .number {{ color: #27ae60; }}
        
        .type-summary {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .type-summary h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .type-counts {{
            display: flex;
            gap: 20px;
        }}
        
        .type-count {{
            padding: 10px 20px;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #3498db;
            cursor: pointer;
            transition: background 0.2s;
        }}
        
        .type-count:hover {{
            background: #e9ecef;
        }}
        
        .type-count.json_only {{
            border-color: #9b59b6;
        }}
        
        .type-count.json {{
            border-color: #3498db;
        }}
        
        .type-count.image {{
            border-color: #e67e22;
        }}
        
        .section {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            overflow: hidden;
        }}
        
        .section-header {{
            padding: 20px;
            font-size: 1.5em;
            font-weight: bold;
            color: white;
        }}
        
        .section-header.errors {{
            background-color: #e74c3c;
        }}
        
        .section-header.json_only {{
            background-color: #9b59b6;
        }}
        
        .section-header.json {{
            background-color: #3498db;
        }}
        
        .section-header.image {{
            background-color: #e67e22;
        }}
        
        .section-header.warnings {{
            background-color: #f39c12;
        }}
        
        .section-header.matches {{
            background-color: #27ae60;
        }}
        
        .error-group {{
            border: 1px solid #dee2e6;
            border-radius: 4px;
            margin: 10px 20px;
            overflow: hidden;
        }}
        
        .error-group-header {{
            background: #f8f9fa;
            padding: 10px 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }}
        
        .error-group-header:hover {{
            background: #e9ecef;
        }}
        
        .error-group-header .count {{
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.9em;
        }}
        
        .error-group-content {{
            display: none;
            padding: 15px;
            background: white;
        }}
        
        .error-group-content.show {{
            display: block;
        }}
        
        .comparison-item {{
            border-bottom: 1px solid #ecf0f1;
            padding: 20px;
        }}
        
        .comparison-item:last-child {{
            border-bottom: none;
        }}
        
        .key-name {{
            font-family: 'Courier New', monospace;
            background-color: #f8f9fa;
            padding: 5px 10px;
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 10px;
            font-weight: bold;
            word-break: break-all;
        }}
        
        .message {{
            color: #7f8c8d;
            margin-bottom: 15px;
        }}
        
        .image-comparison {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            align-items: flex-start;
        }}
        
        .image-panel {{
            flex: 1;
            text-align: center;
        }}
        
        .image-panel h4 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
            background: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
        }}
        
        .image-panel img {{
            max-width: 100%;
            max-height: 400px;
            border: 2px solid #ecf0f1;
            border-radius: 4px;
            background: white;
        }}
        
        .diff-panel {{
            flex: 1;
            text-align: center;
        }}
        
        .diff-canvas {{
            border: 2px solid #e74c3c;
            border-radius: 4px;
            max-width: 100%;
        }}
        
        .json-diff {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 15px 0;
            overflow-x: auto;
        }}
        
        .json-diff pre {{
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
        }}
        
        .hash-comparison {{
            display: flex;
            gap: 20px;
            margin: 15px 0;
        }}
        
        .hash-panel {{
            flex: 1;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        }}
        
        .hash-panel h5 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .hash-value {{
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            word-break: break-all;
            background-color: white;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        }}
        
        .toggle-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin: 10px 0;
        }}
        
        .toggle-btn:hover {{
            background: #2980b9;
        }}
        
        .collapsible {{
            display: none;
        }}
        
        .collapsible.show {{
            display: block;
        }}
        
        .pixel-diff-controls {{
            margin: 10px 0;
            text-align: center;
        }}
        
        .pixel-diff-controls button {{
            background: #8e44ad;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin: 0 5px;
        }}
        
        .pixel-diff-controls button:hover {{
            background: #7d3c98;
        }}
        
        .no-image {{
            padding: 40px;
            background: #f8f9fa;
            border: 2px dashed #dee2e6;
            border-radius: 4px;
            color: #6c757d;
        }}
        
        .navigation {{
            position: sticky;
            top: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 100;
        }}
        
        .navigation h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .nav-links {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .nav-link {{
            padding: 8px 16px;
            background: #f8f9fa;
            border-radius: 4px;
            text-decoration: none;
            color: #495057;
            transition: background 0.2s;
        }}
        
        .nav-link:hover {{
            background: #e9ecef;
        }}
        
        .nav-link.error {{
            border-left: 3px solid #e74c3c;
        }}
        
        .nav-link.warning {{
            border-left: 3px solid #f39c12;
        }}
        
        .nav-link.match {{
            border-left: 3px solid #27ae60;
        }}
        
        .side-by-side-comparison {{
            display: none;
            margin-top: 15px;
        }}
        
        .side-by-side-comparison.show {{
            display: flex;
            gap: 20px;
        }}
        
        .json-panel {{
            flex: 1;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
        }}
        
        .json-panel h5 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-weight: bold;
        }}
        
        .json-panel pre {{
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .json-line {{
            padding: 2px 4px;
            margin: 1px 0;
            border-radius: 2px;
        }}
        
        .json-line.added {{
            background-color: #d4edda;
            border-left: 3px solid #28a745;
        }}
        
        .json-line.removed {{
            background-color: #f8d7da;
            border-left: 3px solid #dc3545;
        }}
        
        .json-line.modified {{
            background-color: #fff3cd;
            border-left: 3px solid #ffc107;
        }}
        
        .diff-legend {{
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
            font-size: 0.85em;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 1px solid #dee2e6;
        }}
        
        .legend-color.added {{
            background-color: #d4edda;
        }}
        
        .legend-color.removed {{
            background-color: #f8d7da;
        }}
        
        .legend-color.modified {{
            background-color: #fff3cd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Comparison Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Comparing: {os.path.basename(input_file)} vs {os.path.basename(validation_file)}</p>
    </div>
    
    <div class="navigation">
        <h3>Quick Navigation</h3>
        <div class="nav-links">
"""

    # Add navigation links
    if errors_by_type['json_only']:
        html_content += f'            <a href="#json_only_errors" class="nav-link error">JSON Only Errors ({len(errors_by_type["json_only"])})</a>\n'
    if errors_by_type['json']:
        html_content += f'            <a href="#json_errors" class="nav-link error">JSON Errors ({len(errors_by_type["json"])})</a>\n'
    if errors_by_type['image']:
        html_content += f'            <a href="#image_errors" class="nav-link error">Image Errors ({len(errors_by_type["image"])})</a>\n'
    if warnings:
        html_content += f'            <a href="#warnings" class="nav-link warning">Warnings ({len(warnings)})</a>\n'
    if matches:
        html_content += f'            <a href="#matches" class="nav-link match">Matches ({len(matches)})</a>\n'

    html_content += """        </div>
    </div>
    
    <div class="summary">
        <div class="summary-card errors" onclick="document.getElementById('all_errors').scrollIntoView();">
            <h3>Total Errors</h3>
            <div class="number">"""
    
    html_content += f"{total_errors}"
    
    html_content += f"""</div>
            <p>Differences found</p>
        </div>
        <div class="summary-card warnings" onclick="document.getElementById('warnings').scrollIntoView();">
            <h3>Warnings</h3>
            <div class="number">{len(warnings)}</div>
            <p>Issues to review</p>
        </div>
        <div class="summary-card matches" onclick="document.getElementById('matches').scrollIntoView();">
            <h3>Matches</h3>
            <div class="number">{len(matches)}</div>
            <p>Tests passed</p>
        </div>
    </div>
    
    <div class="type-summary" id="all_errors">
        <h3>Error Breakdown by Type</h3>
        <div class="type-counts">
"""

    if errors_by_type['json_only']:
        html_content += f"""            <div class="type-count json_only" onclick="document.getElementById('json_only_errors').scrollIntoView();">
                <strong>JSON Only:</strong> {len(errors_by_type['json_only'])} errors
            </div>
"""
    if errors_by_type['json']:
        html_content += f"""            <div class="type-count json" onclick="document.getElementById('json_errors').scrollIntoView();">
                <strong>JSON:</strong> {len(errors_by_type['json'])} errors
            </div>
"""
    if errors_by_type['image']:
        html_content += f"""            <div class="type-count image" onclick="document.getElementById('image_errors').scrollIntoView();">
                <strong>Images:</strong> {len(errors_by_type['image'])} errors
            </div>
"""

    html_content += """        </div>
    </div>
"""

    # Add json_only errors section with grouping
    if errors_by_type['json_only']:
        html_content += f'''
    <div class="section" id="json_only_errors">
        <div class="section-header json_only">JSON Only Errors ({len(errors_by_type['json_only'])})</div>
'''
        
        # Group errors by diff pattern
        grouped_errors = group_errors_by_diff(errors_by_type['json_only'])
        
        for group_key, group_errors in grouped_errors.items():
            if group_key.startswith('_no_diff_'):
                # Individual errors without grouping
                for error in group_errors[:5]:
                    html_content += f'''
        <div class="comparison-item">
            <div class="key-name">{error['key']}</div>
            <div class="message">{error['message']}</div>
        </div>
'''
            else:
                # Grouped errors
                diff_preview = group_key[:100] + '...' if len(group_key) > 100 else group_key
                group_id = abs(hash(group_key))
                
                html_content += f'''
        <div class="error-group">
            <div class="error-group-header" onclick="toggleErrorGroup('group_{group_id}')">
                <div>
                    <strong>Common Error Pattern:</strong>
                    <code>{diff_preview}</code>
                </div>
                <span class="count">{len(group_errors)} occurrences</span>
            </div>
            <div id="group_{group_id}" class="error-group-content">
'''
                
                for error in group_errors[:10]:
                    error_id = abs(hash(error["key"]))
                    # Safely encode JSON data for JavaScript
                    result_data_json = json.dumps(error.get('result_data', {}))
                    validation_data_json = json.dumps(error.get('validation_data', {}))
                    # Escape for HTML attribute
                    result_data_escaped = result_data_json.replace("'", "\\'").replace('"', '&quot;')
                    validation_data_escaped = validation_data_json.replace("'", "\\'").replace('"', '&quot;')
                    
                    html_content += f'''
                <div class="comparison-item">
                    <div class="key-name">{error['key']}</div>
                    <button class="toggle-btn" onclick="toggleCollapsible('diff_{error_id}')">Show/Hide Diff Summary</button>
                    <div id="diff_{error_id}" class="json-diff collapsible">
                        <pre>{str(error.get('diff', {}))}</pre>
                    </div>
                    <button class="toggle-btn" onclick="loadAndShowComparison('{error_id}', this)" 
                            data-result='{result_data_escaped}' 
                            data-validation='{validation_data_escaped}'>Show Side-by-Side Comparison</button>
                    <div id="compare_{error_id}" class="side-by-side-comparison collapsible"></div>
                </div>
'''
                
                if len(group_errors) > 10:
                    html_content += f'''
                <div class="comparison-item">
                    <p style="text-align: center; color: #7f8c8d;">... and {len(group_errors) - 10} more similar errors</p>
                </div>
'''
                
                html_content += '''
            </div>
        </div>
'''
        
        html_content += '''
    </div>
'''

    # Add json errors section with grouping
    if errors_by_type['json']:
        html_content += f'''
    <div class="section" id="json_errors">
        <div class="section-header json">JSON Errors ({len(errors_by_type['json'])})</div>
'''
        
        # Group errors by diff pattern
        grouped_errors = group_errors_by_diff(errors_by_type['json'])
        
        for group_key, group_errors in grouped_errors.items():
            if group_key.startswith('_no_diff_'):
                # Individual errors without grouping
                for error in group_errors[:5]:
                    html_content += f'''
        <div class="comparison-item">
            <div class="key-name">{error['key']}</div>
            <div class="message">{error['message']}</div>
        </div>
'''
            else:
                # Grouped errors
                diff_preview = group_key[:100] + '...' if len(group_key) > 100 else group_key
                group_id = abs(hash(group_key))
                
                html_content += f'''
        <div class="error-group">
            <div class="error-group-header" onclick="toggleErrorGroup('group_{group_id}')">
                <div>
                    <strong>Common Error Pattern:</strong>
                    <code>{diff_preview}</code>
                </div>
                <span class="count">{len(group_errors)} occurrences</span>
            </div>
            <div id="group_{group_id}" class="error-group-content">
'''
                
                for error in group_errors[:10]:
                    error_id = abs(hash(error["key"]))
                    # Safely encode JSON data for JavaScript
                    result_data_json = json.dumps(error.get('result_data', {}))
                    validation_data_json = json.dumps(error.get('validation_data', {}))
                    # Escape for HTML attribute
                    result_data_escaped = result_data_json.replace("'", "\\'").replace('"', '&quot;')
                    validation_data_escaped = validation_data_json.replace("'", "\\'").replace('"', '&quot;')
                    
                    html_content += f'''
                <div class="comparison-item">
                    <div class="key-name">{error['key']}</div>
                    <button class="toggle-btn" onclick="toggleCollapsible('diff_{error_id}')">Show/Hide Diff Summary</button>
                    <div id="diff_{error_id}" class="json-diff collapsible">
                        <pre>{str(error.get('diff', {}))}</pre>
                    </div>
                    <button class="toggle-btn" onclick="loadAndShowComparison('{error_id}', this)" 
                            data-result='{result_data_escaped}' 
                            data-validation='{validation_data_escaped}'>Show Side-by-Side Comparison</button>
                    <div id="compare_{error_id}" class="side-by-side-comparison collapsible"></div>
                </div>
'''
                
                if len(group_errors) > 10:
                    html_content += f'''
                <div class="comparison-item">
                    <p style="text-align: center; color: #7f8c8d;">... and {len(group_errors) - 10} more similar errors</p>
                </div>
'''
                
                html_content += '''
            </div>
        </div>
'''
        
        html_content += '''
    </div>
'''

    # Add image errors section
    if errors_by_type['image']:
        html_content += f'''
    <div class="section" id="image_errors">
        <div class="section-header image">Image Errors ({len(errors_by_type['image'])})</div>
'''
        
        for error in errors_by_type['image'][:20]:  # Limit to first 20 for images
            html_content += f'''
        <div class="comparison-item">
            <div class="key-name">{error['key']}</div>
            <div class="message">{error['message']}</div>
'''
            
            # Add image comparison with file paths
            result_path = error.get('result_path')
            validation_path = error.get('validation_path')
            
            # Check if files exist and get appropriate src
            result_img_src = None
            validation_img_src = None
            
            if result_path and os.path.exists(result_path):
                # Use relative path for images
                result_img_src = result_path
            
            if validation_path and os.path.exists(validation_path):
                # Use relative path for images
                validation_img_src = validation_path
            
            html_content += f'''
            <div class="image-comparison">
                <div class="image-panel">
                    <h4>Current Result</h4>
                    {f'<img src="{result_img_src}" alt="Current result" id="img1_{abs(hash(error["key"]))}">' if result_img_src else '<div class="no-image">Image not found</div>'}
                </div>
                <div class="image-panel">
                    <h4>Expected (Validation)</h4>
                    {f'<img src="{validation_img_src}" alt="Validation" id="img2_{abs(hash(error["key"]))}">' if validation_img_src else '<div class="no-image">Image not found</div>'}
                </div>
'''
            
            # Only add diff panel if both images exist
            if result_img_src and validation_img_src:
                html_content += f'''
                <div class="diff-panel">
                    <h4>Pixel Differences</h4>
                    <canvas id="diff_{abs(hash(error['key']))}" class="diff-canvas"></canvas>
                    <div class="pixel-diff-controls">
                        <button onclick="generatePixelDiff('{abs(hash(error["key"]))}')">Generate Pixel Diff</button>
                    </div>
                </div>
'''
            
            html_content += '''
            </div>
'''
            
            # Add hash comparison
            html_content += f'''
            <div class="hash-comparison">
                <div class="hash-panel">
                    <h5>Current Hash</h5>
                    <div class="hash-value">{error.get('result_hash', 'N/A')}</div>
                </div>
                <div class="hash-panel">
                    <h5>Expected Hash</h5>
                    <div class="hash-value">{error.get('validation_hash', 'N/A')}</div>
                </div>
            </div>
'''
            
            html_content += '''
        </div>
'''
        
        if len(errors_by_type['image']) > 20:
            html_content += f'''
        <div class="comparison-item">
            <p style="text-align: center; color: #7f8c8d;">... and {len(errors_by_type['image']) - 20} more image errors</p>
        </div>
'''
        
        html_content += '''
    </div>
'''

    # Add warnings section
    if warnings:
        html_content += '''
    <div class="section" id="warnings">
        <div class="section-header warnings">Warnings</div>
'''
        
        for warning in warnings[:50]:
            html_content += f'''
        <div class="comparison-item">
            <div class="key-name">{warning['key']}</div>
            <div class="message">{warning['message']}</div>
        </div>
'''
        
        if len(warnings) > 50:
            html_content += f'''
        <div class="comparison-item">
            <p style="text-align: center; color: #7f8c8d;">... and {len(warnings) - 50} more warnings</p>
        </div>
'''
        
        html_content += '''
    </div>
'''

    # Add matches section (collapsed by default)
    if matches:
        html_content += f'''
    <div class="section" id="matches">
        <div class="section-header matches">Matches ({len(matches)})</div>
        <div class="comparison-item">
            <button class="toggle-btn" onclick="toggleCollapsible('matches_list')">Show/Hide Matching Tests</button>
            <div id="matches_list" class="collapsible">
'''
        
        # Group matches by category
        matches_by_category = {'json_only': [], 'json': [], 'image': [], 'other': []}
        for match in matches:
            category = match.get('category', 'other')
            if category in matches_by_category:
                matches_by_category[category].append(match)
            else:
                matches_by_category['other'].append(match)
        
        for category, category_matches in matches_by_category.items():
            if category_matches:
                html_content += f'''
                <h4 style="margin-top: 15px; color: #2c3e50;">{category.replace('_', ' ').title()} ({len(category_matches)})</h4>
'''
                for match in category_matches[:10]:
                    html_content += f'''
                <div class="key-name" style="margin: 5px;">{match['key']}</div>
'''
                if len(category_matches) > 10:
                    html_content += f'''
                <p style="color: #7f8c8d;">... and {len(category_matches) - 10} more {category} matches</p>
'''
        
        html_content += '''
            </div>
        </div>
    </div>
'''

    # Add JavaScript for interactivity and pixel comparison
    html_content += '''
    <script>
        function toggleCollapsible(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.classList.toggle('show');
            }
        }
        
        function toggleErrorGroup(groupId) {
            const element = document.getElementById(groupId);
            if (element) {
                element.classList.toggle('show');
            }
        }
        
        function loadAndShowComparison(errorId, button) {
            const compareDiv = document.getElementById('compare_' + errorId);
            if (!compareDiv) return;
            
            // Toggle visibility
            if (compareDiv.classList.contains('show')) {
                compareDiv.classList.remove('show');
                return;
            }
            
            // Get JSON data from data attributes
            const resultDataStr = button.getAttribute('data-result').replace(/&quot;/g, '"');
            const validationDataStr = button.getAttribute('data-validation').replace(/&quot;/g, '"');
            
            // Parse the JSON data
            let resultData, validationData;
            try {
                resultData = JSON.parse(resultDataStr);
                validationData = JSON.parse(validationDataStr);
            } catch (e) {
                compareDiv.innerHTML = '<p style="color: red;">Error parsing JSON data: ' + e.message + '</p>';
                compareDiv.classList.add('show');
                return;
            }
            
            // Check if content is already loaded
            if (compareDiv.innerHTML.trim() !== '') {
                compareDiv.classList.add('show');
                return;
            }
            
            // Create the side-by-side comparison
            const resultJson = JSON.stringify(resultData, null, 2);
            const validationJson = JSON.stringify(validationData, null, 2);
            
            // Create diff visualization
            const diffHtml = createSideBySideDiff(resultJson, validationJson, resultData, validationData);
            
            compareDiv.innerHTML = diffHtml;
            compareDiv.classList.add('show');
        }
        
        function createSideBySideDiff(resultJson, validationJson, resultData, validationData) {
            // Create a simple diff by comparing the objects
            const resultLines = resultJson.split('\\n');
            const validationLines = validationJson.split('\\n');
            
            // Find differences in the data
            const diffs = findJsonDifferences(resultData, validationData);
            
            let html = `
                <div class="diff-legend">
                    <div class="legend-item">
                        <div class="legend-color added"></div>
                        <span>Added in Current</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color removed"></div>
                        <span>Missing in Current</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color modified"></div>
                        <span>Modified</span>
                    </div>
                </div>
                <div style="display: flex; gap: 20px;">
                    <div class="json-panel">
                        <h5>Current Result</h5>
                        <pre>${highlightJsonDiff(resultJson, diffs, 'result')}</pre>
                    </div>
                    <div class="json-panel">
                        <h5>Expected (Validation)</h5>
                        <pre>${highlightJsonDiff(validationJson, diffs, 'validation')}</pre>
                    </div>
                </div>
            `;
            
            return html;
        }
        
        function findJsonDifferences(obj1, obj2, path = '') {
            const diffs = [];
            
            // Helper to add a diff entry
            const addDiff = (key, type) => {
                const fullPath = path ? `${path}.${key}` : key;
                diffs.push({ path: fullPath, type: type });
            };
            
            // Check obj1 keys
            if (typeof obj1 === 'object' && obj1 !== null) {
                for (const key in obj1) {
                    const newPath = path ? `${path}.${key}` : key;
                    
                    if (!(key in obj2)) {
                        addDiff(key, 'added');
                    } else if (typeof obj1[key] === 'object' && typeof obj2[key] === 'object') {
                        // Recursively check nested objects
                        diffs.push(...findJsonDifferences(obj1[key], obj2[key], newPath));
                    } else if (obj1[key] !== obj2[key]) {
                        addDiff(key, 'modified');
                    }
                }
            }
            
            // Check obj2 keys not in obj1
            if (typeof obj2 === 'object' && obj2 !== null) {
                for (const key in obj2) {
                    if (!(key in obj1)) {
                        addDiff(key, 'removed');
                    }
                }
            }
            
            return diffs;
        }
        
        function highlightJsonDiff(jsonStr, diffs, side) {
            let highlightedJson = jsonStr;
            
            // Sort diffs by path length (longest first) to avoid replacement issues
            diffs.sort((a, b) => b.path.length - a.path.length);
            
            // Apply highlighting based on diffs
            diffs.forEach(diff => {
                const pathParts = diff.path.split('.');
                const lastPart = pathParts[pathParts.length - 1];
                
                // Create a regex to find the key in the JSON string
                const keyRegex = new RegExp(`("${lastPart}"\\s*:)`, 'g');
                
                let className = '';
                if (side === 'result') {
                    if (diff.type === 'added') className = 'added';
                    else if (diff.type === 'removed') className = '';  // Don't highlight in result
                    else if (diff.type === 'modified') className = 'modified';
                } else {
                    if (diff.type === 'added') className = '';  // Don't highlight in validation
                    else if (diff.type === 'removed') className = 'removed';
                    else if (diff.type === 'modified') className = 'modified';
                }
                
                if (className) {
                    // Find lines containing this key and wrap them
                    const lines = highlightedJson.split('\\n');
                    const newLines = lines.map(line => {
                        if (line.includes(`"${lastPart}"`) && line.includes(':')) {
                            return `<span class="json-line ${className}">${line}</span>`;
                        }
                        return line;
                    });
                    highlightedJson = newLines.join('\\n');
                }
            });
            
            return highlightedJson;
        }
        
        function generatePixelDiff(imageId) {
            const img1 = document.getElementById('img1_' + imageId);
            const img2 = document.getElementById('img2_' + imageId);
            const canvas = document.getElementById('diff_' + imageId);
            
            if (!img1 || !img2 || !canvas) {
                alert('Images not found for comparison');
                return;
            }
            
            const ctx = canvas.getContext('2d');
            
            // Set canvas size to match images
            const maxWidth = Math.max(img1.naturalWidth || img1.width, img2.naturalWidth || img2.width);
            const maxHeight = Math.max(img1.naturalHeight || img1.height, img2.naturalHeight || img2.height);
            
            canvas.width = maxWidth;
            canvas.height = maxHeight;
            
            // Create temporary canvases for each image
            const canvas1 = document.createElement('canvas');
            const canvas2 = document.createElement('canvas');
            const ctx1 = canvas1.getContext('2d');
            const ctx2 = canvas2.getContext('2d');
            
            canvas1.width = canvas2.width = maxWidth;
            canvas1.height = canvas2.height = maxHeight;
            
            // Draw images to temporary canvases
            ctx1.drawImage(img1, 0, 0, maxWidth, maxHeight);
            ctx2.drawImage(img2, 0, 0, maxWidth, maxHeight);
            
            // Get image data
            const imageData1 = ctx1.getImageData(0, 0, maxWidth, maxHeight);
            const imageData2 = ctx2.getImageData(0, 0, maxWidth, maxHeight);
            const diffData = ctx.createImageData(maxWidth, maxHeight);
            
            // Simple pixel difference
            const data1 = imageData1.data;
            const data2 = imageData2.data;
            const diff = diffData.data;
            
            let diffPixels = 0;
            
            for (let i = 0; i < data1.length; i += 4) {
                const r1 = data1[i], g1 = data1[i+1], b1 = data1[i+2];
                const r2 = data2[i], g2 = data2[i+1], b2 = data2[i+2];
                
                // Calculate difference
                const dr = Math.abs(r1 - r2);
                const dg = Math.abs(g1 - g2);
                const db = Math.abs(b1 - b2);
                const avgDiff = (dr + dg + db) / 3;
                
                if (avgDiff > 10) {  // Threshold for difference
                    // Highlight difference in red
                    diff[i] = 255;     // Red
                    diff[i+1] = 0;     // Green
                    diff[i+2] = 0;     // Blue
                    diff[i+3] = 255;   // Alpha
                    diffPixels++;
                } else {
                    // Copy original pixel but make it semi-transparent
                    diff[i] = Math.max(r1, r2);
                    diff[i+1] = Math.max(g1, g2);
                    diff[i+2] = Math.max(b1, b2);
                    diff[i+3] = 100;   // Semi-transparent
                }
            }
            
            // Draw difference to canvas
            ctx.putImageData(diffData, 0, 0);
            
            // Add difference count
            const diffPercent = ((diffPixels / (maxWidth * maxHeight)) * 100).toFixed(2);
            const existingInfo = canvas.parentNode.querySelector('.diff-info');
            if (existingInfo) {
                existingInfo.remove();
            }
            const diffInfo = document.createElement('p');
            diffInfo.className = 'diff-info';
            diffInfo.textContent = `Difference: ${diffPixels} pixels (${diffPercent}%)`;
            diffInfo.style.textAlign = 'center';
            diffInfo.style.color = '#e74c3c';
            diffInfo.style.fontWeight = 'bold';
            canvas.parentNode.appendChild(diffInfo);
        }
    </script>
</body>
</html>
'''

    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML report generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Compare test results and generate HTML report')
    parser.add_argument('input_json', help='Input JSON file to compare (e.g., test_results_head.json)')
    parser.add_argument('--validation', '-v', default='test_validation.json', 
                      help='Validation JSON file to compare against (default: test_validation.json)')
    parser.add_argument('--output', '-o', help='Output HTML file name (auto-generated if not specified)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_json):
        print(f"Error: Input file '{args.input_json}' not found")
        return 1
    
    if not os.path.exists(args.validation):
        print(f"Error: Validation file '{args.validation}' not found")
        return 1
    
    print(f"Comparing {args.input_json} against {args.validation}")
    
    try:
        errors, warnings, matches = compare_results(args.input_json, args.validation, args.output)
        
        print(f"Comparison complete:")
        print(f"  Total Errors: {errors}")
        print(f"  Warnings: {warnings}")  
        print(f"  Matches: {matches}")
        
        return 0 if errors == 0 else 1
        
    except Exception as e:
        print(f"Error during comparison: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())