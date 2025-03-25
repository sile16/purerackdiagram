import time
from io import BytesIO
import asyncio
import base64
import logging
import os
import uuid
import zipfile
import io
import json
import traceback

import boto3
from PIL import Image, ImageDraw, ImageFont

from purerackdiagram.utils import combine_images_vertically
import purerackdiagram
from purerackdiagram import RackDiagramException, InvalidConfigurationException, InvalidDatapackException

# Configure logging for Lambda
logger = logging.getLogger()
bucket_name = "images.purestorage"

use_s3_size_limit = 4  # MiB limit for inline responses

# Set to DEBUG to see more details in CloudWatch
log_level = 'DEBUG'

if len(logger.handlers) > 0:
    logger.setLevel(log_level)
else:
    logging.basicConfig(level=log_level)

# Get environment from Lambda environment variables
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'Production')
METRIC_NAMESPACE = f"PureRackDiagram-{ENVIRONMENT}"

logger.info(f"Using metric namespace: {METRIC_NAMESPACE}")

# CloudWatch metrics client - only initialize if running in Lambda
try:
    # When running in AWS Lambda, this will work
    cloudwatch = boto3.client('cloudwatch')
except Exception as e:
    # For local testing, create a mock object
    logger.info(f"Running locally, CloudWatch metrics disabled: {str(e)}")
    class MockCloudWatch:
        def put_metric_data(self, **kwargs):
            logger.debug(f"Mock CloudWatch metric: {kwargs}")
            pass
    cloudwatch = MockCloudWatch()

def emit_exception_metric(exception_type):
    """
    Emit a CloudWatch metric for the exception type
    This allows creating graphs based on exception types
    """
    try:
        # Emit exception count by type
        cloudwatch.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'ExceptionCount',
                    'Dimensions': [
                        {
                            'Name': 'ExceptionType',
                            'Value': exception_type
                        }
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
        
        # Also emit a total error count metric
        cloudwatch.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'TotalErrorCount',
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
        
        logger.info(f"Emitted CloudWatch metric for exception type: {exception_type}")
    except Exception as e:
        logger.error(f"Failed to emit CloudWatch metric: {str(e)}")
        logger.error(traceback.format_exc())

VERSION = 5
program_time_s = time.time()

def upload_to_s3(buffered, extension, contenttype, disposition):
    s3 = boto3.client('s3')
    unique_key = str(uuid.uuid4())
    file_key = f"cache/{unique_key}.{extension}"
    buffered.seek(0)
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=buffered.getvalue(),
            ContentType=contenttype,
            ContentDisposition=disposition
        )
        logger.info(f"Successfully uploaded to S3: {file_key}")
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        logger.error(traceback.format_exc())
        return None
    return f"https://s3.amazonaws.com/{bucket_name}/{file_key}"


def text_to_image(text):
    root_path = os.path.dirname(purerackdiagram.__file__)
    ttf_path = os.path.join(root_path, "Lato-Regular.ttf")
    font = ImageFont.truetype(ttf_path, size=36)
    color = (255, 255, 255, 255)
    background_color = (0, 0, 0, 255)
    lines = text.splitlines()
    x = 10
    y = 20
    _,_,_,line_height = font.getbbox('hg')
    total_height = line_height * len(lines) + y * 2
    total_width = max([font.getbbox(line)[2] for line in lines]) + 2 * x
    img = Image.new('RGBA', (total_width, total_height), background_color)
    draw = ImageDraw.Draw(img)
    for line in lines:
        draw.text((x, y), line, fill=color, font=font)
        y = y + line_height
    return img


def draw_triangle_up(draw, x, y, size, color):
    draw.polygon([(x, y - size), (x + size, y + size), (x - size, y + size)],
                 fill=color, outline=color)

def draw_triangle_down(draw, x, y, size, color):
    draw.polygon([(x, y + size), (x + size, y - size), (x - size, y - size)],
                 fill=color, outline=color)


def sort_ports(all_ports):
    def port_key(port):
        name = port.get('name', 'ct0.eth0')
        parts = name.split('.')
        controller = parts[0]
        if len(parts) > 1:
            protocol_and_number = parts[1]
        else:
            protocol_and_number = "eth0"
        protocol = ''.join([char for char in protocol_and_number if not char.isdigit()])
        number = ''.join([char for char in protocol_and_number if char.isdigit()])
        return (controller, protocol, int(number))
    return sorted(all_ports, key=port_key)


def draw_ports_on_image(img, all_ports, draw_ports_flag, img_original_size):
    draw = ImageDraw.Draw(img)
    size = 16
    for p in all_ports:
        services = p.get('services', [])
        if 'management' in services and len(services) == 1:
            color = '#00B2A9'
            if draw_ports_flag:
                draw_triangle_up(draw, p['loc'][0], p['loc'][1], size, color)
            p['symbol_name'] = "Management"
            p['symbol_shape'] = "triangle_up"
            p['symbol_color'] = color

        elif services and services[0] == 'replication':
            color = '#934DD6'
            if draw_ports_flag:
                draw_triangle_up(draw, p['loc'][0], p['loc'][1], size, color)
            p['symbol_name'] = "Replication"
            p['symbol_shape'] = "triangle_up"
            p['symbol_color'] = color

        elif 'port_type' not in p:
            continue

        elif p['port_type'] == 'sas':
            color = 'blue'
            if draw_ports_flag:
                draw.rectangle((p['loc'][0] - size, p['loc'][1] - size/2,
                                p['loc'][0] + size, p['loc'][1] + size/2),
                               fill=color, outline=color)
            p['symbol_name'] = "SAS"
            p['symbol_shape'] = "rectangle"
            p['symbol_color'] = color

        elif services and services[0] == 'shelf':
            color = '#FCDC4D'
            if draw_ports_flag:
                draw_triangle_down(draw, p['loc'][0], p['loc'][1], size, color)
            p['symbol_name'] = "Shelf"
            p['symbol_shape'] = "triangle_down"
            p['symbol_color'] = color

        elif p['port_type'] == 'fc':
            color = '#FE5000'
            if draw_ports_flag:
                draw.rectangle((p['loc'][0] - size, p['loc'][1] - size,
                                p['loc'][0] + size, p['loc'][1] + size),
                               fill=color, outline=color)
            p['symbol_name'] = "Fibre Channel"
            p['symbol_shape'] = "square"
            p['symbol_color'] = color

        elif p['port_type'] == 'eth_roce':
            color = "#FD9627"
            if draw_ports_flag:
                draw_triangle_up(draw, p['loc'][0], p['loc'][1], size, color)
            p['symbol_name'] = "Ethernet / RoCE"
            p['symbol_shape'] = "triangle_up"
            p['symbol_color'] = color

        elif p['port_type'] == 'eth':
            color = '#D90368'
            if draw_ports_flag:
                draw_triangle_up(draw, p['loc'][0], p['loc'][1], size, color)
            p['symbol_name'] = "Ethernet"
            p['symbol_shape'] = "triangle_up"
            p['symbol_color'] = color

        else:
            logger.warning(f"Unknown port type: {p['port_type']}")


def resize_image_and_ports(img, all_ports):
    max_height = 4604
    if img.size[1] > max_height:
        wpercent = (max_height / float(img.size[1]))
        hsize = int((float(img.size[0]) * float(wpercent)))
        img = img.resize((hsize, max_height), Image.Resampling.LANCZOS)
        for p in all_ports:
            p['loc'] = (int(p['loc'][0] * wpercent), int(p['loc'][1] * wpercent))
    return img


def create_vssx_for_image(img, all_ports, diagram, params):
    ru = diagram.config['ru']
    h_inches = "{:.2f}".format(ru*1.75)
    if params['model'] == 'fb':
        name = "fb"
        stencil_name = "Pure FlashBlade"
        items = ['chassis', 'face', 'direction']
    elif 'fb-s' in params['model'] or 'fb-e' in params['model']:
        stencil_name = "Pure FlashBlade"
        name = params['model']
        items = ['face','dfm_count', 'dfm_size', 'blades']
    elif 'fa' in params['model']:
        stencil_name = "Pure FlashArray"
        name = params['model']+"_"+params['datapacks'].replace("/", '-')
        items = ['face', 'direction']
    else:
        stencil_name = "Pure Unknown Model " + params['model']
        name = "pure_visio"
        items = []

    for n in items:
        name += "_"+str(diagram.config[n])

    root_path = os.path.dirname(__file__)
    vssx_path = os.path.join(root_path, "vssx/vssx_template.zip")
    master1_template_path = os.path.join(root_path, "vssx/master1_template.xml")
    masters_template_path = os.path.join(root_path, "vssx/masters_template.xml")

    img_original_size = img.size
    connection_template = """
                <Row T='Connection' IX='{}'>
                    <Cell N='X' V='{:.10f}' U='IN' F='Width*{:.10f}'/>
                    <Cell N='Y' V='{:.10f}' U='IN' F='Height*{:.10f}'/>
                    <Cell N='DirX' V='0'/>
                    <Cell N='DirY' V='0'/>
                    <Cell N='Type' V='0'/>
                    <Cell N='AutoGen' V='0'/>
                    <Cell N='Prompt' V='' F='No Formula'/>
                </Row>
                """
    ix = 2
    connection_points = ""
    for p in all_ports:
        x_w = 1.0 * (p['loc'][0] / img_original_size[0])
        x_in = 19 * x_w
        y_h = 1 - 1.0 * (p['loc'][1] / img_original_size[1])
        y_in = ru * 1.75 * y_h
        connection_points += connection_template.format(ix, x_in, x_w, y_in, y_h)
        ix += 1

    master1 = None
    with open(master1_template_path, 'r') as mf:
        master1 = mf.read()

    master1 = master1.replace('<template_h_in>', h_inches)
    master1 = master1.replace('<template_h_u>', str(ru))
    master1 = master1.replace('<template_name>', stencil_name)
    master1 = master1.replace('<additional_connection_points>', connection_points)

    masters = None
    with open(masters_template_path, 'r') as mf:
        masters = mf.read()
    stamp = int((time.time())*10)
    unique_id = f"{stamp:07X}"[-7:]
    masters = masters.replace('<template_unique_id>', unique_id)
    masters = masters.replace('<template_name>', stencil_name)

    buffered_image = BytesIO()
    img.save(buffered_image, format="PNG")
    buffered_image.seek(0)

    with open(vssx_path, 'rb') as vssx_file:
        zipfile_raw = vssx_file.read()

    zipfile_buffered = io.BytesIO(zipfile_raw)
    with zipfile.ZipFile(zipfile_buffered, 'a') as zipf:
        zipf.writestr('visio/media/image1.png', buffered_image.getvalue())
        zipf.writestr('visio/masters/master1.xml', master1)
        zipf.writestr('visio/masters/masters.xml', masters)

    zipfile_buffered.seek(0)
    return name, zipfile_buffered


def handle_individual_processing(img_ports, diagram, params):
    draw_ports_flag = False
    if 'ports' in params and (
        params['ports'] == True or
        params['ports'].upper() == "TRUE" or
        params['ports'].upper() == "YES"):
        draw_ports_flag = True

    vssx_flag = 'vssx' in params and params['vssx']

    memory_zip = BytesIO()
    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        index = 1
        for component in img_ports:
            # component is expected to be {'img':..., 'ports':...}
            img = component['img']
            all_ports = component['ports']

            if all_ports:
                all_ports = sort_ports(all_ports)
            draw_ports_on_image(img, all_ports, draw_ports_flag, img.size)
            img = resize_image_and_ports(img, all_ports)

            if vssx_flag:
                name, vssx_buffer = create_vssx_for_image(img, all_ports, diagram, params)
                filename = f"{name}_{index}.vssx"
                zipf.writestr(filename, vssx_buffer.getvalue())
            else:
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                filename = f"component_{index}.png"
                zipf.writestr(filename, buffered.getvalue())
            index += 1

    memory_zip.seek(0)
    zip_file_size = len(memory_zip.getvalue()) / (1024*1024)
    if zip_file_size > use_s3_size_limit:
        link = upload_to_s3(memory_zip, "zip", "application/zip", 'attachment; filename="components.zip"')
        return {
            "statusCode": 302,
            "headers": {
                "Location": link,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET'
            }
        }

    zip_str = base64.b64encode(memory_zip.getvalue()).decode('utf-8')
    return {
        "statusCode": 200,
        "body": zip_str,
        "headers": {
            "Content-Type": "application/zip",
            'content-disposition': 'attachment; filename="components.zip"',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET'
        },
        "isBase64Encoded": True
    }


def emit_success_metric():
    """Emit a success metric to CloudWatch"""
    try:
        cloudwatch.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'SuccessCount',
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
        logger.info("Emitted CloudWatch success metric")
    except Exception as e:
        logger.error(f"Failed to emit CloudWatch success metric: {str(e)}")
        
def emit_array_type_metric(params, diagram=None):
    """
    Emit metrics for array type (FlashArray vs FlashBlade) and FlashArray model
    
    Args:
        params: The query parameters dictionary
        diagram: Optional diagram object with configuration
    """
    try:
        model = params.get('model', '').lower()
        model_metrics = []
        
        # Determine if this is a FlashArray or FlashBlade
        if model.startswith('fa'):
            array_type = 'FlashArray'
            
            # Add model-specific metrics if available
            if diagram and hasattr(diagram, 'config'):
                generation = diagram.config.get('generation', '')
                release = str(diagram.config.get('release', ''))
                model_num = str(diagram.config.get('model_num', ''))
                
                if generation and model_num:
                    model_type = f"{generation.upper()}{model_num}r{release}"
                    model_metrics.append({
                        'MetricName': 'ModelType',
                        'Dimensions': [{'Name': 'Model', 'Value': model_type}],
                        'Value': 1,
                        'Unit': 'Count'
                    })
                    
                    # Also track by generation for broader metrics
                    model_metrics.append({
                        'MetricName': 'Generation',
                        'Dimensions': [{'Name': 'Type', 'Value': generation.upper()}],
                        'Value': 1,
                        'Unit': 'Count'
                    })
        elif model.startswith('fb'):
            array_type = 'FlashBlade'
        else:
            array_type = 'Unknown'
        
        # Emit array type metric
        metrics = [
            {
                'MetricName': 'ArrayType',
                'Dimensions': [{'Name': 'Type', 'Value': array_type}],
                'Value': 1,
                'Unit': 'Count'
            }
        ]
        
        # Add the model metrics if we have any
        metrics.extend(model_metrics)
        
        cloudwatch.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=metrics
        )
        
        logger.info(f"Emitted CloudWatch metrics for array type: {array_type}")
    except Exception as e:
        logger.error(f"Failed to emit array type metrics: {str(e)}")
        logger.error(traceback.format_exc())
        
def create_response(status_code, body, headers=None, is_base64_encoded=False, params=None, diagram=None):
    """
    Helper function to create a response dictionary with automatic success metrics
    
    Args:
        status_code: HTTP status code
        body: Response body
        headers: Optional response headers
        is_base64_encoded: Whether the body is base64 encoded
        params: Query parameters for metrics
        diagram: Diagram object for model metrics
    """
    if headers is None:
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET'
        }
    else:
        # Ensure CORS headers are present
        if 'Access-Control-Allow-Origin' not in headers:
            headers['Access-Control-Allow-Origin'] = '*'
        if 'Access-Control-Allow-Methods' not in headers:
            headers['Access-Control-Allow-Methods'] = 'GET'
    
    response = {
        "statusCode": status_code,
        "body": body,
        "headers": headers
    }
    
    if is_base64_encoded:
        response["isBase64Encoded"] = True
    
    # Emit success metric for 2xx status codes
    if 200 <= status_code < 300:
        emit_success_metric()
        
        # Also emit array type metrics if we have params
        if params:
            emit_array_type_metric(params, diagram)
        
    return response

def handler(event, context):
    global program_time_s
    program_time_s = time.time()
    params = {}
    diagram = None

    try:
        request_id = context.aws_request_id if context and hasattr(context, 'aws_request_id') else 'unknown'
        logger.info(f"Lambda invoked with request_id: {request_id}")
        logger.debug(f"Full event: {json.dumps(event)}")
        
        if ("queryStringParameters" not in event
                or event["queryStringParameters"] is None):
            logger.info("No query parameters found, returning default response")
            return create_response(
                status_code=200,
                body='Hello from Lambda!',
                headers={"Content-Type": "text/plain"}
                # No params or diagram to pass for metrics
            )

        params = event["queryStringParameters"]
        logger.info(f"Processing request with parameters: {json.dumps(params)}")
        
        diagram = purerackdiagram.get_diagram(params)
        logger.info(f"Diagram created: {diagram}")
        
        img_ports_list = asyncio.run(diagram.get_image())
        logger.info("Images created successfully")

        # Check for "individual" param
        individual = False
        if 'individual' in params:
            individual = True

        if individual:
            # img_ports_list expected as a list of dict, each containing 'img' and 'ports'
            return handle_individual_processing(img_ports_list, diagram, params)

        # If not individual, do old vertical combine:
        final_img, all_ports = combine_images_vertically(img_ports_list)
        img_original_size = final_img.size
        draw_ports_flag = False
        if 'ports' in params and (
            params['ports'] == True or
            params['ports'].upper() == "TRUE"
            or params['ports'].upper() == "YES"):
            draw_ports_flag = True

        if all_ports:
            all_ports = sort_ports(all_ports)

        draw_ports_on_image(final_img, all_ports, draw_ports_flag, img_original_size)
        final_img = resize_image_and_ports(final_img, all_ports)

        buffered = BytesIO()
        final_img.save(buffered, format="PNG")
        size_of_buffered_in_mib = len(buffered.getvalue()) / ( 1024 * 1024 )

        if 'vssx' in params and params['vssx']:
            name, vssx_buffer = create_vssx_for_image(final_img, all_ports, diagram, params)
            zip_file_size = len(vssx_buffer.getvalue()) / (1024 * 1024)
            if zip_file_size > use_s3_size_limit:
                s3_link = upload_to_s3(vssx_buffer, "vssx", "application/vnd.ms-visio.stencil", f'attachment; filename="{name}.vssx"')
                return {
                    "statusCode": 302,
                    "headers": {
                        "Location": s3_link,
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET'
                    }
                }
            zip_str = base64.b64encode(vssx_buffer.getvalue()).decode('utf-8')
            content_disposition = f'attachment; filename="{name}.vssx"'
            return create_response(
                status_code=200,
                body=zip_str,
                headers={
                    "Content-Type": "application/vnd.ms-visio.stencil",
                    'content-disposition': content_disposition
                },
                is_base64_encoded=True,
                params=params,
                diagram=diagram
            )
        else:
            data = {"image_type": "png",
                    "config": diagram.config,
                    "ports": all_ports,
                    "execution_duration": time.time() - program_time_s,
                    "error": None,
                    "image_size": final_img.size,
                    "image_mib": size_of_buffered_in_mib,
                    "params": params,
                    "image": None }

            if 'json_only' in params:
                return create_response(
                    status_code=200,
                    body=json.dumps(data, indent=4),
                    headers={"Content-Type": "application/json"},
                    params=params,
                    diagram=diagram
                )

            if size_of_buffered_in_mib > use_s3_size_limit:
                link = upload_to_s3(buffered, "png", "image/png", 'inline')
                data["image"] = link
                data['image_type'] = "link"
            else:
                data["image"] = base64.b64encode(buffered.getvalue()).decode('utf-8')
                data['image_type'] = "png"

            if 'json' in params and params['json']:
                return create_response(
                    status_code=200,
                    body=json.dumps(data, indent=4),
                    headers={"Content-Type": "application/json"},
                    params=params,
                    diagram=diagram
                )

            if size_of_buffered_in_mib > use_s3_size_limit:
                return {
                    "statusCode": 302,
                    "headers": {"Location": data["image"],
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'GET'}
                }

            return create_response(
                status_code=200,
                body=data['image'],
                headers={"Content-Type": "image/png"},
                is_base64_encoded=True,
                params=params,
                diagram=diagram
            )

    # Catch all exceptions and then handle by type
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        error_type = e.__class__.__name__
        
        # Determine the status code based on error type
        status_code = 500  # Default as server error
        if error_type == 'InvalidDatapackException':
            status_code = 400
            logger.info(f"Invalid datapack: {error_msg}")
            emit_exception_metric('InvalidDatapackException')
            
            # Format user-friendly message
            if "Pick from One of the Following" in error_msg:
                # The error message already has the list of valid options
                user_friendly_error = error_msg
            else:
                # Add more context if needed
                user_friendly_error = f"Datapack configuration invalid. {error_msg}"
        
        elif error_type == 'InvalidConfigurationException':
            status_code = 400
            logger.info(f"Invalid configuration: {error_msg}")
            emit_exception_metric('InvalidConfigurationException')
            
            # Format user-friendly message
            if "Pick from One of the Following" in error_msg or "please provide a valid" in error_msg.lower() or "valid" in error_msg.lower():
                # The error message already has the list of valid options
                user_friendly_error = error_msg
            else:
                # Add more context if needed
                user_friendly_error = f"Configuration invalid. {error_msg}"
                
                # Check for specific model or value errors that might need more context
                if "valid model" in error_msg.lower():
                    user_friendly_error = f"Model configuration invalid. {error_msg}"
                elif "valid cards" in error_msg.lower():
                    user_friendly_error = f"Cards configuration invalid. {error_msg}"
        
        elif error_type == 'RackDiagramException':
            status_code = 400
            logger.info(f"Rack diagram error: {error_msg}")
            emit_exception_metric('RackDiagramException')
            
            # Format user-friendly message
            if "Pick from One of the Following" in error_msg or "please provide a valid" in error_msg.lower() or "valid" in error_msg.lower():
                # The error message already has the list of valid options
                user_friendly_error = error_msg
            else:
                # Add more context if needed
                user_friendly_error = f"Rack diagram configuration invalid. {error_msg}"
        
        else:
            # Handle other exceptions as server errors
            status_code = 500
            logger.error(f"Server error: {error_msg}")
            logger.error(f"Stack trace: {stack_trace}")
            emit_exception_metric('ServerError')
            
            # Format user-friendly message for server errors
            if "Pick from One of the Following" in error_msg or "please provide a valid" in error_msg.lower() or "valid" in error_msg.lower():
                # The error message already has the list of valid options
                user_friendly_error = error_msg
            else:
                # Check for specific error types to provide more context
                if "datapacks" in error_msg.lower() or "dp" in error_msg.lower():
                    user_friendly_error = f"Datapack configuration invalid. {error_msg}"
                elif "model" in error_msg.lower():
                    user_friendly_error = f"Model configuration invalid. {error_msg}"
                elif "card" in error_msg.lower() or "pci" in error_msg.lower():
                    user_friendly_error = f"Cards configuration invalid. {error_msg}"
                else:
                    user_friendly_error = f"Configuration error: {error_msg}"
        
        # Log stack trace and request parameters
        logger.debug(f"Stack trace: {stack_trace}")
        logger.info(f"Request parameters: {json.dumps(params)}")
        
        # Return appropriate response based on request format
        if 'json' in params and params['json']:
            data = {}
            if diagram:
                try:
                    data["config"] = diagram.config
                    data["ports"] = all_ports
                except Exception as e:
                    logger.error(f"Error adding diagram details to error response: {str(e)}")
            
            data["error"] = user_friendly_error
            data["error_type"] = error_type
            data["execution_duration"] = time.time() - program_time_s
            data["params"] = params
            data["image_type"] = None
            data["image"] = None

            return {
                    "statusCode": status_code,
                    "body": json.dumps(data, indent=4),
                    "headers": {"Content-Type": "application/json",
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'GET'} }

        else:
            img = text_to_image(user_friendly_error)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

            return {
                "statusCode": status_code,
                "body": img_str,
                "headers": {"Content-Type": "image/png",
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Methods': 'GET'},
                "isBase64Encoded": True
            }
    
