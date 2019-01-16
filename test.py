import PureRackdiagram
from pprint import pprint


def main():

    event = {
        "queryStringParameters": {
            "model": "FA-X70R1",
            "datapacks": "22/45-45/45-63/31",
            "face":"front"
        },
        "test": True,
    }

    pprint(PureRackdiagram.handler(event, None))


if __name__ == "__main__":
    main()
