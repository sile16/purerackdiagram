import PureRackdiagram
from pprint import pprint


def main():

    event = {
        "queryStringParameters": {
            "model": "fa-m20r2",
            "datapacks": "38/38-31/63-127/0",
            "direction":"down",
            "chassis": 2,
            "addoncards":"4fc,4fc,2eth",
            "face":"back"
        },
        "test": True,
    }

    pprint(PureRackdiagram.handler(event, None))


if __name__ == "__main__":
    main()
