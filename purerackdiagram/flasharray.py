from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
# from io import BytesIO
import asyncio
from . import utils
from .utils import RackImage, combine_images_vertically, add_ports_at_offset
import logging
import os
from pprint import pformat
import re

root_path = os.path.dirname(utils.__file__)
ttf_path = os.path.join(root_path, "Lato-Regular.ttf")

logger = logging.getLogger()

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
         # wait until the base image is loaded
        await self.start_img_event.wait()

        fm_loc = self.img_info['fm_loc']

       
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

           
            fm_rotated = fm_img.rotate(-90, expand=True)
            
            
            first_fm = True
            for x in range(cur_module, min(28, num_modules + cur_module)):
                if first_fm:
                    dp.append(fm_loc[x])
                    dp.append("")
                    first_fm = False

                if x < 20:
                    self.tmp_img.paste(fm_img, fm_loc[x])
                    dp[5] = fm_loc[x]
                else:
                    self.tmp_img.paste(fm_rotated, fm_loc[x])
                    ## raise the y value of sthe starting point.
                    dp[4] = (dp[4][0],min(fm_loc[x][1], dp[4][1]))
                    
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
                right = True

                #self.tmp_img = apply_dp_label(self.tmp_img,
                #                              dp_size,
                #                              x_offset,
                #                              y_offset,
                #                              right,
                #                              full)

                self.tmp_img = apply_dp_labelv2(self.tmp_img, dp_size+"TB", dp[4], dp[5])
                

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

        # add port names, has to be done in order so must
        # be after all the tasks are done.
        await self.add_port_names()

        return {'img': self.tmp_img, 'ports': self.ports}
    
    # Add port names to each port if it's missing i.e. ct0.eth7
    async def add_port_names(self):
        
        # add port names
        # find all on board ports first
        # select all ports that don't have a pci_slot key
        
              
        port_naming_key = None
        if self.config['generation'] == 'xl':
            port_naming_key = 'port_naming_xl'
        elif self.config['generation'] == 'e':
            port_naming_key = 'port_naming_xcr4'
        elif self.config['generation'] in ['x', 'c'] :
            if self.config['release'] == 4:
                port_naming_key = 'port_naming_xcr4'
            else:
                port_naming_key = 'port_naming_xcr2'
        
        if port_naming_key:
            port_naming = utils.global_config[port_naming_key]
        else:
            return
        
        prev_ctslotmezz = None
        p_i = 0
            
        for port in self.ports:
            if 'name' in port:
                continue

            if 'port_type' in port and 'controller' in port:
                port_type = port['port_type']
                if port_type == 'eth_roce':
                    port_type = 'eth'
                
                # because we don't have an indication on when we switch to the next card we need to 
                # use this slightly messy approach.
                    
                if 'pci_slot' in port:
                    if prev_ctslotmezz != (port['controller'] + str(port['pci_slot'])):
                        p_i = port_naming[port['pci_slot']][port_type]
                        prev_ctslotmezz = port['controller'] + str(port['pci_slot'])
                elif 'mezz' in port:
                    if prev_ctslotmezz != (port['controller'] + 'mezz'):
                        p_i = port_naming['mezz'][port_type]
                        prev_ctslotmezz = port['controller'] + 'mezz'
                else:
                    continue


                # special case the management port on the xcr4
                if port_naming_key == 'port_naming_xcr4' and port['pci_slot'] == 0:
                    if port['pci_card'] != 'mgmt2ethbaset' and p_i == 5:
                        port_naming[0]['eth'] += 1

                # Add the name to the port
                port['name'] = f"{port['controller']}.{port_type}{p_i}"
                # Increment the counter
                p_i += 1


    async def get_base_img(self, key):
        self.tmp_img = await RackImage(key).get_image()
        self.start_img_event.set()

    async def add_nvram(self):
        #base image already has 1 NVRAM populated, so this is only for the second one.

        if self.config['generation'] == 'c':
            # always add second nvram on 'c' array
            pass
        elif  self.config['generation'] == 'e':
            #e probably has only 1 nvram, but i'm not sure.
            #todo: check nvrams on e
            return
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

        if self.config['generation'] == 'e':
            if slot in [1,2]:
                height = "fh"
            else:
                height = "hh"

        elif self.config['generation'] == 'xl':
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
        await self.start_img_event.wait() # why is this here ?

        # check to see if this is the default card in this slot

        card_is_default = False
        if self.config['default_pci_config'][slot] == card_type:
            card_is_default = True
        
        height_str = "Full Height"
        if height == "hh":
            height_str = "Half Height"
        
        #Get port name
        

        additional_keys  = {'pci_slot': slot,
                            'pci_slot_height': height_str, 
                            'pci_card': card_type,
                            'default_card': card_is_default,
                            'controller': "ct0" }
        # ct0
        cord = self.img_info['ct0_pci_loc'][slot]
        self.tmp_img.paste(card_img, cord)
        add_ports_at_offset(key, cord, self.ports, additional_keys.copy())

        # ct1
        cord = self.img_info['ct1_pci_loc'][slot]
        additional_keys['controller'] = "ct1"
        add_ports_at_offset(key, cord, self.ports, additional_keys.copy())
        self.tmp_img.paste(card_img, cord)

    async def add_mezz(self):
        if self.config["generation"] == "xl":
            return
        
        if self.config["release"] == 4:
            return
    
        if self.config["generation"] == 'e':
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
        # starts with no, then we change to yes if it's the last datapack.
        right = False
        slots = {}

        # of chassis slots
        await self.start_img_event.wait()

        total_fm_count = 20
        current_index = 0
        dp_count = len(self.config["chassis_datapacks"])
        fm_loc = self.img_info['fm_loc']

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
            

            if self.config['fm_label']:
                apply_fm_label(fm_img, fm_str, fm_type)
  

            await self.start_img_event.wait()
            if not right:
                the_range = list(range(current_index, current_index + num_modules))
                current_index += num_modules
            else:
                # this is hard coded 20, probably fine
                the_range = list(range(20-num_modules, 20))

           

            first_fm = True # used store the first fm location
            for x in the_range:
                if first_fm:
                    dp.append(fm_loc[x])
                    dp.append(fm_loc[x])
                    first_fm = False
                
                if len(dp) == 6:
                    if fm_loc[x][0] >= dp[5][0] :
                        dp[5] = fm_loc[x]
                    else:
                        dp.append(fm_loc[x])
                        dp.append(fm_loc[the_range[-1]])

                
                
                    
                
                # self.tmp_img.save("tmp.png")
                #if not right and x >= num_modules and self.config["generation"] != 'xl':
                #    # for short DMM modules, fill the rest with blanks
                #    self.tmp_img.paste(blank_img, fm_loc[x])
                #else:

                if x in slots and slots[x] != "blank":
                    if fm_type == "blank":
                        pass
                    else:
                        raise Exception(
                            "Overlapping datapacks, check data pack sizes dont exceed chassis size of 20.")
                else:
                    # check to make sure index is not out of range:
                    if x >= len(fm_loc):
                        raise Exception(
                            "Too many fm modules, check data pack sizes dont exceed chassis size of:"+str(len(fm_loc))) 
                    self.tmp_img.paste(fm_img, fm_loc[x])
                    # keep track of modules, to detect overlaps
                    slots[x] = fm_type
        
        # add blanks to slots without
        blank_img = await RackImage("png/pure_fa_fm_blank.png").get_image()
        if self.config['fm_label']:
            apply_fm_label(blank_img, "Blank", "")
    
            for x in range(total_fm_count):
                if x not in slots:
                    self.tmp_img.paste(blank_img, fm_loc[x])
        

        
        if self.config['dp_label']:
            right = False
            for dp in self.config["chassis_datapacks"]:
                fm_str = dp[0]
                fm_type = dp[1]
                num_modules = dp[2]
                dp_size = dp[3]

                if len(dp) > 4:
                    start_loc = dp[4]
                    end_loc = dp[5]
                    # use the new apply_dp_label
                    self.tmp_img = apply_dp_labelv2(self.tmp_img, dp_size + "TB", start_loc, end_loc)
                    
                    if len(dp) > 6:
                        
                        start_loc = dp[6]
                        end_loc = dp[7]
                        self.tmp_img = apply_dp_labelv2(self.tmp_img,"..Continued", start_loc, end_loc)
        
                       


                else:
                   

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
        if c['generation'] == 'xl' :
            text = "{}r{}".format(c['model_num'],
                                    c['release'])
        elif c['generation'] == 'e':
            if c['release'] == 1:
                text = ""
            else:
                text = "{}r{}".format(c['generation'].upper(),
                                    c['model_num'])
        else:
            text = "{}{}r{}".format(c['generation'].upper(),
                                    c['model_num'],
                                    c['release'])
        draw.text(loc, text, (255, 255, 255, 220), font=font)


def apply_fm_label(fm_img, fm_str, fm_type):
    # writing flash module text lables
    utils.apply_text_centered(fm_img, fm_str, 18)
    if fm_type != "blank":
        utils.apply_text_centered(fm_img, fm_type, 32)

def apply_dp_labelv2(img, dp_size, start_loc_provided, end_loc_provided):
    if dp_size == '0TB':
        return img
    
    global ttf_path
    # temp image same size as our chassis.
    tmp = Image.new('RGBA', img.size, (0, 0, 0, 0))

    # Create a drawing context for it.
    draw = ImageDraw.Draw(tmp)

    x_buffer = 50
    y_buffer = 75
    y_size = 420

    start_loc = (min(start_loc_provided[0], end_loc_provided[0]),
                min(start_loc_provided[1], end_loc_provided[1]))
    end_loc = (max(start_loc_provided[0], end_loc_provided[0]),
                max(start_loc_provided[1], end_loc_provided[1]))


    box_loc = (start_loc[0] + x_buffer, start_loc[1] + y_buffer)

    end_loc = (end_loc[0] + x_buffer,
                (end_loc[1] + y_size))

    draw.rectangle((box_loc, end_loc), fill=(199, 89, 40, 127))
    box_center = ((box_loc[0] + end_loc[0]) // 2,
                  (box_loc[1] + end_loc[1]) // 2)
    font = ImageFont.truetype(ttf_path, size=85)
    w, h = draw.textsize(dp_size, font=font)
    text_loc = (box_center[0] - w/2, box_center[1] - h/2)
    draw.text(text_loc, dp_size , fill=(255, 255, 255, 220), font=font)
    logger.debug("converting image to RGBA")
    alpha_tmp = img.convert("RGBA")
    logger.debug("converted image to RGBA, doing composite")
    composite_img = Image.alpha_composite(alpha_tmp, tmp)
    logger.debug("done composite")
    return composite_img

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
    logger.debug("converting image to RGBA")
    alpha_tmp = img.convert("RGBA")
    logger.debug("converted image to RGBA, doing composite")
    composite_img = Image.alpha_composite(alpha_tmp, tmp)
    logger.debug("done composite")
    return composite_img


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
        config['default_pci_config'] = pci_config.copy()

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
                    fh_order = [2, 3, 7, 0, 6, 4, 1, 8, 5]
                    hh_order = [2, 3, 7, 0, 6, 4, 1, 8, 5]
                elif config["generation"] == 'e':
                    fh_order = [0, 1, 2, 3, 4]
                    hh_order = [0, 1, 2, 3, 4]
                elif (config['generation'] == 'x' or config['generation'] == 'c') and config['release'] == 4:
                    fh_order = [0, 1, 2, 3, 4]
                    hh_order = [0, 1, 2, 3, 4]
                else:
                    fh_order = [0, 1]
                    hh_order = [2, 0, 1, 3]
                order = fh_order

                if card == "2fc" or card == "2eth" or card == "2ethbaset":
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
        #  Parse Data Packs & Shelf 

        chassis_dp_size_lookup = None
        shelf_dp_size_lookup = None
        if('x' in config["model_str"] or 'm' in config["model_str"]):
           
            chassis_dp_size_lookup = utils.global_config['chassis_dp_size_lookup']
            shelf_dp_size_lookup = utils.global_config['shelf_dp_size_lookup']
        else:
            chassis_dp_size_lookup = utils.global_config['qlc_chassis_dp_size_lookup']
            shelf_dp_size_lookup = utils.global_config['qlc_shelf_dp_size_lookup']

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
                        datapacks.append(chassis_dp_size_lookup[dp].copy())
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
                        datapacks.append(shelf_dp_size_lookup[dp].copy())
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
        if config['model_str'] == 'fa-er1-f':

            pass

        # mode-str of type  "fa-m70r2" or "fa-x70" or "fa-xl130" or fa-xl170r2
        # Split string on the - and transition to numbers
        results = re.split('(\d+)|-|r', config["model_str"])
        config["generation"] = results[2]
        if config['generation'] == 'e':
            config['model_num'] = ""
        else:
            config['model_num'] = int(results[3])

        if "r" in config["model_str"]:
            if config['generation'] == 'e':
                config["release"] = int(results[5])
            else:
                config["release"] = int(results[7])
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
            # this probably should be in the config.yaml
            default_mezz = 'emezz'
            valid_mezz = [None, 'emezz', 'smezz']
            if config['generation'] in ['xl', 'e']:
                default_mezz = None
            elif config['generation'] in ['x','c'] and config["release"] == 4:
                default_mezz = None
            elif config['generation'] == 'm':
                default_mezz = 'smezz'
            elif config['generation'] == 'x' and config["model_num"] == 10:
                default_mezz = 'None'
            elif config['generation'] == 'c':
                if config['release'] == 3 and config['model_num'] == 40:
                    default_mezz = None
                else:
                    default_mezz = 'emezz'

            config["mezz"] = params.get("mezz", default_mezz)
            if config['mezz'] == "":
                config['mezz'] = default_mezz
            
            if config['mezz'] and config['mezz'].upper() == 'NONE':
                config['mezz'] = None

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
                if csize in utils.global_config['qlc_chassis_dp_size_lookup']:
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
