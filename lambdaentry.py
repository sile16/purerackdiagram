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
import queue
import logging
from threading import Thread
import purerackdiagram
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import os
from pprint import pformat

logger = logging.getLogger()
logger.setLevel(logging.INFO)

version = 4
program_time_s = time.time()


def text_to_image(text, width):
    root_path = os.path.dirname(purerackdiagram.__file__)
    ttf_path = os.path.join(root_path, "Lato-Regular.ttf")
    font = ImageFont.truetype(ttf_path, size=36)
    color = (255, 255, 255, 220)

    # get each line of the text
    lines = text.splitlines()

    x = 10  # x Margin
    y = 20  # y margin
    # we use h and g becasue they are the tallest and lowest letters
    line_height = font.getsize('hg')[1]
    #  all lines plus top and bottom margin.
    total_height = line_height * len(lines) + y * 2
    total_width = max([font.getsize(line)[0] for line in lines]) + 2 * x

    img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for line in lines:
        # draw the line on the image
        draw.text((x, y), line, fill=color, font=font)

        # update the y position so that we can use it for next line
        y = y + line_height

    return img


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        logger.info(
            '{:>5}  Duration: {:.2f} ms, Start: {:.2f} - {:.2f}'.format(
                method.__name__,
                (te - ts) * 1000,
                (ts - program_time_s)*1000,
                (te - program_time_s)*1000))
        return result
    return timed


@timeit
def build_img(q, loop, diagram, params):
    """ this is a wrapper around the simple diagram.get_image to
        to allow it to be ran in a thread and to be cancelleable."""
    try:
        img = loop.run_until_complete(diagram.get_image())
        q.put({'name': 'build', 'img': img})
    except RuntimeError:
        logging.info('CancelledError')

    return


@timeit
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

        result_queue = queue.Queue()

        # doing this out here so we can stop the loop if necessary.
        loop = asyncio.get_event_loop()
        build_img_thread = Thread(target=build_img, args=(result_queue,
                                                          loop,
                                                          diagram,
                                                          params))

        # start build thread
        build_img_thread.start()

        # block until either the image is found in s3 cache,
        # or we built the image locally
        first_result = result_queue.get()

        # we built the image first
        if first_result['name'] == 'build':
            img = first_result['img']

            # reformat image to be passed back directly to API caller
            buffered = BytesIO()
            img.save(buffered, format="PNG")

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
