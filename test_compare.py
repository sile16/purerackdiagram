#!/usr/bin/env python3

import json
import jsondiff
import argparse
import os
import base64
from datetime import datetime
import hashlib

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

def get_file_path_from_key(key, results, validation, base_dir="test_results"):
    """Get the actual file path for a given key"""
    # Try to get path from results first
    if key in results and isinstance(results[key], dict) and 'path' in results[key]:
        return os.path.join(base_dir, results[key]['path'])
    
    # Fallback: construct path from key
    # Remove extensions and add appropriate one based on key
    base_key = key.replace('.json', '').replace('.json_only', '')
    
    if '.png' in key or (key in results and isinstance(results[key], str)):
        return os.path.join(base_dir, "head", base_key + '.png')
    elif '.json' in key:
        return os.path.join(base_dir, "head", base_key + '.json')
    
    return None

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
    
    # Compare results
    errors = []
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
                'message': f'Key exists in validation but not in results'
            })
            continue
            
        if key not in validation:
            warnings.append({
                'key': key,
                'type': 'missing_in_validation', 
                'message': f'Key exists in results but not in validation'
            })
            continue
        
        # Skip VSSX files (always different due to unique keys)
        if 'vssx' in key:
            continue
            
        # Extract comparable data
        result_compare = extract_result_data(result_value)
        validation_compare = extract_result_data(validation_value)
        
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
                
                diff = jsondiff.diff(val_json, res_json)
                
                if diff:
                    # Check for non-deterministic cases
                    if 'individual-str_True' in key:
                        warnings.append({
                            'key': key,
                            'type': 'non_deterministic',
                            'message': 'Non-deterministic individual mode',
                            'diff': diff
                        })
                    else:
                        errors.append({
                            'key': key,
                            'type': 'json_diff',
                            'message': 'JSON content differs',
                            'diff': diff,
                            'result_data': res_json,
                            'validation_data': val_json
                        })
                else:
                    matches.append({'key': key, 'type': 'json_match'})
                    
            except Exception as ex:
                errors.append({
                    'key': key,
                    'type': 'comparison_error',
                    'message': f'Error comparing JSON: {str(ex)}',
                    'result_data': result_compare,
                    'validation_data': validation_compare
                })
        else:
            # Hash/binary comparison
            if result_compare != validation_compare:
                # Check for non-deterministic cases
                if 'individual-str_True' in key:
                    warnings.append({
                        'key': key,
                        'type': 'non_deterministic',
                        'message': 'Non-deterministic ZIP file with timestamps'
                    })
                else:
                    errors.append({
                        'key': key,
                        'type': 'hash_diff',
                        'message': 'Image/binary content differs',
                        'result_hash': result_compare,
                        'validation_hash': validation_compare,
                        'has_images': True
                    })
            else:
                matches.append({'key': key, 'type': 'hash_match'})
    
    # Generate HTML report
    generate_html_report(results, validation, errors, warnings, matches, output_html)
    
    return len(errors), len(warnings), len(matches)

def generate_html_report(results, validation, errors, warnings, matches, output_file):
    """Generate HTML report with embedded images and comparisons"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Comparison Report</title>
    <script src="https://cdn.jsdelivr.net/npm/pixelmatch@5.3.0/bin/pixelmatch.js"></script>
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
        
        .section-header.warnings {{
            background-color: #f39c12;
        }}
        
        .section-header.matches {{
            background-color: #27ae60;
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
        }}
        
        .message {{
            color: #7f8c8d;
            margin-bottom: 15px;
        }}
        
        .image-comparison {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        
        .image-panel {{
            flex: 1;
            text-align: center;
        }}
        
        .image-panel h4 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .image-panel img {{
            max-width: 100%;
            max-height: 400px;
            border: 2px solid #ecf0f1;
            border-radius: 4px;
        }}
        
        .diff-panel {{
            flex: 1;
            text-align: center;
        }}
        
        .diff-canvas {{
            border: 2px solid #e74c3c;
            border-radius: 4px;
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
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Comparison Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="summary-card errors">
            <h3>Errors</h3>
            <div class="number">{len(errors)}</div>
            <p>Differences found</p>
        </div>
        <div class="summary-card warnings">
            <h3>Warnings</h3>
            <div class="number">{len(warnings)}</div>
            <p>Issues to review</p>
        </div>
        <div class="summary-card matches">
            <h3>Matches</h3>
            <div class="number">{len(matches)}</div>
            <p>Tests passed</p>
        </div>
    </div>
"""

    # Add errors section
    if errors:
        html_content += '''
    <div class="section">
        <div class="section-header errors">Errors</div>
'''
        
        for error in errors:
            html_content += f'''
        <div class="comparison-item">
            <div class="key-name">{error['key']}</div>
            <div class="message">{error['message']}</div>
'''
            
            if error['type'] == 'hash_diff' and error.get('has_images'):
                # Add image comparison for binary differences
                result_path = get_file_path_from_key(error['key'], results, validation)
                validation_path = get_file_path_from_key(error['key'], validation, results, "test_results")
                
                result_img_data = get_image_data_url(result_path) if result_path else None
                validation_img_data = get_image_data_url(validation_path) if validation_path else None
                
                if result_img_data or validation_img_data:
                    html_content += f'''
            <div class="image-comparison">
                <div class="image-panel">
                    <h4>Current Result</h4>
                    {f'<img src="{result_img_data}" alt="Current result" id="img1_{abs(hash(error["key"]))}">' if result_img_data else '<p>Image not found</p>'}
                </div>
                <div class="image-panel">
                    <h4>Validation</h4>
                    {f'<img src="{validation_img_data}" alt="Validation" id="img2_{abs(hash(error["key"]))}">' if validation_img_data else '<p>Image not found</p>'}
                </div>
                <div class="diff-panel">
                    <h4>Pixel Differences</h4>
                    <canvas id="diff_{abs(hash(error['key']))}" class="diff-canvas"></canvas>
                    <div class="pixel-diff-controls">
                        <button onclick="generatePixelDiff('{abs(hash(error["key"]))}')">Generate Pixel Diff</button>
                    </div>
                </div>
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
                    <h5>Validation Hash</h5>
                    <div class="hash-value">{error.get('validation_hash', 'N/A')}</div>
                </div>
            </div>
'''
            
            elif error['type'] == 'json_diff':
                # Add JSON diff
                html_content += f'''
            <button class="toggle-btn" onclick="toggleCollapsible('diff_{abs(hash(error["key"]))}')">Show/Hide JSON Diff</button>
            <div id="diff_{abs(hash(error['key']))}" class="json-diff collapsible">
                <pre>{json.dumps(error.get('diff', {}), indent=2, default=str)}</pre>
            </div>
'''
            
            html_content += '''
        </div>
'''
        
        html_content += '''
    </div>
'''

    # Add warnings section
    if warnings:
        html_content += '''
    <div class="section">
        <div class="section-header warnings">Warnings</div>
'''
        
        for warning in warnings:
            html_content += f'''
        <div class="comparison-item">
            <div class="key-name">{warning['key']}</div>
            <div class="message">{warning['message']}</div>
        </div>
'''
        
        html_content += '''
    </div>
'''

    # Add matches section (collapsed by default)
    if matches:
        html_content += f'''
    <div class="section">
        <div class="section-header matches">Matches ({len(matches)})</div>
        <div class="comparison-item">
            <button class="toggle-btn" onclick="toggleCollapsible('matches_list')">Show/Hide Matching Tests</button>
            <div id="matches_list" class="collapsible">
'''
        
        for match in matches[:20]:  # Show first 20 matches
            html_content += f'''
                <div class="key-name" style="margin: 5px;">{match['key']}</div>
'''
        
        if len(matches) > 20:
            html_content += f'''
                <p style="margin-top: 15px; color: #7f8c8d;">... and {len(matches) - 20} more matches</p>
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
            element.classList.toggle('show');
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
            
            // Simple pixel difference (since pixelmatch might not be available)
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
            const diffInfo = document.createElement('p');
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
        print(f"  Errors: {errors}")
        print(f"  Warnings: {warnings}")  
        print(f"  Matches: {matches}")
        
        return 0 if errors == 0 else 1
        
    except Exception as e:
        print(f"Error during comparison: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())