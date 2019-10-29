from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
# from io import BytesIO
import asyncio
from . import utils
from .utils import RackImage, combine_images_vertically
# import logging
import os
from pprint import pformat

root_path = os.path.dirname(utils.__file__)
ttf_path = os.path.join(root_path, "Lato-Regular.ttf")


class FAShelf():
    def __init__(self, params):
        self.config = params
        self.start_img_event = asyncio.Event()

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
        return self.tmp_img

    # load the first base image
    async def get_base_img(self):
        c = self.config
        key = "png/pure_fa_{}_shelf_{}.png".format(c["shelf_type"], c["face"])
        self.tmp_img = await RackImage(key).get_image()
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
            fm_loc = get_chassis_fm_loc()
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
                dp_size = dp[3]
                y_offset = 50
                x_offset = 162
                self.tmp_img = apply_dp_label(self.tmp_img,
                                              dp_size,
                                              x_offset,
                                              y_offset,
                                              right)
                right = True

    async def add_sas_fms(self):
        cur_module = 0
        for dp in self.config["datapacks"]:
            fm_str = dp[0]
            fm_type = dp[1]
            num_modules = dp[2]
            dp_size = dp[3]

            dp_start = cur_module
            fm_img_str = "png/pure_fa_fm_{}.png".format(fm_type)
            fm_img = await RackImage(fm_img_str).get_image()

            if self.config['fm_label']:
                apply_fm_label(fm_img, fm_str, fm_type)

            await self.start_img_event.wait()
            fm_loc = get_sas_fm_loc()

            for x in range(cur_module, min(24, cur_module + num_modules)):
                self.tmp_img.paste(fm_img, fm_loc[x])

            # apply dp label after fm modules
            if self.config['dp_label']:
                y_offset = 0
                x_offset = 90
                right = False
                if dp_start > 9:
                    right = True
                self.tmp_img = apply_dp_label(self.tmp_img,
                                              dp_size,
                                              x_offset,
                                              y_offset,
                                              right)

            cur_module += num_modules


class FAChassis():

    def __init__(self, params):
        config = params.copy()
        del config["shelves"]
        self.config = config
        self.start_img_event = asyncio.Event()
        self.ch0_fm_loc = None

    async def get_image(self):
        c = self.config
        key = "png/pure_fa_{}".format(c["generation"])

        if c["face"] == "front" and c["bezel"]:
            key += "_bezel.png"
            return await RackImage(key).get_image()

        # not doing bezel
        key += "_{}.png".format(c["face"])

        tasks = []
        tasks.append(self.get_base_img(key))

        if c["face"] == "front":
            tasks.append(self.add_fms())
            tasks.append(self.add_nvram())
            tasks.append(self.add_model_text())
        else:
            tasks.append(self.add_cards())
            tasks.append(self.add_mezz())

        # run all the tasks concurrently
        await asyncio.gather(*tasks)
        return self.tmp_img

    async def get_base_img(self, key):
        self.tmp_img = await RackImage(key).get_image()
        self.start_img_event.set()

    async def add_nvram(self):
        if self.config['generation'] == 'x' or \
           self.config['generation'] == 'c':
            nv1 = (1263, 28)
            nv2 = (1813, 28)
        else:
            nv1 = (1255, 20)
            nv2 = (1805, 20)

        if self.config['generation'] == 'c':
            # always add second nvram on 'c' array
            pass
        elif self.config["model_num"] < 70:
            # Don't add second nvram on less  than 70
            return

        nvram_img = await RackImage("png/pure_fa_x_nvram.png").get_image()
        await self.start_img_event.wait()
        self.tmp_img.paste(nvram_img, nv1)
        self.tmp_img.paste(nvram_img, nv2)

    async def add_cards(self):
        pci = self.config["pci_config"]

        tasks = []
        for x in range(4):
            if pci[x]:
                tasks.append(self.add_card(x, pci[x]))
        await asyncio.gather(*tasks)

    async def add_card(self, slot, card_type):
        # y offset from CT1 -> CT0
        y_offset = 378
        if self.config['generation'] == 'x' or \
                self.config['generation'] == 'c':
            pci_loc = [(1198, 87), (1198, 203), (2069, 87), (2069, 203)]
        elif self.config['generation'] == 'm':
            pci_loc = [(1317, 87), (1317, 201), (2182, 87), (2182, 201)]

        if slot < 2:
            height = "fh"
        else:
            height = "hh"

        key = "png/pure_fa_{}_{}.png".format(card_type, height)
        card_img = await RackImage(key).get_image()
        await self.start_img_event.wait()
        cord = pci_loc[slot]
        self.tmp_img.paste(card_img, cord)
        ct0_cord = (cord[0], cord[1] + y_offset)
        self.tmp_img.paste(card_img, ct0_cord)

    async def add_mezz(self):
        # if self.config["generation"] != "x" or self.config['mezz'] is None:
        #    return
        if self.config['mezz']:
            key = "png/pure_fa_x_{}.png".format(self.config["mezz"])
            mezz_img = await RackImage(key).get_image()
            await self.start_img_event.wait()
            if self.config['generation'] == 'x' or \
               self.config['generation'] == 'c':
                self.tmp_img.paste(mezz_img, (585, 45))
                self.tmp_img.paste(mezz_img, (585, 425))
            elif self.config['generation'] == 'm':
                self.tmp_img.paste(mezz_img, (709, 44))
                self.tmp_img.paste(mezz_img, (709, 421))

    async def add_fms(self):
        # is  this the right side data pack ?
        # starts with no, then we change to yes after first one
        right = False
        for dp in self.config["chassis_datapacks"]:
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
                the_range = range(0, num_modules)
            else:
                # Populate from the righ to the left
                # easiest  way to follow the DMM rules
                the_range = reversed(range(20-num_modules, 20))

            fm_loc = get_chassis_fm_loc(self.config['generation'])

            for x in the_range:
                # self.tmp_img.save("tmp.png")
                if not right and x >= num_modules:
                    # for short DMM modules, fill the rest with blanks
                    self.tmp_img.paste(blank_img, fm_loc[x])
                else:
                    self.tmp_img.paste(fm_img, fm_loc[x])

            if self.config['dp_label']:
                y_offset = 244
                x_offset = 130

                self.tmp_img = apply_dp_label(self.tmp_img,
                                              dp_size,
                                              x_offset,
                                              y_offset,
                                              right)
            # the next DP must be the right side.
            right = True

    async def add_model_text(self):
        global ttf_path

        if self.config['generation'] == 'x' or \
           self.config['generation'] == 'c':
            loc = (2759, 83)
        else:
            loc = (2745, 120)

        await self.start_img_event.wait()
        c = self.config
        draw = ImageDraw.Draw(self.tmp_img)

        font = ImageFont.truetype(ttf_path, size=24)
        text = "{}{}r{}".format(c['generation'].upper(),
                                c['model_num'],
                                c['release'])
        draw.text(loc, text, (255, 255, 255, 220), font=font)


def apply_fm_label(fm_img, fm_str, fm_type):
    # writing flash module text lables
    utils.apply_text_centered(fm_img, fm_str, 18)
    utils.apply_text_centered(fm_img, fm_type, 32)


def apply_dp_label(img, dp_size, x_offset, y_offset, right):
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

    # put DP on left or right
    box_loc2 = (box_loc[0]+box_size[0], box_loc[1]+box_size[1])

    draw.rectangle((box_loc, box_loc2), fill=(199, 89, 40, 127))
    box_center = ((box_loc[0] + box_loc2[0]) // 2,
                  (box_loc[1] + box_loc2[1]) // 2)
    font = ImageFont.truetype(ttf_path, size=85)
    w, h = draw.textsize(dp_size+"TB", font=font)
    text_loc = (box_center[0] - w/2, box_center[1] - h/2)
    draw.text(text_loc, dp_size + "TB", fill=(255, 255, 255, 220), font=font)

    alpha_tmp = img.convert("RGBA")
    return Image.alpha_composite(alpha_tmp, tmp)


# x,y coordinates for all chassis fms.
def get_chassis_fm_loc(model='x'):
    # these are the anchor locations, and
    # offsets are calculated to fill in holes
    ch0_fm_loc = [None] * 28
    ch0_fm_loc[0] = (165, 250)
    ch0_fm_loc[4] = (714, 250)
    ch0_fm_loc[8] = (1265, 250)
    ch0_fm_loc[12] = (1817, 250)
    ch0_fm_loc[20] = (164, 27)

    x_offset = 105
    for x in range(20):
        if ch0_fm_loc[x] is None:
            loc = list(ch0_fm_loc[x - 1])
            loc[0] += int(x_offset)
            ch0_fm_loc[x] = tuple(loc)

    y_offset = x_offset
    x_offset = 550
    for x in range(20, 28):
        if ch0_fm_loc[x] is None:
            loc = list(ch0_fm_loc[x - 1])
            if x % 2 == 0:
                loc[0] += x_offset
                loc[1] -= y_offset
            else:
                loc[1] += y_offset
            ch0_fm_loc[x] = tuple(loc)

    if model != 'x':
        # adjust slightly for the //m image
        for x in range(len(ch0_fm_loc)):
            ch0_fm_loc[x] = (ch0_fm_loc[x][0] - 9, ch0_fm_loc[x][1] - 7)

    return ch0_fm_loc


# x,y coordinates for all sas fms
def get_sas_fm_loc():
    fm_loc = [None] * 24
    fm_loc[0] = (138, 1)
    fm_loc[12] = (1450, 1)
    x_offset = 105

    for x in range(24):
        if fm_loc[x] is None:
            loc = list(fm_loc[x - 1])
            loc[0] += x_offset
            fm_loc[x] = tuple(loc)
    return fm_loc


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
        if pci_lookup_str in pci_config_lookup:
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
                order = [0, 1]
                if card == "2fc" or card == "2eth" or card == "2ethbaset":
                    # card population order for a half or full card slot
                    order = [2, 0, 1, 3]

                # populate add on cards by the order
                for slot in order:
                    if pci_config[slot] is None:
                        pci_config[slot] = card
                        break

        config["pci_config"] = pci_config

        # pci3 = '2fc'  overrides everything
        for x in range(4):
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
                        if dp != '0':
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

        config["shelves"] = shelves

    def __init__(self, params):
        # front or back
        config = {}

        # mode-str of type  "fa-m70r2" or "fa-x70"
        config["model_str"] = params["model"].lower()
        config["generation"] = config["model_str"][3:4]
        config["model_num"] = int(config["model_str"][4:6])
        config["direction"] = params.get("direction", "up").lower()

        if "r" in config["model_str"] and len(config["model_str"]) > 7:
            config["release"] = int(config["model_str"][7:8])
        else:
            config["release"] = 1

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
            csize = params.get('csize', '')
            if csize not in csize_lookup:
                raise Exception(
                    "Please use a valid csize: {}".format(
                        pformat(csize_lookup.keys())))

            params['datapacks'] = csize_lookup[csize]

        # need for both as shelf type is encoded in DP sizes
        self._init_datapacks(config, params)
        self.config = config

    async def get_image(self):
        tasks = []

        tasks.append(FAChassis(self.config).get_image())
        for shelf in self.config["shelves"]:
            tasks.append(FAShelf(shelf).get_image())

        # go get the cached versions or build images
        # this returns the results of the all the tasks in a list
        all_images = await asyncio.gather(*tasks)

        if self.config["direction"] == "up":
            all_images.reverse()

        return combine_images_vertically(all_images)
