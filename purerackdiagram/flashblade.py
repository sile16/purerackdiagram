import asyncio
import re
from os.path import join
from PIL import ImageDraw
from PIL import ImageFont

from .utils import RackImage, add_ports_at_offset, global_config, apply_text, InvalidConfigurationException


class FBDiagram():
    """
    A class to generate FlashBlade rack diagrams based on configuration parameters.
    """
    
    def __init__(self, params):
        self.ports = []

        config = {}
        config["chassis"] = int(params.get("chassis", 1))
        config['ru'] = config["chassis"]*4
        config["face"] = params.get("face", "front").lower()
        config["xfm_face"] = params.get("xfm_face", "").lower()
        config['direction'] = params.get("direction", "up").lower()
        config['efm'] = params.get('efm', 'efm310').lower()
        config['xfm_model'] = params.get('xfm_model', '3200e').lower()


        
        if not config['efm']:
            config['efm'] = "efm310"

        if config['xfm_face'] == "":
            config['xfm_face'] = config['face']
        elif config['xfm_face'] not in ['front', 'back', 'bezel']:
            raise InvalidConfigurationException(f"Invalid XFM Face, {config['xfm_face']}")

        valid_efm = ['efm110', 'efm310']
        if config['efm'] not in valid_efm:
            raise InvalidConfigurationException('please provide a valid efm: {}'.format(valid_efm))
        
        valid_xfm_model =['3200e', '8400']
        if config['xfm_model'] not in valid_xfm_model:
            raise InvalidConfigurationException('please provide a valid xfm_model: {}'.format(valid_xfm_model))

        blades = params.get('blades', "17:0-6").lower()

        # pattern 17:0-7,52:8-10
        blade_pattern = global_config['fb_blade_reg_pattern']

        if not re.compile(blade_pattern).match(blades):
            raise InvalidConfigurationException(
                "Invalid blade pattern, expecting \"17:0-8,52:23-48\" for 17TB blades in slots 0-8, and 52TB in  ")

        # convert from that format to an index of the label for each blade index
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
        if config['chassis'] > 1:
            default_xfm = True

        config["xfm"] = params.get("xfm", default_xfm)
        config["xfm_show_front"] = params.get("xfm_show_front", False)

        if config['xfm'] == "":
            config['xfm'] = default_xfm

        for item in ["xfm"]:
            if config[item] in ['False', 'false', 'FALSE', 'no', '0', '']:
                config[item] = False

        if config['xfm']:
            config['ru'] += 2

        self.config = config

    async def build_chassis(self, number):
        face = self.config["face"]
        if face == 'front':
            img_key = "png/pure_fb_front.png"
        else:
            img_key = "png/pure_fb_back_{}.png".format(self.config['efm'])

        if img_key in global_config:
            self.img_info = global_config[img_key]

        ports = []
        add_ports_at_offset(img_key, (0, 0), ports)

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
                    apply_text(img, label, x_offset +
                               x_blade_size*index, y_offset, 36)

        return {'img': img, 'ports': ports}

    async def get_rack_image_with_ports(self, key):
        ports = []
        add_ports_at_offset(key, (0, 0), ports)
        return {'img': await RackImage(key).get_image(), 'ports': ports}

    async def get_image(self):
        tasks = []

        for i in range(self.config["chassis"]):
            tasks.append(self.build_chassis(i))

        if self.config['xfm']:
            xfm_face = self.config['xfm_face']
            for x in range(2):
                tasks.append(
                self.get_rack_image_with_ports(f"png/pure_fb_xfm_{self.config['xfm_model']}_{xfm_face}.png"))
            

        all_images = await asyncio.gather(*tasks)
        if self.config["direction"] == "up":
            all_images.reverse()

        return all_images

    async def get_image_metadata_only(self):
        """Lightweight version of get_image for json_only mode."""
        tasks = []

        for i in range(self.config["chassis"]):
            tasks.append(self.build_chassis_metadata_only(i))

        if self.config['xfm']:
            xfm_face = self.config['xfm_face']
            for x in range(2):
                tasks.append(
                self.get_rack_metadata_only(f"png/pure_fb_xfm_{self.config['xfm_model']}_{xfm_face}.png"))
            

        all_metadata = await asyncio.gather(*tasks)
        if self.config["direction"] == "up":
            all_metadata.reverse()

        return all_metadata

    async def build_chassis_metadata_only(self, chassis_idx):
        """Metadata-only version of build_chassis for json_only mode."""
        face = self.config["face"]
        if face == 'front':
            img_key = "png/pure_fb_front.png"
        else:
            img_key = "png/pure_fb_back.png"

        ports = []
        add_ports_at_offset(img_key, (0, 0), ports)
        img_size = global_config[img_key]['size']
        return {'img_size': img_size, 'ports': ports}

    async def get_rack_metadata_only(self, key):
        """Metadata-only version of get_rack_image_with_ports for json_only mode."""
        ports = []
        add_ports_at_offset(key, (0, 0), ports)
        img_size = global_config[key]['size']
        return {'img_size': img_size, 'ports': ports}
    
        # final_img, all_ports = combine_images_vertically(all_images)
        # self.ports = all_ports
        # return final_img
