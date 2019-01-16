import PureRackdiagram
from pprint import pprint


def main():

    event = {
        "queryStringParameters": {
            "model": "FA-X70R2",
            "datapacks": "22/38-45/90-22/45-63/31",
            "face": "back",
            "addoncards": "2eth40",
            "protocol":"eth",
            "fm_label":"",
            "dp_label":""
        },
        "test": True,
    }

    pprint(PureRackdiagram.handler(event, None))


if __name__ == "__main__":
    main()
