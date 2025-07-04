import yaml
import asyncio
import concurrent
# import time
import logging
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageTransform
# from io import BytesIO
import os
import purerackdiagram

logger = logging.getLogger()

cache = {}
cache_lock = asyncio.Lock()
root_path = os.path.dirname(purerackdiagram.__file__)
ttf_path = os.path.join(root_path, "Lato-Regular.ttf")


class MockImage:
    """A lightweight mock image that has size properties but skips PIL operations"""
    
    def __init__(self, size, mode="RGBA"):
        self.size = size
        self.mode = mode
        self.readonly = False
        self.format = "PNG"
        self.im = None  # Mock core image object
    
    @classmethod
    def from_config(cls, image_path):
        """Create a MockImage from config size data"""
        config_key = f"png/{os.path.basename(image_path)}"
        
        if config_key in global_config and 'size' in global_config[config_key]:
            width, height = global_config[config_key]['size']
            return cls((width, height))
        else:
            # Fallback: load image to get size, but don't keep it in memory
            with Image.open(image_path) as img:
                return cls(img.size)
    
    def paste(self, im, box=None):
        """Mock paste operation - does nothing"""
        pass
    
    def resize(self, size, resample=None):
        """Mock resize operation - returns new MockImage with new size"""
        return MockImage(size, self.mode)
    
    def save(self, fp, format=None, **params):
        """Mock save operation - does nothing"""
        pass
    
    def convert(self, mode):
        """Mock convert operation - returns new MockImage with new mode"""
        return MockImage(self.size, mode)
    
    def load(self):
        """Mock load operation - does nothing"""
        pass
    
    def getdraw(self, mode=None):
        """Mock getdraw operation - returns mock draw object"""
        return MockImageDraw()
    
    def rotate(self, angle, resample=0, expand=0, center=None, translate=None, fillcolor=None):
        """Mock rotate operation - returns self or new MockImage"""
        if expand:
            # For expand=True, we'd normally change size, but for simplicity return same size
            return MockImage(self.size, self.mode)
        return self
    
    def crop(self, box=None):
        """Mock crop operation - returns new MockImage"""
        if box:
            width = box[2] - box[0]
            height = box[3] - box[1]
            return MockImage((width, height), self.mode)
        return MockImage(self.size, self.mode)
    
    def _new(self, core_image):
        """Mock _new method for PIL compatibility"""
        return MockImage(self.size, self.mode)
    
    def copy(self):
        """Mock copy method"""
        return MockImage(self.size, self.mode)


class MockImageDraw:
    """A mock ImageDraw that does nothing"""
    
    def __init__(self):
        pass
        
    def text(self, xy, text, fill=None, font=None, anchor=None, spacing=4, align="left"):
        """Mock text drawing - does nothing"""
        pass
        
    def rectangle(self, xy, fill=None, outline=None, width=1):
        """Mock rectangle drawing - does nothing"""
        pass
        
    def polygon(self, xy, fill=None, outline=None, width=1):
        """Mock polygon drawing - does nothing"""
        pass
        
    def textbbox(self, xy, text, font=None, anchor=None, spacing=4, align="left"):
        """Mock textbbox - returns mock bounding box"""
        # Return a reasonable fake bounding box
        text_len = len(str(text)) if text else 0
        return (0, 0, text_len * 10, 20)  # fake width based on text length

global_config = None
with open(os.path.join(root_path, 'config.yaml'), 'r') as f:
    global_config = yaml.full_load(f)
global_config['ttf_path'] = ttf_path

# Custom exceptions for better error handling
class RackDiagramException(Exception):
    """Base exception class for all rack diagram errors"""
    pass

class InvalidConfigurationException(RackDiagramException):
    """Exception raised for invalid user configuration inputs"""
    pass

class InvalidDatapackException(InvalidConfigurationException):
    """Exception specifically for datapack validation errors"""
    pass



class RackImage():
    """This loads a file from disk and caches it.  If it's already been
    loaded it returns the cached object.  Originally, we were loading
    images from an S3 bucket, however, now to
    improve performance images are loaded
    directly from local FS.  So the benefit of this caching is questionable
    but is already written.  Probably could replace this whole class
    with img = Image.open(key)  lol!
    """

    def __init__(self, key, json_only=False):
        global root_path

        # key is the file name, s3 terminology.
        self.key = os.path.join(root_path, key)
        self.original_key = key
        self.img = None
        self.json_only = json_only
        self.io_lock = asyncio.Lock()

        # on object creation, see if this key has laready been requested.
        # potential race, if two object check but... worst case is we miss
        # a caching opportunity and just load twice.
        cache_key = f"{key}_{json_only}"
        if cache_key in cache:
            self.primary = False
            self.primary_obj = cache[cache_key]
        else:
            cache[cache_key] = self
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
                if isinstance(self.img, MockImage):
                    return self.img  # MockImages don't need copying
                else:
                    return self.img.copy()

            loop = asyncio.get_event_loop()

            # reading through asyncIO, it seems some OS
            # implementations are not truly Async!!!
            # now i'm going back to threads...
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(pool, self.load_img)

            if isinstance(self.img, MockImage):
                return self.img  # MockImages don't need copying
            else:
                return self.img.copy()

    def load_img(self):
        # load image from disk or create MockImage
        if self.json_only:
            # Create MockImage from config size data
            self.img = MockImage.from_config(self.key)
            logger.debug("Created MockImage for: {}".format(self.key))
        else:
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


def bool_param_get(config, key, default=False):
    if key in config:
        value = str(config[key]).lower().strip()
        if value == "":
            return default
        if value in ['true', '1', 'yes']:
            return True
        elif value in ['false', '0', 'no']:
            return False
        else:
            raise InvalidConfigurationException(f"Invalid boolean value for parameter '{key}': '{config[key]}'. Expected: true, false, 1, 0, yes, no")
    return default

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
    
    # Check if all images are MockImages
    all_mock = all(isinstance(img, MockImage) for img in images)
    any_mock = any(isinstance(img, MockImage) for img in images)
    
    if all_mock:
        # Create a MockImage for the combined result
        new_im = MockImage((total_width, total_height))
    elif any_mock:
        # Mixed images - this shouldn't happen, but handle gracefully
        logger.warning("Mixed MockImage and PIL Images detected, forcing MockImage mode")
        new_im = MockImage((total_width, total_height))
    else:
        # Regular PIL image combination
        new_im = Image.new("RGBA", (total_width, total_height))

    y_offset = 0
    all_ports = []
    for imp in image_ports:
        im = imp['img']
        ports = imp['ports']

        # center the x difference if an image is slightly smaller width
        x_offset = int((total_width - im.size[0]) / 2)
        
        # Only paste if not using MockImages
        if not isinstance(new_im, MockImage) and not isinstance(im, MockImage):
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
    new_im = new_im.convert('RGB')  # Works for both PIL Images and MockImages

    return new_im, all_ports


def apply_text(img, text, x_loc, y_loc, font_size=15, rotate_degrees=0):
    global ttf_path

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(ttf_path, size=font_size)
    #w, _ = draw.textsize(text, font=font)

    _, _, w, _ = draw.textbbox((0,0), text=text, font=font)
    #if w != w_new:
    #    Exception("Wrong new w")


    x_loc = x_loc - w // 2
    
    draw.text((x_loc, y_loc), text, fill=(199, 89, 40), font=font)


def apply_text_centered(img, text, y_loc, font_size=15):
    x_loc = img.size[0] // 2
    apply_text(img, text, x_loc, y_loc, font_size)


def draw_skewed_text(image, location, text, font, skew_angle=15, fill="red"):
    """
    Draws skewed text onto an existing image without affecting the original image content.

    :param image: PIL.Image - The base image to draw text on.
    :param location: tuple - (x, y) coordinates where the text should start.
    :param text: str - The text to draw.
    :param font_path: str - Path to the TTF font file.
    :param font_size: int - Size of the font.
    :param skew_angle: float - Angle to skew the text in degrees.
    :param fill: str or tuple - Color of the text.
    """
    

 # Calculate the text bounding box size using getbbox
    text_bbox = font.getbbox(text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Create a larger temporary image for the text, allowing extra space for skewing
    extra_width = int(abs(skew_angle) * 0.5 * text_height)
    temp_image_width = text_width + extra_width * 2  # Adding extra space on both sides
    temp_image_height = text_height + extra_width
    text_image = Image.new("RGBA", (temp_image_width, temp_image_height), (255, 255, 255, 0))
    
    # Draw the text onto the temporary image centered
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text((extra_width, 0), text, font=font, fill=fill)
    
    # Calculate the skew transformation matrix
    skew_factor = skew_angle * 0.1
    skew_matrix = (1, skew_factor, 0, 0, 1, 0)

    # Apply the skew to the text image
    skewed_text_image = text_image.transform(
        (temp_image_width, temp_image_height),
        ImageTransform.AffineTransform(skew_matrix),
        resample=Image.Resampling.BICUBIC
    )

    # Paste the skewed text image onto the original image at the specified location
    image = image.convert("RGBA")  # Ensure the base image supports alpha
    image.alpha_composite(skewed_text_image, (location[0], location[1]))

    return image
