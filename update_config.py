import yaml

# Updates the config.yaml file with location information


def main():
    # args no arg unless we need to have this tool to more
    # Generate, the offsets programatically for slot locations for each chassis

    config = static_global_config()

    update_static_fm_loc(config)
    update_static_model_port_loc(config)

    # it will generate non existent model / revision combinations
    # but it's okay, we won't ever use them, or when an XL-130r2 comes out
    # we can go in a add it to the config special cased if necessary.
    
    for rel in [1, 2, 3, 4]:
        
        for gen in ['m', 'x', 'c', 'e']:
            rev_list = ['']
            if (gen != 'm' and gen != 'xl') and (rel == 4 or rel == 1):
                rev_list = ['', 'b']
            for rev in rev_list:
                update_static_pci_loc(config, gen, rel, rev)
                update_static_mezz_loc(config, gen, rel, rev)
                update_static_model_loc(config, gen, rel, rev)
                update_static_nvram_loc(config, gen, rel, rev)

        for gen in ['xl']:
            update_static_pci_loc(config, gen, rel, '')
            update_static_model_loc(config, gen, rel, '')


    update_static_card_port_loc(config)
    update_static_mezz_port_loc(config)

    update_static_fbs_blade_loc(config)

    with open('purerackdiagram/config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    with open('ui/config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    

def static_global_config():
    return {


        'port_naming_xcr2':{
            'mezz': { 'eth':6, 'sas': 0},
            0: { 'eth': 10, 'fc': 0, 'sas': 4},
            1: { 'eth': 14, 'fc': 4, 'sas': 4},
            2: { 'eth': 18, 'fc': 8, 'sas': 4},
            3: { 'eth': 22, 'fc': 12, 'sas': 4},
        },
        
        'port_naming_xcr4':{
            0: { 'eth': 5, 'fc': 0, 'sas': 0},
            1: { 'eth': 10, 'fc': 4, 'sas': 4},
            2: { 'eth': 14, 'fc': 8, 'sas': 0},
            3: { 'eth': 18, 'fc': 12, 'sas': 0},
            4: { 'eth': 22, 'fc': 16, 'sas':0},
        },

        'port_naming_xl':{
            0: { 'eth': 2, 'fc': 0, 'sas': 0},
            1: { 'eth': 6, 'fc': 4, 'sas': 4},
            2: { 'eth': 10, 'fc': 8, 'sas': 0},
            3: { 'eth': 14, 'fc': 12, 'sas': 0},
            4: { 'eth': 18, 'fc': 16, 'sas':0},
            5: { 'eth': 12, 'fc': 20, 'sas':0},
            6: { 'eth': 26, 'fc': 24, 'sas':0},
            7: { 'eth': 30, 'fc': 28, 'sas':0},
            8: { 'eth': 34, 'fc': 32, 'sas':0},
        },

        "pci_valid_cards": ["2eth", "2eth25roce", "2eth40", "2eth100", "2eth100roce",
                            "4eth25", "2ethbaset", "mgmt2ethbaset",
                            "2fc", "4fc",
                            "sas", "dca", "blank"],   

        "pci_config_lookup": {

            # New E R1
             "fa-er1b-fc": [ None, None, None, None, None],

            # New E R1
             "fa-er1-fc": ["mgmt2ethbaset", None, None, None, None],

             # New x R4b
            "fa-x20r4b-fc": [None, None, None, "2fc", None],
            "fa-x50r4b-fc": [None, "4fc", None, None, None],
            "fa-x70r4b-fc": [None, "4fc", None, "2fc", "dca"],
            "fa-x90r4b-fc": [None, "4fc", None, "2fc", "dca"],
            
            "fa-x20r4b-eth": [None, None, None, "2eth", None],
            "fa-x50r4b-eth": [None, None, None, "4eth25", None],
            "fa-x70r4b-eth": [None, None, None, "4eth25", "dca"],
            "fa-x90r4b-eth": [None, None, None, "4eth25", "dca"],

                         # New C R4b
            
            "fa-c50r4b-fc": [None, "4fc", None, None, None],
            "fa-c70r4b-fc": [None, "4fc", None, "2fc", "dca"],
            "fa-c90r4b-fc": [None, "4fc", None, "2fc", "dca"],
            
            "fa-c50r4b-eth": [None, None, None, "4eth25", None],
            "fa-c70r4b-eth": [None, None, None, "4eth25", "dca"],
            "fa-c90r4b-eth": [None, None, None, "4eth25", "dca"],

            # New x R4
            "fa-x20r4-fc": ["mgmt2ethbaset", None, None, "2fc", None],
            "fa-x50r4-fc": ["mgmt2ethbaset", "4fc", None, None, None],
            "fa-x70r4-fc": ["mgmt2ethbaset", "4fc", None, "2fc", "dca"],
            "fa-x90r4-fc": ["mgmt2ethbaset", "4fc", None, "2fc", "dca"],
            
            "fa-x20r4-eth": ["mgmt2ethbaset", None, None, "2eth", None],
            "fa-x50r4-eth": ["mgmt2ethbaset", "2eth", None, "2eth", None],
            "fa-x70r4-eth": ["mgmt2ethbaset", "2eth", None, "2eth", "dca"],
            "fa-x90r4-eth": ["mgmt2ethbaset", "2eth", None, "2eth", "dca"],

            # New C R4
            "fa-c50r4-fc": ["mgmt2ethbaset", "4fc", None, None, None],
            "fa-c70r4-fc": ["mgmt2ethbaset", "4fc", None, "2fc", "dca"],
            "fa-c90r4-fc": ["mgmt2ethbaset", "4fc", None, "2fc", "dca"],

            "fa-c50r4-eth": ["mgmt2ethbaset", "2eth", None, "2eth", None],
            "fa-c70r4-eth": ["mgmt2ethbaset", "2eth", None, "2eth", "dca"],
            "fa-c90r4-eth": ["mgmt2ethbaset", "2eth", None, "2eth", "dca"],


            "fa-x10r3-fc": [None, None, "2fc", None],
            "fa-x20r3-fc": [None, None, "2fc", None],
            "fa-x50r3-fc": ["4fc", None, None, None],
            "fa-x70r3-fc": ["4fc", None, "2fc", None],
            "fa-x90r3-fc": ["4fc", None, "2fc", None],
            "fa-x10r3-eth": [None, None, None, None],
            "fa-x20r3-eth": [None, None, None, None],
            "fa-x50r3-eth": ["2eth", None, None, None],
            "fa-x70r3-eth": ["2eth", None, None, None],
            "fa-x90r3-eth": ["2eth", None, None, None],
            "fa-x10r2-fc": [None, None, "2fc", None],
            "fa-x20r2-fc": [None, None, "2fc", None],
            "fa-x50r2-fc": ["4fc", None, None, None],
            "fa-x70r2-fc": ["4fc", None, "2fc", None],
            "fa-x90r2-fc": ["4fc", None, "2fc", None],
            "fa-x10r2-eth": [None, None, None, None],
            "fa-x20r2-eth": [None, None, None, None],
            "fa-x50r2-eth": ["2eth", None, None, None],
            "fa-x70r2-eth": ["2eth", None, None, None],
            "fa-x90r2-eth": ["2eth", None, None, None],
            "fa-m10r2-fc": [None, None, "2fc", None],
            "fa-m20r2-fc": [None, None, "2fc", None],
            "fa-m50r2-fc": ["2fc", None, "2fc", None],
            "fa-m70r2-fc": ["4fc", None, "2fc", None],
            "fa-m10r2-eth": [None, None, None, None],
            "fa-m20r2-eth": [None, None, "2eth", None],
            "fa-m50r2-eth": ["2eth", None, "2eth", None],
            "fa-m70r2-eth": ["2eth", None, "2eth", None],
            "fa-x70r1-eth": ["2eth", None, "2eth", None],
            "fa-x70r1-fc": ["4fc", None, "2fc", None],
            "fa-c40r1-eth": ["2eth", None, None, None],
            "fa-c40r1-fc": ["4fc", None, None, None],
            "fa-c60r1-eth": ["2eth", None, None, None],
            "fa-c60r1-fc": ["4fc", None, None, None],
            "fa-c40r3-eth": [None, None, None, None],
            "fa-c40r3-fc": ["2fc", None, None, None],
            "fa-c60r3-eth": ["2eth", None, None, None],
            "fa-c60r3-fc": ["4fc", None, None, None],
            "fa-xl130r1-eth": [None, "2eth", None, None, None, "dca", None, None, None],
            "fa-xl130r1-fc": [None, "4fc", None, None, None, "dca", None, None, "2fc"],
            "fa-xl170r1-eth": [None, "2eth", None, None, None, "dca", None, None, None],
            "fa-xl170r1-fc": [None, "4fc", None, None, None, "dca", None, None, "2fc"]

        },

        # the UI Datapack chart loads directly from this as well. 
        "chassis_dp_size_lookup": {
            "0": ["Blank", "blank", 10, "0"],
            "0.02": ["Blank", "blank", 2, "0"],
            "0.04": ["Blank", "blank", 4, "0"],
            "0.06": ["Blank", "blank", 6, "0"],
            "0.08": ["Blank", "blank", 8, "0"],
            "0.10": ["Blank", "blank", 10, "0"],
            "0.12": ["Blank", "blank", 12, "0"],
            "0.14": ["Blank", "blank", 14, "0"],
            "0.16": ["Blank", "blank", 16, "0"],
            "0.18": ["Blank", "blank", 18, "0"],
            "0.20": ["Blank", "blank", 20, "0"],

            "3": ["750GB", "scm", 4, "DM Cache 3"],
            "6": ["750GB", "scm", 8, "DM Cache 6"],

            "11": ["1.1TB", "nvme", 10, "11"],
            "13": ["1.1TB", "nvme", 12, "13"],
            "15": ["1.1TB", "nvme", 14, "15"],
            "18": ["1.1TB", "nvme", 16, "18"],
            "20": ["1.1TB", "nvme", 18, "20"],

            "22": ["2.2TB", "nvme", 10, "22"],
            "27": ["2.2TB", "nvme", 12, "27"],
            "31": ["2.2TB", "nvme", 14, "31"],
            "36": ["2.2TB", "nvme", 16, "36"],
            "40": ["2.2TB", "nvme", 18, "40"],
            "44": ["2.2TB", "nvme", 20, "44"],

            "45": ["4.5TB", "nvme", 10, "45"],
            "63": ["4.5TB", "nvme", 14, "63"],
            "72": ["4.5TB", "nvme", 16, "72"],
            "81": ["4.5TB", "nvme", 18, "81"],
            "90": ["4.5TB", "nvme", 20, "90"],
            
            "91": ["9.1TB", "nvme", 10, "91"],
            "109": ["9.1TB", "nvme", 12, "109"],
            "127": ["9.1TB", "nvme", 14, "127"],
            "145": ["9.1TB", "nvme", 16, "145"],
            "164": ["9.1TB", "nvme", 18, "164"],


            "183": ["18.3TB", "nvme", 10, "183"],
            "219": ["18.3TB", "nvme", 12, "219"],
            "256": ["18.3TB", "nvme", 14, "256"],
            "292": ["18.3TB", "nvme", 16, "292"],
            "329": ["18.3TB", "nvme", 18, "329"],

            "366": ["36.6TB", "nvme", 10, "366"],
            "439": ["36.6TB", "nvme", 12, "439"],
            "512": ["36.6TB", "nvme", 14, "512"],
            "585": ["36.6TB", "nvme", 16, "585"],
            "658": ["36.6TB", "nvme", 18, "658"],

            # this is a duplicate of the 10x 36.6 pack
            # so you will have to do 183/183

            #"366": ["18.3TB", "nvme", 20, "366"],

            # SAS PACKS
            "4.8": ["480GB", "sas", 10, "4.8"],
            "5.0": ["500GB", "sas", 10, "5"],
            "9.6": ["960GB", "sas", 10, "9.6"],
            "10.0": ["1TB", "sas", 10, "10"],
            "19.2": ["1.9TB", "sas", 10, "19.2"],
            "20.0": ["2TB", "sas", 10, "20"],
            "38.0": ["3.8TB", "sas", 10, "38"],
            "76.0": ["7.6TB", "sas", 10, "76"]
        },

        "qlc_chassis_dp_size_lookup": {

            # this is legacy //C 
            "366": ["18.3TB", "nvme-qlc", 20, "366"],

            # // 18.6 TB PACKS, added 1/23/2024
            "186": ["18.6TB", "nvme-qlc", 10, "186"],
            "223": ["18.6TB", "nvme-qlc", 12, "223"],
            "260": ["18.6TB", "nvme-qlc", 14, "260"],
            "297": ["18.6TB", "nvme-qlc", 16, "297"],
            "334": ["18.6TB", "nvme-qlc", 18, "334"],

            # //C 24.0 TB PACKS, added 11/16/2022, new drive size
            "240": ["24.0TB", "nvme-qlc", 10, "240"],
            "288": ["24.0TB", "nvme-qlc", 12, "288"],
            "336": ["24.0TB", "nvme-qlc", 14, "336"],
            "384": ["24.0TB", "nvme-qlc", 16, "384"],
            "432": ["24.0TB", "nvme-qlc", 18, "432"],
            "480": ["24.0TB", "nvme-qlc", 20, "480"],


            # //C 24.7 TB PACKS
            
            "247": ["24.7TB", "nvme-qlc", 10, "247"],
            "296": ["24.7TB", "nvme-qlc", 12, "296"],
            "345": ["24.7TB", "nvme-qlc", 14, "345"],
            "395": ["24.7TB", "nvme-qlc", 16, "395"],
            "444": ["24.7TB", "nvme-qlc", 18, "444"],
            "494": ["24.7TB", "nvme-qlc", 20, "494"],

            # //C 37.5 TB Packs 6/6/2024
            "375": ["37.5TB", "nvme-qlc", 10, "375"],
            "450": ["37.5TB", "nvme-qlc", 12, "450"],
            "525": ["37.5TB", "nvme-qlc", 14, "525"],
            "600": ["37.5TB", "nvme-qlc", 16, "600"],
            "675": ["37.5TB", "nvme-qlc", 18, "675"],
            # "750": ["37.5TB", "nvme-qlc", 20, "760"],  # conflict with 10x 75 TB

            # //C 48.2 TB PACKS, added 11/16/2022, new drive size
            "482": ["48.2TB", "nvme-qlc", 10, "482"],
            "578": ["48.2TB", "nvme-qlc", 12, "578"],
            "674": ["48.2TB", "nvme-qlc", 14, "674"],
            "771": ["48.2TB", "nvme-qlc", 16, "771"],
            "867": ["48.2TB", "nvme-qlc", 18, "867"],
            "964": ["48.2TB", "nvme-qlc", 20, "964"],


            # //C 49.2 TB PACKS
            "492": ["49.2TB", "nvme-qlc", 10, "492"],
            "590": ["49.2TB", "nvme-qlc", 12, "590"],
            "688": ["49.2TB", "nvme-qlc", 14, "688"],
            "787": ["49.2TB", "nvme-qlc", 16, "787"],
            "885": ["49.2TB", "nvme-qlc", 18, "885"],
            "984": ["49.2TB", "nvme-qlc", 20, "984"],

            # // E 75 TB Packs
            "750": ["75TB", "nvme-qlc", 10, "750"],
            "900": ["75TB", "nvme-qlc", 12, "900"],
            "1050": ["75TB", "nvme-qlc", 14, "1050"],
            "1200": ["75TB", "nvme-qlc", 16, "1200"],
            "1350": ["75TB", "nvme-qlc", 18, "1350"],
            "1500": ["75TB", "nvme-qlc", 20, "1500"],
        },

        "csize_lookup": {
            
            "839": "494-345",
            "879": "366-512",
            "1182": "494-688",
            "1185": "494-345/345",
            "1329": "984-345",
            "1390": "366-512-512",
            "1476": "984-492",
            "1531": "494-345/345-345",
            "1574": "984-590",
            "1672": "984-688",
            "1771": "984-787",
            "1869": "984-885",
            "1877": "494-345/345-345/345",

            #added 11/16/2022 the new 24.0 & 48.2 TB packs
            "816": "480-336",
            "1154": "480-674",
            "1300": "964-336",
            "1446": "964-482",
            "1488": "480-674-336",
            "1542": "964-578",
            "1638": "964-674",
            "1735": "964-771",
            "1824": "480-674-674",
            "1831": "964-867",
            "1928": "964-964",
            "2120": "964-1253",
            "2313": "964-1349",



        },

        "shelf_dp_size_lookup": {
            "0": ["Blank", "blank", 14, "0"],
            "0.02": ["Blank", "blank", 2, "0"],
            "0.04": ["Blank", "blank", 4, "0"],
            "0.06": ["Blank", "blank", 6, "0"],
            "0.08": ["Blank", "blank", 8, "0"],
            "0.10": ["Blank", "blank", 10, "0"],
            "0.12": ["Blank", "blank", 12, "0"],
            "0.14": ["Blank", "blank", 14, "0"],
            "0.16": ["Blank", "blank", 16, "0"],
            "0.18": ["Blank", "blank", 18, "0"],

            "11": ["1.1TB", "nvme", 10, "11"],
            "13": ["1.1TB", "nvme", 12, "13"],
            "15": ["1.1TB", "nvme", 14, "15"],
            "18": ["1.1TB", "nvme", 16, "18"],
            "20": ["1.1TB", "nvme", 18, "20"],

            "22": ["2.2TB", "nvme", 10, "22"],
            "27": ["2.2TB", "nvme", 12, "27"],
            "31": ["2.2TB", "nvme", 14, "31"],
            "36": ["2.2TB", "nvme", 16, "36"],
            "40": ["2.2TB", "nvme", 18, "40"],

            "45": ["4.5TB", "nvme", 10, "45"],
            "63": ["4.5TB", "nvme", 14, "63"],
            "72": ["4.5TB", "nvme", 16, "72"],
            "81": ["4.5TB", "nvme", 18, "81"],
            
            "91": ["9.1TB", "nvme", 10, "91"],
            "109": ["9.1TB", "nvme", 12, "109"],
            "127": ["9.1TB", "nvme", 14, "127"],
            "145": ["9.1TB", "nvme", 16, "145"],
            "164": ["9.1TB", "nvme", 18, "164"],

            "183": ["18.3TB", "nvme", 10, "183"],
            "219": ["18.3TB", "nvme", 12, "219"],
            "256": ["18.3TB", "nvme", 14, "256"],
            "292": ["18.3TB", "nvme", 16, "292"],
            "329": ["18.3TB", "nvme", 18, "329"],

            "366": ["36.6TB", "nvme", 10, "366"],
            "439": ["36.6TB", "nvme", 12, "439"],
            "512": ["36.6TB", "nvme", 14, "512"],
            "585": ["36.6TB", "nvme", 16, "585"],
            "658": ["36.6TB", "nvme", 18, "658"],

            # SAS Shelves
            # added decimals to old SAS media to avoid conflict with new nvme sizes.
            "6.1": ["256GB", "sas", 24, "6"],
            "11.5": ["960GB", "sas", 12, "11"],
            "12.3": ["512GB", "sas", 24, "12"],
            "22.8": ["1.9TB", "sas", 12, "23"],
            "24.0": ["1TB", "sas", 24, "24"],
            "45.6": ["3.8TB", "sas", 12, "45"],
            "91.2": ["7.6TB", "sas", 12, "91"]
        },


        "qlc_shelf_dp_size_lookup": {

             # this is legacy //C when we used tlc actually
            "512": ["18.3TB", "nvme-qlc", 28, "512"],

                        # // 18.6 TB PACKS, add 1/23/2024
            "186": ["18.6TB", "nvme-qlc", 10, "186"],
            "223": ["18.6TB", "nvme-qlc", 12, "223"],
            "260": ["18.6TB", "nvme-qlc", 14, "260"],
            "297": ["18.6TB", "nvme-qlc", 16, "297"],
            "334": ["18.6TB", "nvme-qlc", 18, "334"],


            # //C 24.0 TB PACKS added 11/16/2022, new drive size
            "240": ["24.0TB", "nvme-qlc", 10, "240"],
            "288": ["24.0TB", "nvme-qlc", 12, "288"],
            "336": ["24.0TB", "nvme-qlc", 14, "336"],
            "384": ["24.0TB", "nvme-qlc", 16, "384"],
            "432": ["24.0TB", "nvme-qlc", 18, "432"],
            "480": ["24.0TB", "nvme-qlc", 20, "480"],
            "528": ["24.0TB", "nvme-qlc", 22, "528"],
            "576": ["24.0TB", "nvme-qlc", 24, "576"],
            "624": ["24.0TB", "nvme-qlc", 26, "624"],
            "672": ["24.0TB", "nvme-qlc", 28, "672"],

            # //C 24.7 TB PACKS
            "247": ["24.7TB", "nvme-qlc", 10, "247"],
            "296": ["24.7TB", "nvme-qlc", 12, "296"],
            "345": ["24.7TB", "nvme-qlc", 14, "345"],
            "395": ["24.7TB", "nvme-qlc", 16, "395"],
            "444": ["24.7TB", "nvme-qlc", 18, "444"],
            "494": ["24.7TB", "nvme-qlc", 20, "494"],
            "543": ["24.7TB", "nvme-qlc", 22, "543"],
            "592": ["24.7TB", "nvme-qlc", 24, "592"],
            "642": ["24.7TB", "nvme-qlc", 26, "642"],
            "691": ["24.7TB", "nvme-qlc", 28, "691"],

            # //C 37.5 TB Packs 6/6/2024
            "375": ["37.5TB", "nvme-qlc", 10, "375"],
            "450": ["37.5TB", "nvme-qlc", 12, "450"],
            "525": ["37.5TB", "nvme-qlc", 14, "525"],
            "600": ["37.5TB", "nvme-qlc", 16, "600"],
            "675": ["37.5TB", "nvme-qlc", 18, "675"],
            # "750": ["37.5TB", "nvme-qlc", 20, "760"],  # conflict with 10x 75 TB

            # //C 48.2 TB PACKS added 11/16/2022, new drive size
            "482": ["48.2TB", "nvme-qlc", 10, "480"],
            "578": ["48.2TB", "nvme-qlc", 12, "578"],
            "674": ["48.2TB", "nvme-qlc", 14, "674"],
            "771": ["48.2TB", "nvme-qlc", 16, "771"],
            "867": ["48.2TB", "nvme-qlc", 18, "867"],
            "964": ["48.2TB", "nvme-qlc", 20, "964"],
            "1060": ["48.2TB", "nvme-qlc", 22, "1060"],
            "1156": ["48.2TB", "nvme-qlc", 24, "1156"],
            "1253": ["48.2TB", "nvme-qlc", 26, "1253"],
            "1349": ["48.2TB", "nvme-qlc", 28, "1349"],

            # //C 49.2 TB PACKS
            "492": ["49.2TB", "nvme-qlc", 10, "492"],
            "590": ["49.2TB", "nvme-qlc", 12, "590"],
            "688": ["49.2TB", "nvme-qlc", 14, "688"],
            "787": ["49.2TB", "nvme-qlc", 16, "787"],
            "885": ["49.2TB", "nvme-qlc", 18, "885"],
            "984": ["49.2TB", "nvme-qlc", 20, "984"],
            "1082": ["49.2TB", "nvme-qlc", 22, "1082"],
            "1180": ["49.2TB", "nvme-qlc", 24, "1180"],
            "1279": ["49.2TB", "nvme-qlc", 26, "1279"],
            "1377": ["49.2TB", "nvme-qlc", 28, "1377"],

            # E Data packs
            # // E 75 TB Packs
            "750": ["75TB", "nvme-qlc", 10, "750"],
            "900": ["75TB", "nvme-qlc", 12, "900"],
            "1050": ["75TB", "nvme-qlc", 14, "1050"],
            "1200": ["75TB", "nvme-qlc", 16, "1200"],
            "1350": ["75TB", "nvme-qlc", 18, "1350"],
            "1500": ["75TB", "nvme-qlc", 20, "1500"],
            "1650": ["75TB", "nvme-qlc", 22, "1650"],
            "1800": ["75TB", "nvme-qlc", 24, "1800"],
            "1950": ["75TB", "nvme-qlc", 26, "1950"],
            "2100": ["75TB", "nvme-qlc", 28, "2100"],

            
        },

        "fb_blade_reg_pattern": "^([0-9]+:[0-9]+(-[0-9]+)?,?)+$"
    }

## Add FlashBlade S blade locations in the chassis.
def update_static_fbs_blade_loc(config):

    for key in ['png/pure_fbs_front.png', 'png/pure_fbe_front.png']:

        blade_loc = [None] * 10
        blade_loc[0] = (163, 34)
        blade_offset = 255
        for x in range(10):
            if blade_loc[x] is None:
                loc = list(blade_loc[x - 1])
                loc[0] += blade_offset
                blade_loc[x] = tuple(loc)
        config[key] = {'blade_loc': blade_loc}

    key = 'png/pure_fbs_blade.png'
    fm_loc = [
        (10, 16), (122, 16),
        (10, 630), (122, 630)
    ]
   

    model_text_loc =  (199, 549)

    config[key] = {'fm_loc': fm_loc,
                   'model_text_loc': model_text_loc }

## Add FlashModules locations on the front of the chassis.
def update_static_fm_loc(config):
    # Location of Flash Module Location

    ######################
    ## SAS SHELF
    ######################

    fm_loc = [None] * 24
    fm_loc[0] = (138, 1)
    fm_loc[12] = (1450, 1)
    x_offset = 105

    for x in range(24):
        if fm_loc[x] is None:
            loc = list(fm_loc[x - 1])
            loc[0] += x_offset
            fm_loc[x] = tuple(loc)
    key = 'png/pure_fa_sas_shelf_front.png'
    if key not in config:
        config[key] = {}
    config[key]['fm_loc'] = fm_loc

    #################################
    ## FA Chassis Flash Modules for M, X, C, NVMe Shelf
    ######################

    # x,y coordinates for all chassis fms.
    # Chassis FM locations
    # these are the anchor locations, and
    # offsets are calculated to fill in holes
    ch0_fm_loc = [None] * 28
    ch0_fm_loc[0] = (165, 250)
    ch0_fm_loc[4] = (714, 250)
    ch0_fm_loc[8] = (1265, 250)
    ch0_fm_loc[12] = (1817, 250)
    ch0_fm_loc[20] = (164, 27)

    x_offset = 105
    for x in range(20):
        if ch0_fm_loc[x] is None:  # skips anchor locations
            loc = list(ch0_fm_loc[x - 1])
            loc[0] += int(x_offset)
            ch0_fm_loc[x] = tuple(loc)

    y_offset = x_offset
    x_offset = 550
    for x in range(20, 28):
        if ch0_fm_loc[x] is None:
            loc = list(ch0_fm_loc[x - 1])
            if x % 2 == 0:
                loc[0] += x_offset
                loc[1] -= y_offset
            else:
                loc[1] += y_offset
            ch0_fm_loc[x] = tuple(loc)

    # add chassis
    for rel in range(1, 5):
        for rev in ['', 'b']:
            key = f'png/pure_fa_x_r{rel}{rev}_front.png'
            if key not in config:
                config[key] = {}
            config[key]['fm_loc'] = ch0_fm_loc.copy()

            # C is the same:
            key = f'png/pure_fa_c_r{rel}{rev}_front.png'
            if key not in config:
                config[key] = {}
            config[key]['fm_loc'] = ch0_fm_loc.copy()

            # E is the same:
            if rel == 1:
                key = f'png/pure_fa_e_r{rel}{rev}_front.png'
                if key not in config:
                    config[key] = {}
                config[key]['fm_loc'] = ch0_fm_loc.copy()

    # nvme shelves are the same:
    key = 'png/pure_fa_nvme_shelf_front.png'
    if key not in config:
        config[key] = {}
    config[key]['fm_loc'] = ch0_fm_loc.copy()

    # adjust slightly for the //m image
    for x in range(len(ch0_fm_loc)):
        ch0_fm_loc[x] = (ch0_fm_loc[x][0] - 9, ch0_fm_loc[x][1] - 7)

    for rel in range(1, 3):
        key = f'png/pure_fa_m_r{rel}_front.png'
        if key not in config:
            config[key] = {}
        config[key]['fm_loc'] = ch0_fm_loc.copy()

    #################################
    ## FA Chassis Flash Modules for XL
    ######################

    # XL is different lets start over for XL
    ch0_fm_loc = [None] * 40
    ch0_fm_loc[0] = (161, 175)
    ch0_fm_loc[10] = (1460, 175)
    ch0_fm_loc[20] = (161, 730)
    ch0_fm_loc[30] = (1460, 730)
    
    x_offset = 126

    for x in range(len(ch0_fm_loc)):
        if ch0_fm_loc[x] is None:  # skips anchor locations
            loc = list(ch0_fm_loc[x - 1])
            loc[0] += int(x_offset)
            ch0_fm_loc[x] = tuple(loc)
    
    key = 'png/pure_fa_xl_r1_front.png'
    if key not in config:
        config[key] = {}
    config[key]['fm_loc']= ch0_fm_loc.copy()





def update_static_pci_loc(config, generation, release, rev):
    pci_loc = None
    if (generation == 'x' or generation == 'c') and release < 4:
        pci_loc = [(1198, 87), (1198, 203), (2069, 87), (2069, 203)]
        ct1_y_offset = 380

    # R4
    elif (generation == 'x' or generation == 'c') and release == 4:
        pci_loc = [(679, 83), (1225, 83), (1225, 203), (2075, 83), (2075, 203)]
        ct1_y_offset = 378

    # E r1
    elif generation == 'e':
        pci_loc = [(679, 83), (1225, 83), (1225, 203), (2075, 83), (2075, 203)]
        ct1_y_offset = 378


    elif generation == 'm':
        pci_loc = [(1317, 87), (1317, 201), (2182, 87), (2182, 201)]
        ct1_y_offset = 378

    elif generation == 'xl':
        pci_loc = [(330, 365), (330, 480), 
                   (885, 365), (885, 480),
                   (1609, 365),(1609, 480),
                   (2150, 365), (2150, 480), (2150, 603)]
        ct1_y_offset = 480

    key = f'png/pure_fa_{generation}_r{release}{rev}_back.png'
    if key not in config:
        config[key] = {}

    config[key]['ct0_pci_loc'] = pci_loc.copy()

    ## Now calculate all the pci slot locations for ct1
    for i in range(len(pci_loc)):
        # add a y_offset to calculate the ct0 coordinates
        cord = pci_loc[i]
        pci_loc[i] = (cord[0], cord[1] + ct1_y_offset)

    
    config[key]['ct1_pci_loc'] = pci_loc.copy()

    

    


def update_static_nvram_loc(config, generation, release, rev):
    key = f'png/pure_fa_{generation}_r{release}{rev}_front.png'
    if key not in config:
        config[key] = {}

    if generation == 'x' or \
            generation == 'c' or generation == 'e':
        nv1 = (1263, 28)
        nv2 = (1813, 28)
    elif generation != "xl":
        nv1 = (1255, 20)
        nv2 = (1805, 20)

    config[key]['nvram_loc'] = [nv1, nv2].copy()

    return config


def update_static_mezz_loc(config, generation, release, rev):
    key = f'png/pure_fa_{generation}_r{release}{rev}_back.png'
    if key not in config:
        config[key] = {}

    if generation == 'x' or \
            generation == 'c':
        config[key]['ct0_mezz_loc'] = (585, 45)
        config[key]['ct1_mezz_loc'] = (585, 425)
    else:
        config[key]['ct0_mezz_loc'] = (709, 44)
        config[key]['ct1_mezz_loc'] = (709, 421)
    


def update_static_model_loc(config, generation, release, rev):
    key = f'png/pure_fa_{generation}_r{release}{rev}_front.png'
    if key not in config:
        config[key] = {}

    if generation == 'x' or \
            generation == 'c' :
        loc = (2759, 83)
    elif generation == 'e':
        loc = (2770, 222)
    elif generation == 'xl':
        loc = (22, 245)
    else:
        loc = (2745, 120)

    config[key]['model_text_loc'] = loc

def add_ports_to_key(ports_loc, key, port_info, config):
    ports = []
    for ploc in ports_loc:
        port_info_copy = port_info.copy()
        port_info_copy['loc'] = ploc 
        ports.append(port_info_copy)
    config[key] = {'ports': ports}


def update_static_card_port_loc(config):
    # calculate the port location based on the offset. 

    ###  All the FC cards.

    port_info = {'port_type': 'fc',
                'port_connector': 'sfp',
                'port_speeds': ['32g', '64g'],
                'port_sfp_present': True,
                'port_sfp_speed': ['32g'] ,
                'port_sfp_connector': 'lc',
                'services': ['data', 'replication']}
     
     
    ports_loc = [(158, 40), (256, 40)]
    keys = ['png/pure_fa_2fc_fh.png', 'png/pure_fa_2fc_hh.png']

    # the ports are in the same location on both fh and hh cards, so we can use the same port_info
    for k in keys:
        add_ports_to_key(ports_loc, k, port_info, config)
    
    # same port info for 4 port cards, but differnt locations on fh and hh
    ports_loc = [(252, 40), (343, 40), (432, 40), (524, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_4fc_fh.png',  port_info, config)

    ports_loc = [(48, 40), (138, 40), (230, 40), (322, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_4fc_hh.png', port_info, config)
    

    #2 Eth 10/25Gb Optical - FA-XCR4-25G-iSCSI 2-Port
    

    port_info = {'port_type': 'eth',
                'port_connector': 'sfp',
                'port_speeds': ['10g', '25g'],
                'port_sfp_present': True,
                'port_sfp_speed': ['10g'],
                'port_sfp_connector': 'lc',
                'services': ['data', 'replication']}
    

    k = 'png/pure_fa_2eth_hh.png'
    ports_loc = [(158, 40), (256, 40)]
    add_ports_to_key(ports_loc, k, port_info, config)

    k = 'png/pure_fa_2eth_fh.png'
    add_ports_to_key(ports_loc, k, port_info, config)


     #2 Eth 10/25Gb Optical - FA-XCR4-25G-iSCSI/ROCE 2-Port
    port_info = {'port_type': 'eth_roce',
                'port_connector': 'sfp',
                'port_speeds': ['10g', '25g'],
                'port_sfp_present': True,
                'port_sfp_speed': ['10g'],
                'port_sfp_connector': 'lc',
                'services': ['data', 'replication']}
    

    k = 'png/pure_fa_2eth25roce_hh.png'
    ports_loc = [(158, 40), (256, 40)]
    add_ports_to_key(ports_loc, k, port_info, config)

    k = 'png/pure_fa_2eth25roce_fh.png'
    add_ports_to_key(ports_loc, k, port_info, config)
    

    #4 Eth 10/25Gb Optical - FA-25G-ETH/TCP 4-Port

    # same port info for 4 port cards, but differnt locations on fh and hh

    port_info['port_type'] = 'eth'
    ports_loc = [(252, 40), (343, 40), (432, 40), (524, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_4eth25_fh.png',  port_info, config)

    ports_loc = [(48, 40), (138, 40), (230, 40), (322, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_4eth25_hh.png', port_info, config)



    # 2 Eth 10/25Gb 10GBaseT - FA-CNTRL-10GBaseT 2-Port 
    ports_loc = [(155, 40), (265, 40)]
    keys = ['png/pure_fa_2ethbaset_fh.png',
            'png/pure_fa_2ethbaset_hh.png']
    
    port_info = {'port_type': 'eth',
                'port_connector': 'rj45',
                'port_speeds': ['1g' ,'10g'],
                'port_sfp_present': False,
                'port_sfp_speed': [] ,
                'port_sfp_connector': None,
                'services': ['data', 'replication']}


    for k in keys:
        add_ports_to_key(ports_loc, k , port_info, config)

    # 2 Eth 10/25Gb 10GBaseT - FA-CNTRL-10GBaseT 2-Port 
    # Used for management ONLY, used in the XR4
    # only one port is available, but we will use the same port info
    ports_loc = [(155, 40)]
    port_info['services'] = ['management']

    add_ports_to_key(ports_loc, 'png/pure_fa_mgmt2ethbaset_fh.png', port_info, config )
    add_ports_to_key(ports_loc, 'png/pure_fa_mgmt2ethbaset_hh.png', port_info, config )
    



   # 2 Eth 40Gb - FA-CNTRL-40G-iSCSI 2-Port


    port_info = {'port_type': 'eth',
            'port_connector': 'qsfp',
            'port_speeds': ['40g'],
            'port_sfp_present': False,
            'port_sfp_speed': [] ,
            'port_sfp_connector': None,
            'services': ['data', 'replication']}


    ports_loc = [(210, 40), (410, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_2eth40_fh.png', port_info, config)
   

    ports_loc = [(70, 40), (245, 40) ]
    add_ports_to_key(ports_loc, 'png/pure_fa_2eth40_hh.png', port_info, config)

    # 2 Eth 100Gb - FA-100G-ETH/TCP 2-Port
    port_info['port_speeds'] = ['40g', '100g']

    ports_loc = [(210, 40), (410, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_2eth100_fh.png', port_info, config)
   
    ports_loc = [(70, 40), (245, 40) ]
    add_ports_to_key(ports_loc, 'png/pure_fa_2eth100_hh.png', port_info, config)

    #2 Eth 100Gb RoCE - FA-XCR4-100G-iSCSI/ROCE 2-Port


    port_info['port_type'] = 'eth_roce'
    port_info['services'] = ['data', 'replication', 'shelf']
    ports_loc = [(210, 40), (410, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_2eth100roce_fh.png', port_info, config)
   
    ports_loc = [(70, 40), (245, 40) ]
    add_ports_to_key(ports_loc, 'png/pure_fa_2eth100roce_hh.png', port_info, config)

    port_info = {'port_type': 'sas',
            'port_connector': 'sas',
            'port_speeds': ['6g', '12g'],
            'port_sfp_present': False,
            'port_sfp_speed': [] ,
            'port_sfp_connector': None,
            'services': ['shelf']}
    

    # add_ports_to_key(ports_loc, 'png/pure_fa_sas_hh.png', port_info, config)
    # same port info for 4 port cards, but differnt locations on fh and hh
    ports_loc = [(191, 46), (263, 46), (340, 46), (412, 46)]
    add_ports_to_key(ports_loc, 'png/pure_fa_sas_fh.png',  port_info, config)

    ports_loc = [(69, 40), (148, 40), (225, 40), (303, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_sas_hh.png', port_info, config)



def update_static_model_port_loc(config):

    ## adding the LOM  port locations

    #################################
    ## FA Chassis Flash Modules for M / X / C
    ######################

    for release in [1, 2, 3, 4]:
        ct0ports = None
        if release == 4: 
            ct0ports = [ {'loc': (671, 308),
                'name': 'ct0.eth0',
                'port_type': 'eth_roce',
                'port_connector': 'qsfp28',
                'port_speeds': ['50g', '100g'],
                'port_sfp_present': False,
                'port_sfp_speed': [] ,
                'port_sfp_connector': None,
                'services': ['shelf'] },

                {'loc': (786, 308),
                'name': 'ct0.eth1',
                'port_type': 'eth_roce',
                'port_connector': 'qsfp28',
                'port_speeds': ['50g', '100g'],
                'port_sfp_present': False,
                'port_sfp_speed': [],
                'port_sfp_connector': None,
                'services': ['shelf']},

                {'loc': (902, 308),
                'name': 'ct0.eth2',
                'port_type': 'eth',
                'port_connector': 'sfp',
                'port_speeds': ['10g', '25g'],
                
                'port_sfp_present': True,
                'port_sfp_speeds': ['10g'] ,
                'port_sfp_connector': 'LC',

                'services': ['replication', 'data']},
                
                {'loc': (990, 308),
                 'name': 'ct0.eth3',

                'port_type': 'eth',
                'port_connector': 'sfp',
                'port_speeds': ['10g', '25g'],

                'port_sfp_present': True,
                'port_sfp_speed': ['10g'] ,
                'port_sfp_connector': 'LC',

                'services': ['replication', 'data']},

                {'loc': (1945, 220),
                'name': 'ct0.eth4',
                'port_type': 'eth',
                'port_connector': 'rj45',
                'port_speeds': ['1g'],
                
                'port_sfp_present': False,
                'port_sfp_speed': [],
                'port_sfp_connector': None,

                'services': ['management']}
                ]
        else:
        # These are all the ct0 ports
        # rev < 4
            ct0ports = [
            {   'loc': (671, 316),
                'name': 'ct0.eth0',
                'port_type': 'eth',
                
                'port_connector': 'rj45',
                'port_speeds': ['1g'],
                'port_sfp_present': False,
                'port_sfp_speed': [],
                'port_sfp_connector': None,
                'services': ['management']
            },

            {
                'name': 'ct0.eth1',
                'loc': (788, 316),
                'port_type': 'eth',

                'port_connector': 'rj45',
                'port_speeds': ['1g'],
                'port_sfp_present': False,
                'port_sfp_speed': [],
                'port_sfp_connector': None,
                'services': ['management']
            },
            
            {
                'loc': (1880, 221),
                'port_type': 'eth',
                'name': 'ct0.eth2',
                'port_connector': 'sfp',
                'port_speeds': ['10g', '25g'],

                'port_sfp_present': True,
                'port_sfp_speed': ['10g'] ,
                'port_sfp_connector': 'LC',

                'services': ['replication', 'data']

            },
            {
                'loc': (1880, 293),
                'port_type': 'eth',
                'name': 'ct0.eth3',
                'port_connector': 'sfp',
                'port_speeds': ['10g', '25g'],

                'port_sfp_present': True,
                'port_sfp_speed': ['10g'] ,
                'port_sfp_connector': 'LC',

                'services': ['replication', 'data']
                
            },
            {
                'loc': (1965, 221),
                'port_type': 'eth',
                'name': 'ct0.eth4',
                
                'port_connector': 'sfp',
                'port_speeds': ['10g', '25g'],

                'port_sfp_present': True,
                'port_sfp_speed': ['10g'] ,
                'port_sfp_connector': 'LC',

                'services': ['data', 'replication']},
            {
                'loc': (1965, 293),
                'port_type': 'eth',
                'name': 'ct0.eth5',

                'port_connector': 'sfp',
                'port_speeds': ['10g', '25g'],

                'port_sfp_present': True,
                'port_sfp_speed': ['10g'] ,
                'port_sfp_connector': 'LC',

                'services': ['data', 'replication']}]
        
        rev_list = ['']
        if release == 4:
            #release 4 is the first time we had a revision
            # we set the loopoing params for these:
            rev_list = ['','b']

        for rev in rev_list:
            if release == 4 and rev == 'b':
                ct0ports.append({'loc': (1945, 293),
                'name': 'ct0.eth5',
                'port_type': 'eth',
                'port_connector': 'rj45',
                'port_speeds': ['1g'],
                
                'port_sfp_present': False,
                'port_sfp_speed': [],
                'port_sfp_connector': None,

                'services': ['management']})




            ct1ports = []
            for p in ct0ports:
                p_copy = p.copy()
                p_copy['loc'] = (p['loc'][0], p['loc'][1] + 380)
                p_copy['name'] = p_copy['name'].replace('ct0', 'ct1')
                ct1ports.append(p_copy)

            key = f'png/pure_fa_x_r{release}{rev}_back.png'
            if key not in config:
                config[key] = {}
            config[key]['ports'] = ct0ports + ct1ports

            key = f'png/pure_fa_c_r{release}{rev}_back.png'
            if key not in config:
                config[key] = {}
            config[key]['ports'] = ct0ports + ct1ports

            # E is the same as Xr4, 
            if release == 4:
                key = f'png/pure_fa_e_r1{rev}_back.png'
                if key not in config:
                    config[key] = {}
                config[key]['ports'] = ct0ports + ct1ports


        #################################
        ## FA Chassis Rear Ports for XL
        ######################

        ct0ports = [
            {'loc': (837, 685),
            'port_type': 'eth',
            'name': 'ct0.eth0',
            
            'port_connector': 'rj45',
            'port_speeds': ['1g'],
            
            'port_sfp_present': False,
            'port_sfp_speeds': [] ,
            'port_sfp_connector': None,
            'services': ['management']},

            {'loc': (955, 685),
            'port_type': 'eth',
            'name': 'ct0.eth1',            
            
            'port_connector': 'rj45',
            'port_speeds': ['1g'],
            
            'port_sfp_present': False,
            'port_sfp_speeds': [] ,
            'port_sfp_connector': None,
            'services': ['management']}]

        ct1ports = []
        for p in ct0ports:
            p_copy = p.copy()
            p_copy['loc'] = (p['loc'][0], p['loc'][1] + 478)
            p_copy['name'] = p_copy['name'].replace('ct0', 'ct1')
            ct1ports.append(p_copy)


        key = 'png/pure_fa_xl_r1_back.png'
        if key not in config:
            config[key] = {}
        config[key]['ports'] = ct0ports + ct1ports

    ##########################
    # NVME Shelf BAck
    ##########################

    ct0ports = [
        {'loc': (735, 315),
         'port_type': 'eth',
         'name': 'ct0.eth0',
         'port_connector': 'qsfp28',
        'port_speeds': ['50g', '100g'],
        'port_sfp_present': False,
        'port_sfp_speed': [] ,
        'port_sfp_connector': None,
        'services': ['shelf']
         },
        {'loc': (854, 315),
         'port_type': 'eth',
         'name': 'ct0.eth1',
         'port_speeds': ['50g', '100g'],
        'port_sfp_present': False,
        'port_sfp_speed': [] ,
        'port_sfp_connector': None,
        'services': ['shelf'],
        'port_connector': 'qsfp28'},
        {'loc': (976, 315),
         'port_type': 'eth',
         'name': 'ct0.eth2',
         'port_speeds': ['50g', '100g'],
        'port_sfp_present': False,
        'port_sfp_speed': [] ,
        'port_sfp_connector': None,
        'services': ['shelf'],
        'port_connector': 'qsfp28'},
        {'loc': (1090, 315),
         'port_type': 'eth',
         'name': 'ct0.eth3',
         'port_speeds': ['50g', '100g'],
        'port_sfp_present': False,
        'port_sfp_speed': [] ,
        'port_sfp_connector': None,
        'services': ['shelf'], 
        'port_connector': 'qsfp28'}]

    ct1ports = []
    for p in ct0ports:
        new_port = p.copy()
        new_port['loc'] = (p['loc'][0], p['loc'][1] + 380)
        new_port['name'] = p['name'].replace('ct0', 'ct1')
        ct1ports.append(new_port)

    key = 'png/pure_fa_nvme_shelf_back.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ct0ports + ct1ports


    #### PureFB Back #####

    ct0ports = [
        {'loc': (1362, 200),
         'port_type': 'eth',
         'name': 'fm0.eth1'},
        {'loc': (1362, 290),
         'port_type': 'eth',
         'name': 'fm0.eth2'},
        {'loc': (1482, 200),
         'port_type': 'eth',
         'name': 'fm0.eth3'},
        {'loc': (1482, 290),
         'port_type': 'eth',
         'name': 'fm0.eth4'},
        {'loc': (1326, 95),
         'port_type': 'eth',
         'name': 'mgmt'}]

    ct1ports = []
    for p in ct0ports:
        new_port = p.copy()
        new_port['loc'] = p['loc'][0], p['loc'][1] + 365
        new_port['name'] = p['name'].replace('fm0', 'fm1')
        ct1ports.append(new_port)

    key = 'png/pure_fb_back_efm310.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ct0ports + ct1ports

    ct0ports = [
        {'loc': (1362, 224),
         'port_type': 'eth',
         'name': 'fm0.eth1'},
        {'loc': (1362, 314),
         'port_type': 'eth',
         'name': 'fm0.eth2'},
        {'loc': (1482, 224),
         'port_type': 'eth',
         'name': 'fm0.eth3'},
        {'loc': (1482, 314),
         'port_type': 'eth',
         'name': 'fm0.eth4'}]

    ct1ports = []
    for p in ct0ports:
        new_port = p.copy()
        new_port['loc'] = p['loc'][0], p['loc'][1] + 370
        new_port['name'] = p['name'].replace('fm0', 'fm1')
        ct1ports.append(new_port)

    key = 'png/pure_fb_back_efm110.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ct0ports[0:5] + ct1ports[0:5]

    # Pure FB /S Back Ports

    ct0ports = [
        {'loc': (350, 420),
         'port_type': 'eth',
         'name': 'fm0.eth1',
         'port_connector': 'qsfp28',
         'port_speeds': ['10g', '25g', '40g', '100g'],
         'port_sfp_present': False,
         'port_sfp_speed': [] ,
         'port_sfp_connector': None,
         'services': ['data', 'replication', 'management'] 
        },
        {'loc': (463, 420),
         'port_type': 'eth',
         'name': 'fm0.eth2',
         'port_connector': 'qsfp28',
         'port_speeds': ['10g', '25g', '40g', '100g'],
         'port_sfp_present': False,
         'port_sfp_speed': [] ,
         'port_sfp_connector': None,
         'services': ['data', 'replication', 'management'] },
        {'loc': (572, 420),
         'port_type': 'eth',
         'name': 'fm0.eth3',
         'port_connector': 'qsfp28',
         'port_speeds': ['10g', '25g', '40g', '100g'],
         'port_sfp_present': False,
         'port_sfp_speed': [] ,
         'port_sfp_connector': None,
         'services': ['data', 'replication', 'management']},
        {'loc': (687, 420),
         'port_type': 'eth',
         'name': 'fm0.eth4',
         'port_connector': 'qsfp28',
         'port_speeds': ['10g', '25g', '40g', '100g'],
         'port_sfp_present': False,
         'port_sfp_speed': [] ,
         'port_sfp_connector': None,
         'services': ['data', 'replication', 'management']},
         {'loc': (1149, 363),
         'port_type': 'eth',
         'name': 'fm0.eth5',
         'port_connector': 'rj45',
         'port_speeds': ['1g'],
         'port_sfp_present': False,
         'port_sfp_speed': [] ,
         'port_sfp_connector': None,
         'services': ['management']}

         # Removing last 4 ports because they are ianctive from request of 
         # the Pure Advisor team.
         
#        {'loc': (1923, 420),
#         'port_type': 'eth',
#         'name': 'fm0.eth5'},
#        {'loc': (2029, 420),
#         'port_type': 'eth',
#         'name': 'fm0.eth6'},
#        {'loc': (2146, 420),
#         'port_type': 'eth',
#         'name': 'fm0.eth7'},
#        {'loc': (2256, 425),
#         'port_type': 'eth',
#         'name': 'fm0.eth8'},
#        {'loc': (1149, 364),
#         'port_type': 'eth',
#         'name': 'mgmt'}
    ]

    ct1ports = []
    for p in ct0ports:
        new_port = p.copy()
        new_port['loc'] = p['loc'][0], p['loc'][1] + 490
        new_port['name'] = p['name'].replace('fm0', 'fm1')
        ct1ports.append(new_port)

    key = 'png/pure_fbs_back.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ct0ports[0:9] + ct1ports[0:9]

    key = 'png/pure_fbe_back.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ct0ports[0:9] + ct1ports[0:9]
    
    # Pure FB /S Management Port


    # Pure FB BAck XFM

    start = (261, 95)
    y_offset = 90
    x1_offset = 111
    x2_offset = 253

    
    for xfm_model in ['3200e', '8400']:
        ports = []
        curr_loc = start
        for p in range(0, 32, 4):
            services = ['chassis uplink']
            if p > 19:
                services = ['data', 'replication', 'management']
            if p == 28:
                services = ['reserved']
            port_speeds = ['10g', '25g', '40g', '100g']
            if xfm_model == "8400":
                port_speeds.append('200g')
                port_speeds.append('400g')
        
            ports.append({'loc': curr_loc,
                        'port_type': 'eth',
                        'name': f'eth{p}',
                        'port_connector': 'qsfp28',
                        'port_speeds': port_speeds,
                        'port_sfp_present': False,
                        'port_sfp_speed': [] ,
                        'port_sfp_connector': None,
                        'services': services})
            ports.append({'loc': (curr_loc[0], curr_loc[1] + y_offset),
                        'port_type': 'eth',
                        'name': f'eth{p + 1}',
                        'port_connector': 'qsfp28',
                        'port_speeds': port_speeds,
                        'port_sfp_present': False,
                        'port_sfp_speed': [] ,
                        'port_sfp_connector': None,
                        'services': services})
            if p == 28:
                services = ['Cross Connect']
            ports.append({'loc': (curr_loc[0] + x1_offset, curr_loc[1] ),
                        'port_type': 'eth',
                        'name': f'eth{p + 2}',
                        'port_connector': 'qsfp28',
                        'port_speeds': port_speeds,
                        'port_sfp_present': False,
                        'port_sfp_speed': [] ,
                        'port_sfp_connector': None,
                        'services': services})
            ports.append({'loc': (curr_loc[0] + x1_offset, curr_loc[1] + y_offset),
                        'port_type': 'eth',
                        'name': f'eth{p + 3}',
                        'port_connector': 'qsfp28',
                        'port_speeds': port_speeds,
                        'port_sfp_present': False,
                        'port_sfp_speed': [] ,
                        'port_sfp_connector': None,
                        'services': services})
            curr_loc = (curr_loc[0] + x2_offset, curr_loc[1])
        mgmt_loc = (2423, 205)
        if xfm_model == '3200e':
            mgmt_loc = (2282, 178)
        ports.append({'loc': mgmt_loc,
                    'port_type': 'eth',
                    'name': 'mgmt',
                    'port_connector': 'rj45',
                    'port_speeds': ['1g'],
                    'port_sfp_present': False,
                    'port_sfp_speed': [] ,
                    'port_sfp_connector': None,
                    'services': ['management']})

        key = f'png/pure_fb_xfm_{xfm_model}_back.png'
        if key not in config:
            config[key] = {}
        config[key]['ports'] = ports


def update_static_mezz_port_loc(config):
    ports = [(80, 112), (184, 112), (292, 112), (396, 112)]
    key = 'png/pure_fa_x_emezz.png'
    port_type = 'eth'
    all_ports = []
    for p in ports:
        all_ports.append({
            'loc': p,
            'mezz': True, 

            'port_type': 'eth_roce',
            'port_connector': 'qsfp28',
            'port_speeds': ['50g'],
            'port_sfp_present': False,
            'port_sfp_speed': [] ,
            'port_sfp_connector': None,
            'services': ['shelf'] 
            })
    config[key] = {'ports': all_ports}

    ports = [(158, 110), (217, 110), (283, 110), (341, 110)]
    key = 'png/pure_fa_x_smezz.png'
    port_type = 'sas'
    all_ports = []
    for p in ports:
        all_ports.append({'loc': p, 
                          'port_type': port_type,
                          'mezz': True,
                          'services': ['shelf']})
    config[key] = {'ports': all_ports}


if __name__ == "__main__":
    main()
