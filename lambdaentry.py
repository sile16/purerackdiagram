"""
Entry point for AWS Lambda, def handler()
Starts generating the rack image and checking for a cached version
at the same time.  Will return which ever is created or found first.

All AWS specific stuff and s3 caching is here.
"""
import time
import os
import sys
from io import BytesIO
import asyncio
import concurrent
import base64
import boto3
import queue

import logging
import hashlib
from threading import Thread
from concurrent.futures import CancelledError
import purerackdiagram


logger = logging.getLogger()
logger.setLevel(logging.INFO)

version = 3


s3_base_url = 'https://s3.amazonaws.com/'
bucket = 'images.purestorage'

program_time_s = time.time()
def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        logger.info('{:>5}  Duration: {:.2f} ms, Start: {:.2f} - {:.2f}'.format(
                    method.__name__,
                    (te - ts) * 1000,
                    (ts - program_time_s)*1000,
                    (te - program_time_s)*1000 ))
        return result
    return timed

def generate_id(config):
    """Create a hash of the config to map to a cached object in s3"""
    config_str = "{}{}".format(version, config)
    return hashlib.sha1(config_str.encode("utf-8")).hexdigest()[:20]

@timeit
def build_img(q, loop, diagram, params):
    """ this is a wrapper around the simple diagram.get_image to 
        to allow it to be ran in a thread and to be cancelleable."""
    try:
        if 'local_delay' in params:
            logging.info("Local delay of {}".format(params['local_delay']))
            time.sleep(params['local_delay'])
        img = loop.run_until_complete(diagram.get_image())
        q.put({'name':'build','img':img})
    except RuntimeError:
        logging.info('CancelledError')
 
    return

@timeit
def check_cache_and_upload(q, key, img_queue):
    """ this checks to see if an image exists, if so alert main thread, so it can
        redirect the client to this s3 key.  Otherwise, wait until the image is
        generated, pull from the img_queue and upload to s3 for next time. """

    session = boto3.session.Session()
    s3 = session.client('s3')
    
    if key_exists(s3, key):
        logger.info("We found a cache object!! Yeah")
        q.put({'name':'cache','result':True})
        #just in case build still finished before us, pull the img from queue
        img_queue.get()
        img_queue.task_done()
    else:
        #Only if we didn't find it in cache we will upload it.
        img = img_queue.get()
        upload_img(s3, img, key)
        img_queue.task_done()

@timeit
def key_exists(s3, key):
    """ check if a key exists in s3 bucket """
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=key
    )
    for obj in response.get('Contents', []):
        if obj['Key'] == key:
            #we found our cache object
            return True
    return False


@timeit
def upload_img(s3, img, key):
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    s3.put_object(Bucket=bucket, Key=key, Body=buffer, ContentType='image/png')
    logger.info("S3 object uploaded.")


@timeit
def handler(event, context):
    """ This is the entry point for AWS Lambda, API Gateway
    We start two threads, 1 to check to see if this config already exists in S3
    and another that starts building the imgae.  Which ever one finishes first
    is returned.  Either a binary image streamed directly back or a 403 redirect to
    the s3 object.  After generating the image, it's uploaded to s3 as a cache.
    """
    global program_time_s
    program_time_s = time.time()

    try:
        if ("queryStringParameters" not in event
        or event["queryStringParameters"] is None):

            return {"statusCode": 500, "body": "no query params. event={} and context={}".format(event,vars(context))}
        
        params = event["queryStringParameters"]

        #Initialize our diagram from the params, parse all the params
        diagram = purerackdiagram.get_diagram(params)

        cache_key = "cache/{}".format(generate_id(diagram.config))
        
        result_queue = queue.Queue()
        img_queue = queue.Queue()

        #doing this out here so we can stop the loop if necessary.
        loop = asyncio.get_event_loop()
        check_cache_and_upload_thread = Thread(target=check_cache_and_upload, 
                                               args=(result_queue, cache_key, img_queue))
        build_img_thread = Thread(target=build_img, args=(result_queue, loop, diagram, params))
        
        #start both threads concurrently
        check_cache_and_upload_thread.start()
        build_img_thread.start()
        
        #block until either the image is found in s3 cache, or we built the image locally
        first_result = result_queue.get()
        if first_result['name'] == 'cache':
            #stop trying to build our image
            for task in asyncio.Task.all_tasks():
                task.cancel()
                #logging.info('bye, exiting in a minute...')  
            try:
                loop.stop()
            except:
                pass

            #stuff empty object into queue, so that s3_check_and_upload thread closes nicely.
            img_queue.put(None)
            
            return {
                "statusCode": 301,
                "body": "",
                "headers": {"Location": "{}{}/{}".format(s3_base_url,bucket,cache_key) } 
            }

        #we built the image first
        elif first_result['name'] == 'build':
            img = first_result['img']

            #put image into image queue to be uploaded to s3 in other thread
            img_queue.put(img)
            
            #reformat image to be passed back directly to API caller
            buffered = BytesIO()
            img.save(buffered, format="PNG")
        
            #convert to base64 and encode utf-8
            #this is required for a binary object passed back through amazon API gateway
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            #when running in lambda we HAVE to wait until upload done before returning
            img_queue.join()
            return_data = {
                    "statusCode": 200,
                    "body": img_str,
                    "headers": {"Content-Type": "image/png"},
                    "isBase64Encoded": True
                }

            return return_data

    
    except Exception as e:
        logger.error("{}\nOriginal Params: {}".format(e, params))
        return {
            "statusCode": 500,
            "body": "{}".format(e),
            "headers": {"Content-Type": "text/plain"}
        }