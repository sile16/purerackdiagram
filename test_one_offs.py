
import jsonurl_py as jsonurl
import urllib.parse

more_tests = [
    {
        "queryStringParameters": {
            "chassis_gen": "1",
            "datapacks": "1350",
            "dp_label": "TRUE",
            "face": "back",
            "ports": "True",
            "json_only": "True",
            "model": "fa-C70R4b",
            "protocol": "ETH"
        }
    },
   {
        "queryStringParameters": {
            "chassis_gen": "1",
            "datapacks": "1350",
            "dp_label": "TRUE",
            "face": "back",
            "ports": "True",
            "json": "True",
            "model": "fa-C70R4b",
            "protocol": "ETH"
        }
    },

    {
        "queryStringParameters": {
            "chassis_gen": "1",
            "datapacks": "1350",
            "dp_label": "True",
            "face": "front",
            "model": "fa-C70R4b",
            "ports": "True",
            "protocol": "ETH"
        }
    },
    #model=fa-x20r4b&protocol=fc&face=back&datapacksv2=((datapacks%3A((fm_size%3A9.1TB%2Cfm_count%3A10)))%2C(datapacks%3A((fm_size%3A2TB%2Cfm_count%3A3))))&fm_label=TRUE&dp_label=TRUE&addoncards=2eth100&chassis_gen=2
    {
        "queryStringParameters": {
            "model": "fa-x20r4b",
            "protocol": "fc",
            "face": "back",
            "datapacksv2": urllib.parse.unquote("((datapacks%3A((fm_size%3A9.1TB%2Cfm_count%3A10)))%2C(datapacks%3A((fm_size%3A2TB%2Cfm_count%3A3))))"),
            "fm_label": "TRUE",
            "dp_label": "TRUE",
            "addoncards": "2eth100",
            "chassis_gen": "2"
        }
    },
    {
        "queryStringParameters": {
            "model": "fb-s200r2",
            "face": "front",
            "dfm_label": True,
            "bladesv2": jsonurl.dumps([
                {
                    "gen": "1",
                    "blades": [
                        {
                            "bays": [1, 2, 3, 4],
                            "fm_size": "24TB",
                            "blade_count": 5,
                            "blade_model": "fb-s200r2"
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