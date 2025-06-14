
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
  
  // Check if jsonurl library loaded
  console.log("Document ready - checking for jsonurl library:");
  console.log('jsonurl available:', typeof jsonurl !== 'undefined');
  console.log('JSONURL available:', typeof JSONURL !== 'undefined');
  console.log('JsonUrl available:', typeof JsonUrl !== 'undefined');
  console.log('JsonURL available:', typeof JsonURL !== 'undefined');
  console.log('All window keys:', Object.keys(window).filter(k => k.toLowerCase().includes('json')));
  
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
  
  // Set default values to TRUE for fm_label and dp_label
  fa_option_fm_label.val('TRUE');
  fa_option_dp_label.val('TRUE');
  var fa_option_addoncards = build_input('#fa_option_addoncards', "");
  var fa_option_ports = build_select('#fa_option_ports', FA_OPTIONS.ports);
  var fa_option_mezz = build_select('#fa_option_mezz', FA_OPTIONS.mezz);
  var fa_option_dc_power = build_select('#fa_option_dc_power', FA_OPTIONS.dc_power);
  var fa_option_individual = build_select('#fa_option_individual', FA_OPTIONS.individual);
  var fa_option_chassis_gen = build_select('#fa_option_chassis_gen', FA_OPTIONS.chassis_gen);
  
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
    
    // Check if we're using datapacks v2
    const datapacksV2Jsonurl = fa_option_datapacks.attr('data-datapacksv2');
    console.log('fa_url: checking for datapacksv2 attr:', datapacksV2Jsonurl);
    if (datapacksV2Jsonurl) {
      // Use datapacksv2 parameter - jsonurl is already URL-safe, no need to encode again
      url += "&datapacksv2=" + datapacksV2Jsonurl;
      console.log('fa_url: added datapacksv2 parameter');
    } else {
      // Use regular datapacks parameter
      url += "&datapacks="  + fa_option_datapacks.val();
      console.log('fa_url: using regular datapacks parameter');
    }
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

    if (fa_option_chassis_gen.val() != ''){
      url += "&chassis_gen=" + fa_option_chassis_gen.val();
    }

    console.log('fa_url: final URL:', url);
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
    
    // Check if we're using bladesv2
    const bladesV2Jsonurl = fbs_option_blades.attr('data-bladesv2');
    console.log('fbs_url: checking for bladesv2 attr:', bladesV2Jsonurl);
    if (bladesV2Jsonurl) {
      // Use bladesv2 parameter - jsonurl is already URL-safe, no need to encode again
      url += "&bladesv2=" + bladesV2Jsonurl;
      console.log('fbs_url: added bladesv2 parameter');
    } else {
      // Use regular blade parameters
      url += "&no_of_blades=" + fbs_option_blades.val();
      console.log('fbs_url: using regular blade parameters');
    }
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

  // Datapacks v2 functionality
  let datapacksV2Data = [
    { datapacks: [] } // Start with just chassis (first shelf)
  ];

  // Toggle between original datapacks and datapacks v2
  $("#toggle-datapacks-v2").click(function() {
    const isV2Visible = $("#datapacks-v2-section").is(":visible");
    
    if (isV2Visible) {
      // Switch back to original
      $("#datapacks-v2-section").hide();
      $("#datapacks").show();
      $("#datapack-chart-button").show();
      $("#datapack-chart").show();
      $("#auto-update").parent().hide(); // Hide auto-update checkbox
      $(this).text("Use Advanced Datapack Builder");
      
      // Clear the datapacksv2 parameter when switching back
      fa_option_datapacks.removeAttr('data-datapacksv2');
    } else {
      // Switch to v2
      $("#datapacks-v2-section").show();
      $("#datapacks").hide();
      $("#datapack-chart-button").hide();
      $("#datapack-chart").hide();
      $("#auto-update").parent().show(); // Show auto-update checkbox
      $(this).text("Use Simple Datapack Input");
      
      // Initialize display and set initial parameter
      updateDatapacksV2Display();
      updateTargetShelfDropdown();
      
      // Initially clear the FM Size field to show full datalist options
      $("#fm-size").val("");
      
      // Set placeholder to show what the default would be
      const firstOption = $("#fm-sizes option:first").val();
      $("#fm-size").attr("placeholder", `Default: ${firstOption}`);
      
      // Add focus event to clear field and show full datalist
      $("#fm-size").on("focus", function() {
        if ($(this).val() === firstOption) {
          $(this).val("");
        }
      });
      
      // Add blur event to set default if field is empty
      $("#fm-size").on("blur", function() {
        if ($(this).val().trim() === "") {
          $(this).val(firstOption);
        }
      });
      
      updateDatapacksV2Parameter(); // Set initial empty parameter
    }
  });

  // Add datapack to selected shelf
  $("#add-datapack").click(function() {
    const dpLabel = $("#dp-label").val();
    const fmSize = $("#fm-size").val();
    const fmCount = parseInt($("#fm-count").val());
    const fmType = $("#fm-type").val();
    const firstSlot = $("#first-slot").val();
    const targetShelf = parseInt($("#target-shelf").val());

    if (!fmSize || !fmCount) {
      alert("Please fill in FM Size and FM Count");
      return;
    }

    const datapack = {
      fm_size: fmSize,
      fm_count: fmCount
    };

    // Only add dp_label if it's not empty (to allow default generation)
    if (dpLabel && dpLabel.trim() !== '') {
      datapack.dp_label = dpLabel;
    }

    // Only add fm_type if it's not blank (allow backend to auto-detect)
    if (fmType && fmType.trim() !== '') {
      datapack.fm_type = fmType;
    }

    if (firstSlot) {
      datapack.first_slot = parseInt(firstSlot);
    }

    // Ensure target shelf exists
    while (datapacksV2Data.length <= targetShelf) {
      datapacksV2Data.push({ datapacks: [] });
    }

    datapacksV2Data[targetShelf].datapacks.push(datapack);
    
    // Clear form
    $("#dp-label").val("");
    $("#fm-size").val("");
    $("#fm-count").val("10");
    $("#first-slot").val("");
    
    updateDatapacksV2Display();
    updateDatapacksV2Parameter();
  });

  // Add new shelf
  $("#add-shelf").click(function() {
    datapacksV2Data.push({ datapacks: [] });
    updateTargetShelfDropdown();
    // Set the dropdown to the newly added shelf (highest number)
    $("#target-shelf").val(datapacksV2Data.length - 1);
    updateDatapacksV2Display();
  });

  // Update target shelf dropdown
  function updateTargetShelfDropdown() {
    const dropdown = $("#target-shelf");
    dropdown.empty();
    
    for (let i = 0; i < datapacksV2Data.length; i++) {
      const label = i === 0 ? "Chassis" : `Shelf ${i - 1}`;
      dropdown.append(`<option value="${i}">${label}</option>`);
    }
  }

  // Update the display of current datapacks
  function updateDatapacksV2Display() {
    $("#shelves-v2-container").empty();
    
    for (let i = 0; i < datapacksV2Data.length; i++) {
      const shelfName = i === 0 ? "Chassis" : `Shelf ${i - 1}`;
      let shelfHtml = `<div class="shelf-section" style="margin-bottom: 20px; border: 1px solid #ddd; padding: 10px;">
        <h5>${shelfName}
          ${i > 0 ? `<button class="btn btn-sm btn-warning pull-right" onclick="removeShelf(${i})">Remove Shelf</button>` : ''}
        </h5>`;
      
      if (datapacksV2Data[i].datapacks.length === 0) {
        shelfHtml += `<p style="color: #999; font-style: italic;">No datapacks configured</p>`;
      } else {
        datapacksV2Data[i].datapacks.forEach((dp, index) => {
          shelfHtml += createDatapackDisplay(dp, i, index);
        });
      }
      
      shelfHtml += `</div>`;
      $("#shelves-v2-container").append(shelfHtml);
    }
  }

  // Create HTML display for a datapack
  function createDatapackDisplay(datapack, shelfIndex, datapackIndex) {
    const fmType = datapack.fm_type ? `(${datapack.fm_type})` : '(auto-detect)';
    const slotInfo = datapack.first_slot ? ` - Slot: ${datapack.first_slot}` : '';
    const labelInfo = datapack.dp_label ? `${datapack.dp_label} - ` : '';
    
    return `
      <div class="datapack-display" style="border: 1px solid #ccc; padding: 8px; margin: 5px 0; background-color: #f9f9f9;">
        <strong>Datapack:</strong> 
        ${labelInfo}${datapack.fm_count} x ${datapack.fm_size} ${fmType}${slotInfo}
        <button class="btn btn-xs btn-danger pull-right" onclick="removeDatapack(${shelfIndex}, ${datapackIndex})">Remove</button>
      </div>
    `;
  }

  // Remove datapack function (global scope)
  window.removeDatapack = function(shelfIndex, datapackIndex) {
    datapacksV2Data[shelfIndex].datapacks.splice(datapackIndex, 1);
    updateDatapacksV2Display();
    updateDatapacksV2Parameter();
  };

  // Remove shelf function (global scope)
  window.removeShelf = function(shelfIndex) {
    if (shelfIndex > 0) { // Can't remove chassis (index 0)
      datapacksV2Data.splice(shelfIndex, 1);
      updateTargetShelfDropdown();
      
      // Set dropdown to the highest remaining shelf (last shelf after chassis)
      const highestShelfIndex = datapacksV2Data.length - 1;
      $("#target-shelf").val(highestShelfIndex);
      
      updateDatapacksV2Display();
      updateDatapacksV2Parameter();
    }
  };

  // Update the datapacksv2 parameter for the API call
  function updateDatapacksV2Parameter() {
    // Check all possible ways jsonurl might be exposed
    console.log('Window object keys containing jsonurl:', Object.keys(window).filter(k => k.toLowerCase().includes('jsonurl')));
    console.log('Available jsonurl:', typeof jsonurl !== 'undefined' ? jsonurl : 'undefined');
    console.log('Available JSONURL:', typeof JSONURL !== 'undefined' ? JSONURL : 'undefined');
    console.log('Available window.jsonurl:', typeof window.jsonurl !== 'undefined' ? window.jsonurl : 'undefined');
    console.log('Available JsonUrl:', typeof JsonUrl !== 'undefined' ? JsonUrl : 'undefined');
    console.log('Available JsonURL:', typeof JsonURL !== 'undefined' ? JsonURL : 'undefined');
    console.log('Available window.JsonUrl:', typeof window.JsonUrl !== 'undefined' ? window.JsonUrl : 'undefined');
    console.log('Available window.JsonURL:', typeof window.JsonURL !== 'undefined' ? window.JsonURL : 'undefined');
    
    let jsonurlLib = null;
    if (typeof JsonURL !== 'undefined') {
      jsonurlLib = JsonURL;
    } else if (typeof window.JsonURL !== 'undefined') {
      jsonurlLib = window.JsonURL;
    } else if (typeof jsonurl !== 'undefined') {
      jsonurlLib = jsonurl;
    } else if (typeof JSONURL !== 'undefined') {
      jsonurlLib = JSONURL;
    } else if (typeof JsonUrl !== 'undefined') {
      jsonurlLib = JsonUrl;
    }
    
    if (!jsonurlLib) {
      console.error('jsonurl library not loaded yet');
      return;
    }
    
    console.log('Using jsonurl library:', jsonurlLib);
    
    // Use jsonurl to encode the data for URL transmission
    const jsonurlString = jsonurlLib.stringify(datapacksV2Data);
    fa_option_datapacks.attr('data-datapacksv2', jsonurlString);
    
    console.log('Updated datapacksv2 parameter:', jsonurlString);
    console.log('Auto-update enabled:', $("#auto-update").is(":checked"));
    
    // Automatically update the image if auto-update is enabled
    if ($("#auto-update").is(":checked")) {
      console.log('Triggering auto-update...');
      get_url();
    }
  }

  // ============ BLADESV2 FUNCTIONALITY ============
  
  // Initialize bladesv2 data structure
  let bladesV2Data = [
    { gen: '1', blades: [] } // Chassis 0
  ];

  // Toggle between simple and advanced blade builder
  $('#toggle-blades-v2').click(function() {
    const isV2Visible = $('#blades-v2-section').is(':visible');
    
    if (isV2Visible) {
      // Switch back to simple
      $('#blades-v2-section').hide();
      $('#blades').show();
      $('#auto-update-blades').parent().hide();
      $(this).text('Use Advanced Blade Builder');
      
      // Show the legacy dfm fields
      $('#fbs_option_dfm_size').closest('.row').show();
      $('#fbs_option_dfm_count').closest('.row').show();
      
      // Clear the bladesv2 parameter when switching back
      fbs_option_blades.removeAttr('data-bladesv2');
    } else {
      // Switch to advanced
      $('#blades-v2-section').show();
      $('#blades').hide();
      $('#auto-update-blades').parent().show();
      $(this).text('Use Simple Blade Input');
      
      // Hide the legacy dfm fields since they're part of the old way
      $('#fbs_option_dfm_size').closest('.row').hide();
      $('#fbs_option_dfm_count').closest('.row').hide();
      
      // Initialize with default data
      updateBladesV2Display();
      updateBladesV2Parameter();
    }
  });

  // Add blade configuration
  $('#add-blade-config').click(function() {
    const dfmSize = $('#dfm-size').val().trim();
    const bladeCount = parseInt($('#blade-count').val());
    const firstSlot = parseInt($('#first-slot-blade').val());
    const targetChassis = parseInt($('#target-chassis').val());
    
    // Get selected bays
    const selectedBays = [];
    $('#blade-form input[type="checkbox"]:checked').each(function() {
      selectedBays.push(parseInt($(this).val()));
    });
    
    // Validation
    if (!dfmSize) {
      alert('Please enter DFM Size');
      return;
    }
    
    if (selectedBays.length === 0) {
      alert('Please select at least one bay');
      return;
    }
    
    if (isNaN(bladeCount) || bladeCount < 1) {
      alert('Blade Count must be at least 1');
      return;
    }
    
    if (isNaN(firstSlot) || firstSlot < 1 || firstSlot > 10) {
      alert('First Slot must be between 1 and 10');
      return;
    }
    
    // Create blade configuration object
    const bladeConfig = {
      bays: selectedBays,
      dfm_size: dfmSize,
      blade_count: bladeCount,
      first_slot: firstSlot,
      blade_model: 'fb-s200' // Default for now
    };
    
    // Add to data structure
    if (targetChassis >= bladesV2Data.length) {
      // Add new chassis if needed
      while (bladesV2Data.length <= targetChassis) {
        bladesV2Data.push({ gen: '1', blades: [] });
      }
    }
    
    bladesV2Data[targetChassis].blades.push(bladeConfig);
    
    // Clear form
    $('#dfm-size').val('');
    $('#blade-count').val('1');
    $('#first-slot-blade').val('1');
    $('#blade-form input[type="checkbox"]').prop('checked', false);
    
    // Update display and parameter
    updateBladesV2Display();
    updateBladesV2Parameter();
  });

  // Add new chassis
  $('#add-chassis').click(function() {
    bladesV2Data.push({ gen: '1', blades: [] });
    
    // Update dropdown
    const newChassisIndex = bladesV2Data.length - 1;
    $('#target-chassis').append(`<option value="${newChassisIndex}">Chassis ${newChassisIndex}</option>`);
    $('#target-chassis').val(newChassisIndex);
    
    updateBladesV2Display();
    updateBladesV2Parameter();
  });

  function updateBladesV2Display() {
    let html = '';
    
    bladesV2Data.forEach((chassis, chassisIndex) => {
      if (chassis.blades.length > 0) {
        const chassisTitle = chassisIndex === 0 ? "Chassis" : `Chassis ${chassisIndex}`;
        html += `<div class="shelf-section">
          <h5>${chassisTitle} 
            ${chassisIndex > 0 ? `<button class="btn btn-xs btn-danger" onclick="removeChassis(${chassisIndex})">Remove</button>` : ''}
          </h5>`;
        
        chassis.blades.forEach((blade, bladeIndex) => {
          const baysText = blade.bays.join(', ');
          html += `<div class="datapack-item">
            <span><strong>Bays ${baysText}:</strong> ${blade.dfm_size} × ${blade.blade_count} blades (starting slot ${blade.first_slot})</span>
            <button class="btn btn-xs btn-danger" onclick="removeBladeConfig(${chassisIndex}, ${bladeIndex})">Remove</button>
          </div>`;
        });
        
        html += '</div>';
      }
    });
    
    $('#chassis-v2-container').html(html);
  }

  function updateBladesV2Parameter() {
    if (typeof JsonURL !== 'undefined') {
      try {
        const jsonurl = JsonURL.stringify(bladesV2Data);
        fbs_option_blades.attr('data-bladesv2', jsonurl);
        
        console.log('BladesV2 parameter updated:', jsonurl);
        console.log('Auto-update enabled:', $("#auto-update-blades").is(":checked"));
        
        // Automatically update the image if auto-update is enabled
        if ($("#auto-update-blades").is(":checked")) {
          console.log('Triggering auto-update...');
          get_url();
        }
      } catch (error) {
        console.error('Error encoding bladesv2 data:', error);
      }
    } else {
      console.warn('JsonURL library not available');
    }
  }

  // Global functions for remove buttons
  window.removeBladeConfig = function(chassisIndex, bladeIndex) {
    bladesV2Data[chassisIndex].blades.splice(bladeIndex, 1);
    updateBladesV2Display();
    updateBladesV2Parameter();
  };

  window.removeChassis = function(chassisIndex) {
    if (chassisIndex > 0) { // Don't allow removing chassis 0
      bladesV2Data.splice(chassisIndex, 1);
      
      // Update dropdown
      $('#target-chassis').empty();
      bladesV2Data.forEach((chassis, index) => {
        $('#target-chassis').append(`<option value="${index}">Chassis ${index}</option>`);
      });
      
      // Set to highest remaining chassis
      const highestChassis = bladesV2Data.length - 1;
      $('#target-chassis').val(highestChassis);
      
      updateBladesV2Display();
      updateBladesV2Parameter();
    }
  };

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

