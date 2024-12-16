
//global variable to store the vssx_url
var vssx_url = "";

// Function to update API endpoint based on radio button selection
function updateApiEndpoint() {
  const selectedEnvironment = document.querySelector('input[name="api-environment"]:checked').value;
  if (selectedEnvironment === 'prod') {
    API_ENDPOINT = API_ENDPOINT_PROD;
  } else if (selectedEnvironment === 'staging') {
    API_ENDPOINT = API_ENDPOINT_STAGING;
  }
}




const pythonTupleType = new jsyaml.Type('tag:yaml.org,2002:python/tuple', {
  kind: 'sequence',
  construct: function (data) {
    return data; // Treat tuples as arrays in JavaScript
  },
});

const customSchema = jsyaml.DEFAULT_SCHEMA.extend([pythonTupleType]);


$(function () {
  console.log("ready!");
    // Event listener for radio button change
  document.querySelectorAll('input[name="api-environment"]').forEach(radio => {
    radio.addEventListener('change', updateApiEndpoint);
  });

  fetch("config.yaml")
  .then((response) => response.text())
  .then((yamlText) => {

    try {
      const data = jsyaml.load(yamlText, { schema: customSchema });

      console.log('Loaded data:', data); // Log the loaded data

      // Populate the chart with the data from the YAML file
      const categories = ["nvme", "scm", "nvme-qlc", "sas", "blank"];

      const sortTable = (table, columnIndex, order) => {
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        const sortedRows = rows.sort((a, b) => {
          const aValue = parseFloat(a.children[columnIndex].textContent);
          const bValue = parseFloat(b.children[columnIndex].textContent);
      
          if (isNaN(aValue) || isNaN(bValue)) {
            return 0;
          }
      
          return order === 'asc' ? aValue - bValue : bValue - aValue;
        });
        table.querySelector('tbody').innerHTML = sortedRows.map(row => row.outerHTML).join('');
      };

      const createTable = (lookupList) => {
        if (!lookupList || lookupList.length === 0) {
          return ''; // Return an empty string if lookupData is null, undefined, or empty
        }
        let tableHtml = `
          <table class="table-responsive">
            <thead>
              <tr>
                <th class="sortable">DP Size TB<span class="sort-arrow">&nbsp;</span></th>
                <th class="sortable">Module Count <span class="sort-arrow">&nbsp;</span></th>
                <th class="sortable">Module Size <span class="sort-arrow">&nbsp;</span></th>
                <th class="sortable">DP Label <span class="sort-arrow">&nbsp;</span></th>
              </tr>
            </thead>
            <tbody>
        `;

        lookupList.forEach(item => {
          if (categories.includes(item[1])) {
            tableHtml += `
              <tr>
                <td>${item[4]}</td> <!-- Key is now the last element in the array -->
                <td>${item[2]}</td>
                <td>${item[0]}</td>
                <td>${item[3]}</td>
              </tr>
            `;
          }
        });

        tableHtml += `
            </tbody>
          </table>
        `;
        return tableHtml;
      };

      let activeTabIndex = -1;

      const createSubTabs = (lookupList, parentId) => {

        subTabsHtml = `<div id="${parentId}-dp-tabs">`;
        subTabsHtml += '<ul>';
        subTabContentHtml = '';

        /// Iterate through the categories
        categories.forEach((category) => {
          subTabsHtml += `<li><a href="#${parentId}-${category}">${category}</a></li>`;

          // Filter the list to include only the desired category
          const filteredList = lookupList.filter(item => item[1] === category);

          // Create the content Divs for each tab
          subTabContentHtml += `
            <div id="${parentId}-${category}">
              ${createTable(filteredList)}
            </div>
          `;
        });

        //end the list
        subTabsHtml += '</ul>';
        subTabContentHtml += '</div>';

        return subTabsHtml + subTabContentHtml;
      };

      
      // Function to convert dictionary objects into lists of arrays
      const convertDictToList = (dict) => {
        return Object.entries(dict).map(([key, value]) => [...value, key]);
      };

      // Converting dictionary objects into lists of arrays
      const chassisList = convertDictToList(data.chassis_dp_size_lookup);
      const shelfList = convertDictToList(data.shelf_dp_size_lookup);
      const qlcChassisList = convertDictToList(data.qlc_chassis_dp_size_lookup);
      const qlcShelfList = convertDictToList(data.qlc_shelf_dp_size_lookup);

      // Merging lists
      const mergedChassisList = chassisList.concat(qlcChassisList);
      const mergedShelfList = shelfList.concat(qlcShelfList);

      
      document.querySelector("#chassis-dp").innerHTML = createSubTabs(mergedChassisList, 'chassis');
      //document.querySelector("#chassis-dp").innerHTML = createSubTabs(, 'chassis');
      document.querySelector("#shelf-dp").innerHTML = createSubTabs(mergedShelfList, 'shelf');
      //document.querySelector("#shelf-dp").innerHTML = createSubTabs(qlcShelfLookupData, 'shelf');
      $("#chassis-dp-tabs").tabs();
      $("#shelf-dp-tabs").tabs();

      // Event delegation for sorting table headers
      document.addEventListener("click", (event) => {
        const header = event.target.closest(".sortable");
        if (!header) return;

        const columnIndex = Array.prototype.indexOf.call(header.parentNode.children, header);
        let sortOrder = header.getAttribute("data-sort-order") || "asc";
        sortOrder = sortOrder === "asc" ? "desc" : "asc";
        header.setAttribute("data-sort-order", sortOrder);

        const table = header.closest("table");
        sortTable(table, columnIndex, sortOrder);

        // Remove arrows from other headers in the same table
        table.querySelectorAll("th").forEach((th) => {
          if (th !== header) {
            const arrowSpan = th.querySelector(".sort-arrow");
            if (arrowSpan) {
              arrowSpan.innerHTML = "&nbsp;";
            }
          }
        });

        // Update the arrow direction for the clicked header
        const arrow = sortOrder === "asc" ? "&uarr;" : "&darr;";
        const arrowSpan = header.querySelector(".sort-arrow");
        if (arrowSpan) {
          arrowSpan.innerHTML = arrow;
        } else {
          const newArrowSpan = document.createElement("span");
          newArrowSpan.className = "sort-arrow";
          newArrowSpan.innerHTML = arrow;
          header.appendChild(newArrowSpan);
        }
      });

    } catch (error) {
      console.error('Error loading YAML data:', error);
    }
  });

  $('#option-tabs').tabs();
  $('#datapack-tabs').tabs();
  $('#chassis-dp-tabs').tabs();
  $('#shelf-dp-tabs').tabs();

  var fa_option_model = build_select('#fa_option_model', FA_OPTIONS.model);
  
  // set selected option for fa_option_model to x20r4
  fa_option_model.val('fa-x20r4b');

  var fa_option_protocol = build_select('#fa_option_protocol', FA_OPTIONS.protocol);
  var fa_option_face = build_select('#fa_option_face', FA_OPTIONS.face);
  var fa_option_datapacks = build_input('#fa_option_datapacks', "366");
  var fa_option_csize = build_select('#fa_option_csize', FA_OPTIONS.csizes);
  var fa_option_bezel = build_select('#fa_option_bezel', FA_OPTIONS.bezel);
  var fa_option_direction = build_select('#fa_option_direction', FA_OPTIONS.direction);
  var fa_option_fm_label = build_select('#fa_option_fm_label', FA_OPTIONS.fm_label);
  var fa_option_dp_label = build_select('#fa_option_dp_label', FA_OPTIONS.dp_label);
  var fa_option_addoncards = build_input('#fa_option_addoncards', "");
  var fa_option_ports = build_select('#fa_option_ports', FA_OPTIONS.ports);
  var fa_option_mezz = build_select('#fa_option_mezz', FA_OPTIONS.mezz);
  var fa_option_dc_power = build_select('#fa_option_dc_power', FA_OPTIONS.dc_power);
  var fa_option_individual = build_select('#fa_option_individual', FA_OPTIONS.individual);
  
  var fa_option_pci = [];

  //loop through pci_select_0 - 8 to build the select options:
  // createa an array of results of build_select
  for (var i = 0; i < 9; i++) {
    var pci_select = "#pci_select_" + i;
    fa_option_pci[i] = build_select(pci_select,  FA_OPTIONS.addoncards);
    
     // Add a blank option as the default for each select element and set it as selected
  fa_option_pci[i].prepend($("<option>").attr({'value': '', 'selected': 'selected'}).text(''));
  }
  
  fa_option_addoncards.prop("readonly",true);
  $(".addon_card").click( function(event){
    cardvalue = $(this).attr('id');
    curr_val = fa_option_addoncards.val();
    if (curr_val == ""){
      fa_option_addoncards.val(cardvalue);
    }
    else {
      fa_option_addoncards.val(curr_val + "," + cardvalue);
    }
  
  });

  fa_option_addoncards.attr;

  var fb_option_face = build_select('#fb_option_face', FB_OPTIONS.face);
  var fb_option_direction = build_select('#fb_option_direction', FB_OPTIONS.direction);
  var fb_option_chassis = build_select('#fb_option_chassis', FB_OPTIONS.chassis);
  var fb_option_xfm = build_select('#fb_option_xfm', FB_OPTIONS.xfm);
  var fb_option_blades = build_input('#fb_option_blades', FB_OPTIONS.blades);
  var fb_option_efm = build_select('#fb_option_efm', FB_OPTIONS.efm);
  var fb_option_ports = build_select('#fb_option_ports', FB_OPTIONS.ports);
  var fb_option_xfm_face = build_select('#fb_option_xfm_face', FB_OPTIONS.xfm_face);
  var fb_option_xfm_model = build_select('#fb_option_xfm_model', FB_OPTIONS.xfm_model);
  var fb_option_individual = build_select('#fb_option_individual', FB_OPTIONS.individual);
  

  var fbs_option_model = build_select('#fbs_option_model', FBS_OPTIONS.model);
  var fbs_option_dfm_size = build_select('#fbs_option_dfm_size', FBS_OPTIONS.dfm_size);
  var fbs_option_dfm_count = build_select('#fbs_option_dfm_count', FBS_OPTIONS.dfm_count);
  var fbs_option_face = build_select('#fbs_option_face', FBS_OPTIONS.face);
  var fbs_option_direction = build_select('#fbs_option_direction', FBS_OPTIONS.direction);
  var fbs_option_xfm = build_select('#fbs_option_xfm', FBS_OPTIONS.xfm);
  var fbs_option_blades = build_input('#fbs_option_blades', FBS_OPTIONS.blades);
  var fbs_option_ports = build_select('#fbs_option_ports', FBS_OPTIONS.ports);
  var fbs_option_xfm_face = build_select('#fbs_option_xfm_face', FBS_OPTIONS.xfm_face);
  var fbs_option_xfm_model = build_select('#fbs_option_xfm_model', FBS_OPTIONS.xfm_model);
  var fbs_option_bezel = build_select('#fbs_option_bezel', FBS_OPTIONS.bezel);
  var fbs_option_individual = build_select('#fbs_option_individual', FBS_OPTIONS.individual);
  




  var fa_url = function(){
    // the function to generate the url for FA image based on options

    var url = API_ENDPOINT;
    url += "model="  + fa_option_model.val();
    url += "&protocol="  + fa_option_protocol.val();
    url += "&face="  + fa_option_face.val();
    url += "&datapacks="  + fa_option_datapacks.val();
    if(fa_option_bezel.val()){
      url += "&bezel="  + fa_option_bezel.val();
    }
    if(fa_option_direction.val()){
      url += "&direction="  + fa_option_direction.val();
    }
    if(fa_option_fm_label.val()){
      url += "&fm_label="  + fa_option_fm_label.val();
    }
    if(fa_option_dp_label.val()){
      url += "&dp_label="  + fa_option_dp_label.val();
    }

    if(fa_option_dc_power.val()){
      url += "&dc_power="  + fa_option_dc_power.val();
    }


    if(fa_option_addoncards.val()){
      url += "&addoncards="  + fa_option_addoncards.val();
    }
    if (fa_option_csize.val() !== "Current Sizes:") {
      url += "&csize=" + fa_option_csize.val();
    }
    for (var i = 0; i < fa_option_pci.length; i++) {
      var x = fa_option_pci[i];
      if (x.val() !== "") {
        url += "&pci" + i + "=" + x.val();
      }
    }
    
    var  ports_val = fa_option_ports.val();
    if (ports_val){
      url += "&ports=" + ports_val;
    }

    var mezz_val = fa_option_mezz.val();
    if (mezz_val) {
        url += "&mezz=" + fa_option_mezz.val();
    }

    if (fa_option_individual.val() != ''){
      url += "&individual";
    }

    return url;
  };




  var fb_url = function() {
    // the function to generate the url for FB image based on options

    var url = API_ENDPOINT;
    url += "model=fb"; // it is fixed value, but reserved for future expension
    url += "&chassis="  + fb_option_chassis.val();
    url += "&face="  + fb_option_face.val();
    url += "&blades=" + fb_option_blades.val();
    
    if(fb_option_direction.val()){
      url += "&direction="  + fb_option_direction.val();
    }
    if(fb_option_xfm.val()){
      url += "&xfm=" + fb_option_xfm.val();
    }

    if(fb_option_efm.val()){
      url += "&efm=" + fb_option_efm.val();
    }
    if(fb_option_xfm_face.val()) {
      url += "&xfm_face=" + fb_option_xfm_face.val();
    }

    if (fb_option_ports.val()){
      url += "&ports=" + fb_option_ports.val();
    }

    if (fb_option_xfm_model.val()){
      url += "&xfm_model=" + fb_option_xfm_model.val();
    }

    if (fb_option_individual.val() != ''){
      url += "&individual";
    }

    return url;
  };

  var fbs_url = function() {
    // the function to generate the url for FB image based on options

    var url = API_ENDPOINT;
    url += "model="  + fbs_option_model.val();
    url += "&face="  + fbs_option_face.val();
    
    url += "&no_of_blades=" + fbs_option_blades.val();
    url += "&no_of_drives_per_blade=" + fbs_option_dfm_count.val();
    url += "&drive_size=" + fbs_option_dfm_size.val();
    
    if(fbs_option_direction.val()){
      url += "&direction="  + fbs_option_direction.val();
    }
    if(fbs_option_xfm.val()){
      url += "&xfm=" + fbs_option_xfm.val();
    }
    if(fbs_option_xfm_face.val()){
      url += "&xfm_face=" + fbs_option_xfm_face.val();
    }

    if(fbs_option_bezel.val()){
      url += "&bezel=" + fbs_option_bezel.val();
    }

    var ports_val = fbs_option_ports.val();
    if (ports_val){
      url += "&ports=" + ports_val;
    }

    if (fbs_option_xfm_model.val()){
      url += "&xfm_model=" + fbs_option_xfm_model.val();
    }

    if (fbs_option_individual.val() != ''){
      url += "&individual";
    }

    return url;
  };

  function createTooltipContent(port) {
    const descriptions = {
      name: "Name",
      pci_card: "PCI Card",
      pci_slot: "PCI Slot",
      pci_slot_height: "PCI Slot Height",
      default_card: "Default Card",
      port_type: "Port Type",
      services: "Services",
      port_connector: "Port Connector",
      port_speeds: "Port Speeds",
      port_sfp_present: "Port SFP Present",
      port_sfp_connector: "Port SFP Connector",
      port_sfp_speed: "Port SFP Speed",
      
      //controller: "Controller",
      symbol_name: "Symbol Name",
      //symbol_shape: "Symbol Shape",
      //symbol_color: "Symbol Color"
      // Add any additional fields as needed
    };
  
    let content = "";
  
    for (const key in descriptions) {
      if (port.hasOwnProperty(key) && port[key] != null) {
        let value = port[key];
  
        // Format array values
        if (Array.isArray(value)) {
          value = value.join(", ");
        }
  
        // Format boolean values
        if (typeof value === "boolean") {
          value = value ? "Yes" : "No";
        }
  
        content += `${descriptions[key]}: ${value}\n`;
      }
    }
  
    return content;
  }

  async function get_url() {
    var active_tab_idx = $('#option-tabs').tabs( "option", "active" );
    console.log(active_tab_idx);

    if (active_tab_idx == 0) {
      url = fa_url();
    }
    else if (active_tab_idx == 1) {
      url = fb_url();
    }
    else if (active_tab_idx == 2){
      url = fbs_url();
    };
    
    //set the global variable vssx_url
    vssx_url = url + "&vssx=True";
    visio_url = url + "&vssx=True";
    
    $('#img_url').html('<a target="_blank" href="' + url + '">' + url + '</a>');
    $('#visio_url').html('<a target="_blank" href="' + visio_url + '">' + visio_url + '</a>');

    url_wo_individual = url.replace("&individual","") + "&json=True";
    const response = await fetch(url_wo_individual);
    var diagram = await response.json();

    if ( diagram.error ) {
      $('#rack_diagram').attr('src', "").hide();
      $('#error_msg').text(diagram.error);
      $("#error-div").show();

    } else {
      $('#error_msg').text("");
      $("#error-div").hide();

      var image_src_url = null;

      if ( diagram.image_type == "png" ) {
        const img_base64encoded = await fetch(`data:image/png;base64,${diagram.image}`);
        const blob = await img_base64encoded.blob();
        image_src_url = await URL.createObjectURL(blob);

        delete diagram.image;
      } else if (diagram.image_type == "link") {
        image_src_url = diagram.image;
      } else {
        console.log("Unknown image type");
        //exit the function
        return;
      }
      
      
      // Set the src and wait for the image to load
      $('#rack_diagram').off('load').on('load', function() {
        var parentElement = $('#rack_diagram_wrapper');

          // Remove existing tooltips
        $('.port-tooltip').remove();



        // Get the natural and displayed size of the image
        var naturalWidth = this.naturalWidth;
        var naturalHeight = this.naturalHeight;
        var displayedWidth = $(this).width();
        var displayedHeight = $(this).height();

        // Calculate the scale factors
        var widthScaleFactor = displayedWidth / naturalWidth;
        var heightScaleFactor = displayedHeight / naturalHeight;

        diagram.ports.forEach(port => {
          var scaledLeft = port.loc[0] * widthScaleFactor;
          var scaledTop = port.loc[1] * heightScaleFactor;
          var portSize = 20; // Example size, adjust as needed

          // Adjust for centering
          scaledLeft -= portSize / 2;
          scaledTop -= portSize / 2;

          var portElement = $('<div>').css({
            'position': 'absolute',
            'left': scaledLeft + 'px',
            'top': scaledTop + 'px',
            'width': portSize + 'px',
            'height': portSize + 'px',
            //'background-color': 'red',
            'cursor': 'pointer',
            'z-index': 10
          });

          // Tooltip div
          var tooltipContent = createTooltipContent(port);
          var tooltip = $('<div>').addClass('port-tooltip').css({
            'position': 'absolute',
            'display': 'none', // Hidden by default
            'background-color': 'white',
            'border': '1px solid black',
            'padding': '5px',
            'z-index': 20,
            'pointer-events': 'none', // Ignore mouse events
            'white-space': 'pre-wrap'
          }).text(tooltipContent);

          $('body').append(tooltip); // Append tooltip to body to ensure it's not clipped

          // Show tooltip on hover
          // Show tooltip on hover
          portElement.on('mouseenter', function(e) {
            tooltip.css({
              'top': (e.pageY + 10) + 'px', // Position below cursor
              'left': (e.pageX + 10) + 'px',
              'display': 'block'
            });
          }).on('mouseleave', function() {
            tooltip.hide();
          });

          parentElement.append(portElement);
        });
      });

      $('#rack_diagram').attr('src', image_src_url).show();
      console.log("Image src set to:", $('#rack_diagram').attr('src'));

      // Manually trigger load if the image is already loaded
      /*if ($('#rack_diagram')[0].complete) {
        $('#rack_diagram').trigger('load');
      }*/
      
      $('#img_info').text(JSON.stringify(diagram, null, 3));
    }
  }
  

  

  $("#display").click(function () {
    get_url();
  });

  $("#download_visio").click(async function () {
    await get_url();
    location.href = vssx_url;
  })

  function show_hide_fields() {

    if (fa_option_model.val().includes('fa-c')) {
      $('#csize').show();
      $('#mezz').hide();
    }
    else {
      $('#csize').hide();
    }

    if (fa_option_face.val() == 'front') {
      $('#fa_fm_label').show();
      $('#fa_dp_label').show();
      $('#fa_bezel').show();

      $('#mezz').hide();
      $('#ports').hide();
      $('#fa_dc_power').hide();

      $('#protocol').hide();
      $('#addoncards').hide();
      $('#pci_dropdowns').hide();
    }
    else {
      $('#fa_fm_label').hide();
      $('#fa_dp_label').hide();
      $('#fa_bezel').hide();
      
      $('#fa_dc_power').show();
      $('#protocol').show();
      $('#addoncards').show();
      $('#pci_dropdowns').show();
      $("#mezz").show();
      $("#ports").show();
      
    
      if (fa_option_model.val().includes('fa-xl')) {
        //show pci 4-8
        $("#mezz").hide();
        $('#pci_select_4').show();
        $('#pci_select_5').show();
        $('#pci_select_6').show();
        $('#pci_select_7').show();
        $('#pci_select_8').show();
        
      }
      else if (fa_option_model.val().includes('r4') || fa_option_model.val().includes('e'))  {
          $("#mezz").hide();
          $('#pci_select_4').show();
          $('#pci_select_5').hide();
          $('#pci_select_6').hide();
          $('#pci_select_7').hide();
          $('#pci_select_8').hide();
      
      } else {
        $('#pci_select_4').hide();
        $('#pci_select_5').hide();
        $('#pci_select_6').hide();
        $('#pci_select_7').hide();
        $('#pci_select_8').hide();
      }
    }

  }
  
  $("#fa_option_model > select").change(show_hide_fields);
  $("#fa_option_face > select").change(show_hide_fields);
});

