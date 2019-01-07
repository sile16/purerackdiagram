import PureRackdiagram
import os
from pprint import pprint

def main():

    event = {
        'queryStringParameters': {
            'model':'FA-X70R2',
            'shelves':'sas-24,sas-12,nvme-12',
            'face':'back'
        },
        "test": True
    }

    pprint(PureRackdiagram.handler(event, None))

if __name__ == "__main__":
    main()