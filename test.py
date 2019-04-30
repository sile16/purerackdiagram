from pprint import pprint
import logging
import base64
import threading
import hashlib
import io
import queue
import os
import lambdaentry
from purerackdiagram.utils import global_config
import purerackdiagram
import asyncio
import json

logger = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

save_dir = 'test_results/'

#38/38-31/63-127/0
#0/38-0/45-0/45-0/63

def test_lambda():
    #local_delay puts a delay into build_img so they we can test the cache lookkup
    event1 = {
        "queryStringParameters": {
            "model": "fa-x70r1",
            "datapacks": "19.2/0-31/63-0/0",
            "chassis": 2,
            "addoncards":"4fc,4fc,2eth",
            "face":"back",
            "fm_label":True,
            "dp_label":True,
            "mezz":"emezz",
            "local_delay":0
        }
    }

    event2 = {
        "queryStringParameters": {
            "model": "fb",
            "chassis": 2,
            "face":"back",
            'direction':'up',
            'efm':"efm110",
            'local_delay':0,
            'blades': '17:0-6,52:23-29'
        }
    }

    event3 = {
        "queryStringParameters": {
            "model": "fa-x70r1",
            "protocol":"fc",
            "direction":"up",
            "datapacks": "91/91-45/45",
            "addoncards":"",
            "face":"back",
            "fm_label":"FALSE",
            "dp_label":"FALSE",
            "bezel":"FALSE",
            "local_delay":3
        }
    }

    results  = lambdaentry.handler(event2, None)

    if results['headers'].get("Content-Type") == 'image/png':
        if 'body' in results:
            img_str = base64.b64decode(results['body'].encode('utf-8'))
            with open('tmp.png', 'wb') as outfile:
                outfile.write(img_str)
            del results['body']
        

    pprint(results)



class TestWorker(threading.Thread):
    def __init__(self, q, results):
        threading.Thread.__init__(self)
        self.q = q
        self.results = results

    def run(self):
        #loop = asyncio.new_event_loop()
        #asyncio.set_event_loop(loop)

        while True:
            item = self.q.get()

            #diagram = purediagram.get_diagram(item)
            #img = loop.run_until_complete(diagram.get_image())
            if 'addoncards' in item:
                if item['addoncards'] == "2ethbaset":
                    a=2
            img = purerackdiagram.get_image_sync(item)

            name = ""
            for n in item.values():
                if isinstance(n, str):
                    n = n.replace("/",'-')
                name += str(n)+"_"
            name += '.png'
            
            h = hashlib.sha256()
            with io.BytesIO() as memf:
                img.save(memf,'PNG')
                data = memf.getvalue()
                h.update(data)
                img.save(os.path.join(save_dir,name))
        
                self.results[name] = h.hexdigest()
            self.q.task_done()



def test_all(args):
    models = global_config['pci_config_lookup']
    dps = ['45/45-31/63-45']

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    results = {}
    q = queue.Queue()
    for _ in range(args.t):
        t = TestWorker(q, results)
        t.setDaemon(True)
        t.start()

    count = 0
    ## front:
    for model in models:
        for dp_label in [True, False]:
            for dp in dps:
                #if count > 3:
                #    break
                count += 1
                model = model[:8]
                params = {"model":model, 
                            "fm_label":True, 
                            "dp_label": dp_label, 
                            "datapacks":dp}
                q.put(params)
                        
    
    #back:
    addon_cards = global_config['pci_valid_cards']

    for model in models:
        for card in addon_cards:
            for dp in dps:
                model = model[:8]
                params = {"model":model, 
                          "datapacks":dp,
                          "addoncards":card,
                          "face": "back"}
                q.put(params)

    
    q.join()
    
    with open("test_results.json","w") as f:
        json.dump(results, f)

    with open("test_validation.json") as f:
        validation = json.load(f)

    errors = 0
    for key in results:
        if key not in validation:
            errors += 1
            print("WARNING missing key:{}".format(key))
        elif results[key] != validation[key]:
            errors += 1
            print("Error Image Changed!!:{}".format(key))
    print("Test Complete {} Errors Found".format(errors))


def main(args):
    if args.testtype == 'all':
        test_all(args)
    else:
        test_lambda()
        

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('testtype', choices=['all', 'lambda'], default='lambda',
                        nargs='?', 
                        help="Test all options, or test through lamdba entry")
    parser.add_argument('-t',type=int, help="number of threads", default=1)
    main(parser.parse_args())
