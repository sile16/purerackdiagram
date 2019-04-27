import asyncio
import re
import os
from PIL import ImageDraw
from PIL import ImageFont
from .utils import RackImage, combine_images_vertically, global_config, apply_text

class FBDiagram():
    def __init__(self, params):
        
        config = {}
        config["chassis"] = int(params.get("chassis", 1))
        config["face"] = params.get("face", "front").lower()
        config['direction'] = params.get("direction","up").lower()
        blades = params.get('blades',"17:0-6").lower()

        #pattern 17:0-7,52:8-10
        blade_pattern = global_config['fb_blade_reg_pattern']

        if not re.compile(blade_pattern).match(blades):
            raise Exception("Invalid blade pattern, expecting \"17:0-8,52:23-48\" for 17TB blades in slots 0-8, and 52TB in  ")

        #convert from that format to an index of the label for each blade index
        blade_labels = {}
        if config['face'] == 'front':
            for item in blades.split(','):
                if item:
                    item_split = item.split(':')
                    b_range = item_split[1]
                    if '-' in b_range:
                        b_range = b_range.split('-')
                        start = int(b_range[0])
                        end = int(b_range[1]) + 1
                        if end < start:
                            end = start + 1
                    else:
                        start = int(b_range)
                        end = start + 1
                    
                    for i in range(start, end):
                        blade_labels[i] = item_split[0]
        config['blade_labels'] = blade_labels

        default_xfm = False
        if config['chassis'] > 1 :
            default_xfm = True

        config["xfm"] = params.get("xfm",default_xfm)
        
        if config['xfm'] == "":
            config['xfm'] = default_xfm

        for item in ["xfm"]:
            if config[item] in ['False','false','FALSE','no','0','']:
                config[item] = False
        self.config = config

    async def build_chassis(self, number):
        face = self.config["face"]
        img_key = "png/pure_fb_{}.png".format(face)
        img = await RackImage(img_key).get_image()

        if face == "front":
            blade_index_offset = number * 15
            x_offset = 260
            x_blade_size = 164
            y_offset = 967
            for index in range(15):
                blade_num = index + blade_index_offset
                if blade_num in self.config['blade_labels']:
                    label = self.config['blade_labels'][blade_num]
                    label = "{} TB".format(label)
                    apply_text(img, label, x_offset + x_blade_size*index, y_offset, 36)                

        return img


    async def get_image(self):
        tasks = []


        for i in range(self.config["chassis"]):
            tasks.append(self.build_chassis(i))
        
        if self.config['xfm']:
            tasks.append(
                RackImage('png/pure_fb_xfm_{}.png'.format(self.config["face"])).
                            get_image())
            tasks.append(
                RackImage('png/pure_fb_xfm_{}.png'.format(self.config["face"])).
                            get_image())

        all_images = await asyncio.gather(*tasks)
        if self.config["direction"] == "up":
            all_images.reverse()

        return combine_images_vertically(all_images)