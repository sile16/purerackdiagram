
$(function() {
  console.log( "ready!" );

  $('#option-tabs').tabs();

  var fa_option_model = build_select('#fa_option_model', FA_OPTIONS.model);
  var fa_option_protocol = build_select('#fa_option_protocol', FA_OPTIONS.protocol);
  var fa_option_face = build_select('#fa_option_face', FA_OPTIONS.face);
  var fa_option_datapacks = build_input('#fa_option_datapacks', FA_OPTIONS.datapacks);
  var fa_option_bezel = build_select('#fa_option_bezel', FA_OPTIONS.bezel);
  var fa_option_direction = build_select('#fa_option_direction', FA_OPTIONS.direction);
  var fa_option_fm_label = build_select('#fa_option_fm_label', FA_OPTIONS.fm_label);
  var fa_option_dp_label = build_select('#fa_option_dp_label', FA_OPTIONS.dp_label);
  var fa_option_addoncards = buile_multipleselect('#fa_option_addoncards', FA_OPTIONS.addoncards);

  var fb_option_face = build_select('#fb_option_face', FB_OPTIONS.face);
  var fb_option_direction = build_select('#fb_option_direction', FB_OPTIONS.direction);
  var fb_option_chassis = build_select('#fb_option_chassis', FB_OPTIONS.chassis);
  var fb_option_xfm = build_select('#fb_option_xfm', FB_OPTIONS.xfm);
  var fb_option_blades = build_input('#fb_option_blades', FB_OPTIONS.blades);
  var fb_option_efm = build_select('#fb_option_efm', FB_OPTIONS.efm);


  var fa_url = function(){
    // the function to generate the url for FA image based on options

    var url = API_ENDPOINT;
    url += "&model="  + fa_option_model.val();
    url += "&protocol="  + fa_option_protocol.val();
    url += "&face="  + fa_option_face.val();
    url += "&datapacks="  + fa_option_datapacks.val();
    url += "&bezel="  + fa_option_bezel.val();
    url += "&direction="  + fa_option_direction.val();
    url += "&fm_label="  + fa_option_fm_label.val();
    url += "&dp_label="  + fa_option_dp_label.val();
    url += "&addoncards="  + fa_option_addoncards.val();

    var mezz_val = fa_option_mezz.val();
    console.log(mezz_val);
    if (mezz_val) {
        url += "&mezz=" + fa_option_mezz.val();
    }

    return url;
  };


  var fb_url = function() {
    // the function to generate the url for FB image based on options

    var url = API_ENDPOINT;
    url += "&model=fb"; // it is fixed value, but reserved for future expension
    url += "&chassis="  + fb_option_chassis.val();
    url += "&face="  + fb_option_face.val();
    url += "&direction="  + fb_option_direction.val();
    url += "&xfm=" + fb_option_xfm.val();
    url += "&blades=" + fb_option_blades.val();
    url += "&efm=" + fb_option_efm.val();

    return url;
  }

  var fa_option_mezz = build_select('#fa_option_mezz', FA_OPTIONS.mezz);

  $("#display").click(function () {

    var active_tab_idx = $('#option-tabs').tabs( "option", "active" );
    console.log(active_tab_idx);

    if (active_tab_idx == 0) {
      url = fa_url();
    }
    else if (active_tab_idx == 1) {
      url = fb_url();
    }
    else {
      url = API_ENDPOINT + 'OE_WIP';
    }

    console.log(url);

    $('#rack_digram').attr('src', url);

    $('#img_url').html('<a target="_blank" href="' + url + '">' + url + '</a>');
  });
});