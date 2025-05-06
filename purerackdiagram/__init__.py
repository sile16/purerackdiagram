from .flashblade import FBDiagram
from .flashblades import FBSDiagram
from .flasharray import FADiagram
from io import BytesIO
import asyncio

default_array_model = 'fa-x20r2'

from purerackdiagram.utils import (
    InvalidConfigurationException,
)

def get_diagram(params):
    model = params.get('model', default_array_model).lower()
    params['model'] = model

    if model.startswith("fa"):
        diagram = FADiagram(params)
    elif model.startswith("fb-s"):
        diagram = FBSDiagram(params)
    elif model.startswith("fb-e"):
        diagram = FBSDiagram(params)
    elif model.startswith("fb"):
        diagram = FBDiagram(params)
    # elif model.startswith("fr"):
    #    diagram = OEDiagram(params)
    else:
        raise InvalidConfigurationException("Error unknown model, looking for fa or fb or fb-s or fb-e ")

    return diagram


def get_image_sync(params):
    diagram = get_diagram(params)
    img = asyncio.run(diagram.get_image())
    return img


def get_image_bytes_png_sync(params):
    buffered = BytesIO()
    img = get_image_sync(params)
    img.save(buffered, format="PNG")
    return buffered
