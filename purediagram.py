from flashblade import FBDiagram
from flasharray import FADiagram

from utils import RackImage, combine_images_vertically


default_array_model = 'fa-x20r2'

def get_diagram(params):
    model = params.get('model',default_array_model).lower()
    params['model'] = model

    if model.startswith("fa"):
        diagram = FADiagram(params)
    elif model.startswith("fb"):
        diagram = FBDiagram(params)
    #elif model.startswith("oe"):
    #    diagram = OEDiagram(params)
    else:
        raise Exception("Error unknown model, looking for fa or fb or oe")

    return diagram