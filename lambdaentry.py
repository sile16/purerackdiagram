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
import purerackdiagram
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

version = 4
program_time_s = time.time()


def text_to_image(text, width):
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



def handler(event, context):
    """ This is the entry point for AWS Lambda, API Gateway
    We start two threads, 1 to check to see if this config already exists in S3
    and another that starts building the imgae.  Which ever one finishes first
    is returned.  Either a binary image streamed directly back or a 403
    redirect to the s3 object.  After generating the image,
    it's uploaded to s3 as a cache.
    """
    global program_time_s
    program_time_s = time.time()

    try:
        if ("queryStringParameters" not in event
                or event["queryStringParameters"] is None):

            return {"statusCode": 500,
                    "body": "no query params. event={} and context={}".format(
                        event,
                        vars(context))}

        params = event["queryStringParameters"]

        # Initialize our diagram from the params, parse all the params
        diagram = purerackdiagram.get_diagram(params)

        # do the work to generate the image
        img = asyncio.run(diagram.get_image())

        # resize if too large:
        # will break google slides if file is too big
        max_height = 4604
        if img.size[1] > max_height:
            wpercent = (max_height/float(img.size[1]))
            hsize = int((float(img.size[0]) * float(wpercent)))
            img = img.resize((hsize, max_height), Image.ANTIALIAS)

        # reformat image to be passed back directly to API caller
        buffered = BytesIO()
        img.save(buffered, format="PNG")

        # do we want a visio template or the raw image:
        if 'vssx' in params and params['vssx']:
            ru = diagram.config['ru']
            h_inches = "{:.2f}".format(ru*1.75)

            # building a visio template
            root_path = os.path.dirname(__file__)
            vssx_path = os.path.join(root_path, "vssx/vssx_template.zip")
            master1_template_path = os.path.join(root_path, "vssx/master1_template.xml")
            masters_template_path = os.path.join(root_path, "vssx/masters_template.xml")

            # adjust the stencil height
            master1 = None
            with open(master1_template_path, 'r') as mf:
                master1 = mf.read()

            master1 = master1.replace('<template_h_in>', h_inches)
            master1 = master1.replace('<template_h_u>', str(ru))

            # create uniqueID for this template
            masters = None
            with open(masters_template_path, 'r') as mf:
                masters = mf.read()
            
            stamp = int((time.time())*10)
            # Get only the right 7 digits of HEX
            unique_id = f"{stamp:07X}"[-7:]
            masters = masters.replace('<template_unique_id>', unique_id)
            
            # do import down here, so we don't have load if not needed
            import zipfile
            import io

            # read file into memory
            zipfile_raw = None
            with open(vssx_path, 'rb') as vssx_file:
                zipfile_raw = vssx_file.read()

            zipfile_buffered = io.BytesIO(zipfile_raw)

            # add the image and master1 file to zip file.
            with zipfile_buffered as zfb:
                with zipfile.ZipFile(zfb, 'a') as zipf:
                    # Add a file located at the source_path to the destination within the zip
                    zipf.writestr('visio/media/image1.png', buffered.getvalue())
                    zipf.writestr('visio/masters/master1.xml', master1)
                    zipf.writestr('visio/masters/masters.xml', masters)
                    zipf.close()
                zip_str = base64.b64encode(zfb.getvalue()).decode('utf-8')

            # when running in lambda we HAVE to wait until
            # upload done before returning
            return_data = {
                "statusCode": 200,
                "body": zip_str,
                "headers": {"Content-Type": "application/vnd.ms-visio.stencil",
                            'content-disposition': 'attachment; filename="pure_diagram.vssx"'},
                "isBase64Encoded": True
            }

            return return_data

        else:

            # convert to base64 and encode utf-8
            # this is required for a binary object passed back
            # through amazon API gateway
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # when running in lambda we HAVE to wait until
            # upload done before returning
            return_data = {
                "statusCode": 200,
                "body": img_str,
                "headers": {"Content-Type": "image/png"},
                "isBase64Encoded": True
            }

            return return_data

    except Exception as e:
        error_msg = str(e)
        logger.error("{}\nOriginal Params: {}".format(error_msg, params))

        # return the error message as an image
        img = text_to_image(error_msg, 1024)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return {
            "statusCode": 200,
            "body": img_str,
            "headers": {"Content-Type": "image/png"},
            "isBase64Encoded": True
        }
