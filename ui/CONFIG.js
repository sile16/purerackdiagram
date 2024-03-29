
API_ENDPOINT = "https://61fuj0h54e.execute-api.us-east-1.amazonaws.com/default/rackdiagram?";
// API_ENDPOINT = "rackdiagram?"

// the options values for FlashArray configurations
//
var FA_OPTIONS = {
    model: ['X Arrays:', 'fa-x20r4', 'fa-x50r4', 'fa-x70r4', 'fa-x90r4',
                         'fa-x10r3', 'fa-x20r3', 'fa-x50r3', 'fa-x70r3', 'fa-x90r3',
                         'fa-x10r2', 'fa-x20r2', 'fa-x50r2', 'fa-x70r2', 'fa-x90r2',
                         'fa-x70r1',
            'XL Arrays:', 'fa-xl130r1', 'fa-xl170r1',
            'C Arrays:', 'fa-c50r4', 'fa-c70r4', 'fa-c90r4',
                         'fa-c40r3', 'fa-c60r3',
                         'fa-c40r1', 'fa-c60r1',
            'E Arrays:', 'fa-Er1',
            'M Arrays:', 'fa-m10r2', 'fa-m20r2', 'fa-m50r2', 'fa-m70r2'],
    protocol: ['fc', 'eth'],
    face: ['front', 'back'],
    datapacks: '63',
    csizes: ['Current Sizes:', '240', '288', '366', '384', '480', '482',
              '578', '674', '771', '816','867', '964', '1154', '1300', '1446',
              '1488', '1542', '1638', '1735', '1824', '1831', '1928', '2120', '2313',
              'Legacy Sizes:', '247', '296', '345', '366', '395', '492', '494', 
             '590', '688', '787','839', 
             '879', '885', '984', '1182',
             '1185', '1329', '1390', '1476', '1531', '1574', 
             '1672', '1771', '1869', '1877'],
    bezel: ['FALSE', 'TRUE'],
    direction: ['up', 'down'],
    fm_label: ['TRUE', 'FALSE'],
    dp_label: ['FALSE', 'TRUE'],
    addoncards: [ '2fc', '4fc', '2ethbaset', '2eth', '2eth25roce', '4eth25', '2eth40', '2eth100', '2eth100roce', 
                  'sas', 'dca', 'mgmt2ethbaset', 'blank'],
    mezz: ['', 'smezz', 'emezz'],
    ports: ['FALSE', 'TRUE']
};


var FB_OPTIONS = {
    face: ['front', 'back'],
    chassis: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
    xfm: ['', 'FALSE', 'TRUE'],
    direction: ['up', 'down'],
    blades: '17:0-14,52:15-129',
    efm: ['', 'efm110', 'efm310'],
    ports: ['FALSE', 'TRUE'],
    xfm_face: ['', 'front', 'back']
};

var FBS_OPTIONS = {
    model: ['fb-s200', 'fb-s500', 'fb-e'],
    face: ['front', 'back'],
    xfm: ['', 'FALSE', 'TRUE'],
    direction: ['up', 'down'],
    blades: '18',
    ports: ['FALSE', 'TRUE'],
    dfm_size: ['24', '48', '75'],
    dfm_count: ['1', '2', '3', '4'],
    xfm_face: ['', 'front', 'back'],
    bezel: ['FALSE', 'TRUE']
};
