
API_ENDPOINT = "https://61fuj0h54e.execute-api.us-east-1.amazonaws.com/default/rackdiagram?";
// API_ENDPOINT = "rackdiagram?"

// the options values for FlashArray configurations
//
var FA_OPTIONS = {
    model: ['fa-x10r3', 'fa-x20r3', 'fa-x50r3', 'fa-x70r3', 'fa-x90r3',
            'fa-x10r2', 'fa-x20r2', 'fa-x50r2', 'fa-x70r2', 'fa-x90r2',
            'fa-x70r1', 'fa-c40', 'fa-c60', 'fa-m10r2', 'fa-m20r2', 'fa-m50r2', 'fa-m70r2'],
    protocol: ['fc', 'eth'],
    face: ['front', 'back'],
    datapacks: '3/127-45/0',
    csizes: ['247', '345', '366', '494', '839', '879', '984', '1185', '1390', '1531', '1672', '1877'],
    bezel: ['FALSE', 'TRUE'],
    direction: ['up', 'down'],
    fm_label: ['TRUE', 'FALSE'],
    dp_label: ['FALSE', 'TRUE'],
    addoncards: ['4fc', '2fc', '2eth', '2eth40', 'sas', '2ethbaset'],
    mezz: ['', 'smezz', 'emezz']
};


var FB_OPTIONS = {
    face: ['front', 'back'],
    chassis: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
    xfm: ['', 'FALSE', 'TRUE'],
    direction: ['up', 'down'],
    blades: '17:0-14,52:15-129',
    efm: ['', 'efm110', 'efm310']
};
