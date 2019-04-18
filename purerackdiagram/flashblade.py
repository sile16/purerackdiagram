import asyncio
from .utils import RackImage, combine_images_vertically


class FBDiagram():
    def __init__(self, params):
        config = {}
        config["chassis"] = int(params.get("chassis", 1))
        config["face"] = params.get("face", "front").lower()
        config['direction'] = params.get("direction","up").lower()

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


    async def get_image(self):
        tasks = []

        img_key = "png/pure_fb_{}.png".format(self.config["face"])

        for _ in range(self.config["chassis"]):
            tasks.append(RackImage(img_key).get_image())
        
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