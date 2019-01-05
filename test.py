import PureRackdiagram
import os
from pprint import pprint

def main():

    event = {
        'queryStringParameters': {
            'model':'FA-X70R2'
        },
        "test": True
    }

    pprint(PureRackdiagram.handler(event, None))

if __name__ == "__main__":
    main()