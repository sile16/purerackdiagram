import PureRackdiagram
from pprint import pprint


def main():

    event = {
        "queryStringParameters": {
            "model": "fb",
            "chassis": 2,
            "face":"back"
        },
        "test": True,
    }

    pprint(PureRackdiagram.handler(event, None))


if __name__ == "__main__":
    main()
