"""
Entry point for AWS Lambda, def handler()
Starts generating the rack image and checking for a cached version
at the same time.  Will return which ever is created or found first.

All AWS specific stuff and s3 caching is here.
"""
import time
from io import BytesIO
import asyncio
import base64
import logging
import os
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import uuid
import boto3
import math


import purerackdiagram

logger = logging.getLogger()
bucket_name = "images.purestorage"

use_s3_size_limit = 4  # useing 4MiB with base64 encoding to stay under 6MIB limit

log_level = os.getenv('log_level', 'WARNING').upper()

if len(logger.handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logger.setLevel(log_level)
else:
    logging.basicConfig(level=log_level)

VERSION = 5
program_time_s = time.time()



def upload_to_s3(buffered, extension, contenttype, disposition):
    """ Uploads a file to S3 """
    logger.debug("uploading to s3")
    s3 = boto3.client('s3')
    
    unique_key = str(uuid.uuid4())
    file_key = f"cache/{unique_key}.{extension}"
    
    # Reset the buffer's pointer to the beginning
    buffered.seek(0)

    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=buffered.getvalue(),
            ContentType=contenttype,
            ContentDisposition=disposition
        )
    except Exception as e:
        # Log the exception or handle as you see fit
        print(f"Error uploading to S3: {e}")
        return None

    # Return the complete S3 URL or just the file key based on your requirements
    return f"https://s3.amazonaws.com/{bucket_name}/{file_key}"


def text_to_image(text):
    root_path = os.path.dirname(purerackdiagram.__file__)
    ttf_path = os.path.join(root_path, "Lato-Regular.ttf")
    font = ImageFont.truetype(ttf_path, size=36)
    color = (255, 255, 255, 255)
    background_color = (0, 0, 0, 255)

    # get each line of the text
    lines = text.splitlines()

    x = 10  # x Margin
    y = 20  # y margin
    # we use h and g becasue they are the tallest and lowest letters
    line_height = font.getsize('hg')[1]
    #  all lines plus top and bottom margin.
    total_height = line_height * len(lines) + y * 2
    total_width = max([font.getsize(line)[0] for line in lines]) + 2 * x

    img = Image.new('RGBA', (total_width, total_height), background_color)
    draw = ImageDraw.Draw(img)
    for line in lines:
        # draw the line on the image
        draw.text((x, y), line, fill=color, font=font)

        # update the y position so that we can use it for next line
        y = y + line_height

    return img

# function to draw a triangle to a PIL image using polygon
def draw_triangle_up(draw, x, y, size, color):
    draw.polygon([(x, y - size), (x + size, y + size), (x - size, y + size)],
                 fill=color, outline=color)
    
def draw_triangle_down(draw, x, y, size, color):
    draw.polygon([(x, y + size), (x + size, y - size), (x - size, y - size)],
                 fill=color, outline=color)


def draw_diamond(draw, x, y, size, color):
    # Top triangle (pointing up)
    draw.polygon([(x, y - size), (x + size, y), (x - size, y)],
                 fill=color, outline=color)
    # Bottom triangle (pointing down)
    draw.polygon([(x, y + size), (x + size, y), (x - size, y)],
                 fill=color, outline=color)



def draw_pentagon(draw, x, y, size, color):
    # Calculate vertices for the pentagon
    vertices = []
    for i in range(5):
        angle = 2 * math.pi * i / 5
        vertex_x = x + size * math.sin(angle)
        vertex_y = y - size * math.cos(angle)  # Subtracting since the y-coordinates in most graphic systems increase downwards
        vertices.append((vertex_x, vertex_y))

    draw.polygon(vertices, fill=color, outline=color)


def handler(event, context):
    """ Lambda Entry
    """
    global program_time_s
    program_time_s = time.time()
    params = {}
    diagram = None

    try:
        if ("queryStringParameters" not in event
                or event["queryStringParameters"] is None):
            
            return {
                'statusCode': 200,
                'headers': {
                    "Content-Type": "text/plain",
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET'
                },
                'body': 'Hello from Lambda!' }

        params = event["queryStringParameters"]

        # Initialize our diagram from the params, parse all the params
        diagram = purerackdiagram.get_diagram(params)
        logger.debug(f"diagram: {diagram}")

        # do the work to generate the image
        img = asyncio.run(diagram.get_image())
        logger.debug("img created Succefully")

        # save original image dimensions needed for port pixel->in calculation
        img_original_size = img.size
        draw_ports = False
        if 'ports' in params and (
            params['ports'] == True or
            params['ports'].upper() == "TRUE"
            or params['ports'].upper() == "YES"):
            draw_ports = True
        


        

        logger.debug("adding ports to image")
        # Draw
        draw = ImageDraw.Draw(img)
        

        for p in diagram.ports:
            services = p.get('services', [])
            size = 16
            symbol_name = ""
            symbol_shape = ""
            symbol_color = ""
                

            if 'management' in services and len(services) == 1:
                #dedicated management port
                #on FlashBlade some ports have management & data servcies so we skip those with the len==1
                #color = '#D90368'
                #draw.ellipse((p['loc'][0] - size, p['loc'][1] - size,
                #          p['loc'][0] + size, p['loc'][1] + size),
                #         fill=color, outline=color)
                color = '#00B2A9'
                if draw_ports:
                    draw_triangle_up(draw, p['loc'][0], p['loc'][1], size, color)


                p['symbol_name'] = "Management"
                p['symbol_shape'] = "triangle_up"
                p['symbol_color'] = color

        

            elif services and services[0] == 'replication':
                color = '#934DD6'
                if draw_ports:
                    draw_triangle_up(draw, p['loc'][0], p['loc'][1], size, color)

                p['symbol_name'] = "Replication"
                p['symbol_shape'] = "triangle_up"
                p['symbol_color'] = color

            elif services and services[0] == 'shelf' :
                color = '#FCDC4D'
                if draw_ports:
                    draw_triangle_down(draw, p['loc'][0], p['loc'][1], size, color)

                p['symbol_name'] = "Shelf"
                p['symbol_shape'] = "triangle_down"
                p['symbol_color'] = color
            
                
            elif 'port_type' not in p:
                # we need port type to check any further info.
                continue
            
            elif p['port_type'] == 'fc':
                # pick the color :
                # use Pillow to define a color with rgb values: 235, 149, 52
                # then convert to hex
                # https://stackoverflow.com/questions/3380726/converting-a-rgb-color-tuple-to-a-six-digit-code-in-python
                # color #FE5000
                color = '#FE5000'
                
                #draw_triangle_up(draw, p['loc'][0], p['loc'][1], size, color)
                if draw_ports:
                    draw.rectangle((p['loc'][0] - size, p['loc'][1] - size,
                            p['loc'][0] + size, p['loc'][1] + size),
                            fill=color, outline=color)
                
                p['symbol_name'] = "Fibre Channel"
                p['symbol_shape'] = "square"
                p['symbol_color'] = color

            elif p['port_type'] == 'sas':
                color = 'blue'
                #draw a rectangle
                if draw_ports:
                    draw.rectangle((p['loc'][0] - size, p['loc'][1] - size/2,
                            p['loc'][0] + size, p['loc'][1] + size/2),
                            fill=color, outline=color)
                
                p['symbol_name'] = "SAS"
                p['symbol_shape'] = "rectangle"
                p['symbol_color'] = color

    
                continue
                
            
            
            elif p['port_type'] == 'eth_roce':
                color = "#FD9627"
                #draw triangle up
                if draw_ports:
                    draw_triangle_up(draw, p['loc'][0], p['loc'][1], size, color)

                p['symbol_name'] = "Ethernet / RoCE"
                p['symbol_shape'] = "triangle_up"
                p['symbol_color'] = color

            elif p['port_type'] == 'eth':
                color = '#D90368'
                #draw triangle down
                if draw_ports:
                    draw_triangle_up(draw, p['loc'][0], p['loc'][1], size, color)

                p['symbol_name'] = "Ethernet"
                p['symbol_shape'] = "triangle_up"
                p['symbol_color'] = color
                
            else:
                logger.warning(f"Unknown port type: {p['port_type']}")

                # draw a diamond with color of green
                # color = 'green'
                
                # draw.polygon([(p['loc'][0], p['loc'][1] - size),
                #              (p['loc'][0] + size, p['loc'][1]),
                #              (p['loc'][0], p['loc'][1] + size),
                #              (p['loc'][0] - size, p['loc'][1])],
                #             fill=color, outline=color)
        ## end of ports for loop     
                    

        # resize if too large:
        # will break google slides if file is too big
        max_height = 4604
        if img.size[1] > max_height:
            logger.debug("resizing image")
            wpercent = (max_height / float(img.size[1]))
            hsize = int((float(img.size[0]) * float(wpercent)))
            img = img.resize((hsize, max_height), Image.ANTIALIAS)

            #Also need to resize all the port locations in the json
            #Since we are resizing the image
            if 'ports' in params and (
                params['ports'] == True or
                params['ports'].upper() == "TRUE"
                or params['ports'].upper() == "YES"):

                #resizing the port locations
                for p in diagram.ports:
                     p['loc'] = (int(p['loc'][0] * wpercent), int(p['loc'][1] * wpercent))



        # reformat image to be passed back directly to API caller
        logger.debug("converting image to base64")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        size_of_buffered_in_mib = len(buffered.getvalue()) / ( 1024 * 1024 )
        logger.debug(f"Max size const: {use_s3_size_limit} MiB") 
        logger.debug(f"size of buffered image: {size_of_buffered_in_mib} MiB")

        # do we want a visio template or the raw image:
        if 'vssx' in params and params['vssx']:
            logger.debug("creating a visio template")
            ru = diagram.config['ru']
            h_inches = "{:.2f}".format(ru*1.75)

            # generate a name for this config
            items = []
            name = ""
            if params['model'] == 'fb':
                name += "fb"
                stencil_name = "Pure FlashBlade"
                items = ['chassis', 'face', 'direction', 'efm']
            else:
                # this is FlashArray
                stencil_name = "Pure FlashArray"
                name += params['model']
                name += "_" + params['datapacks'].replace("/", '-')
                items = ['face', 'direction']

            for n in items:
                name += "_" + str(diagram.config[n])

            # building a visio template
            root_path = os.path.dirname(__file__)
            vssx_path = os.path.join(root_path, "vssx/vssx_template.zip")
            master1_template_path = os.path.join(
                root_path, "vssx/master1_template.xml")
            masters_template_path = os.path.join(
                root_path, "vssx/masters_template.xml")

            connection_template = """
                <Row T='Connection' IX='{}'>
                    <Cell N='X' V='{:.10f}' U='IN' F='Width*{:.10f}'/>
                    <Cell N='Y' V='{:.10f}' U='IN' F='Height*{:.10f}'/>
                    <Cell N='DirX' V='0'/>
                    <Cell N='DirY' V='0'/>d
                    <Cell N='Type' V='0'/>
                    <Cell N='AutoGen' V='0'/>
                    <Cell N='Prompt' V='' F='No Formula'/>
                </Row>
                """
            ports = diagram.ports

            ix = 2
            connection_points = ""
            for p in ports:
                x_w = 1.0 * (p['loc'][0] / img_original_size[0])
                x_in = 19 * x_w
                # I think the y 0,0 location is bottom left
                # all my images are from top left, so need to reverse Y loc
                y_h = 1 - 1.0 * (p['loc'][1] / img_original_size[1])
                y_in = ru * 1.75 * y_h

                connection_points += connection_template.format(
                    ix, x_in, x_w, y_in, y_h)
                ix += 1

            # adjust the stencil height
            master1 = None
            with open(master1_template_path, 'r') as mf:
                master1 = mf.read()

            master1 = master1.replace('<template_h_in>', h_inches)
            master1 = master1.replace('<template_h_u>', str(ru))
            master1 = master1.replace('<template_name>', stencil_name)
            master1 = master1.replace(
                '<additional_connection_points>', connection_points)

            # create uniqueID for this template
            masters = None
            with open(masters_template_path, 'r') as mf:
                masters = mf.read()

            stamp = int((time.time())*10)
            # Get only the right 7 digits of HEX
            unique_id = f"{stamp:07X}"[-7:]
            masters = masters.replace('<template_unique_id>', unique_id)
            masters = masters.replace('<template_name>', stencil_name)

            # do import down here, so we don't have load if not needed
            import zipfile
            import io

            # read file into memory
            logger.debug("zipping the vssx file")
            zipfile_raw = None
            with open(vssx_path, 'rb') as vssx_file:
                zipfile_raw = vssx_file.read()

            zipfile_buffered = io.BytesIO(zipfile_raw)

            # add the image and master1 file to zip file.
            with zipfile.ZipFile(zipfile_buffered, 'a') as zipf:
                # Add a file located at the source_path to the destination within the zip
                zipf.writestr('visio/media/image1.png', buffered.getvalue())
                zipf.writestr('visio/masters/master1.xml', master1)
                zipf.writestr('visio/masters/masters.xml', masters)
                    
            zip_file_size = zipfile_buffered.tell()
            logger.debug(f"zip file size: {zip_file_size}")
            zipfile_buffered.seek(0)

            if zip_file_size > use_s3_size_limit:  # If more than 5.5 MiB
                
                logger.debug("uploading vssx to s3")
                
                s3_link = upload_to_s3(zipfile_buffered, "vssx", "application/vnd.ms-visio.stencil", f'attachment; filename="{name}.vssx"')
                
                return {
                    "statusCode": 302,
                    "headers": {
                        "Location": s3_link, 
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET'
                    }

                }
            zip_str = base64.b64encode(zipfile_buffered.getvalue()).decode('utf-8')

            # when running in lambda we HAVE to wait until
            # upload done before returning
            content_disposition = 'attachment; filename="{}.vssx"'.format(name)
            return_data = {
                "statusCode": 200,
                "body": zip_str,
                "headers": {"Content-Type": "application/vnd.ms-visio.stencil",
                            'content-disposition': content_disposition,
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Methods': 'GET'},
                "isBase64Encoded": True
            }

            return return_data

        else:
            # convert to base64 and encode utf-8
            # this is required for a binary object passed back
            # through amazon API gateway
            
            data = {"image_type": "png",
                    "config": diagram.config,
                    "ports": diagram.ports,
                    "execution_duration": time.time() - program_time_s,
                    "error": None,
                    "image_size": img.size,
                    "image_mib": size_of_buffered_in_mib,
                    "params": params, 
                    "image": None}
            
            
            import json 

            if 'json_only' in params:
                logger.debug("returning json only")
                return {
                    "statusCode": 200,
                    "body": json.dumps(data, indent=4),
                    "headers": {"Content-Type": "application/json", 
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'GET'} }
            
            logger.debug("base64 encoding image")
            img_str = ""

            if size_of_buffered_in_mib > use_s3_size_limit:
                logger.debug("image is too large, uploading to s3")
                link = upload_to_s3(buffered, "png", "image/png", 'inline')
                data["image"] = link
                data['image_type'] = "link"
            else:
                data["image"] = base64.b64encode(buffered.getvalue()).decode('utf-8')
                data['image_type'] = "png"

            if 'json' in params and params['json']:
                logger.debug("returning json")
                return {
                    "statusCode": 200,
                    "body": json.dumps(data, indent=4),
                    "headers": {"Content-Type": "application/json", 
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'GET'}
                }

            # when running in lambda we HAVE to wait until
            # upload done before returning
            if size_of_buffered_in_mib > use_s3_size_limit:
                logger.debug("returning image link")
                
                return {
                    "statusCode": 302,
                    "headers": {"Location": data["image"], 
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'GET'}
                }
            
            logger.debug("returning image in png format")
            return {
                "statusCode": 200,
                "body": data['image'],
                "headers": {"Content-Type": "image/png", 
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Methods': 'GET'},
                "isBase64Encoded": True
            }

    except Exception as except_e:
        error_msg = str(except_e)
        logger.error("{}\nOriginal Params: {}".format(error_msg, params))

        if 'json' in params and params['json']:

            data = {}
            if diagram:
                data["config"] = diagram.config
                data["ports"] = diagram.ports
            
            data["error"] = error_msg
            data["execution_duration"] = time.time() - program_time_s
            data["params"] = params
            data["image_type"] = None
            data["image"] = None

            import json
            return {
                    "statusCode": 200,
                    "body": json.dumps(data, indent=4),
                    "headers": {"Content-Type": "application/json",
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'GET'} }
        
        else:
            # return the error message as an image
            # returning the error as an image so that it can be
            logger.debug("converting the error into an image")
            img = text_to_image(error_msg)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

            return {
                "statusCode": 200,
                "body": img_str,
                "headers": {"Content-Type": "image/png",
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Methods': 'GET'},
                "isBase64Encoded": True
            }
