import logging
import os
from pprint import pformat
import re
import asyncio

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
# from io import BytesIO

from . import utils
from .utils import RackImage, add_ports_at_offset, InvalidConfigurationException, InvalidDatapackException, bool_param_get

import jsonurl_py as jsonurl


root_path = os.path.dirname(utils.__file__)
ttf_path = os.path.join(root_path, "Lato-Regular.ttf")

logger = logging.getLogger()
logger.setLevel(logging.WARNING)

class FAShelf():
    def __init__(self, params):
        self.config = params
        self.json_only = bool_param_get(params,'json_only', False)
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
        else:
            tasks.append(self.add_power())

        # load the base image and FMs simultaniously.
        await asyncio.gather(*tasks)
        return {'img':self.tmp_img, 'ports': self.ports}

    # load the first base image
    async def get_base_img(self):
        c = self.config
        key = "png/pure_fa_{}_shelf_{}.png".format(c["shelf_type"], c["face"])

        self.tmp_img = await RackImage(key, self.json_only).get_image()

        # Load image info
        self.img_info = {}
        if key in utils.global_config:
            self.img_info = utils.global_config[key]

        if 'ports' in self.img_info:
            self.ports = self.img_info['ports']

        self.start_img_event.set()

    async def add_power(self):

        if self.config.get('dc_power', False):

            key = "png/pure_fa_dc_1300.png"

            dc_power_img = await RackImage(key, self.json_only).get_image()
            await self.start_img_event.wait()
            self.tmp_img.paste(dc_power_img, self.img_info['psu_loc'][0])
            self.tmp_img.paste(dc_power_img, self.img_info['psu_loc'][1])

    async def add_nvme_fms(self):
        cur_module = 0
         # wait until the base image is loaded
        await self.start_img_event.wait()

        fm_loc = self.img_info['fm_loc']

        total_fm_count = 28
        rotate_after = 19 

        for dp in self.config["datapacks"]:
            dpv2_start_index = -1

            if len(dp) > 4:
                # we are storing values in a list which should be a dictionary
                # as each index corresponds to a different value.
                # however, we are re-using it to pass fm loc, so we need to pull out this extra value
                # and then remove it from the list so it doesn't break the rest of the code.
                dpv2_start_index = dp[4]
                del dp[4]

            

            fm_str = dp[0]
            fm_type = dp[1]
            img_name = 'png/pure_fa_fm_{}.png'.format(fm_type)
            num_modules = dp[2]

            if fm_str == 'Blank':
                num_modules = 14

            fm_img = await RackImage(img_name, self.json_only).get_image()

            if self.config['fm_label']:
                apply_fm_label(fm_img, fm_str, fm_type)

           
            fm_rotated = fm_img.rotate(-90, expand=True)
            
            
            first_fm = True
            the_range = list(range(cur_module, min(28, num_modules + cur_module)))
            cur_module += num_modules
            # curr_modules keeps track of next free location
            # however with dpv2 they can pass in their own.
            if dpv2_start_index != -1:
                the_range = list(range(dpv2_start_index, dpv2_start_index + num_modules))
                cur_module = dpv2_start_index + num_modules
            for x in the_range:
                if x >= total_fm_count:
                    raise InvalidConfigurationException(
                        f"Too many fm modules, check data pack sizes dont exceed chassis size of {total_fm_count}" )
                
                if first_fm:
                    dp.append(fm_loc[x])
                    dp.append(fm_loc[x])
                    dp.append(x > rotate_after) # rotate after
                    first_fm = False
                
                if len(dp) == 7: #Length of 7 means we have a continious DP so far,
                    if fm_loc[x][0] >= dp[5][0] :
                        # The x is to the right, so just update the current DP range with new furthest FM loc
                        dp[5] = fm_loc[x]
                    else:
                        # We are starting a new range because the x is to the left,
                        # these will be in location dp[6] and dp[7]
                        dp.append(fm_loc[x])
                        dp.append(fm_loc[the_range[-1]])
                        dp.append(x > rotate_after) # rotate after

                if x <= rotate_after:
                    self.tmp_img.paste(fm_img, fm_loc[x])
                else:
                    self.tmp_img.paste(fm_rotated, fm_loc[x])
                


        # add datapack labels
        if self.config['dp_label']:
            for dp in self.config["datapacks"]:
                dp_size = dp[3]
                
                if len(dp) > 4:
                    start_loc = dp[4]
                    end_loc = dp[5]
                    rotate = dp[6]
                    try:
                        float(dp_size)
                        text = str(dp_size) + "TB"
                    except (ValueError, TypeError):
                        text = dp_size
                
                    self.tmp_img = apply_dp_labelv2(self.tmp_img, text, start_loc, end_loc, rotate)

                # if it's a continue DP then add the second section.
                if len(dp) > 7:
                    start_loc = dp[7]
                    end_loc = dp[8]
                    rotate = dp[9]
                    text = "..Continued"

                    # use the new apply_dp_label
                    self.tmp_img = apply_dp_labelv2(self.tmp_img, text , start_loc, end_loc, rotate)


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
            fm_img = await RackImage(fm_img_str, self.json_only).get_image()

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
        if "shelves" in config:
            del config["shelves"]
        self.config = config
        self.json_only = config.get('json_only', False)
        self.start_img_event = asyncio.Event()
        self.ch0_fm_loc = None
        self.ports = []
        self.lock = asyncio.Lock()




    async def get_image(self):
        # build the image
        c = self.config
        key = f"png/pure_fa_{c['generation']}_r{c['release']}{c['rev']}"
        


        chassis_gen = ""
        if c["face"] == "front":
            if  c["bezel"]:
                key += "_bezel.png"
                img =  await RackImage(key, self.json_only).get_image()
                return {'img': img, 'ports': []}
            
            if c['release'] in [1] and c['generation'] in ['c', 'e'] or (
                c['release'] in [4] and c['generation'] in ['x', 'c']
            ):
                # check for the next generation chassis
                if c['chassis_gen'] == '2':
                    chassis_gen = "_cg2"

        # not doing bezel
        key += f"_{c['face']}{chassis_gen}.png"

        

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
            tasks.append(self.add_power())

        # run all the tasks concurrently
        await asyncio.gather(*tasks)

        # add port names, has to be done in order so must
        # be after all the tasks are done.

        # add a thread lock here:

        async with self.lock:
            await self.add_port_names()

        return {'img': self.tmp_img, 'ports': self.ports}
    
    # Add port names to each port if it's missing i.e. ct0.eth7
    async def add_port_names(self):
        
        # add port names
        # find all on board ports first
        # select all ports that don't have a pci_slot key

        # add a thread safety lock
      


        
              
        port_naming_key = None
        if self.config['generation'] == 'xl':
            port_naming_key = 'port_naming_xl'
        elif self.config['generation'] == 'e':
            port_naming_key = 'port_naming_xcr4'
        elif self.config['generation'] in ['x', 'c', 'rc'] :
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
                continue # it already has a name so skip

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
                # if port_naming_key == 'port_naming_xcr4' and port['pci_slot'] == 0:
                #    if port['pci_card'] == 'mgmt2ethbaset' and p_i == 6:
                #        p_i = 5
                #    elif port['pci_card'] == 'mgmt2ethbaset' and p_i == 5:
                #        p_i = 7

                # Add the name to the port
                # special case the management port in slot 0
                if port_naming_key == 'port_naming_xcr4' and port['pci_slot'] == 0 \
                          and port['pci_card'] == 'mgmt2ethbaset' and p_i == 6:
                    port['name'] = f"{port['controller']}.{port_type}5"
                else:
                    port['name'] = f"{port['controller']}.{port_type}{p_i}"
                # Increment the counter
                p_i += 1


    async def get_base_img(self, key):
        self.tmp_img = await RackImage(key, self.json_only).get_image()
        self.start_img_event.set()

    async def add_power(self):
        if self.config['generation'] == 'xl':
            return

        if self.config.get('dc_power', False):
            if self.config['dc_power'] == True:
                if self.config['generation'] == 'e':
                    key = "png/pure_fa_dc_1300.png"
                elif self.config['model_num'] == 20:
                    key = "png/pure_fa_dc_1300.png"
                else:
                    key = "png/pure_fa_dc_2000.png"
            else:
                key = f"png/pure_fa_dc_{self.config['dc_power']}.png"

            dc_power_img = await RackImage(key, self.json_only).get_image()
            await self.start_img_event.wait()
            if 'psu_loc' in self.img_info:
                self.tmp_img.paste(dc_power_img, self.img_info['psu_loc'][0])
                self.tmp_img.paste(dc_power_img, self.img_info['psu_loc'][1])
        

    async def add_nvram(self):
        #base image already has 1 NVRAM populated, so this is only for the second one.
        if self.config['chassis_gen'] == '2':
            #gen 2 chassis don't use nvrams
            return

        if self.config['generation'] == 'c':
            # always add second nvram on 'c' array
            if self.config["model_num"] < 60:
                # Don't add second nvram on c40 or c50
                return
            # C60 & c70 do have 4 nvrams
            pass
        elif  self.config['generation'] == 'e':
            # e uses distrubted NVRAM, so todo:
            # Need to change the base image in order to remove
            # and then re-add NVRams.... or add a blank to cover
            # the base image.
            return
        elif self.config['generation'] == 'xl':
            return
        elif self.config["model_num"] < 70:
            # Don't add second nvram on less  than 70
            return
        

        nvram_img = await RackImage("png/pure_fa_x_nvram.png", self.json_only).get_image()

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

        card_img = await RackImage(key, self.json_only).get_image()
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
        try:
            cord = self.img_info['ct0_pci_loc'][slot]
        except KeyError:
            print("KeyError: ct0_pci_loc for slot {}".format(slot))
            raise InvalidConfigurationException(
                f"Invalid configuration for slot {slot}, check your config.yaml file.")
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
        
        if self.config["release"] == 3 and \
            self.config["model_num"] == 20 and \
            self.config["generation"] == 'rc':
            return

        if self.config['mezz']:
            key = "png/pure_fa_x_{}.png".format(self.config["mezz"])
            mezz_img = await RackImage(key, self.json_only).get_image()
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

        # todo add these details into the config.yaml
        total_fm_count = 20
        rotate_after = 1000 # i.e. no rotation

        if self.config['generation'] == 'xl':
            total_fm_count = 40
            rotate_after = 40 #i.e. no rotation
        
        elif self.config['chassis_gen'] == '2':
            total_fm_count = 28
            rotate_after = 19
        

        current_index = 0
        dp_count = len(self.config["chassis_datapacks"])
        fm_loc = self.img_info['fm_loc']

        for dp_i in range(dp_count):
            dp = self.config["chassis_datapacks"][dp_i]
            dpv2_start_index = -1

            if len(dp) > 4:
                # we are storing values in a list which should be a dictionary
                # as each index corresponds to a different value.
                # however, we are re-using it to pass fm loc, so we need to pull out this extra value
                # and then remove it from the list so it doesn't break the rest of the code.
                dpv2_start_index = dp[4]
                del dp[4]

            # see if this is the last data pack or not
            if dp_i > 0 and dp_i + 1 == dp_count:
                # If it's m or X need to populated the 
                # last datapack from the right side
                if self.config['generation'] != 'xl' and self.config['generation'] != 'c':
                    right = True

            fm_str = dp[0]
            fm_type = dp[1]
            num_modules = dp[2]
            dp_size = dp[3]

            file_name = "png/pure_fa_fm_{}.png".format(fm_type)
            fm_img = await RackImage(file_name, self.json_only).get_image()
            

            if self.config['fm_label']:
                apply_fm_label(fm_img, fm_str, fm_type)
  

            await self.start_img_event.wait()
            if not right:
                the_range = list(range(current_index, current_index + num_modules))
                current_index += num_modules
            else:
                the_range = list(range(total_fm_count-num_modules, total_fm_count))
            
            #dp version2
            if dpv2_start_index != -1:
                the_range = list(range(dpv2_start_index, dpv2_start_index + num_modules))
                current_index = the_range[-1] + 1
            
            first_fm = True # used store the first fm location
            for x in the_range:
                if x >= total_fm_count:
                    raise InvalidConfigurationException(
                        f"Too many fm modules, check data pack sizes dont exceed chassis size of {total_fm_count}" )
                if first_fm:
                    dp.append(fm_loc[x]) # dp[4] is the start location of the DP
                    dp.append(fm_loc[x]) # dp[5] is the end, but we just put this as initial, it will be updated later
                    dp.append(x > rotate_after) # rotate after
                    
                        
                    first_fm = False
                
                if len(dp) == 7: #Length of 7 means we have a continious DP so far, 
                    if fm_loc[x][0] >= dp[5][0] :
                        # The x is to the right, so just update the current DP range with new furthest FM loc
                        dp[5] = fm_loc[x]
                    else:
                        # We are starting a new range because the x is to the left,
                        # these will be in location dp[6] and dp[7]
                        dp.append(fm_loc[x])
                        dp.append(fm_loc[the_range[-1]])
                        dp.append(x > rotate_after) # rotate after

                # self.tmp_img.save("tmp.png")
                #if not right and x >= num_modules and self.config["generation"] != 'xl':
                #    # for short DMM modules, fill the rest with blanks
                #    self.tmp_img.paste(blank_img, fm_loc[x])
                #else:
                fm_rotated = fm_img.rotate(-90, expand=True)

                if x in slots and slots[x] != "blank":
                    if fm_type == "blank":
                        pass
                    else:
                        raise InvalidConfigurationException(
                            f"Overlapping datapacks, check data pack sizes dont exceed chassis size of {total_fm_count}")
                else:
                    # check to make sure index is not out of range:
                    if x >= len(fm_loc):
                        raise InvalidConfigurationException(
                            f"Too many fm modules, check data pack sizes dont exceed chassis size of {total_fm_count}" )
                    
                    if x > rotate_after:
                        self.tmp_img.paste(fm_rotated, fm_loc[x])
                    else:
                        self.tmp_img.paste(fm_img, fm_loc[x])
                    # keep track of modules, to detect overlaps
                    slots[x] = fm_type
        
        # add blanks to slots without
        blank_img = await RackImage("png/pure_fa_fm_blank.png", self.json_only).get_image()
        if self.config['fm_label']:
            apply_fm_label(blank_img, "Blank", "")
    
            for x in range(total_fm_count):
                if x not in slots:
                    if x > rotate_after:
                        self.tmp_img.paste(blank_img.rotate(-90, expand=True), fm_loc[x])
                    else:
                        self.tmp_img.paste(blank_img, fm_loc[x])
                
        

        
        if self.config['dp_label']:
            right = False
            for dp in self.config["chassis_datapacks"]:
                fm_str = dp[0]
                fm_type = dp[1]
                num_modules = dp[2]
                dp_size = dp[3]
                

                # just checks the dp info has the start_loc and end_loc
                if len(dp) > 4:
                    start_loc = dp[4]
                    end_loc = dp[5]
                    rotate = dp[6]
                    try:
                        float(dp_size)
                        text = str(dp_size) + "TB"
                    except (ValueError, TypeError):
                        text = dp_size

                    self.tmp_img = apply_dp_labelv2(self.tmp_img, text , start_loc, end_loc, rotate)

                # if it's a continue DP then add the second section.
                if len(dp) > 7:
                    start_loc = dp[7]
                    end_loc = dp[8]
                    rotate = dp[9]
                    text = "..Continued"

                    # use the new apply_dp_label
                    self.tmp_img = apply_dp_labelv2(self.tmp_img, text , start_loc, end_loc, rotate)
    
                       

    async def add_model_text(self):
        global ttf_path

        loc = self.img_info['model_text_loc']

        await self.start_img_event.wait()
        c = self.config
        draw = ImageDraw.Draw(self.tmp_img)

        font = ImageFont.truetype(ttf_path, size=24)

        text = ""
        if c['generation'] == 'xl' :
            text = "{}r{}".format(c['model_num'],
                                    c['release'])
        elif c['generation'] == 'e':
            if c['release'] == 1:
                text = "" #change to 
                
        elif (c['generation'] == 'c' or c['generation'] == 'rc') and c['model_num'] == 20:
            text = "{}{}".format(c['generation'].upper(),
                                    c['model_num'])

        else:
            text = "{}{}r{}".format(c['generation'].upper(),
                                    c['model_num'],
                                    c['release'])
            

        if c['chassis_gen'] == '2':
            #Draw the Generation Letter on the 2nd gen chassis
            draw.text((2785,160), f" {c['generation'].upper()} ", (255, 255, 255, 220), font=font)
        
        draw.text(loc, text, (255, 255, 255, 220), font=font)


def apply_fm_label(fm_img, fm_str, fm_type):
    # writing flash module text lables
    utils.apply_text_centered(fm_img, fm_str, 18)
    if fm_type != "blank":
        utils.apply_text_centered(fm_img, fm_type, 32)

def apply_dp_labelv2(img, dp_size, start_loc_provided, end_loc_provided, rotated=False):
    if dp_size == '0TB':
        return img
    
    # Handle MockImage case early
    if hasattr(img, '__class__') and img.__class__.__name__ == 'MockImage':
        return img  # For MockImages, just return the original image
    
    global ttf_path
    # temp image same size as our chassis.
    tmp = Image.new('RGBA', img.size, (0, 0, 0, 0))

    # Create a drawing context for it.
    draw = ImageDraw.Draw(tmp)

    x_buffer = 50
    y_buffer = 75
    y_size = 420
    x_size = 0

    if rotated:
        y_size = 75 # this is for the shelf and gen2 chassis
        y_buffer = 20
        x_size = 350

    start_loc = (min(start_loc_provided[0], end_loc_provided[0]),
                min(start_loc_provided[1], end_loc_provided[1]))
    end_loc = (max(start_loc_provided[0], end_loc_provided[0]),
                max(start_loc_provided[1], end_loc_provided[1]))


    box_loc = (start_loc[0] + x_buffer, start_loc[1] + y_buffer)

    end_loc = (end_loc[0] + x_buffer + x_size,
                (end_loc[1] + y_size))

    draw.rectangle((box_loc, end_loc), fill=(199, 89, 40, 127))
    box_center = ((box_loc[0] + end_loc[0]) // 2,
                  (box_loc[1] + end_loc[1]) // 2)
    font = ImageFont.truetype(ttf_path, size=85)
    #w, h = draw.textsize(dp_size, font=font)
    _,_,w,h = draw.textbbox((0,0), text=dp_size, font=font)

    #if w!=w_new or h !=h_new :
    #    Exception("new bbox wrong values")

    

    text_loc = (box_center[0] - w/2, box_center[1] - h/2)
    draw.text(text_loc, dp_size , fill=(255, 255, 255, 220), font=font)
    #logger.debug("converting image to RGBA")
    alpha_tmp = img.convert("RGBA")
    #logger.debug("converted image to RGBA, doing composite")
    composite_img = Image.alpha_composite(alpha_tmp, tmp)
    #logger.debug("done composite")
    return composite_img

def apply_dp_label(img, dp_size, x_offset, y_offset, right, full=False):
    # Handle MockImage case early
    if hasattr(img, '__class__') and img.__class__.__name__ == 'MockImage':
        return img  # For MockImages, just return the original image
        
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
    #w, h = draw.textsize(dp_size + "TB", font=font)
    _,_,w,h = draw.textbbox((0,0), text=dp_size + "TB", font=font)
    #if w!=w_new or h !=h_new :
    #    Exception("new bbox wrong values")


    text_loc = (box_center[0] - w/2, box_center[1] - h/2)
    draw.text(text_loc, dp_size + "TB", fill=(255, 255, 255, 220), font=font)
    #logger.debug("converting image to RGBA")
    alpha_tmp = img.convert("RGBA")
    #logger.debug("converted image to RGBA, doing composite")
    composite_img = Image.alpha_composite(alpha_tmp, tmp)
    #logger.debug("done composite")
    return composite_img


# FADiagram does most of the logical config parsing and validation of configuration
#
class FADiagram():

    def _init_pci_cards(self, config, params):
        pci_valid_cards = utils.global_config['pci_valid_cards']
        pci_config_lookup = utils.global_config['pci_config_lookup']

        pci_config = [None, None, None, None]
        c = config
        pci_lookup_str = f'fa-{c["generation"]}{c["model_num"]}r{c["release"]}{c["rev"]}-{config["protocol"]}'
        
        
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
                    raise InvalidConfigurationException("invalid pci card: {}, valid cards:{}".format(
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
                elif (config['generation'] == 'x' or config['generation'] == 'c') and config['release'] == 4 and (config['rev'] == 'b' or config['rev'] == 'c'):
                    if card == "2eth100roce":
                        fh_order = [0, 1, 2, 3, 4]
                        hh_order = [0, 1, 2, 3, 4]
                    else:
                        fh_order = [1, 2, 3, 4, 0]
                        hh_order = [1, 2, 3, 4, 0]
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
                raise InvalidConfigurationException("invalid pci card: {}, valid cards:{}".format(
                    card, pformat(pci_valid_cards)))
            pci_config[x] = card

    def _init_datapacks_v2(self, config, params):
        #
        try:
            dpv2 = jsonurl.loads(params["datapacksv2"])
        except Exception as e:
            raise InvalidDatapackException("Invalid JSON in datapacksv2: {}".format(e))

        

        def get_default_fm_type(fm_size):
            # default fm type is based on the size
            if fm_size.upper() == "BLANK" or fm_size == "0":
                return "Blank"
            
            if config['generation'] in ['c', 'e', 'rc']:
                return "nvme-qlc"
            
            if fm_size == "750GB":
                return "scm"
            
            return "nvme"
        
        def get_default_dp_label(fm_size, fm_count):
            if fm_size == "Blank":
                return "0TB"
            
            import re
            
            # More robust parsing using regex to handle flexible spacing and formatting
            size_str = fm_size.strip()
            
            # Check for binary and decimal storage units (order matters - check longer units first)
            units_to_check = ['PiB', 'TiB', 'GiB', 'PB', 'TB', 'GB']
            
            for unit_upper in units_to_check:
                # Create regex pattern for flexible matching: number + optional whitespace + unit (case insensitive)
                pattern = r'^(\d+(?:\.\d+)?)\s*(' + re.escape(unit_upper) + r')$'
                match = re.match(pattern, size_str, re.IGNORECASE)
                
                if match:
                    try:
                        size_value = float(match.group(1))
                        # Preserve the original unit with any spacing from the input
                        # Find where the number ends and extract everything after (including spaces)
                        number_end = match.end(1)
                        unit = size_str[number_end:].strip()
                        if not unit:  # Fallback if something goes wrong
                            unit = match.group(2)
                        
                        # Calculate total capacity: fm_size * fm_count
                        total_capacity = size_value * fm_count
                        # Format as integer if it's a whole number, otherwise as float
                        total_capacity = round(total_capacity, 1)
                        if total_capacity == int(total_capacity):
                            return f"{int(total_capacity)} {unit}"
                        else:
                            return f"{total_capacity} {unit}"
                    except ValueError:
                        continue
            
            # If no standard unit found, try to extract any number + text pattern
            fallback_pattern = r'^(\d+(?:\.\d+)?)\s*(.*)$'
            fallback_match = re.match(fallback_pattern, size_str)
            if fallback_match:
                try:
                    size_value = float(fallback_match.group(1))
                    unit = fallback_match.group(2).strip()
                    if unit:
                        total_capacity = size_value * fm_count
                        total_capacity = round(total_capacity, 1)
                        if total_capacity == int(total_capacity):
                            return f"{int(total_capacity)} {unit}"
                        else:
                            return f"{total_capacity} {unit}"
                except ValueError:
                    pass
            
            # If parsing fails, return format: "count x size"
            return f"{fm_count} x {fm_size}"

        
        shelves = []
        
        config["chassis_datapacks"] = []
        config['ru'] = 0 # this allows for any order of keys
        shelf = False
        
        for chassis in dpv2:   
        
            next_chassis_index = 0
            datapacks = []
            chassis_type = chassis.get('chassis_type', 'nvme')
            
            for dp in chassis['datapacks']:
                
                # dp should be of form [fm_str, fm_type, num_modules, dp_label, first_slot]
                
                num_modules = dp['fm_count']
                fm_size = dp['fm_size']
                dp_label = dp.get('dp_label', get_default_dp_label(fm_size, num_modules))
                fm_type = dp.get('fm_type', get_default_fm_type(fm_size) )
                first_slot = dp.get('first_slot', next_chassis_index)
                next_chassis_index = first_slot + num_modules

                datapacks.append(
                    [fm_size, fm_type, num_modules, dp_label, first_slot]
                )

            if shelf:
                shelves.append(
                    {
                        "shelf_type": chassis_type,
                        "datapacks": datapacks,
                        "face": config["face"],
                        "dp_label": config["dp_label"],
                        "fm_label": config["fm_label"],
                    }
                )
                config['ru'] += 3
            else:
                config["chassis_datapacks"] = datapacks
                
                if config['generation'] in ['xl']:
                    config['ru'] = + 5
                else:
                    config['ru'] = + 3
            shelf = True # after first chassis, we are in shelf mode
        config["shelves"] = shelves

            

    def _init_datapacks(self, config, params):
        ######################################
        #  Parse Data Packs & Shelf 

        if "datapacksv2" in params:
            self._init_datapacks_v2(config, params)
            return

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
                        raise InvalidDatapackException("Unknown Chassis: DP: {}\nPick from One of the Following\n{}".
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
                        raise InvalidDatapackException("Unknown Shelf: DP: {}\nPick from One of the Following\n{}".
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
                    shelves.append({'shelf_type': shelf_type, "face": 'back', 'dc_power': config['dc_power']})

                if shelf_type == 'nvme':
                    config['ru'] += 3
                else:
                    config['ru'] += 2

        config["shelves"] = shelves

    def __init__(self, params):
        # front or back
        config = {}
        c=config
        self.ports = []
        self.json_only = params.get('json_only', False)

        config["model_str"] = params["model"].lower()


        # mode-str of type  "fa-m70r2" or "fa-x70" or "fa-xl130" or fa-xl170r2
        # Split string on the - and transition to numbers
        #5/22/2024 we have a format change to fa-x70r4b the b is a revision to the release.

        #splits on instance of change from decimal to letter and - and r
        # 4/1/2025 we now have a new model format of rc20,  so we need to revise to not split on r but keep everything backward compatible.
        # i think we could split on every transition from letter to number and -
        

        try: 
            if "rc" in config["model_str"]:
                results = re.split(r'(?<=[0-9])(?=[A-Za-z])'   # between digit and letter
                                r'|(?<=[A-Za-z])(?=[0-9])'  # between letter and digit
                                r'|-',
                                config["model_str"])
                config["generation"] = results[1]
                config["model_num"] = int(results[2])
                config["release"] = 3
                config["rev"] = ""
                if len(results) > 4:
                    config["release"] = int(results[4])
            else:
                results = re.split(r'(\d+)|-|r', config["model_str"])
                config["generation"] = results[2]
                config["rev"] = ""

                if config['generation'] == 'e':
                    config['model_num'] = ""
                    config['release'] = 1

                else:
                    config['model_num'] = int(results[3])
                    if not results[3].isnumeric():
                        pass
                    if len(results) > 5:
                        config['rev'] = results[5]

                if "r" in config["model_str"]:
                    if config['generation'] == 'e':
                        config["release"] = int(results[5])
                        if len(results) > 6:
                            config["rev"] = results[6]
                    elif config['generation'] == 'rc':
                        if len(results) > 4:
                            config["release"] = int(results[4])
                        if len(results) > 6:
                            config["rev"] = results[6]
                    else:
                        config["release"] = int(results[7])
                        if len(results) > 8:
                            config["rev"] = results[8]
                    
                elif config['generation'] == 'c' and config['model_num'] == 20:
                    config["release"] = 4
                    config["rev"] = 'c'                
                    config["chassis_gen"] = '2'

                else:
                    config["release"] = 1
        except (IndexError, ValueError) as e:
            raise InvalidConfigurationException(
                "Invalid model string: {}, please use the format fa-x70r2, fa-m70r2, fa-xl130, fa-xl170r2".format(
                    config["model_str"]))


        
        config["direction"] = params.get("direction", "up").lower()

        

        if config["generation"] == 'xl':
            config["ru"] = 5  # this gets increased during shelf parsing
        else:
            config["ru"] = 3  # this gets increased during shelf parsing

        
        face = params.get("face", "front")
        if face != "front" and face != "back":
            face = "front"
        config["face"] = face

        config["fm_label"] = params.get("fm_label", False)
        config["dp_label"] = params.get("dp_label", False)
        config["bezel"] = params.get("bezel", False)

        if face == "back":
            config['bezel'] = False
            
            config["dc_power"] = params.get("dc_power", False)
            # check for string versions of no/false
            for item in ["dc_power"]:
                if config[item] in ['False', 'false', 'FALSE', 'no', '0', ""]:
                    config[item] = False
                if config[item] in ['True', "TRUE", 'true', 'yes' ]:
                    config[item] = True

            if config["dc_power"] not in [True, False, "1300", "2000"]:
                raise InvalidConfigurationException("Please use a valid dc_power: 1300, 2000")


            valid_protocols = ['fc', 'eth']
            config["protocol"] = params.get("protocol", "fc").lower()
            if config['protocol'] not in valid_protocols:
                raise InvalidConfigurationException("invalid protocol: {}, valid cards:{}".format(
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
                raise InvalidConfigurationException(
                    f"Please use a valid mezzainine: {pformat(valid_mezz)}")

            self._init_pci_cards(config, params)

        else:
            # face == 'front'
            

            # we guarantted chassis gen will be in the config
            if "chassis_gen" not in params:
                config['chassis_gen'] = '1'
                
                # default to gen2 chassis for 70 & 90 models for x, c R4
                if config['generation'] in ['x', 'c'] and config['model_num'] in [70, 90] and config['release'] == 4:
                    config['chassis_gen'] = '2'

                # c20 is gen 2 chassis
                if config['generation'] == 'c' and config['model_num'] == 20 and config['release'] == 1:
                    config['chassis_gen'] = '2'

                # all e is now default gen 2
                if config['generation'] == 'e':
                    config['chassis_gen'] = '2'
                
            else:
                config["chassis_gen"] = params.get("chassis_gen").lower() # For xcr4 chassis gen 2, will be the new default
                if config["chassis_gen"] not in ['1', '2']:
                    raise InvalidConfigurationException("Please use a valid chassis_gen: 1, 2")

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
                    raise InvalidDatapackException(
                        "Please use a valid csize: {}".format(
                            pformat(csize_lookup.keys())))

            elif 'datapacks' in params and params['datapacks'] != '':
                #they specified the datapacks use those.
                pass
            elif 'datapacksv2' in params and params['datapacksv2'] != '':
                pass
            else:
                raise InvalidDatapackException("Please provide either csize or datapacks")

        # need for both as shelf type is encoded in DP sizes
        self._init_datapacks(config, params)
        self.config = config

    async def get_image(self):
        tasks = []

        chassis_config = self.config.copy()
        chassis_config['json_only'] = self.json_only
        tasks.append(FAChassis(chassis_config).get_image())

        for shelf in self.config["shelves"]:
            shelf_config = shelf.copy()
            shelf_config['json_only'] = self.json_only
            tasks.append(FAShelf(shelf_config).get_image())

        # this returns the results of the all the tasks in a list
        all_image_ports = await asyncio.gather(*tasks)

        if self.config["direction"] == "up":
            all_image_ports.reverse()

        return all_image_ports
    
        #final_img, all_ports = combine_images_vertically(all_image_ports)
        #self.ports = all_ports
        #return final_img
