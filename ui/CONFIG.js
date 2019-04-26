
API_ENDPOINT = "https://61fuj0h54e.execute-api.us-east-1.amazonaws.com/default/rackdiagram?"
// API_ENDPOINT = "rackdiagram?"

// the options values for FlashArray configurations
//
var FA_OPTIONS = {
    model: ['fa-m10r2','fa-m20r2','fa-m50r2','fa-m70r2', 'fa-x10r2','fa-x20r2','fa-x50r2','fa-x70r2', 'fa-x70r1'],
    protocol: ['fc', 'eth'],
    face: ['front', 'back'],
    datapacks: '91/91-45/45',
    bezel: ['FALSE', 'TRUE'],
    direction: ['up', 'down'],
    fm_label: ['FALSE', 'TRUE'],
    dp_label: ['FALSE', 'TRUE'],
    addoncards: ['4fc', '2fc', '2eth', '2eth40', 'sas', '2ethbaset'],
    mezz: ['', 'smezz', 'emezz']
};


var FB_OPTIONS = {
    face: ['front', 'back'],
    chassis: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
    xfm: ['','FALSE','TRUE'],
    direction: ['up', 'down']
}