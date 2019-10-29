"use strict";

function build_select(selector, values) {

  var sel = $('<select>').appendTo($(selector));
  // sel.append($("<option>").attr('value', '').text('All'));

  $(values).each(function (index, value) {
    var item = null;

    if (typeof value === 'string') {
      item = {'val': value, 'text': value};
    }
    else {
      item = this;
    }

    sel.append($("<option>").attr('value', item.val).text(item.text));
  });

  return sel;
}


function build_input(selector, value) {
  var input = $('<input>').appendTo($(selector));
  input.val(value);

  var clear_ui = $('<span class="glyphicon glyphicon-remove" style="cursor: pointer;"></span>').appendTo($(selector));
  clear_ui.click(function () {
    input.val('');
  });

  return input;
}

