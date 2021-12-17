
import yaml

# Updates the config.yaml file with location information


def main():
    # args no arg unless we need to have this tool to more
    # Generate, the offsets programatically for slot locations for each chassis

    config = static_global_config()

    update_static_fm_loc(config)
    update_static_model_port_loc(config)

    for gen in ['m', 'x', 'c']:
        update_static_pci_loc(config, gen)
        update_static_mezz_loc(config, gen)
        update_static_model_loc(config, gen)
        update_static_nvram_loc(config, gen)

    for gen in ['xl']:
        update_static_pci_loc(config, gen)
        update_static_model_loc(config, gen)

    update_static_card_port_loc(config)
    update_static_mezz_port_loc(config)

    with open('purerackdiagram/config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def static_global_config():
    return {

        "pci_valid_cards": ["2eth", "2eth40", "2fc", "4fc", "sas", "2ethbaset"],

        "pci_config_lookup": {
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
            "fa-c60r1-eth": ["2eth", None, None, None],
            "fa-c60r1-fc": ["4fc", None, "2fc", None],
            "fa-xl130r1-eth": [None, "2eth", None, None, None, None, None, None, None],
            "fa-xl130r1-fc": [None, "4fc", None, None, None, None, None, None, "2fc"],
            "fa-xl170r1-eth": [None, "2eth", None, None, None, None, None, None, None],
            "fa-xl170r1-fc": [None, "4fc", None, None, None, None, None, None, "2fc"]

        },

        "chassis_dp_size_lookup": {
            "0": ["Blank", "blank", 10, "0"],
            "3": ["750GB", "scm", 4, "DM Cache 3"],
            "6": ["750GB", "scm", 8, "DM Cache 6"],
            "11": ["1.1TB", "nvme", 10, "11"],
            "22": ["2.2TB", "nvme", 10, "22"],
            "45": ["4.5TB", "nvme", 10, "45"],
            "63": ["4.5TB", "nvme", 14, "63"],
            "72": ["4.5TB", "nvme", 16, "72"],
            "91": ["9.1TB", "nvme", 10, "91"],
            "109": ["9.1TB", "nvme", 12, "109"],
            "126": ["4.5TB", "nvme", 24, "126"],
            "127": ["9.1TB", "nvme", 14, "127"],
            "145": ["9.1TB", "nvme", 16, "145"],
            "183": ["18.3TB", "nvme", 10, "183"],
            "219": ["18.3TB", "nvme", 12, "219"],
            "254": ["9.1TB", "nvme", 24, "254"],
            "256": ["18.3TB", "nvme", 14, "256"],
            "292": ["18.3TB", "nvme", 16, "292"],
            "247": ["24.7TB", "nvme-qlc", 10, "247"],
            "345": ["24.7TB", "nvme-qlc", 14, "345"],
            "366": ["18.3TB", "nvme-qlc", 20, "366"],
            "494": ["24.7TB", "nvme-qlc", 20, "494"],
            "512": ["18.3TB", "nvme", 24, "512"],
            "984": ["49.2TB", "nvme-qlc", 20, "984"],
            "4.8": ["480GB", "sas", 10, "4.8"],
            "5": ["500GB", "sas", 10, "5"],
            "9.6": ["960GB", "sas", 10, "9.6"],
            "10": ["1TB", "sas", 10, "10"],
            "19.2": ["1.9TB", "sas", 10, "19.2"],
            "20": ["2TB", "sas", 10, "20"],
            "38": ["3.8TB", "sas", 10, "38"],
            "76": ["7.6TB", "sas", 10, "76"]
        },

        "csize_lookup": {
            "247": "247",
            "345": "345",
            "366": "366",
            "494": "494",
            "839": "494-345",
            "879": "366-512",
            "984": "984",
            "1185": "494-345/345",
            "1390": "366-512-512",
            "1531": "494-345/345-345",
            "1672": "984-688",
            "1877": "494-345/345-345/345"
        },

        "shelf_dp_size_lookup": {
            "0": ["Blank", "blank", 12, "0"],
            "15": ["1.1TB", "nvme", 14, "15"],
            "31": ["2.2TB", "nvme", 14, "31"],
            "63": ["4.5TB", "nvme", 14, "63"],
            "127": ["9.1TB", "nvme", 14, "127"],
            "256": ["18.3TB", "nvme", 14, "256"],
            "345": ["24.7TB", "nvme-qlc", 14, "345"],
            "688": ["49.2TB", "nvme-qlc", 14, "688"],
            "512": ["18.3TB", "nvme-qlc", 28, "512"],
            "6": ["256GB", "sas", 24, "6"],
            "11": ["960GB", "sas", 12, "11"],
            "12": ["512GB", "sas", 24, "12"],
            "22": ["1.9TB", "sas", 12, "22"],
            "24": ["1TB", "sas", 24, "24"],
            "45": ["3.8TB", "sas", 12, "45"],
            "90": ["7.6TB", "sas", 12, "90"]
        },

        "fb_blade_reg_pattern": "^([0-9]+:[0-9]+(-[0-9]+)?,?)+$"
    }


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
    key = 'png/pure_fa_x_front.png'
    if key not in config:
        config[key] = {}
    config[key]['fm_loc'] = ch0_fm_loc.copy()

    # C is the same:
    key = 'png/pure_fa_c_front.png'
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

    key = 'png/pure_fa_m_front.png'
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
    
    key = 'png/pure_fa_xl_front.png'
    if key not in config:
        config[key] = {}
    config[key]['fm_loc']= ch0_fm_loc.copy()





def update_static_pci_loc(config, generation):
    pci_loc = None
    if generation == 'x' or generation == 'c':
        pci_loc = [(1198, 87), (1198, 203), (2069, 87), (2069, 203)]
        ct1_y_offset = 378

    elif generation == 'm':
        pci_loc = [(1317, 87), (1317, 201), (2182, 87), (2182, 201)]
        ct1_y_offset = 378

    elif generation == 'xl':
        pci_loc = [(325, 373), (325, 497), 
                   (893, 373), (893, 497),
                   (1626, 373),(1626, 497),
                   (2179, 373), (2179, 497), (2179, 615)]
        ct1_y_offset = 497


    key = f'png/pure_fa_{generation}_back.png'
    if key not in config:
        config[key] = {}

    config[key]['ct0_pci_loc'] = pci_loc.copy()

    ## Now calculate all the pci slot locations for ct1
    for i in range(len(pci_loc)):
        # add a y_offset to calculate the ct0 coordinates
        cord = pci_loc[i]
        pci_loc[i] = (cord[0], cord[1] + ct1_y_offset)

    
    config[key]['ct1_pci_loc'] = pci_loc.copy()

    

    


def update_static_nvram_loc(config, generation):
    key = f'png/pure_fa_{generation}_front.png'
    if key not in config:
        config[key] = {}

    if generation == 'x' or \
            generation == 'c':
        nv1 = (1263, 28)
        nv2 = (1813, 28)
    elif generation != "xl":
        nv1 = (1255, 20)
        nv2 = (1805, 20)

    config[key]['nvram_loc'] = [nv1, nv2].copy()

    return config


def update_static_mezz_loc(config, generation):
    key = f'png/pure_fa_{generation}_back.png'
    if key not in config:
        config[key] = {}

    if generation == 'x' or \
            generation == 'c':
        config[key]['ct0_mezz_loc'] = (585, 45)
        config[key]['ct1_mezz_loc'] = (585, 425)
    else:
        config[key]['ct0_mezz_loc'] = (709, 44)
        config[key]['ct1_mezz_loc'] = (709, 421)
    


def update_static_model_loc(config, generation):
    key = f'png/pure_fa_{generation}_front.png'
    if key not in config:
        config[key] = {}

    if generation == 'x' or \
            generation == 'c':
        loc = (2759, 83)
    elif generation == 'xl':
        loc = (22, 330)
    else:
        loc = (2745, 120)

    config[key]['model_text_loc'] = loc

def add_ports_to_key(ports_loc, key, port_type, config):
    ports = []
    for ploc in ports_loc:
        ports.append({'loc': ploc, 'port_type': port_type})
    config[key] = {'ports': ports}


def update_static_card_port_loc(config):
    # calculate the port location based on the offset. 

    
    ports_loc = [(158, 40), (256, 40)]
    keys = [['png/pure_fa_2ethbaset_fh.png', 'eth'],
            ['png/pure_fa_2ethbaset_hh.png', 'eth'],
            ['png/pure_fa_2eth_hh.png', 'eth'],
            ['png/pure_fa_2fc_fh.png', 'fc'],
            ['png/pure_fa_2fc_hh.png', 'fc']]

    for k in keys:
        add_ports_to_key(ports_loc, k[0], k[1], config)

    ports_loc = [(210, 40), (410, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_2eth40_fh.png', 'eth', config)

    ports_loc = [(70, 40), (245, 40) ]
    add_ports_to_key(ports_loc, 'png/pure_fa_2eth40_hh.png', 'eth', config)

    ports_loc = [(252, 40), (343, 40), (432, 40), (524, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_4fc_fh.png', 'fc', config)

    ports_loc = [(48, 40), (138, 40), (230, 40), (322, 40)]
    add_ports_to_key(ports_loc, 'png/pure_fa_4fc_hh.png', 'fc', config)

    # close enough, todo make better? 
    add_ports_to_key(ports_loc, 'png/pure_fa_sas_hh.png', 'sas', config)



def update_static_model_port_loc(config):

    ## adding the LOM  port locations

    #################################
    ## FA Chassis Flash Modules for M / X / C
    ######################


    # These are all the ct0 ports
    ct0ports = [
        {'loc': (671, 316),
         'port_type': 'eth',
         'name': 'ct0.eht0'},
        {'loc': (788, 316),
         'port_type': 'eth',
         'name': 'ct0.eht1'},
        {'loc': (1880, 221),
         'port_type': 'eth',
         'name': 'ct0.eht2'},
        {'loc': (1880, 293),
         'port_type': 'eth',
         'name': 'ct0.eth3'},
        {'loc': (1965, 221),
         'port_type': 'eth',
         'name': 'ct0.eth4'},
        {'loc': (1965, 293),
         'port_type': 'eth',
         'name': 'ct0.eth5'}]

    ct1ports = []
    for p in ct0ports:
        loc = (p['loc'][0], p['loc'][1] + 380)
        name = p['name'].replace('ct0', 'ct1')
        ct1ports.append({'loc': loc, 'name': name, 'port_type': 'eth'})

    key = 'png/pure_fa_x_back.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ct0ports + ct1ports

    key = 'png/pure_fa_c_back.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ct0ports + ct1ports

    ##########################
    # NVME Shelf BAck
    ##########################

    ct0ports = [
        {'loc': (735, 315),
         'port_type': 'eth',
         'name': 'ct0.eht0'},
        {'loc': (854, 315),
         'port_type': 'eth',
         'name': 'ct0.eht1'},
        {'loc': (976, 315),
         'port_type': 'eth',
         'name': 'ct0.eht2'},
        {'loc': (1090, 315),
         'port_type': 'eth',
         'name': 'ct0.eth3'},
        {'loc': (2009, 318),
         'port_type': 'eth',
         'name': 'ct0.eth4'}]

    ct1ports = []
    for p in ct0ports:
        loc = (p['loc'][0], p['loc'][1] + 380)
        name = p['name'].replace('ct0', 'ct1')
        ct1ports.append({'loc': loc, 'name': name, 'port_type': 'eth'})

    key = 'png/pure_fa_nvme_shelf_back.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ct0ports + ct1ports


    #################################
    ## FA Chassis Flash Modules for XL
    ######################

    ct0ports = [
        {'loc': (846, 704),
         'port_type': 'eth',
         'name': 'ct0.eht0'},
        {'loc': (964, 704),
         'port_type': 'eth',
         'name': 'ct0.eht1'}]

    ct1ports = []
    for p in ct0ports:
        loc = (p['loc'][0], p['loc'][1] + 493)
        name = p['name'].replace('ct0', 'ct1')
        ct1ports.append({'loc': loc, 'name': name, 'port_type': 'eth'})


    key = 'png/pure_fa_xl_back.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ct0ports + ct1ports



    #### PureFB Back #####

    ct0ports = [
        {'loc': (1362, 200),
         'port_type': 'eth',
         'name': 'fm0.eht1'},
        {'loc': (1362, 290),
         'port_type': 'eth',
         'name': 'fm0.eht2'},
        {'loc': (1482, 200),
         'port_type': 'eth',
         'name': 'fm0.eht3'},
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
    config[key]['ports'] = ct0ports[0:4] + ct1ports[0:4]

    # Pure FB BAck XFM

    start = (344, 99)
    y_offset = 102
    x1_offset = 120
    x2_offset = 267

    ports = []
    curr_loc = start
    for p in range(0, 32, 4):
        ports.append({'loc': curr_loc,
                      'port_type': 'eth',
                      'name': f'eth{p}'})
        ports.append({'loc': (curr_loc[0], curr_loc[1] + y_offset),
                      'port_type': 'eth',
                      'name': f'eth{p + 1}'})
        ports.append({'loc': (curr_loc[0] + x1_offset, curr_loc[1] ),
                      'port_type': 'eth',
                      'name': f'eth{p + 2}'})
        ports.append({'loc': (curr_loc[0] + x1_offset, curr_loc[1] + y_offset),
                      'port_type': 'eth',
                      'name': f'eth{p + 3}'})
        curr_loc = (curr_loc[0] + x2_offset, curr_loc[1])
    ports.append({'loc': (2455, 103),
                  'port_type': 'eth',
                  'name': 'mgmt'})

    key = 'png/pure_fb_xfm_back.png'
    if key not in config:
        config[key] = {}
    config[key]['ports'] = ports


def update_static_mezz_port_loc(config):
    ports = [(80, 112), (184, 112), (292, 112), (396, 112)]
    key = 'png/pure_fa_x_emezz.png'
    port_type = 'nvme'
    all_ports = []
    for p in ports:
        all_ports.append({'loc': p, 'port_type': port_type})
    config[key] = {'ports': all_ports}

    ports = [(158, 110), (217, 110), (283, 110), (341, 110)]
    key = 'png/pure_fa_x_smezz.png'
    port_type = 'sas'
    all_ports = []
    for p in ports:
        all_ports.append({'loc': p, 'port_type': port_type})
    config[key] = {'ports': all_ports}


if __name__ == "__main__":
    main()
