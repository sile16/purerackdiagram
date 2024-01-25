import yaml
import asyncio
import concurrent
# import time
import logging
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
# from io import BytesIO
import os
import purerackdiagram

logger = logging.getLogger()

cache = {}
cache_lock = asyncio.Lock()
root_path = os.path.dirname(purerackdiagram.__file__)
ttf_path = os.path.join(root_path, "Lato-Regular.ttf")

global_config = None
with open(os.path.join(root_path, 'config.yaml'), 'r') as f:
    global_config = yaml.full_load(f)
global_config['ttf_path'] = ttf_path


class RackImage():
    """This loads a file from disk and caches it.  If it's already been
    loaded it returns the cached object.  Originally, we were loading
    images from an S3 bucket, however, now to
    improve performance images are loaded
    directly from local FS.  So the benefit of this caching is questionable
    but is already written.  Probably could replace this whole class
    with img = Image.open(key)  lol!
    """

    def __init__(self, key):
        global root_path

        # key is the file name, s3 terminology.
        self.key = os.path.join(root_path, key)
        self.img = None
        self.io_lock = asyncio.Lock()

        # on object creation, see if this key has laready been requested.
        # potential race, if two object check but... worst case is we miss
        # a caching opportunity and just load twice.
        if key in cache:
            self.primary = False
            self.primary_obj = cache[key]
        else:
            cache[key] = self
            self.primary = True

    async def get_image(self):
        if not self.primary:
            return await self.primary_obj.get_image()

        # could be called by primary and secondary
        # objects, so secondary must wait here
        async with self.io_lock:

            # same image may be requested multiple times
            # when secondary comes through need to
            # return image that's already loaded
            if self.img:
                return self.img.copy()

            loop = asyncio.get_event_loop()

            # reading through asyncIO, it seems some OS
            # implementations are not truly Async!!!
            # now i'm going back to threads...
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(pool, self.load_img)

            return self.img.copy()

    def load_img(self):
        # load image from disk

        self.img = Image.open(self.key)
        
        # check and convet to RGBA:
        if self.img.format == 'PNG':
            # and is not RGBA
            if not self.img.mode == 'RGBA':
                logger.debug("!!Converting image {self.key} to RGBA")
                self.img = self.img.convert("RGBA")
            else:
                logger.debug("Image {self.key} already in RGBA")
        self.img.load()
           

        logger.debug("Loaded: {}".format(self.key))



def add_ports_at_offset(key, offset, all_ports, additional_keys={}):
    global global_config

    additional_keys = additional_keys.copy()
        
    if key in global_config:
        if 'ports' in global_config[key]:
            ports = global_config[key]['ports']
            for p in ports:
                new_port = p.copy()


                new_loc = (p['loc'][0] + offset[0], p['loc'][1] + offset[1])
                new_port['loc'] = new_loc
                # add additional keys
                
                for k in additional_keys:
                    new_port[k] = additional_keys[k]

                all_ports.append(new_port)

def combine_images_vertically(image_ports):
    """ Combines a list of PIL images vertically
        Args:
            images: List of PIL image objects to be combined
    """
    # pull out the images
    images = [ i['img'] for i in image_ports]
    widths, heights = zip(*(i.size for i in images))
    total_height = sum(heights)
    total_width = max(widths)

    logger.debug("Combining images vertically")
    new_im = Image.new("RGBA", (total_width, total_height))

    y_offset = 0
    all_ports = []
    for imp in image_ports:
        im = imp['img']
        ports = imp['ports']

        # center the x difference if an image is slightly smaller width
        x_offset = int((total_width - im.size[0]) / 2)
        new_im.paste(im, (x_offset, y_offset))

        
        #calculate new port location
        for p in ports:
            new_port = p.copy()
            new_loc = (p['loc'][0] + x_offset, p['loc'][1] + y_offset)
            new_port['loc'] = new_loc
            all_ports.append(new_port)

        y_offset += im.size[1]

    #convert from RGBA to RGB to reduce file size
    logger.debug("Converting image to RGB")
    new_im = new_im.convert('RGB')

    return new_im, all_ports


def apply_text(img, text, x_loc, y_loc, font_size=15, rotate_degrees=0):
    global ttf_path

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(ttf_path, size=font_size)
    w, _ = draw.textsize(text, font=font)
    x_loc = x_loc - w // 2
    
    draw.text((x_loc, y_loc), text, fill=(199, 89, 40), font=font)


def apply_text_centered(img, text, y_loc, font_size=15):
    x_loc = img.size[0] // 2
    apply_text(img, text, x_loc, y_loc, font_size)
