
import json
import yaml

# Updates the config.json file with location information


def update_static_fm_loc(config):

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
        if ch0_fm_loc[x] is None: #skips anchor locations
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


def update_static_pci_loc(config, generation):
    pci_loc = None
    if generation == 'x' or generation == 'c':
        pci_loc = [(1198, 87), (1198, 203), (2069, 87), (2069, 203)]
    elif generation == 'm':
        pci_loc = [(1317, 87), (1317, 201), (2182, 87), (2182, 201)]

    key = f'png/pure_fa_{generation}_back.png'
    if key not in config:
        config[key] = {}

    config[key]['ct1_pci_loc'] = pci_loc.copy()

    ct1_y_offset = 378
    for i in range(4):
        # add a y_offset to calculate the ct0 coordinates
        cord = pci_loc[i]
        pci_loc[i] = (cord[0], cord[1] + ct1_y_offset)

    config[key]['ct0_pci_loc'] = pci_loc.copy()


def update_static_nvram_loc(config, generation):
    key = f'png/pure_fa_{generation}_front.png'
    if key not in config:
        config[key] = {}

    if generation == 'x' or \
            generation == 'c':
        nv1 = (1263, 28)
        nv2 = (1813, 28)
    else:
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
    else:
        loc = (2745, 120)

    config[key]['model_text_loc'] = loc


def main():
    # args no arg unless we need to have this tool to more
    # Generate, the offsets programatically for slot locations for each chassis
    with open('purerackdiagram/config.json') as f:
        config = json.load(f)

    update_static_fm_loc(config)
    for gen in ['m', 'x', 'c']:
        update_static_pci_loc(config, gen)
        update_static_mezz_loc(config, gen)
        update_static_model_loc(config, gen)
        update_static_nvram_loc(config, gen)

    # save config file
    with open('purerackdiagram/config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))

    with open('purerackdiagram/config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


if __name__ == "__main__":
    main()
