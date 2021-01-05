import json
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
logger.setLevel(logging.INFO)

cache = {}
cache_lock = asyncio.Lock()
root_path = os.path.dirname(purerackdiagram.__file__)
ttf_path = os.path.join(root_path, "Lato-Regular.ttf")

global_config = None
with open(os.path.join(root_path, 'config.json'), 'r') as f:
    global_config = json.load(f)


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
        self.img.load()
        logger.debug("Loaded: {}".format(self.key))


def combine_images_vertically(images):
    """ Combines a list of PIL images vertically
        Args:
            images: List of PIL image objects to be combined
    """
    widths, heights = zip(*(i.size for i in images))
    total_height = sum(heights)
    total_width = max(widths)

    new_im = Image.new("RGB", (total_width, total_height))

    y_offset = 0
    for im in images:
        # center the x difference if an image is slightly smaller width
        x_offset = int((total_width - im.size[0]) / 2)
        new_im.paste(im, (x_offset, y_offset))
        y_offset += im.size[1]
    return new_im


def apply_text(img, text, x_loc, y_loc, font_size=15):
    global ttf_path

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(ttf_path, size=font_size)
    w, _ = draw.textsize(text, font=font)
    x_loc = x_loc - w // 2
    draw.text((x_loc, y_loc), text, fill=(199, 89, 40), font=font)


def apply_text_centered(img, text, y_loc, font_size=15):
    x_loc = img.size[0] // 2
    apply_text(img, text, x_loc, y_loc, font_size)


def main():
    # args no arg unless we need to have this tool to more
    # Generate, the offsets programatically for slot locations for each chassis
    pass


if __name__ == "__main__":
    main()
