from pprint import pprint
import logging
import base64
from multiprocessing import Pool
import hashlib
import json
import traceback
import os
import requests

import lambdaentry
from purerackdiagram.utils import global_config

import jsonurl_py as jsonurl



logger = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
logger.addHandler(ch)
logger.setLevel(logging.WARN)

save_dir = 'test_results/'



more_tests = [
    {
        "queryStringParameters": {
            "model": "fa-xl130r5",
            "protocol": "eth",
            "face": "front",
            "datapacksv2": jsonurl.dumps([
                { #CH0
                    'datapacks': [
                        {
                            "dp_label": "Fun Datapack",
                            'fm_size': "6 PB",
                            'fm_count': 33
                        },
                        {
                            'dp_label': "small",
                            'fm_size': "1 PB",
                            'fm_count': 2,
                            'first_slot': 37
                        }
                    ]
                },
                { #sh0
                    'datapacks': [
                        {
                            'fm_size': "6 PB",
                            'fm_count': 13
                        },
                        {
                            'dp_label': "small",
                            'fm_size': "1 PB",
                            'fm_count': 2,
                        }
                    ]
                }
            ]),
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth200roce,2fc"
        }
    },
    {
        "queryStringParameters": {
            "model": "fb-s200",
            "face": "front",
            "dfm_label": True,
            "bladesv2": jsonurl.dumps([
                {  # Chassis 0
                    "gen": "1",
                    "blades": [
                        {
                            "bays": [1, 2],
                            "dfm_size": "24TB",
                            "blade_count": 8,
                            "blade_model": "fb-s200"
                        },
                        {
                            "bays": [3, 4],
                            "dfm_size": "48TB",
                            "blade_count": 6,
                            "first_slot": 3,
                            "blade_model": "fb-s200"
                        }
                    ]
                },
                {  # Chassis 1  
                    "gen": "2",
                    "blades": [
                        {
                            "bays": [1, 2, 3, 4],
                            "dfm_size": "6 TB",
                            "blade_count": 5,
                            "first_slot": 1,
                            "blade_model": "fb-s500"
                        }
                    ]
                }
            ])
        }
    },
    {
        "queryStringParameters": {
            "model": "fb-s200",
            "face": "front",
            "dfm_label": True,
            "bladesv2": jsonurl.dumps([
                {  # Chassis 0
                    "gen": "1",
                    "blades": [
                        {
                            "bays": [1, 2],
                            "dfm_size": "24TB",
                            "blade_count": 8,
                            "blade_model": "fb-s200"
                        },
                        {
                            "bays": [3, 4],
                            "dfm_size": "48TB",
                            "blade_count": 6,
                            "first_slot": 3,
                            "blade_model": "fb-s200"
                        }
                    ]
                },
                {  # Chassis 1  
                    "gen": "2",
                    "blades": [
                        {
                            "bays": [1, 2, 3, 4],
                            "dfm_size": "75TB",
                            "blade_count": 5,
                            "first_slot": 1,
                            "blade_model": "fb-s500"
                        }
                    ]
                }
            ])
        }
    },
    {
        "queryStringParameters": {
            "model": "fb-s200",
            "face": "front",
            "dfm_label": True,
            "bladesv2": jsonurl.dumps([
                {  # Chassis 0
                    "gen": "1",
                    "blades": [
                        {
                            "bays": [1, 2],
                            "dfm_size": "24TB",
                            "blade_count": 10,
                            "first_slot": 1,
                            "blade_model": "fb-s200"
                        },
                        {
                            "bays": [3, 4],
                            "dfm_size": "48TB",
                            "blade_count": 15,
                            "first_slot": 8,
                            "blade_model": "fb-s200"
                        }
                    ]
                },
                {  # Chassis 1  
                    "gen": "2",
                    "blades": [
                        {
                            "bays": [1, 2, 3, 4],
                            "dfm_size": "75TB",
                            "blade_count": 5,
                            "first_slot": 1,
                            "blade_model": "fb-s500"
                        }
                    ]
                }
            ])
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-xl130r5",
            "protocol": "eth",
            "face": "front",
            "datapacksv2": jsonurl.dumps([
                { #CH0
                    'datapacks': [
                        {
                
                            'fm_size': "6 PB",
                            'fm_count': 33
                        },
                        {
                            'dp_label': "small",
                            'fm_size': "1 PB",
                            'fm_count': 2,
                            'first_slot': 37
                        }
                    ]
                },
                { #sh0
                    'datapacks': [
                        {
                            "dp_label": "Shelf DP",
                            'fm_size': "6 PB",
                            'fm_count': 13
                        },
                        {
                            'dp_label': "small",
                            'fm_size': "1 PB",
                            'fm_count': 2,
                        }
                    ]
                }
            ]),
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth200roce,2fc"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x70r2",
            "protocol": "eth",
            "face": "front",
            "datapacks": "366", 
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth200roce,2fc"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-xl130r5",
            "protocol": "eth",
            "face": "front",
            "datapacksv2": jsonurl.dumps([
                { #CH0
                    'datapacks': [
                        {
                            "dp_label": "Fun Datapack",
                            'fm_size': "6 PB",
                            'fm_count': 33
                        },
                        {
                            'dp_label': "small",
                            'fm_size': "1 PB",
                            'fm_count': 2,
                            'first_slot': 37
                        }
                    ]
                },
                { #sh0
                    'datapacks': [
                        {
                            "dp_label": "Shelf DP",
                            'fm_size': "6 PB",
                            'fm_count': 13
                        },
                        {
                            'dp_label': "small",
                            'fm_size': "1 PB",
                            'fm_count': 2,
                        }
                    ]
                }
            ]),
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth200roce,2fc"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-xl130r5",
            "protocol": "eth",
            "face": "front",
            "datapacksv2": jsonurl.dumps([
                {
                    'datapacks': [
                        {
                            "dp_label": "Fun Datapack",
                            'fm_size': "6 PB",
                            'fm_count': 33
                        },
                        {
                            'dp_label': "small",
                            'fm_size': "1 PB",
                            'fm_count': 2,
                            'first_slot': 37
                        }
                    ]
                }
            ]),
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth200roce,2fc"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-xl130r5",
            "protocol": "eth",
            "face": "front",
            "datapacks": "366", 
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth200roce,2fc"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-xl130r5",
            "protocol": "eth",
            "face": "front",
            "bezel": True,
            "datapacks": "366",
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth200roce,2fc"
        }
    },
     {
        "queryStringParameters": {
            "model": "fa-xl130r5",
            "protocol": "eth",
            "face": "back",
            "bezel": True,
            "datapacks": "366", 
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth200roce,2fc"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-rc20",
            "protocol": "eth",
            "face": "front",
            "bezel": True,
            "datapacks": "148", # invalid datapack that should trigger friendly error
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth100,2fc"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-rc20",
            "protocol": "eth",
            "face": "back",
            "datapacks": "148", # invalid datapack that should trigger friendly error
            "dp_label": True,
            "fm_label": True,
            "addoncards": "2eth100,2eth100,2fc"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-rc20",
            "protocol": "eth",
            "face": "front",
            "datapacks": "148", # invalid datapack that should trigger friendly error
            "dp_label": True,
            "fm_label": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-rc20r3",
            "protocol": "fc",
            "face": "front",
            "datapacks": "148", # invalid datapack that should trigger friendly error
            "dp_label": True,
            "fm_label": True,
        }
    },
    # Error test case 1: Invalid datapack
    {
        "queryStringParameters": {
            "model": "fa-x70r4b",
            "protocol": "fc",
            "face": "front",
            "datapacks": "999", # invalid datapack that should trigger friendly error
            "dp_label": True,
            "fm_label": True,
            "json": True  # Return JSON to see error message
        }
    },
    # Error test case 2: Invalid model
    {
        "queryStringParameters": {
            "model": "fa-invalid",
            "protocol": "fc",
            "face": "front",
            "datapacks": "45",
            "dp_label": True,
            "fm_label": True,
            "json": True  # Return JSON to see error message
        }
    },
    # Error test case 3: Invalid PCI card
    {
        "queryStringParameters": {
            "model": "fa-x70r4b",
            "protocol": "fc",
            "face": "back",
            "datapacks": "45",
            "addoncards": "invalid-card",  # Invalid PCI card
            "dp_label": True,
            "fm_label": True,
            "json": True  # Return JSON to see error message
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x70r4b",
            "protocol": "fc",
            "face": "front",
            "datapacks": "11/13/0.06",
            "dp_label": True,
            "fm_label": True,
        }
    },
    {

        "queryStringParameters": {
            "model": "fa-x70r4b",
            "protocol": "fc",
            "face": "front",
            "datapacks": "15/11/0.04",
            "dp_label": True,
            "fm_label": True,
        }
    },
    {

        "queryStringParameters": {
            "model": "fa-x70r4b",
            "protocol": "fc",
            "face": "front",
            "datapacks": "18/11/0.02",
            "dp_label": True,
            "fm_label": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-xl170",
            "protocol": "fc",
            "face": "front",
            "datapacks": "18/13-63/63/63",
            "dp_label": True,
            "fm_label": True,
            
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-er1b",
            "protocol": "eth",
            "face": "front",
            "datapacks": "1050/1050",
            "dp_label": True,
            "fm_label": True,
            
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-xl170",
            "protocol": "fc",
            "face": "front",
            "datapacks": "18/13/18",
            "dp_label": True,
            "fm_label": True,
            
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-er1b",
            "protocol": "fc",
            "face": "front",
            "datapacks": "1050/1050",
            "dp_label": True,
            "fm_label": True,
            
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-er1b",
            "protocol": "fc",
            "face": "front",
            "datapacks": "1050/1050",
            "chassis_gen": "2",
            "dp_label": True,
            "fm_label": True,
            
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-er1b",
            "protocol": "fc",
            "face": "front",
            "datapacks": "0",
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-er1b",
            "protocol": "fc",
            "face": "front",
            "datapacks": "0",
            "chassis_gen": "2"
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-e",
            "protocol": "fc",
            "face": "front",
            "datapacks": "0",
            "chassis_gen": "2"
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-c20r4b",
            "protocol": "fc",
            "face": "front",
            "datapacks": "240",
            "chassis_gen": "2"
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x90r4",
            "datapacks": "183/40",
            "face": "front",
            "dc_power": "",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
            
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-c50r4",
            "datapacks": "186",
            "face": "front",
            "dc_power": "",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
            "chassis_gen": "2"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-c50r4",
            "datapacks": "186",
            "face": "front",
            "dc_power": "",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x50r4b",
            "datapacks": "183-183",
            "face": "back",
            "dc_power": "",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
            "individual": "True",
            "vssx": "True"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x50r4b",
            "datapacks": "183-183",
            "face": "back",
            "dc_power": "",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
            "individual": "True"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x50r4b",
            "datapacks": "183-183",
            "face": "back",
            "dc_power": "",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-e",
            "datapacks": "1050-1050",
            "face": "back",
            "dc_power": "True",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-x50r4b",
            "datapacks": "183-183",
            "face": "back",
            "dc_power": "2000",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x20r4",
            "datapacks": "183-183",
            "face": "back",
            "dc_power": "1300",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x20r4",
            "datapacks": "183-183",
            "face": "back",
            "dc_power": "1300",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x20r4",
            "datapacks": "183-183",
            "face": "back",
            "dc_power": "2000",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x20r4",
            "datapacks": "183-183",
            "face": "back",
            "dc_power": True,
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x50r4",
            "datapacks": "183-183",
            "face": "back",
            "dc_power": True,
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-c20",
            "datapacks": "186/260-1050",
            "face": "back",
            "dc_power": True,
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-c20",
            "datapacks": "186/260",
            "face": "front",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fb-s200",
            "no_of_blades": 18,
            "face": "front",
            "no_of_drives_per_blade": 4,
            "drive_size": 75,
            "ports": "TRUE",
            'bezel': True
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-er1b",
            "datapacks": "186",
            "face": "front",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
            "bezel": True
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-er1b",
            "datapacks": "186",
            "face": "front",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x90r4b",
            "datapacks": "3/0.02/45",
            "face": "back",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
        }
    },
    
      {
        "queryStringParameters": {
            "model": "fb-s200",
            "no_of_blades": 15,
            "face": "front",
            "no_of_drives_per_blade": 4,
            "drive_size": 75,
            "ports": "TRUE",
            "vssx": True
        }
    },
    {
        "queryStringParameters": {
            "model": "fb-e",
            "chassis": 2,
            "addoncards": "2eth100",
            "face": "back",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True
        }
    },
      {
        "queryStringParameters": {
            "model": "fa-x90r4",
            "datapacks": "3/0.02/45",
            "face": "back",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
            "jsononly": True,
            'json': True,
            'addoncards': '2eth100',
            'pci3': '2eth40',
            'pci0': '2eth100'
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x90r4",
            "datapacks": "3/0.02/45",
            "face": "back",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
            "jsononly": True,
            'json': True,
            'addoncards': '2eth100',
            'pci3': '2eth40'
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-x90r4",
            "datapacks": "3/0.02/45",
            "face": "back",
            "dp_label": True,
            "fm_label": True,
            "ports": True
        }
    },
        {
        "queryStringParameters": {
            "model": "fa-c40r1",
            "datapacks": "366",
            "addoncards": "2eth25roce,2eth,2eth",
            "face": "back",
            "dp_label": True,
            "fm_label": True,
            "ports": True,
            "mezz": "smezz"
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-xl170",
            "datapacks": "183/72/91",
            "face": "front",
            "dp_label": True,
            "fm_label": True,
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-xl130",
            "datapacks": "91/91/91/36",
            "chassis": 2,
            "addoncards": "2eth100",
            "face": "back",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True,
            'json': 'True'
        }
    },

    {  ## keep this as an error message on purpose.
        "queryStringParameters": {
            "model": "fa-x20r4",
            "datapacks": "31",
            "direction": "down",
            "chassis": 2,
            "face": "back",
            "dp_label": "True",
            "fm_label": "True",
            "protocol": "fc",
            "addoncards": "sas,4eth25,4fc",
            "ports": "True"
        }
    },
    {  ## keep this as an error message on purpose.
        "queryStringParameters": {
            "model": "fa-x90r4",
            "datapacks": "31",
            "direction": "down",
            "chassis": 2,
            "face": "back",
            "dp_label": "True",
            "fm_label": "True",
            "addoncards": "2eth100,4eth25,2eth25roce,2eth",
            "ports": "True"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-er1",
            "datapacks": "750",
            "chassis": 2,
            "addoncards": "2eth100",
            "face": "back",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-e",
            "datapacks": "750",
            "chassis": 2,
            "addoncards": "2eth100",
            "face": "front",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-e",
            "datapacks": "750",
            "chassis": 2,
            "addoncards": "2eth100",
            "bezel": True,
            "face": "front",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True
        }
    },
    
    {
        "queryStringParameters": {
            "model": "fa-xl130",
            "datapacks": "91",
            "chassis": 2,
            "addoncards": "2eth100",
            "face": "back",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True
        }
    },
    {  ## keep this as an error message on purpose.
        "queryStringParameters": {
            "model": "fa-x90r2",
            "datapacks": "38.0-31",
            "direction": "down",
            "chassis": 2,
            "face": "front",
            "dp_label": "True",
            "fm_label": "True",
            "json": "True"
        }
    },
    
    {
        "queryStringParameters": {
            "model": "fb-e",
            "no_of_blades": 100,
            "face": "back",
            "no_of_drives_per_blade": 4,
            "drive_size": 48,
            "ports": "TRUE"
        }
    },
     {  ## keep this as an error message on purpose.
        "queryStringParameters": {
            "model": "fa-x90r2",
            "datapacks": "38.0/38.0-31/63-127/0",
            "direction": "down",
            "chassis": 2,
            "face": "front",
            "dp_label": "True",
            "fm_label": "True",
            "json": "True"
        }
    },
     {  ## keep this as an error message on purpose.
        "queryStringParameters": {
            "model": "fa-x90r2",
            "datapacks": "38.0/38.0-31/63-127/0",
            "direction": "down",
            "chassis": 2,
            "face": "front",
            "dp_label": "True",
            "fm_label": "True",
            "json": "True"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-xl130",
            "datapacks": "91/91/91",
            "chassis": 2,
            "addoncards": "2eth100",
            "face": "back",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True,
            "json": "True"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x50r4",
            "datapacks": "63/0",
            "protocol": "FC",
            "addoncards": "",
            "face": "back",
            "fm_label": "True",
            "dp_label": "True",
            "local_delay": 0,
            "ports": "True"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x50r4",
            "datapacks": "63/0",
            "protocol": "FC",
            "addoncards": "",
            "face": "back",
            "fm_label": "True",
            "dp_label": "True",
            "local_delay": 0,
            "ports": "True",
            "vssx": "True"
        }
    },
        {
        "queryStringParameters": {
            "model": "fa-x50r4",
            "datapacks": "63/0",
            "protocol": "FC",
            "addoncards": "",
            "face": "back",
            "fm_label": "True",
            "dp_label": "True",
            "local_delay": 0,
            "ports": "True",
            "json": "True"
        }
    },
        {
        "queryStringParameters": {
            "model": "fb-e",
            "no_of_blades": 30,
            "face": "front",
            "no_of_drives_per_blade": 3,
            "drive_size": 24,
            "ports": "TRUE"
        }
    },
    {
        "queryStringParameters": {
            "model": "fb-e",
            "no_of_blades": 30,
            "face": "front",
            "no_of_drives_per_blade": 3,
            "drive_size": 24,
            "ports": "TRUE"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x50r4",
            "datapacks": "63/0",
            "protocol": "FC",
            "addoncards": "4fc,2eth,2eth40,2fc,2fc",
            "face": "back",
            "fm_label": "True",
            "dp_label": "True",
            "local_delay": 0,
            "ports": "True"
        }
    },
    {
        "queryStringParameters": {
            "model": "fb-s200",
            "no_of_blades": 10,
            "face": "front",
            "no_of_drives_per_blade": 3,
            "drive_size": 24,
            "ports": "TRUE"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-c40r3",
            "datapacks": "366",
            "protocol": "eth",
            "chassis": 2,
            "addoncards": "",
            "face": "back",
            "fm_label": "True",
            "dp_label": "True",
            "local_delay": 0,
            "ports": "True"
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-xl130",
            "datapacks": "91/91/91",
            "chassis": 2,
            "addoncards": "",
            "face": "front",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-xl130",
            "datapacks": "63/0",
            "chassis": 2,
            "addoncards": "",
            "face": "back",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-xl130",
            "datapacks": "63/0",
            "chassis": 2,
            "addoncards": "sas,2fc,4fc,2eth,2ethbaset,2eth40,2fc,2fc,2fc,2fc",
            "face": "back",
            "fm_label": True,
            "dp_label": True,
            "mezz": "smezz",
            "local_delay": 0,
            "ports": True
        }
    },

    {
        "queryStringParameters": {
            "model": "fb",
            "chassis": 2,
            "face": "back",
            'direction': 'up',
            'efm': "efm310",
            'local_delay': 0,
            'blades': '17:0-6,52:23-29',
            'ports': True
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-x70r1",
            "protocol": "fc",
            "direction": "up",
            "datapacks": "91/91-45/45",
            "addoncards": "",
            "face": "back",
            "fm_label": "FALSE",
            "dp_label": "FALSE",
            "bezel": "FALSE",
            "local_delay": 3
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-c60",
            "protocol": "eth",
            "direction": "up",
            "datapacks": "91/91-45/45",
            "csize": '879',
            "addoncards": "",
            "face": "back",
            "fm_label": "True",
            "dp_label": "Ture",
            "bezel": "FALSE"
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-x70r1",
            "protocol": "fc",
            "direction": "up",
            "datapacks": "292-45/45",
            "addoncards": "",
            "face": "front",
            "fm_label": "True",
            "dp_label": "FALSE"
        }
    },

    {
        "queryStringParameters": {
            "model": "fb",
            "chassis": 10,
            "face": "back",
            'direction': 'up',
            'efm': "efm310",
            'blades': '17:0-6,52:23-29'
        }
    },

    {
        "queryStringParameters": {
            "model": "fa-x70r1",
            "protocol": "fc",
            "direction": "up",
            "datapacks": "0/127",
            "addoncards": "",
            "face": "front",
            "fm_label": "True",
            "dp_label": "FALSE"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x70r1",
            "protocol": "fc",
            "direction": "up",
            "datapacks": "127/0",
            "addoncards": "",
            "face": "front",
            "fm_label": "True",
            "dp_label": "FALSE"
        }
    },
    {
        "queryStringParameters": {
            "model": "fa-x70r1",
            "protocol": "fc",
            "direction": "up",
            "datapacks": "3/127",
            "addoncards": "",
            "face": "front",
            "fm_label": "True",
            "dp_label": "True"
        }
    }
]


def test_lambda(params, outputfile):
    results = lambdaentry.handler(params, None)
    
    # Check for error status codes (4xx)
    if 400 <= results['statusCode'] < 500:
        if results['headers'].get("Content-Type") == 'application/json':
            # Parse the JSON response to inspect error message
            try:
                if type(results['body']) is str:
                    error_data = json.loads(results['body'])
                else:
                    error_data = results['body']

                error_msg = error_data.get('error', 'Unknown error')
                error_type = error_data.get('error_type', 'Unknown')
                logger.info(f"Error response ({results['statusCode']}): {error_type} - {error_msg}")
                
            except json.JSONDecodeError:
                logger.error("Failed to parse error JSON response")
        elif results['headers'].get("Content-Type") == 'image/png':
            # If it's an image error message, we can't inspect it directly
            logger.info(f"Error response ({results['statusCode']}) as image")

    # If statusCode is 302, follow the redirect
    if results['statusCode'] == 302:
        location = results['headers']['Location']
        response = requests.get(location)
        content_type = response.headers.get('Content-Type')
        logger.info(f"Redirected to {location} with content type {content_type}")
        
        # Update the body and headers of the results to hide the redirect
        results['body'] = base64.b64encode(response.content).decode('utf-8')
        results['headers']['Content-Type'] = content_type
        results['statusCode'] = 200  # Update status code to OK
        
        # Save the response content to the appropriate file
        #if content_type == 'image/png':
        #    ext = '.png'
        #elif content_type == 'application/vnd.ms-visio.stencil':
        #    ext = '.vssx'
        #elif content_type == 'application/json':
        #    ext = '.json'
        #else:
        #    ext = ''
        
        #with open(outputfile + ext, 'wb') as outfile:
        #    outfile.write(response.content)

    
    if results['headers'].get("Content-Type") == 'image/png':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            with open(outputfile + '.png', 'wb') as outfile:
                outfile.write(img_str)

    elif results['headers'].get("Content-Type") == 'application/vnd.ms-visio.stencil':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            with open(outputfile + '.vssx', 'wb') as outfile:
                outfile.write(img_str)

    elif results['headers'].get("Content-Type") == 'application/zip':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            with open(outputfile + '.zip', 'wb') as outfile:
                outfile.write(img_str)

    elif results['headers'].get("Content-Type") == 'application/json':
        if 'body' in results:
            #img_str = json.dumps(results['body'], indent=4, ensure_ascii=False)
            # replace this '"execution_duration": 0.8748149871826172', with '"execution_duration": 1',
            # match for any value

            obj = json.loads(results['body'])
            obj['execution_duration'] = 1
            del obj['image']
            #results['body'] = json.dumps(obj, indent=4, ensure_ascii=False)
            results['body'] = obj

            with open(outputfile + '.json', 'w',  encoding='utf-8') as outfile:
                json.dump(obj, outfile, indent=4, ensure_ascii=False)
            #del results['body']

    return results


def create_test_image_original(item, count, total):
    """Original function, kept for reference"""
    
    folder = "test_results"
    file_name = f"{item['model']}"
    for n in ['face', 'bezel', 'mezz', 'fm_label', 'dp_label', 'addoncards', 'ports', 'csize', 'datapacks',  
    'no_of_chassis', 'no_of_blades', 'efm', 'direction', 'drive_size', 'no_of_drives_per_blade', 'vssx', 'json', 'chassis_gen' ]:
        if n in item:
            if n == 'datapacks':
                file_name += f"_{str(item[n]).replace('/', '-')}"
            else:
                file_name += f"_{n}-{item[n]}"
    

# Now define the new create_test_image function
def create_test_image(item, count, total):
    folder = "test_results"
    file_name = f"{item['model']}"
    for n in ['face', 'bezel', 'mezz', 'fm_label', 'dp_label', 'addoncards', 'ports', 'csize', 'datapacks',  
    'no_of_chassis', 'no_of_blades', 'efm', 'direction', 'drive_size', 'no_of_drives_per_blade', 'vssx', 'json', 'chassis_gen' ]:
        if n in item:
            if n == 'datapacks':
                file_name += f"_{str(item[n]).replace('/', '-')}"
            else:
                file_name += f"_{n}-{item[n]}"

    try:
        results = test_lambda({"queryStringParameters":item}, os.path.join(folder, file_name))

        h = hashlib.sha256()
        content_type = results['headers'].get("Content-Type")
        status_code = results['statusCode']

        # Check for error responses (4xx, 5xx)
        if 400 <= status_code < 600:
            print(f"{count} of {total}   {file_name} - ERROR {status_code}")
            
            # For JSON errors, we can examine the detailed message
            if content_type == 'application/json' and 'body' in results:
                try:
                    if type(results['body']) is str:
                        # If body is a string, decode it
                        error_data = json.loads(results['body'])
                    else:
                        error_data = results['body']
                    error_msg = error_data.get('error', 'Unknown error')
                    error_type = error_data.get('error_type', 'Unknown')
                    
                    # Return error details for validation and testing
                    return({file_name: {
                        "status": status_code,
                        "error_type": error_type,
                        "error_msg": error_msg
                    }})
                except json.JSONDecodeError:
                    print(f"  Failed to parse error JSON")
                    return({file_name: {
                        "status": status_code,
                        "error": "Failed to parse error JSON"
                    }})
        
        # For successful responses or errors that aren't in JSON format
        print(f"{count} of {total}   {file_name} - Status: {status_code}")
        if content_type == 'application/json':
            return({file_name: results['body']})
        else:
            # For other content types, use the body directly
            h.update(results['body'].encode('utf-8'))
            return({file_name: h.hexdigest()})

    except Exception as ex_unknown:
        print(f"Caught exception in image: {file_name}")
        traceback.print_exc()
        return({file_name: {
            "status": 500,
            "error": str(ex_unknown),
            "traceback": traceback.format_exc()
        }})

#    if "fa-er1-f" in item['model'] :
#        pass

    # Original implementation replaced by the new create_test_image function above

    


def get_all_tests():
    models = global_config['pci_config_lookup']
    dps = ['45/45-31/63-45-24.0', '3/127-24.0-45']

    valid_chassis_dps = list(global_config['chassis_dp_size_lookup'].keys())
    #valid_chassis_dps += list(global_config['qlc_chassis_dp_size_lookup'].keys())
    valid_shelf_dps = list(global_config['shelf_dp_size_lookup'].keys())
    #valid_shelf_dps += list(global_config['qlc_shelf_dp_size_lookup'].keys())

    # get the keys of diction csize_lookup
    csizes = list(global_config['csize_lookup'].keys())
    #csizes = ['964', '984']
    #global_config.csize_lookup

    count = 0

    for test in more_tests:
        #if not test['queryStringParameters'].get('json'):
        #    continue
        yield test['queryStringParameters']
        count += 1

    for cg in ['1', '2']:
        for model in ['x50r4', 'c50r4', 'c20', 'c50r4b', 'x50r4b', 'er1', 'er1b']:
                params = {"model": f"fa-{model}",
                            "datapacks": "0",
                            "face": "front",
                            'chassi_gen': cg,
                            "fm_label": True,
                            "dp_label": True,
                            }
                yield params
    
    
    # Test all Models with a front data pack and shelf.
    for model in models:
        #continue
        model = model.split('-')[0] + '-' + model.split('-')[1]
        if 'c' in model or 'e' in model:
            count += 1
            params = {"model": model,
                        "fm_label": True,
                        "dp_label": True,
                        "csize": '984'}
            yield params
        else:
            for dp in dps:
                count += 1
                params = {"model": model,
                            "fm_label": True,
                            "dp_label": True,
                            "datapacks": dp}
                yield params

        # The bezel.
        params = {"model": model,
                    "fm_label": True,
                    "dp_label": True,
                    "bezel": True,
                    "datapacks": '366'}
        yield params

    for csize in csizes:
        count += 1
        params = {"model": 'fa-c60',
                    "fm_label": True,
                    "dp_label": True,
                    "csize": csize}
        yield params
    
    #Test all Datapacks on the front.
    for dp in valid_chassis_dps:
        count += 1
        params = {"model": "fa-x70r1",
                    "fm_label": True,
                    "dp_label": True,
                    "datapacks": dp}
        yield params

    for dp in valid_shelf_dps:
        count += 1
        params = {"model": "fa-x70r4",
                    "fm_label": True,
                    "dp_label": True,
                    "datapacks": f"63-{dp}"}
        yield params
            

    # back:
    addon_cards = global_config['pci_valid_cards']

    #every model and shelf back view.
    for model in models:
        #continue
        model = model.split('-')[0] + '-' + model.split('-')[1]
        
        if 'c' in model or 'e' in model:
            params = {"model": model,
                        "addoncards": '4fc',
                        "face": "back",
                        "csize": '984',
                        "ports": True}
            count += 1
            yield params

        else:
            params = {"model": model,
                        "datapacks": "63-24.0-45",
                        "addoncards": '4fc',
                        "face": "back",
                        "ports": True}
            count += 1
            yield params

        # every model with each card.
        for card in addon_cards:
            params = {"model": model,
                        "datapacks": "366",
                        "addoncards": f"{card},{card},{card}",
                        "face": "back",
                        "ports": True}
            count += 1
            yield params



    

    for blades in [10, 15, 30]:
        for dfms in [2, 4]:
            for size in [24.0, 48.2]:
                for face in ['front', 'back']:
                    params = {"model": "fb-s200",
                              "no_of_blades": blades,
                              "face": face,
                              "no_of_drives_per_blade": dfms,
                              "drive_size": size,
                              "ports": True}
                    count += 1
                    yield params
                    params = {"model": "fb-e",
                              "no_of_blades": blades,
                              "face": face,
                              "no_of_drives_per_blade": dfms,
                              "drive_size": size,
                              "ports": "TRUE"}
                    count += 1
                    yield params

    



def test_all(args):

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Create amultiprocessing pool
    pool = Pool(processes=args.t)
    futures = []
    total_count = 0

    all_items = list(get_all_tests())
    count = 0
    for item in all_items:
        futures.append(pool.apply_async(create_test_image, args=(item, count, len(all_items), )))
        count += 1

    pool.close()
    pool.join()

    results = {}

    for f in futures:
        result = f.get()
        results.update(result)

    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    with open("test_validation.json") as f:
        validation = json.load(f)

    errors = 0
    warnings = 0
    for key in results:
        if key not in validation:
            warnings += 1
            print("WARNING missing key:{}".format(key))
        elif 'json' in key:
            # use jsondiff to compare the two
            # load the two strings into json objects, results
            # compare json

            import jsondiff
            diff = True
            try:
                res_json = results[key]
                val_json = validation[key]
                diff = jsondiff.diff(val_json, res_json)
            except Exception as ex:
                pass

            if diff:
                errors += 1
                print("Error JSON Changed!!:{}".format(key))
                print(diff)
        elif 'vssx' in key:
            pass # always different because unique key
        elif results[key] != validation[key]:
            errors += 1
            print(f"Error Image Changed!!: {key} (file://{os.path.abspath(os.path.join(save_dir, key))}.png)")
    print("Test Complete {} Errors Found {} Warning".format(errors, warnings))


def main(args):
    if args.testtype == 'all':
        test_all(args)
    else:
        test_lambda(more_tests[0], 'tmp')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('testtype', choices=['all', 'lambda'], default='all',
                        nargs='?',
                        help="Test all options, or test through lamdba entry")
    parser.add_argument('-t', type=int, help="number of threads", default=8)
    main(parser.parse_args())
