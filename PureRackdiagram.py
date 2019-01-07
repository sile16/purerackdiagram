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
version = "v1.1"
cached_bucket = None

tasks = []

class RackImage(AIOS3Cache.AIOS3CachedObject):

    def __init__(self, key_or_config):
        self.id = None
        self.params = None
        self.img = None

        if isinstance(key_or_config, dict):
            #this is a cached generated image, we will generate a key
            self.key = 'cache/{}.png'.format(self.generate_id(key_or_config))
        else:
            self.key = key_or_config
        
        super().__init__(self.key, cached_bucket)
    

    async def get_image(self):
        if self.img:
            return self.img
        
        await self.make_exist()
        if self.img:
            return self.img
        else:
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

    def generate_id(self, config):
        config_str = '{}{}'.format(version, config)
        hashstr = hashlib.sha1(config_str.encode('utf-8')).hexdigest()[:20]
        self.id = self.__class__.__name__ + hashstr
        return self.id


class FAShelf(RackImage):
    
    def __init__(self, params):
        self.config = params
        super().__init__(self.config)
        #config = self.parseParams(params)
    
    async def create_image(self):
        c = self.config
        starting_str = 'png/pure_fa_{}_shelf_{}.png'.format(c['shelf_type'],c['face'])
        return await RackImage(starting_str).get_image()


class FAChassis(RackImage):
    
    def __init__(self, params):
        config = params.copy()
        del config['shelves']
        self.config = config
        self.start_img_event = asyncio.Event()
        super().__init__(config)
    
    async def create_image(self):
        c = self.config
        key = "png/pure_fa_{}".format(c['gen_short'])
        
        if c['face'] == 'front' and c['bezel']:
            key += '_bezel.png'
            return await RackImage(key).get_image()
        
        #not doing bezel
        key += "_{}.png".format(c['face'])

        tasks = []
        tasks.append(self.get_base_img(key))

        if c['face'] == 'front':
            tasks.append(self.add_drives())
            tasks.append(self.add_nvram())
        else:
            tasks.append(self.add_cards())
            tasks.append(self.add_mezz())
        
        #run all the tasks concurrently
        await asyncio.gather(*tasks)
        return self.tmp_img

    
    async def get_base_img(self, key):
        self.tmp_img = await RackImage(key).get_image()
        self.start_img_event.set()
            
    
    async def add_nvram(self):
        
        if self.config['model'] < 20:
            return
        
        nvram_img = RackImage("png/pure_fa_x_nvram.png").get_image
        await self.start_img_event.wait()
        self.tmp_img.past(nvram_img, (50,300))

    async def add_cards(self):
        pci0 = (2069,87)
        pci1 = (1199,90)
        pci2 = (1199,204)
        pci3 = (2069,204)


        tasks = []



        await self.start_img_event.wait()

        

    async def add_mezz(self):
        if self.config['gen_short'] != 'x':
            return
        key = 'png/pure_fa_x_{}.png'.format(self.config['mezz'])
        mezz_img = await RackImage(key).get_image()
        await self.start_img_event.wait()
        self.tmp_img.paste(mezz_img, (595,50))
        self.tmp_img.paste(mezz_img, (595,430))





    async def add_drives(self):

        await self.start_img_event.wait()





class FADiagram(RackImage):
    
    def __init__(self, params):
        #front or back
        config = {}
        config['face'] = params.get('face','front')
        config['bezel'] = params.get('bezel',False)
        config['mezz'] = params.get('mezz','emezz')
        config['pci1'] = params.get('pci1',None)
        config['pci2'] = params.get('pci2',None)
        config['pci3'] = params.get('pci3',None)
        config['model_str'] = params['model'].lower()
        config['direction'] = params.get('direction','up')
        config['gen_short'] = config['model_str'][3:4]
        config['model_num'] = int(config['model_str'][4:6])

        
        if 'r' in config['model_str'] and len(config['model_str']) > 7:
            config['model_release']= int(config['model_str'][7:8])
        else:
            config['model_release'] = 1

        shelves = []
        if 'shelves' in params:
            #Shelf of form "dfm-12,sas-24,sas-12,0"  for shelves
            #shelf type of form ""
            if config['gen_short'] == 'x' and config['model_num'] > 20:
                default_shelf_type = 'nvme'
            else:
                default_shelf_type = 'sas'
            for shelf in params['shelves'].split(','):
                shelf_type = default_shelf_type
                shelf_modules = 0
                for item in shelf.split('-'):
                    if item.isnumeric():
                        shelf_modules = int(item)
                    else:
                        if item == 'sas':
                            shelf_type = 'sas'
                        else:
                            shelf_type = 'nvme'
                shelves.append({'shelf_type': shelf_type, 
                                'modules': shelf_modules,
                                'face': config['face']})
        config['shelves'] = shelves

        self.config = config

        super().__init__(config)
    

    async def create_image(self):
        tasks = []

        tasks.append(FAChassis(self.config).get_image())
        for shelf in self.config['shelves']:
            tasks.append(FAShelf(shelf).get_image())

        #go get the cached versions or build images
        #this returns the results of the all the tasks in a list
        all_images = await asyncio.gather(*tasks)

        if self.config['direction'] == 'up':
            all_images.reverse()
    
        return  combine_images_vertically(all_images)



def combine_images_vertically(images):
    widths, heights = zip(*(i.size for i in images))

    total_height = sum(heights)
    total_width = max(widths)

    new_im = Image.new('RGB', (total_width, total_height))

    y_offset = 0
    for im in images:
        #center the x difference
        x_offset = int((total_width - im.size[0]) / 2)
        new_im.paste(im, (x_offset,y_offset))
        y_offset += im.size[1]
    
    return new_im




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
                "Location": "https://s3.amazonaws.com/{}/{}".format(bucket, key)
                }
    })