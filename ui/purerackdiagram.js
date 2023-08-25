const pythonTupleType = new jsyaml.Type('tag:yaml.org,2002:python/tuple', {
  kind: 'sequence',
  construct: function (data) {
    return data; // Treat tuples as arrays in JavaScript
  },
});

const customSchema = jsyaml.DEFAULT_SCHEMA.extend([pythonTupleType]);


$(function () {
  console.log("ready!");

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

      const createTable = (lookupData) => {
        if (!lookupData || lookupData.length === 0) {
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

        Object.entries(lookupData).forEach(([key, item]) => {
          if (categories.includes(item[1])) {
            tableHtml += `
              <tr>
                <td>${key}</td>
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

      const createSubTabs = (lookupData, parentId) => {

        subTabsHtml = `<div id="${parentId}-dp-tabs">`;
        subTabsHtml += '<ul>';
        subTabContentHtml = '';

        // iterate through the categories, Blank, SCM, NVMe, NVMe-QLC, SAS
        categories.forEach((category, index) => {
          
          //create the list in parallel in this loop
          subTabsHtml += `
            <li><a href="#${parentId}-${category}">${category}</a></li>
          `;

          // iterated through the lookupData dictionary of arrays, and filter
          // to include only the category stored in 1 index of the array we are interested in.
          // end filtered_data is a dictionary of arrays maintaining the
          // original key value pairs.
          const filteredData = Object.fromEntries(
            Object.entries(lookupData).filter(([key, value]) => value[1] === category)
          );

          // Create the content Divs for each tab.
          subTabContentHtml += `
              <div id="${parentId}-${category}">
                ${createTable(filteredData)}
              </div>
          `;
        });

        //end the list
        subTabsHtml += '</ul>';
        subTabContentHtml += '</div>';

        return subTabsHtml + subTabContentHtml;
      };

      const chassisLookupData = data.chassis_dp_size_lookup;
      const shelfLookupData = data.shelf_dp_size_lookup;

      document.querySelector("#chassis-dp").innerHTML = createSubTabs(chassisLookupData, 'chassis');
      document.querySelector("#shelf-dp").innerHTML = createSubTabs(shelfLookupData, 'shelf');
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
  fa_option_model.val('fa-x20r4');

  var fa_option_protocol = build_select('#fa_option_protocol', FA_OPTIONS.protocol);
  var fa_option_face = build_select('#fa_option_face', FA_OPTIONS.face);
  var fa_option_datapacks = build_input('#fa_option_datapacks', "63");
  var fa_option_csize = build_select('#fa_option_csize', FA_OPTIONS.csizes);
  var fa_option_bezel = build_select('#fa_option_bezel', FA_OPTIONS.bezel);
  var fa_option_direction = build_select('#fa_option_direction', FA_OPTIONS.direction);
  var fa_option_fm_label = build_select('#fa_option_fm_label', FA_OPTIONS.fm_label);
  var fa_option_dp_label = build_select('#fa_option_dp_label', FA_OPTIONS.dp_label);
  var fa_option_addoncards = build_input('#fa_option_addoncards', "");
  var fa_option_ports = build_select('#fa_option_ports', FA_OPTIONS.ports);
  var fa_option_mezz = build_select('#fa_option_mezz', FA_OPTIONS.mezz);
  
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
  

  var fbs_option_model = build_select('#fbs_option_model', FBS_OPTIONS.model);
  var fbs_option_dfm_size = build_select('#fbs_option_dfm_size', FBS_OPTIONS.dfm_size);
  var fbs_option_dfm_count = build_select('#fbs_option_dfm_count', FBS_OPTIONS.dfm_count);
  var fbs_option_face = build_select('#fbs_option_face', FBS_OPTIONS.face);
  var fbs_option_direction = build_select('#fbs_option_direction', FBS_OPTIONS.direction);
  var fbs_option_xfm = build_select('#fbs_option_xfm', FBS_OPTIONS.xfm);
  var fbs_option_blades = build_input('#fbs_option_blades', FBS_OPTIONS.blades);
  var fbs_option_ports = build_select('#fbs_option_ports', FBS_OPTIONS.ports);
  var fbs_option_xfm_face = build_select('#fbs_option_xfm_face', FBS_OPTIONS.xfm_face);
  var fbs_option_bezel = build_select('#fbs_option_bezel', FBS_OPTIONS.bezel);



  var fa_url = function(){
    // the function to generate the url for FA image based on options

    var url = API_ENDPOINT;
    url += "model="  + fa_option_model.val();
    url += "&protocol="  + fa_option_protocol.val();
    url += "&face="  + fa_option_face.val();
    url += "&datapacks="  + fa_option_datapacks.val();
    url += "&bezel="  + fa_option_bezel.val();
    url += "&direction="  + fa_option_direction.val();
    url += "&fm_label="  + fa_option_fm_label.val();
    url += "&dp_label="  + fa_option_dp_label.val();
    url += "&addoncards="  + fa_option_addoncards.val();
    url += "&csize=" + fa_option_csize.val();

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
    console.log(mezz_val);
    if (mezz_val) {
        url += "&mezz=" + fa_option_mezz.val();
    }

    return url;
  };


  var fb_url = function() {
    // the function to generate the url for FB image based on options

    var url = API_ENDPOINT;
    url += "model=fb"; // it is fixed value, but reserved for future expension
    url += "&chassis="  + fb_option_chassis.val();
    url += "&face="  + fb_option_face.val();
    url += "&direction="  + fb_option_direction.val();
    url += "&xfm=" + fb_option_xfm.val();
    url += "&blades=" + fb_option_blades.val();
    url += "&efm=" + fb_option_efm.val();
    url += "&xfm_face=" + fb_option_xfm_face.val();


    var ports_val = fb_option_ports.val();
    if (ports_val){
      url += "&ports=" + ports_val;
    }

    return url;
  };

  var fbs_url = function() {
    // the function to generate the url for FB image based on options

    var url = API_ENDPOINT;
    url += "model="  + fbs_option_model.val();
    url += "&face="  + fbs_option_face.val();
    url += "&direction="  + fbs_option_direction.val();
    url += "&xfm=" + fbs_option_xfm.val();
    url += "&no_of_blades=" + fbs_option_blades.val();
    url += "&no_of_drives_per_blade=" + fbs_option_dfm_count.val();
    url += "&drive_size=" + fbs_option_dfm_size.val();
    url += "&xfm_face=" + fbs_option_xfm_face.val();
    url += "&bezel=" + fbs_option_bezel.val();
 
    
    //fbs_option_dfm_size

    var ports_val = fbs_option_ports.val();
    if (ports_val){
      url += "&ports=" + ports_val;
    }

    return url;
  };

  

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



    //console.log(url);
    //$('#rack_digram').attr('src', url);

    
    
    visio_url = url + "&vssx=True";
    
    $('#img_url').html('<a target="_blank" href="' + url + '">' + url + '</a>');
    $('#visio_url').html('<a target="_blank" href="' + visio_url + '">' + visio_url + '</a>');

    const response = await fetch(url+"&json=True");
    var diagram = await response.json();

    if ( diagram.error ) {
      $('#rack_digram').attr('src', "");
      $('#error_msg').text(diagram.error);
      $("#error-div").show();
      $('#rack_diagram').hide();
    } else {
      $('#error_msg').text("");
      $("#error-div").hide();
      if ( diagram.image_type == "png" ) {
        const img_base64encoded = await fetch(`data:image/png;base64,${diagram.image}`);
        const blob = await img_base64encoded.blob();
        var objectURL = await URL.createObjectURL(blob);
        delete diagram.image;
        $('#rack_digram').attr('src', objectURL);
      }
      else if (diagram.image_type == "link" ) {
        $('#rack_digram').attr('src', diagram.image);
      }

      $('#rack_diagram').show();
    }

    $('#img_info').text(JSON.stringify(diagram, null, 3));

  }

  $("#display").click(function () {
    get_url();
  });

  $("#download_visio").click(function () {
    url = get_url() + "&vssx=True";
    location.href = url;
  })

  $("#fa_option_model > select").change(function () {
     if (fa_option_model.val().includes('fa-c')) {
       $('#csize').show();
       //$('#datapacks').hide();
       $('#mezz').hide();
       $("#ports").hide();
     }
     else {
      $('#csize').hide();
      //$('#datapacks').show();
      if ( fa_option_face.val() == 'back'){
        $("#mezz").show();
        $("#ports").show();
      }
     }

    if (fa_option_model.val().includes('fa-xl')) {
      //show pci 4-8
      $('#pci_select_4').show();
      $('#pci_select_5').show();
      $('#pci_select_6').show();
      $('#pci_select_7').show();
      $('#pci_select_8').show();
      
    }
    else if (fa_option_model.val().includes('r4'))  {
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

  });

  $("#fa_option_face > select").change(function () {
    if (fa_option_face.val() == 'front') {
      $('#fa_fm_label').show();
      $('#fa_dp_label').show();
      $('#fa_bezel').show();

      $('#mezz').hide();
      $('#ports').hide();

      $('#protocol').hide();
      $('#addoncards').hide();
      $('#pci_dropdowns').hide();
    }
    else {
      $('#fa_fm_label').hide();
      $('#fa_dp_label').hide();
      $('#fa_bezel').hide();
      
      $('#protocol').show();
      $('#addoncards').show();
      $('#pci_dropdowns').show();
      if (fa_option_model.val() != 'fa-c60'){
        $("#mezz").show();
        $("#ports").show();
      }

    }
  });
});

