import PureRackdiagram
from pprint import pprint


def main():

    event = {
        "queryStringParameters": {
            "model": "fa-x20r2",
            "datapacks": "38/38-31/63-127/0",
            "direction":"down",
            "chassis": 2,
            "face":"front"
        },
        "test": True,
    }

    pprint(PureRackdiagram.handler(event, None))


if __name__ == "__main__":
    main()
