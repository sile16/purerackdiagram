"""
Builds a rack diagram and caches results.
"""
import os
import sys
from PIL import Image
import PIL.Image
from io import BytesIO
import asyncio
import botocore
import aiobotocore
from botocore.exceptions import ClientError
import hashlib
import AIOS3Cache
from datetime import datetime
startTime = datetime.now()


#size in pixels of 1 RU
RU = 765 /3
WIDTH = 2844
BORDER = 8

loop = asyncio.get_event_loop()
session = aiobotocore.get_session(loop=loop)

bucket = "images.purestorage"
version = "v1.0"
cached_bucket = None

tasks = []

class RackImage(AIOS3Cache.AIOS3CachedObject):

    def __init__(self, key_or_config):
        self.id = None
        self.config = None
        self.img = None

        if isinstance(key_or_config, dict):
            #this is a cached generated image, we will generate a key
            self.config = key_or_config
            self.key = 'cache/{}.png'.format(self.generate_id())
        else:
            self.key = key_or_config
        
        super().__init__(self.key, cached_bucket)
    

    async def get_image(self):
        if self.img:
            return self.img
        
        await self.make_exist()
        self.img = Image.open(await self.get_obj_data())
        return self.img

    async def get_image_key(self):
        await self.make_exist()
        return self.key
        
    async def make_exist(self):
        async with self.primary_obj.make_lock:
            if await self.exists():
                return
            self.img = await self.create_image()
            #we need to upload
            buffer = BytesIO()
            self.img.save(buffer, "PNG")
            # run this in the future, but don't block now, we have the image locally.
            global tasks
            tasks.append(asyncio.create_task(self.put_obj_data(buffer)))

    async def create_image(self):
        raise Exception("Need to overload create function")

    def generate_id(self):
        config_str = version
        for k, v in self.config.items():
            config_str += "{}{}".format(k,v)
        hashstr = hashlib.sha1(config_str.encode('utf-8')).hexdigest()[:20]
        self.id = self.__class__.__name__ + hashstr
        return self.id


class FAShelves(RackImage):
    
    def __init__(self, params):
        super().__init__(params)
        #config = self.parseParams(params)


class FAChassis(RackImage):
    
    def __init__(self, params):
        super().__init__("png/pure_fa_m_back.png")
        #parse params into a self.config
        #config = self.parseParams(params)
    
    async def create_image(self):
        return await self.get_image()


class FADiagram(RackImage):

    def __init__(self, params):
        super().__init__(params)
        self.params = params
        #config = self.parseParams(params)
    
    async def create_image(self):
        ch0 = FAChassis(self.params)
        return await ch0.get_image()


async def build_diagram(params):
    session = aiobotocore.get_session(loop=loop)
    key = ""
    async with session.create_client('s3') as client:
        global cached_bucket
        cached_bucket = AIOS3Cache.AIOS3CachedBucket(client, bucket)
        diagram = FADiagram(params)
        key = await diagram.get_image_key()
        
        #complete all the uploads
        await asyncio.gather(*tasks)

    return key


def handler(event, context):
    
    if "queryStringParameters" not in event or event["queryStringParameters"] == None :
        return {"statusCode": 200, "body":"no query params"}

    params = event["queryStringParameters"]
    key = loop.run_until_complete(build_diagram(params))

    if 'test' in event:
        print("time elapsed: {}".format(datetime.now() - startTime))
        print("head: {}   get: {}   put: {}".format(
            AIOS3Cache.total_head,
            AIOS3Cache.total_gets,
            AIOS3Cache.total_puts
        ))

    return({"statusCode": 302, 
            "body":"",
            "headers" : {
                "Location": "https://s3.amazonaws.com/{}".format(key)
                }
    })