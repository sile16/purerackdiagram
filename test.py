import PureRackdiagram
from pprint import pprint
import logging

logger = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

#38/38-31/63-127/0
#0/38-0/45-0/45-0/63

def main():

    event = {
        "queryStringParameters": {
            "model": "fa-m20r2",
            "datapacks": "19.2/0-31/63-0/0",
            "chassis": 2,
            "addoncards":"4fc,4fc,2eth",
            "face":"front",
            "fm_label":True,
            "dp_label":True
        },
        "test": True,
    }

    pprint(PureRackdiagram.handler(event, None))


if __name__ == "__main__":
    main()
