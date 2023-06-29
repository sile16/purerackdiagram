from pprint import pprint
import logging
import base64
from multiprocessing import Pool
import hashlib
import io
import os
import lambdaentry
from purerackdiagram.utils import global_config
import purerackdiagram
import json
import traceback

logger = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

save_dir = 'test_results/'

# 38/38-31/63-127/0
# 0/38-0/45-0/45-0/63



more_tests = [
        {
        "queryStringParameters": {
            "model": "fb-s200",
            "no_of_blades": 30,
            "face": "back",
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
            "datapacks": "63/0",
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
            "addoncards": "sas,2fc,4fc,2eth,2ethbaset,2eth40,2fc,2fc,2fc",
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


def test_lambda():
    # Single test functions


    results = lambdaentry.handler(more_tests[0], None)

    if results['headers'].get("Content-Type") == 'image/png':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            with open('tmp.png', 'wb') as outfile:
                outfile.write(img_str)
            del results['body']
    elif results['headers'].get("Content-Type") == 'application/vnd.ms-visio.stencil':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            with open('stencil.vssx', 'wb') as outfile:
                outfile.write(img_str)
            del results['body']

    pprint(results)


def create_test_image(item, count, total):
    file_name = ""
    for n in ['model', 'addoncards', 'face', 'dp_label', 'fm_label', 'csize', 'datapacks', 
    'no_of_chassis', 'no_of_blades', 'drive_size', 'no_of_drives_per_blade' ]:
        if n in item:
            if n == 'datapacks':
                file_name += str(item[n]).replace('/', '-') + "_"
            else:
                file_name += str(item[n]) + "_"
    file_name += '.png'


    try:
        img = purerackdiagram.get_image_sync(item)
    
    except Exception as e:
        print(f"Caught exeption in image: {file_name} ")

        traceback.print_exc()
        print()
        raise e


    h = hashlib.sha256()
    with io.BytesIO() as memf:
        img.save(memf, 'PNG')
        data = memf.getvalue()
        h.update(data)
        img.save(os.path.join(save_dir, file_name))

        # result_q.put({file_name: h.hexdigest()})
        print(f"{count} of {total}   {file_name}")
        return({file_name: h.hexdigest()})


def get_all_tests():
    models = global_config['pci_config_lookup']
    dps = ['45/45-31/63-45', '3/127-24']

    # get the keys of diction csize_lookup
    csizes = list(global_config['csize_lookup'].keys())
    #global_config.csize_lookup
    #csizes = ['247', '296', '345', '366', '395', '492', '494', 
    #         '590', '688', '787', '839', 
    #         '879', '885', '984', '1182',
    #         '1185', '1329', '1390', '1476', '1531', '1574', 
    #         '1672', '1771', '1869', '1877', '1877']

    count = 0
    # front:
    for model in models:
        #continue
        model = model[:8]
        for dp_label in [True, False]:
            if 'c' in model:
                for csize in csizes:
                    count += 1
                    params = {"model": model,
                              "fm_label": True,
                              "dp_label": dp_label,
                              "csize": csize}
                    yield params
            else:
                for dp in dps:
                    # if count > 3:
                    #    break
                    count += 1
                    params = {"model": model,
                              "fm_label": True,
                              "dp_label": dp_label,
                              "datapacks": dp}

                    yield params

    # back:
    addon_cards = global_config['pci_valid_cards']

    for model in models:
        #continue
        model = model[:8]
        for card in addon_cards:
            if 'c' in model:
                for csize in csizes:
                    params = {"model": model,
                              "addoncards": card,
                              "face": "back",
                              "csize": csize}
                    yield params
            else:
                for dp in dps:
                    params = {"model": model,
                              "datapacks": dp,
                              "addoncards": card,
                              "face": "back"}
                    yield params

    for test in more_tests:
        continue
        yield test['queryStringParameters']

    for blades in [7, 10, 15, 30]:
        for dfms in [1, 2, 3, 4]:
            for size in [24.0, 48.2]:
                for face in ['front', 'back']:
                    params = {"model": "fb-s200",
                              "no_of_blades": blades,
                              "face": face,
                              "no_of_drives_per_blade": dfms,
                              "drive_size": size,
                              "ports": "TRUE"}
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
        json.dump(results, f)

    with open("test_validation.json") as f:
        validation = json.load(f)

    errors = 0
    warnings = 0
    for key in results:
        if key not in validation:
            warnings += 1
            print("WARNING missing key:{}".format(key))
        elif results[key] != validation[key]:
            errors += 1
            print("Error Image Changed!!:{}".format(key))
    print("Test Complete {} Errors Found {} Warning".format(errors, warnings))


def main(args):
    if args.testtype == 'all':
        test_all(args)
    else:
        test_lambda()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('testtype', choices=['all', 'lambda'], default='all',
                        nargs='?',
                        help="Test all options, or test through lamdba entry")
    parser.add_argument('-t', type=int, help="number of threads", default=8)
    main(parser.parse_args())
