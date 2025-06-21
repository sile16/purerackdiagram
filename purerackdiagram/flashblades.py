import asyncio
from cmath import exp
from os.path import join
from PIL import ImageDraw
from PIL import Image
from PIL import ImageFont
# Import custom exceptions
import sys
import re
from .utils import InvalidConfigurationException, InvalidDatapackException, RackDiagramException
from .utils import RackImage, add_ports_at_offset, combine_images_vertically, global_config, apply_text

from .flasharray import apply_fm_label
import logging

import jsonurl_py as jsonurl

logging = logging.getLogger(__name__)



class FBSDiagram():
    def __init__(self, params):
        self.ports = []

        config = {}
        raw_model = params.get("model").lower()
        config["model"] = self._parse_and_normalize_model(raw_model)
        config["model_parsed"] = self._parse_model_to_json(config["model"])
        config["chassis"] = int(params.get("no_of_chassis", 1))
        config['ru'] = config["chassis"]*5
        config["face"] = params.get("face", "front").lower()
        config["xfm_face"] = params.get("xfm_face", "").lower()
        config["bezel"] = params.get("bezel", False)
        config['direction'] = params.get("direction", "up").lower()
        config['dfm_size'] = float(params.get("drive_size", 24))
        config['dfm_count'] = int(params.get("no_of_drives_per_blade", 1))
        # Handle bladesv2 or fallback to legacy blades processing
        if "bladesv2" in params:
            config = self._init_blades_v2(params, config)
        else:
            config['blades'] = int(params.get("no_of_blades", 7))

        config['xfm_model'] = params.get('xfm_model', '8400').lower()
        valid_xfm_model =['3200e', '8400']
        if config['xfm_model'] not in valid_xfm_model:
            raise InvalidConfigurationException('please provide a valid xfm_model: {}'.format(valid_xfm_model))

        if config['xfm_face'] == "":
            config['xfm_face'] = config['face']
        elif config['xfm_face'] not in ['front', 'back', 'bezel']:
            raise InvalidConfigurationException(f"Invalid XFM Face, {config['xfm_face']}")


        if not self._is_valid_model_format(config['model']):
            raise InvalidConfigurationException('please provide a valid model format: fb-s{number}[r{version}] or fb-e')

        # Only validate legacy blades if not using bladesv2
        if "bladesv2" not in params:
            if config['blades'] < 0 or config['blades'] > 100 :
                raise InvalidConfigurationException('please provide blades count 0-100.')

            default_chassis = (config['blades'] - 1 )// 10 + 1
            if config['chassis'] < default_chassis:
                config['chassis'] = default_chassis

            valid_dfm_count = [1, 2, 3, 4]
            if config['dfm_count'] not in valid_dfm_count:
                raise InvalidConfigurationException('Valid drive counts: {}'.format(valid_dfm_count))

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

    def _parse_and_normalize_model(self, raw_model):
        """Parse model string and add default r2 if no r-version specified"""
        # Check for existing r-version patterns: fb-s{number}r{version} or fb-er{version}
        if re.match(r'^fb-s(\d+)r(\d+)$', raw_model) or re.match(r'^fb-er(\d+)$', raw_model):
            return raw_model  # Already has r-version
            
        # Check for base model patterns: fb-s{number} or fb-e
        s_match = re.match(r'^fb-s(\d+)$', raw_model)
        if s_match:
            model_number = s_match.group(1)
            # S200 and S500 get default r2, S100 gets default r1
            if model_number in ['200', '500']:
                return f"{raw_model}r2"
            else:
                return f"{raw_model}r1"
        elif raw_model == 'fb-e':
            return 'fb-er1'  # E series gets default r1
            
        # Return as-is for invalid formats (will be caught by validation)
        return raw_model

    def _is_valid_model_format(self, model):
        """Validate model format: fb-s{number}r{version}, fb-er{version}, or fb-e"""
        if model == 'fb-e':
            return True
            
        # Check r-version patterns: fb-s{number}r{version} or fb-er{version}
        return bool(re.match(r'^fb-s(\d+)r(\d+)$|^fb-er(\d+)$', model))

    def _parse_model_to_json(self, model):
        """Parse model string into structured JSON data for easy access.
        
        Returns:
            dict: {
                "type": "s" | "e",
                "number": str (for S-series only),
                "revision": str,
                "full_model": str
            }
        """
        if model == 'fb-e':
            return {
                "type": "e",
                "number": None,
                "revision": "1",  # fb-e is equivalent to fb-er1
                "full_model": model
            }
            
        # Parse fb-er{version} format
        er_match = re.match(r'^fb-er(\d+)$', model)
        if er_match:
            return {
                "type": "e", 
                "number": None,
                "revision": er_match.group(1),
                "full_model": model
            }
            
        # Parse fb-s{number}r{version} format
        s_match = re.match(r'^fb-s(\d+)r(\d+)$', model)
        if s_match:
            return {
                "type": "s",
                "number": s_match.group(1),
                "revision": s_match.group(2),
                "full_model": model
            }
            
        # Fallback (shouldn't happen with proper validation)
        return {
            "type": "unknown",
            "number": None,
            "revision": "1",
            "full_model": model
        }

    def _generate_blade_model_text_from_parsed(self, model_parsed):
        """Generate blade model text from parsed JSON data for display.
        
        Args:
            model_parsed: Dict containing parsed model data
            
        Returns:
            str: Model text for blade display (e.g., "S200", "S200r2", "E", "Er2")
        """
        model_type = model_parsed["type"]
        revision = model_parsed["revision"]
        
        if model_type == "e":
            # E-series: only show r-version if not r1 (preserve backward compatibility)
            if revision == "1":
                return "E"
            else:
                return f"Er{revision}"
                
        elif model_type == "s":
            # S-series: only show r-version if not r1 (preserve backward compatibility)
            number = model_parsed["number"]
            if revision == "1":
                return f"S{number}"
            else:
                return f"S{number}r{revision}"
                
        else:
            # Fallback for unknown types
            return model_parsed["full_model"].split("-")[1].upper()

    def _generate_blade_model_text(self, model):
        """Legacy method - generates blade model text by parsing model string.
        This method is kept for compatibility but now uses the JSON parsing approach.
        """
        model_parsed = self._parse_model_to_json(model)
        return self._generate_blade_model_text_from_parsed(model_parsed)
    
    def _init_blades_v2(self, params, config):
        """Initialize bladesv2 configuration from JSON-encoded parameter"""
        try:
            bladesv2_data = jsonurl.loads(params["bladesv2"])
        except Exception as e:
            raise InvalidDatapackException(f"Invalid bladesv2 JSON: {str(e)}")
        
        # Build final blade configuration data model
        # Structure: chassis_blades[chassis_idx][blade_idx][bay_idx] = fm_config
        chassis_blades = []
        
        # Process each chassis in the input data
        for chassis_idx, chassis in enumerate(bladesv2_data):
            # Ensure we have this chassis initialized
            while chassis_idx >= len(chassis_blades):
                chassis_blades.append([])
                for blade_slot in range(10):  # 10 slots per chassis
                    chassis_blades[-1].append([None, None, None, None])  # 4 bays per blade
            
            # Process each blade configuration group
            for blade_group in chassis.get('blades', []):
                bays = blade_group.get('bays', [])  # Physical bay numbers 1-4
                fm_size = blade_group.get('fm_size', '24TB')
                blade_count = blade_group.get('blade_count', 1)
                first_slot = blade_group.get('first_slot', 1)  # Physical slot number 1-10
                blade_model = blade_group.get('blade_model', config['model'])
                
                # Validate bays (should be 1-4)
                if not isinstance(bays, list) or not bays:
                    raise InvalidDatapackException(f"Invalid bays specification for chassis {chassis_idx}")
                
                # Create FM configuration 
                fm_config = {
                    'fm_size': fm_size,
                    'blade_count': blade_count,
                    'first_slot': first_slot,
                    'blade_model': blade_model
                }
                
                # blade_count determines how many consecutive blade slots to populate
                # starting from first_slot, can span multiple chassis
                start_slot = first_slot - 1  # Convert to 0-based (slot 1 = index 0)
                current_chassis = chassis_idx
                remaining_blades = blade_count
                current_slot = start_slot
                
                while remaining_blades > 0:
                    # Ensure we have enough chassis
                    while current_chassis >= len(chassis_blades):
                        chassis_blades.append([])
                        for blade_slot in range(10):  # 10 slots per chassis
                            chassis_blades[-1].append([None, None, None, None])  # 4 bays per blade
                    
                    # Calculate how many blades to put in current chassis
                    slots_available_in_chassis = 10 - current_slot
                    blades_for_this_chassis = min(remaining_blades, slots_available_in_chassis)
                    
                    # Populate slots in current chassis
                    for slot_offset in range(blades_for_this_chassis):
                        slot_idx = current_slot + slot_offset
                        for bay_num in bays:  # Physical bay numbers 1-4
                            if 1 <= bay_num <= 4:  # Validate bay number
                                bay_idx = bay_num - 1  # Convert to 0-based (bay 1 = index 0)
                                chassis_blades[current_chassis][slot_idx][bay_idx] = fm_config
                    
                    # Update for next chassis
                    remaining_blades -= blades_for_this_chassis
                    current_chassis += 1
                    current_slot = 0  # Start from slot 0 in next chassis
        
        # Store final blade configuration
        config['bladesv2_final'] = chassis_blades
        config['chassis'] = len(chassis_blades)
        
        # Calculate total blades for compatibility
        total_blades = 0
        for chassis in chassis_blades:
            for blade in chassis:
                if any(bay is not None for bay in blade):
                    total_blades += 1
        config['blades'] = total_blades
        
        return config

    async def add_blades(self, base_img, number_of_blades, blade_model_text, chassis_idx=0):
        logging.debug("Adding blades to the image")
        
        # Check if using bladesv2
        if 'bladesv2_final' in self.config:
            await self._add_blades_v2(base_img, chassis_idx, blade_model_text)
        else:
            await self._add_blades_legacy(base_img, number_of_blades, blade_model_text)

    async def _add_blades_legacy(self, base_img, number_of_blades, blade_model_text):
        """Legacy blade addition logic"""
        key = 'png/pure_fbs_blade.png'
        blade_img = await RackImage(key).get_image()
        fm_loc = global_config[key]['fm_loc']

        dfm_name = 'png/pure_fa_fm_nvme.png'
        fm_img = await RackImage(dfm_name).get_image()
        apply_fm_label(fm_img, str(self.config['dfm_size']), "qlc")

        # Paste in the DFMs
        for x in range(self.config['dfm_count']):
            blade_img.paste(fm_img, fm_loc[x])

        # Add model label
        label_loc = global_config[key]['model_text_loc']
        # Move text 4 pixels higher (reduce y coordinate by 4)
        label_loc = (label_loc[0], label_loc[1])
        ttf_path = global_config['ttf_path']
        font_size = 24

        font = ImageFont.truetype(ttf_path, size=font_size)
        _, _, w, h = font.getbbox(blade_model_text)
        txt_size = (w, h)
        
        txtimg = Image.new("RGBA", txt_size, (38, 38, 38))
        txtimg_draw = ImageDraw.Draw(txtimg)
        txtimg_draw.text((0,0), blade_model_text, font=font, fill= (255, 255, 255))

        top_crop = 3
        txtimg = txtimg.crop((0, top_crop, txt_size[0], txt_size[1]))
        txtimg = txtimg.rotate(270, expand=1)
        blade_img.paste(txtimg, label_loc)

        # Paste in the blades
        for x in range(number_of_blades):
            base_img.paste(blade_img, self.img_info['blade_loc'][x])

    async def _add_blades_v2(self, base_img, chassis_idx, blade_model_text):
        """Advanced blade addition logic for bladesv2 using final data model"""
        if chassis_idx >= len(self.config['bladesv2_final']):
            return
            
        chassis_blades = self.config['bladesv2_final'][chassis_idx]
        key = 'png/pure_fbs_blade.png'
        fm_loc = global_config[key]['fm_loc']
        
        # Process each blade (0-9) in this chassis
        for blade_idx, blade_bays in enumerate(chassis_blades):
            if blade_idx >= len(self.img_info['blade_loc']):
                continue
                
            # Check if this blade has any DFMs configured
            if not any(bay is not None for bay in blade_bays):
                continue
                
            # Create blade image for this specific blade
            blade_img = await RackImage(key).get_image()
            
            # Add FMs to each bay in this blade based on configuration
            for bay_idx, fm_config in enumerate(blade_bays):
                if fm_config is None or bay_idx >= len(fm_loc):
                    continue
                    
                # Create FM with specific size
                fm_name = 'png/pure_fa_fm_nvme.png'
                fm_img = await RackImage(fm_name).get_image()
                apply_fm_label(fm_img, str(fm_config['fm_size']), "qlc")
                
                # Paste this FM into the specific bay location on the blade
                blade_img.paste(fm_img, fm_loc[bay_idx])

            # Add model label to the blade
            label_loc = global_config[key]['model_text_loc']
            # Move text 4 pixels higher (reduce y coordinate by 4)
            label_loc = (label_loc[0], label_loc[1])
            ttf_path = global_config['ttf_path']
            font_size = 24

            font = ImageFont.truetype(ttf_path, size=font_size)
            _, _, w, h = font.getbbox(blade_model_text)
            txt_size = (w, h)
            
            txtimg = Image.new("RGBA", txt_size, (38, 38, 38))
            txtimg_draw = ImageDraw.Draw(txtimg)
            txtimg_draw.text((0,0), blade_model_text, font=font, fill= (255, 255, 255))

            top_crop = 3
            txtimg = txtimg.crop((0, top_crop, txt_size[0], txt_size[1]))
            txtimg = txtimg.rotate(270, expand=1)
            blade_img.paste(txtimg, label_loc)

            # Paste this completed blade into the chassis
            base_img.paste(blade_img, self.img_info['blade_loc'][blade_idx])


    async def build_chassis(self, number_of_blades, blade_model_text, chassis_idx=0):
        logging.debug("Building chassis with %s blades", number_of_blades)
        # For legacy mode, limit to 10 blades per chassis
        if 'bladesv2_final' not in self.config:
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
            await self.add_blades(base_img, number_of_blades, blade_model_text, chassis_idx)

        return {'img': base_img, 'ports': ports}

    async def get_rack_image_with_ports(self, key):
        ports = []
        add_ports_at_offset(key, (0, 0), ports)
        return {'img': await RackImage(key).get_image(), 'ports': ports}

    async def get_image(self):
        tasks = []

        logging.debug("Starting to get image for configuration: %s", str(self.config))

        c = self.config
        blade_model_text = self._generate_blade_model_text_from_parsed(self.config['model_parsed'])

        # Convert E-series blade text for chassis (E → EC, ER2 → ECR2, etc.)
        if blade_model_text.startswith("E"):
            if blade_model_text == "E":
                blade_model_text = "EC"
            else:
                # Handle ER2, ER3, etc. → ECR2, ECR3, etc.
                blade_model_text = blade_model_text.replace("E", "EC", 1)

        # Handle bladesv2 or legacy blade processing
        if 'bladesv2_final' in self.config:
            # Use bladesv2 configuration
            for i in range(self.config["chassis"]):
                # For bladesv2, we don't need to track blades_left since it's managed per chassis
                tasks.append(self.build_chassis(0, blade_model_text, i))
                
                # expansions shelves we change the blade model to EX (EC → EX, ECR2 → EXR2, etc.)
                if blade_model_text.startswith("EC"):
                    blade_model_text = blade_model_text.replace("EC", "EX", 1)
        else:
            # Legacy blade processing
            blades_left = c['blades']
            for i in range(self.config["chassis"]):
                tasks.append(self.build_chassis(blades_left, blade_model_text, i))
                blades_left -= 10

                # expansions shelves we change the blade model to EX (EC → EX, ECR2 → EXR2, etc.)
                if blade_model_text.startswith("EC"):
                    blade_model_text = blade_model_text.replace("EC", "EX", 1)

        if self.config['xfm']:
            xfm_face = self.config['xfm_face']
            for x in range(2):
                tasks.append(
                self.get_rack_image_with_ports(f"png/pure_fb_xfm_{self.config['xfm_model']}_{xfm_face}.png"))
            

        all_images = await asyncio.gather(*tasks)
        if self.config["direction"] == "up":
            all_images.reverse()

        return all_images
    
        # final_img, all_ports = combine_images_vertically(all_images)
        # self.ports = all_ports
        # return final_img
