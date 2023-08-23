from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
# from io import BytesIO
import asyncio
from . import utils
from .utils import RackImage, combine_images_vertically, add_ports_at_offset
# import logging
import os
from pprint import pformat
import re

root_path = os.path.dirname(utils.__file__)
ttf_path = os.path.join(root_path, "Lato-Regular.ttf")


class FAShelf():
    def __init__(self, params):
        self.config = params
        self.start_img_event = asyncio.Event()
        self.ports = []

    # Called externally to retrieve the image of the shelf
    async def get_image(self):
        c = self.config
        tasks = []
        tasks.append(self.get_base_img())
        if c["face"] == "front":
            if c["shelf_type"] == "nvme":
                tasks.append(self.add_nvme_fms())
            else:
                tasks.append(self.add_sas_fms())

        # load the base image and FMs simultaniously.
        await asyncio.gather(*tasks)
        return {'img':self.tmp_img, 'ports': self.ports}

    # load the first base image
    async def get_base_img(self):
        c = self.config
        key = "png/pure_fa_{}_shelf_{}.png".format(c["shelf_type"], c["face"])

        self.tmp_img = await RackImage(key).get_image()

        # Load image info
        self.img_info = {}
        if key in utils.global_config:
            self.img_info = utils.global_config[key]

        if 'ports' in self.img_info:
            self.ports = self.img_info['ports']

        self.start_img_event.set()

    async def add_nvme_fms(self):
        cur_module = 0

        for dp in self.config["datapacks"]:
            fm_str = dp[0]
            fm_type = dp[1]
            img_name = 'png/pure_fa_fm_{}.png'.format(fm_type)
            num_modules = dp[2]

            if fm_str == 'Blank':
                num_modules = 14

            fm_img = await RackImage(img_name).get_image()

            if self.config['fm_label']:
                apply_fm_label(fm_img, fm_str, fm_type)

            # wait until the base image is loaded
            await self.start_img_event.wait()

            fm_loc = self.img_info['fm_loc']
            fm_rotated = fm_img.rotate(-90, expand=True)

            for x in range(cur_module, min(28, num_modules + cur_module)):
                if x < 20:
                    self.tmp_img.paste(fm_img, fm_loc[x])
                else:
                    self.tmp_img.paste(fm_rotated, fm_loc[x])
            cur_module += num_modules

        # add datapack labels
        right = False
        if self.config['dp_label']:
            for dp in self.config["datapacks"]:
                num_modules = dp[2]
                full = False
                if num_modules == 28:
                    full = True
                dp_size = dp[3]
                y_offset = 50
                x_offset = 162
                self.tmp_img = apply_dp_label(self.tmp_img,
                                              dp_size,
                                              x_offset,
                                              y_offset,
                                              right,
                                              full)
                right = True

    async def add_sas_fms(self):
        cur_module = 0
        for dp in self.config["datapacks"]:
            fm_str = dp[0]
            fm_type = dp[1]
            num_modules = dp[2]
            if fm_type == 'blank':
                num_modules = 12
            dp_size = dp[3]
            fm_img_str = "png/pure_fa_fm_{}.png".format(fm_type)
            fm_img = await RackImage(fm_img_str).get_image()

            if self.config['fm_label']:
                apply_fm_label(fm_img, fm_str, fm_type)

            await self.start_img_event.wait()
            fm_loc = self.img_info['fm_loc']

            for x in range(cur_module, min(24, cur_module + num_modules)):
                self.tmp_img.paste(fm_img, fm_loc[x])

            cur_module += num_modules

        # apply dp label after fm modules
        right = False
        if self.config['dp_label']:
            for dp in self.config["datapacks"]:
                fm_str = dp[0]
                fm_type = dp[1]
                num_modules = dp[2]
                dp_size = dp[3]

                y_offset = 0
                x_offset = 90
                full = False
                if num_modules == 24:
                    full = True

                self.tmp_img = apply_dp_label(self.tmp_img,
                                              dp_size,
                                              x_offset,
                                              y_offset,
                                              right,
                                              full)
                right = True


# takes the config parsed in FA Diagram and creates the image for the chassis
class FAChassis():

    def __init__(self, params):
        config = params.copy()
        del config["shelves"]
        self.config = config
        self.start_img_event = asyncio.Event()
        self.ch0_fm_loc = None
        self.ports = []

    async def get_image(self):
        # build the image
        c = self.config
        key = "png/pure_fa_{}_r{}".format(c["generation"], c['release'])

        if c["face"] == "front" and c["bezel"]:
            key += "_bezel.png"
            img =  await RackImage(key).get_image()
            return {'img': img, 'ports': []}

        # not doing bezel
        key += "_{}.png".format(c["face"])

        tasks = []
        tasks.append(self.get_base_img(key))

        if key in utils.global_config:
            self.img_info = utils.global_config[key]

        add_ports_at_offset(key, (0, 0), self.ports)


        if c["face"] == "front":
            tasks.append(self.add_fms())
            tasks.append(self.add_nvram())
            tasks.append(self.add_model_text())
        else:
            tasks.append(self.add_cards())
            tasks.append(self.add_mezz())

        # run all the tasks concurrently
        await asyncio.gather(*tasks)
        return {'img': self.tmp_img, 'ports': self.ports}

    async def get_base_img(self, key):
        self.tmp_img = await RackImage(key).get_image()
        self.start_img_event.set()

    async def add_nvram(self):
        

        if self.config['generation'] == 'c':
            # always add second nvram on 'c' array
            pass
        elif self.config['generation'] == 'xl':
            return
        elif self.config["model_num"] < 70:
            # Don't add second nvram on less  than 70
            return

        nvram_img = await RackImage("png/pure_fa_x_nvram.png").get_image()

        await self.start_img_event.wait()
        self.tmp_img.paste(nvram_img, self.img_info['nvram_loc'][0])
        self.tmp_img.paste(nvram_img, self.img_info['nvram_loc'][1])

    async def add_cards(self):
        pci = self.config["pci_config"]

        tasks = []
        for x in range(len(pci)):
            if pci[x]:
                tasks.append(self.add_card(x, pci[x]))
        await asyncio.gather(*tasks)

    async def add_card(self, slot, card_type):
        # todo: add this model specific info to the config.yaml

        if self.config['generation'] == 'xl':
            if slot in [2, 3]:
                height = "fh"
            else:
                height = "hh"
        elif (self.config['generation'] == 'c' or self.config['generation'] == 'x') and self.config['release'] == 4:

            if slot in [1, 2]:
                height = "fh"
            else:
                height = "hh"
        else:
            if slot < 2:
                height = "fh"
            else:
                height = "hh"

        key = "png/pure_fa_{}_{}.png".format(card_type, height)

        card_img = await RackImage(key).get_image()
        await self.start_img_event.wait()

        # ct0
        cord = self.img_info['ct0_pci_loc'][slot]
        self.tmp_img.paste(card_img, cord)
        add_ports_at_offset(key, cord, self.ports)

        # ct1
        cord = self.img_info['ct1_pci_loc'][slot]
        add_ports_at_offset(key, cord, self.ports)
        self.tmp_img.paste(card_img, cord)
    


    async def add_mezz(self):
        if self.config["generation"] == "xl":
            return
        
        if self.config["release"] == 4:
            return

        if self.config['mezz']:
            key = "png/pure_fa_x_{}.png".format(self.config["mezz"])
            mezz_img = await RackImage(key).get_image()
            await self.start_img_event.wait()

            self.tmp_img.paste(mezz_img, self.img_info['ct0_mezz_loc'])
            add_ports_at_offset(key, self.img_info['ct0_mezz_loc'], self.ports)

            self.tmp_img.paste(mezz_img, self.img_info['ct1_mezz_loc'])
            add_ports_at_offset(key, self.img_info['ct1_mezz_loc'], self.ports)


    async def add_fms(self):
        # is  this the right side data pack ?
        # starts with no, then we change to yes after first one
        right = False
        slots = {}

        # of chassis slots
        total_fm_count = len(self.img_info['fm_loc'])
        current_index = 0
        dp_count = len(self.config["chassis_datapacks"])
        for dp_i in range(dp_count):
            dp = self.config["chassis_datapacks"][dp_i]
            # see if this is the last data pack or not
            if dp_i > 0 and dp_i + 1 == dp_count:
                # If it's m or X need to populated the 
                # last datapack from the right side
                if self.config['generation'] != 'xl':
                    right = True

            fm_str = dp[0]
            fm_type = dp[1]
            num_modules = dp[2]
            dp_size = dp[3]

            file_name = "png/pure_fa_fm_{}.png".format(fm_type)
            fm_img = await RackImage(file_name).get_image()
            blank_img = await RackImage("png/pure_fa_fm_blank.png").get_image()

            if self.config['fm_label']:
                apply_fm_label(fm_img, fm_str, fm_type)
                apply_fm_label(blank_img, "", "blank")

            await self.start_img_event.wait()
            if not right:
                the_range = range(current_index, current_index + num_modules)
                current_index += num_modules
            else:
                # this is hard coded 20, probably fine
                the_range = reversed(range(20-num_modules, 20))

            fm_loc = self.img_info['fm_loc']

            for x in the_range:
                # self.tmp_img.save("tmp.png")
                if not right and x >= num_modules and self.config["generation"] != 'xl':
                    # for short DMM modules, fill the rest with blanks
                    self.tmp_img.paste(blank_img, fm_loc[x])
                else:

                    if x in slots and slots[x] != "blank":
                        if fm_type == "blank":
                            pass
                        else:
                            raise Exception(
                                "Overlapping datapacks, check data pack sizes dont exceed chassis size of 20.")
                    else:
                        self.tmp_img.paste(fm_img, fm_loc[x])
                        # keep track of modules, to detect overlaps
                        slots[x] = fm_type


        if self.config['dp_label']:
            right = False
            for dp in self.config["chassis_datapacks"]:
                fm_str = dp[0]
                fm_type = dp[1]
                num_modules = dp[2]
                dp_size = dp[3]

                y_offset = 244
                x_offset = 130
                full = False
                if num_modules == 20:
                    full = True

                self.tmp_img = apply_dp_label(self.tmp_img,
                                              dp_size,
                                              x_offset,
                                              y_offset,
                                              right,
                                              full)
                # the next DP must be the right side.
                right = True

    async def add_model_text(self):
        global ttf_path

        loc = self.img_info['model_text_loc']

        await self.start_img_event.wait()
        c = self.config
        draw = ImageDraw.Draw(self.tmp_img)

        font = ImageFont.truetype(ttf_path, size=24)
        if c['generation'] == 'xl':
            text = "{}r{}".format(c['model_num'],
                                    c['release'])
        else:
            text = "{}{}r{}".format(c['generation'].upper(),
                                    c['model_num'],
                                    c['release'])
        draw.text(loc, text, (255, 255, 255, 220), font=font)


def apply_fm_label(fm_img, fm_str, fm_type):
    # writing flash module text lables
    utils.apply_text_centered(fm_img, fm_str, 18)
    utils.apply_text_centered(fm_img, fm_type, 32)


def apply_dp_label(img, dp_size, x_offset, y_offset, right, full=False):
    global ttf_path
    # temp image same size as our chassis.
    tmp = Image.new('RGBA', img.size, (0, 0, 0, 0))

    # Create a drawing context for it.
    draw = ImageDraw.Draw(tmp)

    x_buffer = 75
    y_buffer = 60

    box_loc = (x_offset + x_buffer, y_offset + y_buffer)

    if right:
        box_loc = (tmp.size[0] // 2 + x_buffer, y_offset + y_buffer)

    box_size = (tmp.size[0] // 2 - 2 * x_buffer - x_offset,
                (tmp.size[1] - 2 * y_buffer - y_offset))
    if full:
        box_size = (tmp.size[0] - 2 * x_buffer - 2 * x_offset,
                    (tmp.size[1] - 2 * y_buffer - y_offset))

    # put DP on left or right
    box_loc2 = (box_loc[0]+box_size[0], box_loc[1]+box_size[1])

    draw.rectangle((box_loc, box_loc2), fill=(199, 89, 40, 127))
    box_center = ((box_loc[0] + box_loc2[0]) // 2,
                  (box_loc[1] + box_loc2[1]) // 2)
    font = ImageFont.truetype(ttf_path, size=85)
    w, h = draw.textsize(dp_size + "TB", font=font)
    text_loc = (box_center[0] - w/2, box_center[1] - h/2)
    draw.text(text_loc, dp_size + "TB", fill=(255, 255, 255, 220), font=font)

    alpha_tmp = img.convert("RGBA")
    return Image.alpha_composite(alpha_tmp, tmp)


# FADiagram does most of the logical config parsing and validation of configuration
#
class FADiagram():

    def _init_pci_cards(self, config, params):
        pci_valid_cards = utils.global_config['pci_valid_cards']
        pci_config_lookup = utils.global_config['pci_config_lookup']

        pci_config = [None, None, None, None]
        pci_lookup_str = "fa-{}{}r{}-{}".format(
            config["generation"],
            config["model_num"],
            config["release"],
            config["protocol"],
        )
        
        pci_config = pci_config_lookup[pci_lookup_str].copy()

        # add on cards
        if "addoncards" in params:
            for card in params["addoncards"].split(","):
                card = card.strip()
                if not card:
                    # meaining it's blank, do nothing.
                    continue

                if card not in pci_valid_cards:
                    raise Exception("invalid pci card: {}, valid cards:{}".format(
                        card, pformat(pci_valid_cards)))

                # card population order for a full height only card
                # Todo: the logic in the XL, is each card has different best
                # practice for population order, may have to just put this 
                # back on the SE to select which slot.
                if config["generation"] == 'xl':
                    fh_order = [2, 3]
                    hh_order = [0, 1, 4, 6, 7, 8]
                elif (config['generation'] == 'x' or config['generation'] == 'c') and config['release'] == 4:
                    fh_order = [1, 2]
                    hh_order = [0, 3, 4]
                else:
                    fh_order = [0, 1]
                    hh_order = [2, 0, 1, 3]
                order = fh_order
                if card == "2fc" or card == "2eth" or card == "2eth10gbaset":
                    # card population order for a half or full card slot
                    order = hh_order

                # populate add on cards by the order
                for slot in order:
                    if pci_config[slot] is None:
                        pci_config[slot] = card
                        break

        config["pci_config"] = pci_config

        # pci3 = '2fc'  overrides everything
        for x in range(len(pci_config)):
            slot = "pci{}".format(x)
            # specific slot overrides
            # make the default, the current config so far.
            card = params.get(slot, pci_config[x])
            if not card:
                continue
            if card not in pci_valid_cards:
                raise Exception("invalid pci card: {}, valid cards:{}".format(
                    card, pformat(pci_valid_cards)))
            pci_config[x] = card

    def _init_datapacks(self, config, params):
        ######################################
        #  Parse Data Packs & Shelf config

        chassis_dp_size_lookup = utils.global_config['chassis_dp_size_lookup']
        shelf_dp_size_lookup = utils.global_config['shelf_dp_size_lookup']

        shelves = []
        config["chassis_datapacks"] = []

        if "datapacks" in params:

            if "m" in config["generation"]:
                default_shelf_type = "sas"
            else:
                default_shelf_type = "nvme"

            # Of form "38/38-90/0"
            dp_configs = params["datapacks"].split("-")
            chassis = dp_configs[0]

            # Pull shelf info into seperate array
            shelf_configs = []
            if len(dp_configs) > 1:
                shelf_configs = dp_configs[1:]

            # Chassis data pack config:
            datapacks = []

            # not displaying chassis DP if there is a bezel
            if not config["bezel"]:
                for dp in chassis.split("/"):
                    if dp in chassis_dp_size_lookup:
                        datapacks.append(chassis_dp_size_lookup[dp])
                    elif dp == '0':
                        pass
                    else:
                        raise Exception("Unknown Chassis: DP: {}\nPick from One of the Following\n{}".
                                        format(dp, pformat(chassis_dp_size_lookup)))

                config["chassis_datapacks"] = datapacks

            # Shelf DPs
            for shelf in shelf_configs:
                datapacks = []
                shelf_type = default_shelf_type

                for dp in shelf.split("/"):
                    if dp in shelf_dp_size_lookup:
                        datapacks.append(shelf_dp_size_lookup[dp])
                        if not dp.startswith('0') :
                            shelf_type = shelf_dp_size_lookup[dp][1]
                            if 'nvme' in shelf_type:
                                shelf_type = 'nvme'
                    else:
                        raise Exception("Unknown Shelf: DP: {}\nPick from One of the Following\n{}".
                                        format(dp, pformat(shelf_dp_size_lookup)))

                if config['face'] == 'front':
                    shelves.append(
                        {
                            "shelf_type": shelf_type,
                            "datapacks": datapacks,
                            "face": config["face"],
                            "dp_label": config["dp_label"],
                            "fm_label": config["fm_label"],
                        }
                    )
                else:
                    shelves.append({'shelf_type': shelf_type, "face": 'back'})

                if shelf_type == 'nvme':
                    config['ru'] += 3
                else:
                    config['ru'] += 2

        config["shelves"] = shelves

    def __init__(self, params):
        # front or back
        config = {}
        self.ports = []

        config["model_str"] = params["model"].lower()

        # mode-str of type  "fa-m70r2" or "fa-x70" or "fa-xl130" or fa-xl170r2
        # Split string on the - and transition to numbers
        results = re.split('(\d+)|-', config["model_str"])
        config["generation"] = results[2]
        config['model_num'] = int(results[3])
        if "r" in config["model_str"]:
            config["release"] = int(results[5])
        else:
            config["release"] = 1
        
        config["direction"] = params.get("direction", "up").lower()

        if config["generation"] == 'xl':
            config["ru"] = 5  # this gets increased during shelf parsing
        else:
            config["ru"] = 3  # this gets increased during shelf parsing

        
        face = params.get("face", "front")
        if face != "front" and face != "back":
            face = "front"
        config["face"] = face

        if face == "back":
            config['bezel'] = False

            valid_protocols = ['fc', 'eth']
            config["protocol"] = params.get("protocol", "fc").lower()
            if config['protocol'] not in valid_protocols:
                raise Exception("invalid protocol: {}, valid cards:{}".format(
                    config["protocol"],
                    pformat(valid_protocols)))

            # hack for the x70r1, is identical to m70r2, so just going to change it internally to m70r2
            if config['generation'] == 'x' and config['release'] == 1 and config['model_num'] == 70:
                config['generation'] = 'm'
                config['release'] = 2

            # Mezz
            # the m70 base image already has the backend SAS ports
            default_mezz = None
            valid_mezz = [None, 'emezz', 'smezz']
            if config['generation'] == 'x' and config["model_num"] >= 20:
                default_mezz = 'emezz'
            elif config['generation'] == 'c':
                default_mezz = 'emezz'
            config["mezz"] = params.get("mezz", default_mezz)
            if config['mezz'] == "":
                config['mezz'] = default_mezz

            if config['mezz'] not in valid_mezz:
                raise Exception(
                    "Please use a valid mezzainine: {}".format(
                        pformat(valid_mezz)))

            self._init_pci_cards(config, params)

        else:
            # face == 'front'
            config["fm_label"] = params.get("fm_label", False)
            config["dp_label"] = params.get("dp_label", False)
            config["bezel"] = params.get("bezel", False)
            # check for string versions of no/false
            for item in ["fm_label", 'dp_label', 'bezel']:
                if config[item] in ['False', 'false', 'FALSE', 'no', '0', '']:
                    config[item] = False

        if config['generation'] == 'c':
            csize_lookup = utils.global_config['csize_lookup']

            if 'csize' in params and params['csize'] != '':
                csize = params.get('csize', '')
                if csize in utils.global_config['chassis_dp_size_lookup']:
                    # we have a direct data pack for that size.
                    params['datapacks'] = csize

                elif csize in csize_lookup:
                    # we have a lookup translation, lets use it
                    params['datapacks'] = csize_lookup[csize]
        
                else:
                    raise Exception(
                        "Please use a valid csize: {}".format(
                            pformat(csize_lookup.keys())))

            elif 'datapacks' in params and params['datapacks'] != '':
                #they specified the datapacks use those.
                pass
            else:
                raise Exception("Please provide either csize or datapacks")

        # need for both as shelf type is encoded in DP sizes
        self._init_datapacks(config, params)
        self.config = config

    async def get_image(self):
        tasks = []

        tasks.append(FAChassis(self.config).get_image())

        for shelf in self.config["shelves"]:
            tasks.append(FAShelf(shelf).get_image())

        # this returns the results of the all the tasks in a list
        all_image_ports = await asyncio.gather(*tasks)

        if self.config["direction"] == "up":
            all_image_ports.reverse()

        final_img, all_ports = combine_images_vertically(all_image_ports)
        self.ports = all_ports
        return final_img
