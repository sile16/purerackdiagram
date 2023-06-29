import asyncio
from cmath import exp
from os.path import join
import re
from PIL import ImageDraw
from PIL import Image
from PIL import ImageFont
from .utils import RackImage, add_ports_at_offset, combine_images_vertically, global_config, apply_text

from .flasharray import apply_fm_label


class FBSDiagram():
    def __init__(self, params):
        self.ports = []

        config = {}
        config["model"] = params.get("model").lower()
        config["chassis"] = int(params.get("no_of_chassis", 1))
        config['ru'] = config["chassis"]*5
        config["face"] = params.get("face", "front").lower()
        config["xfm_face"] = params.get("xfm_face", "").lower()
        config["bezel"] = params.get("bezel", False)
        config['direction'] = params.get("direction", "up").lower()
        config['dfm_size'] = float(params.get("drive_size", 24))
        config['dfm_count'] = int(params.get("no_of_drives_per_blade", 1))
        config['blades'] = int(params.get("no_of_blades", 7))

        if config['xfm_face'] == "":
            config['xfm_face'] = config['face']


        valid_models = ['fb-s200', 'fb-s500', 'fb-e']
        if config['model'] not in valid_models:
            raise Exception('please provide a valid model: {}'.format(valid_models))

        if config['blades'] < 0 or config['blades'] > 100 :
            raise Exception('please provide blades count 0-100.')

        valid_dfms = [24, 24.0, 48, 48.2]
        if config['dfm_size'] not in valid_dfms:
            raise Exception('Valide drive sizes: {}'.format(valid_dfms))

        valid_dfm_count = [1, 2, 3, 4]
        if config['dfm_count'] not in valid_dfm_count:
            raise Exception('Valide drive counts: {}'.format(valid_dfm_count))


        default_chassis = (config['blades'] - 1 )// 10 + 1
        if config['chassis'] < default_chassis:
            config['chassis'] = default_chassis

        default_xfm = False
        if config['chassis'] > 1:
            default_xfm = True

        config["xfm"] = params.get("xfm", default_xfm)
        config["xfm_show_front"] = params.get("xfm_show_front", False)

        if config['xfm'] == "":
            config['xfm'] = default_xfm

        for item in ["xfm", "bezel"]:
            # we don't need to worry about true, because any text will eval to true
            if config[item] in ['False', 'false', 'FALSE', 'no', '0', '']:
                config[item] = False


        if config['xfm']:
            config['ru'] += 2

        self.config = config
    

    async def add_blades(self, base_img, number_of_blades, blade_model_text):
        
        key = 'png/pure_fbs_blade.png'
        blade_img = await RackImage(key).get_image()
        fm_loc = global_config[key]['fm_loc']

        dfm_name = 'png/pure_fa_fm_nvme.png'
        fm_img = await RackImage(dfm_name).get_image()
        apply_fm_label(fm_img, str(self.config['dfm_size']), "qlc")

        # Paste in the DFMs
        for x in range(self.config['dfm_count']):
            blade_img.paste(fm_img, fm_loc[x])

        ##########################################
        # Add model label.
        label_loc = global_config[key]['model_text_loc']
        
        # todo: add this into utilities as a more generic function to apply 
        # rotated tet.
        ttf_path = global_config['ttf_path']
        font_size = 25

        font = ImageFont.truetype(ttf_path, size=font_size)
        txt_size = font.getsize(blade_model_text)
        
        ##make backgroun grey
        txtimg = Image.new("RGB", txt_size, (38, 38, 38))
        txtimg_draw = ImageDraw.Draw(txtimg)
        txtimg_draw.text((0,0), blade_model_text, font=font, fill= (255, 255, 255))

        #Crop the top a little to remove extra spacing along the top
        top_crop = 3
        txtimg = txtimg.crop((0, top_crop, txt_size[0], txt_size[1]))

        #apply_text(txtimg, model_text, 0, 0, font_size=font_size)
        txtimg = txtimg.rotate(270, expand=1)
        blade_img.paste(txtimg, label_loc)


        ############################
        # Paste in the blades.
        for x in range(number_of_blades):
            base_img.paste(blade_img, self.img_info['blade_loc'][x])


    async def build_chassis(self, number_of_blades, blade_model_text):
        number_of_blades = min(10, number_of_blades)
        face = self.config["face"]

        model = blade_model_text[0].lower()

        if face == 'front':
            if self.config['bezel']:
                img_key = f"png/pure_fb{model}_bezel.png"
            else:
                img_key = f"png/pure_fb{model}_front.png"
        else:
            img_key = f"png/pure_fb{model}_back.png"

        if img_key in global_config:
            self.img_info = global_config[img_key]

        ports = []
        add_ports_at_offset(img_key, (0, 0), ports)

        base_img = await RackImage(img_key).get_image()

        if "front" in img_key:
            await self.add_blades(base_img, number_of_blades, blade_model_text)

        return {'img': base_img, 'ports': ports}

    async def get_rack_image_with_ports(self, key):
        ports = []
        add_ports_at_offset(key, (0, 0), ports)
        return {'img': await RackImage(key).get_image(), 'ports': ports}

    async def get_image(self):
        tasks = []

        c = self.config

        blade_model_text = self.config['model'].split("-")[1].upper()

        if blade_model_text == "E":
            blade_model_text = "EC"

        blades_left = c['blades']
        for i in range(self.config["chassis"]):
            tasks.append(self.build_chassis( blades_left, blade_model_text))
            blades_left -= 10

            # expansions shelves we change the blade model to EX
            if blade_model_text == "EC":
                blade_model_text = "EX"


        if self.config['xfm']:

            tasks.append(
                self.get_rack_image_with_ports(f"png/pure_fb_xfm_{c['xfm_face']}.png"))
            tasks.append(
                self.get_rack_image_with_ports(f"png/pure_fb_xfm_{c['xfm_face']}.png"))

        all_images = await asyncio.gather(*tasks)
        if self.config["direction"] == "up":
            all_images.reverse()

        final_img, all_ports = combine_images_vertically(all_images)
        self.ports = all_ports
        return final_img
