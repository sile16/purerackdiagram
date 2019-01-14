import PureRackdiagram
import os
from pprint import pprint

def main():

    event = {
        'queryStringParameters': {
            'model':'FA-X20R2',
            'datapacks':'127',
            'face':'back',
            'addoncards':'2eth40'
        },
        "test": True
    }

    pprint(PureRackdiagram.handler(event, None))

if __name__ == "__main__":
    main()