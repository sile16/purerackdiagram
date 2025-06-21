
API_ENDPOINT = "https://61fuj0h54e.execute-api.us-east-1.amazonaws.com/default/rackdiagram?";
API_ENDPOINT_PROD = "https://61fuj0h54e.execute-api.us-east-1.amazonaws.com/default/rackdiagram?";
API_ENDPOINT_STAGING = "https://61fuj0h54e.execute-api.us-east-1.amazonaws.com/staging/rackdiagram-staging?";

// the options values for FlashArray configurations
//
var FA_OPTIONS = {
    model: ['X Arrays:', 'fa-x20r4b', 'fa-x50r4b', 'fa-x70r4b', 'fa-x90r4b',
                         'fa-x20r4', 'fa-x50r4', 'fa-x70r4', 'fa-x90r4',
                         'fa-x10r3', 'fa-x20r3', 'fa-x50r3', 'fa-x70r3', 'fa-x90r3',
                         'fa-x10r2', 'fa-x20r2', 'fa-x50r2', 'fa-x70r2', 'fa-x90r2',
                         'fa-x70r1',
            'XL Arrays:', 'fa-xl130r5','fa-xl170r5', 'fa-xl130r1', 'fa-xl170r1',
            'C Arrays:', 'fa-rc20', 'fa-c20', 'fa-c50r4b', 'fa-c70r4b', 'fa-c90r4b',
                         'fa-c50r4', 'fa-c70r4', 'fa-c90r4',
                         'fa-c40r3', 'fa-c60r3',
                         'fa-c40r1', 'fa-c60r1',
            'E Arrays:', 'fa-Er1b',
                         'fa-Er1',
            'M Arrays:', 'fa-m10r2', 'fa-m20r2', 'fa-m50r2', 'fa-m70r2'],
    protocol: ['fc', 'eth'],
    face: ['front', 'back'],
    datapacks: '63',
    csizes: ['Current Sizes:', '186', '223', '240', '260', '288', '297', '334', '366', 
              '372', '375', '384', '450', '480', '482',
              '578', '674', '771', '816','867', '964', '1154', '1300', '1446',
              '1488', '1542', '1638', '1735', '1824', '1831', '1928', '2120', '2313',
              'Legacy Sizes:', '247', '296', '345', '366', '395', '492', '494', 
             '590', '688', '787','839', 
             '879', '885', '984', '1182',
             '1185', '1329', '1390', '1476', '1531', '1574', 
             '1672', '1771', '1869', '1877'],
    bezel: ['', 'FALSE', 'TRUE'],
    direction: ['', 'up', 'down'],
    fm_label: ['', 'TRUE', 'FALSE'],
    dp_label: ['', 'FALSE', 'TRUE'],
    dc_power: ['', "TRUE", "1300", "2000"],
    addoncards: [ '2fc', '4fc', '2ethbaset', '2eth', '2eth25roce', '4eth25', '2eth40', '2eth100', '2eth100roce', 
                  'sas', 'dca', 'mgmt2ethbaset', 'blank','2eth200roce'],
    chassis_gen: ['', '1', '2'],
    mezz: ['', 'smezz', 'emezz'],
    ports: ['', 'FALSE', 'TRUE'],
    individual: ['', 'TRUE']
};


var FB_OPTIONS = {
    face: ['front', 'back'],
    chassis: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
    xfm: ['', 'FALSE', 'TRUE'],
    direction: ['up', 'down'],
    blades: '17:0-14,52:15-129',
    efm: ['', 'efm110', 'efm310'],
    ports: ['', 'FALSE', 'TRUE'],
    xfm_face: ['', 'front', 'back','bezel'],
    xfm_model: ['', '3200e', '8400'],
    individual: ['', 'TRUE']
};

var FBS_OPTIONS = {
    model: ['fb-s200r2', 'fb-s500r2', 'fb-s100r1', 'fb-er1', 'fb-s200r1', 'fb-s500r1', 'fb-er2', 'fb-e'],
    face: ['front', 'back'],
    xfm: ['', 'FALSE', 'TRUE'],
    direction: ['', 'up', 'down'],
    blades: '18',
    ports: ['', 'FALSE', 'TRUE'],
    dfm_size: ['24', '37.5', '48', '75', '150'],
    dfm_count: ['1', '2', '3', '4'],
    xfm_face: ['', 'front', 'back', 'bezel'],
    bezel: ['FALSE', 'TRUE'],
    xfm_model: ['', '3200e', '8400'],
    individual: ['', 'TRUE']
};
