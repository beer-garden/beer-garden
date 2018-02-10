/*!
 * Wrapper module for eonasdan-bootstrap-datetimepicker
 *
 * Based on dataTables.lcf.datetimepicker.fr.js:
 * @author Thomas <thansen@solire.fr>
 * @license CC BY-NC 4.0 http://creativecommons.org/licenses/by-nc/4.0/
 */
(function(window, document) {
  var factory = function($, ColumnFilter) {
    'use strict';

    ColumnFilter.filter.rangeBase = $.extend(true, {}, ColumnFilter.filter.range);
    ColumnFilter.filter.range = {};
    $.extend(
      ColumnFilter.filter.range,
      ColumnFilter.filter.rangeBase,
      {
        separator: '~',
        dom: function (th) {
          var self = this;

          // Picket widgets need to be inside a relative-positioned element
          th.css('position', 'relative');

          var pickerElement = $('<input>', { type: self.options.type || 'text' });

          $.each(self.options.attr, function(key, value) {
            pickerElement.attr(key, value);
          });

          self.startPickerElem = pickerElement.clone().attr('placeholder', 'start');
          self.endPickerElem = pickerElement.clone().attr('placeholder', 'end');

          var pickerOptions = {
            format: 'YYYY-MM-DD',
            showClear: true,
            showTodayButton: true,
            useCurrent: false
          };

          self.elements = self.startPickerElem.datetimepicker(pickerOptions)
            .add(self.endPickerElem.datetimepicker(pickerOptions))
            .appendTo(th);

          return self.elements;
        },
        bindEvents: function(){
          var self = this;

          self.startPickerElem.on('dp.change', function() { self.search(); });
          self.endPickerElem.on('dp.change', function() { self.search(); });
        },
        request: function(){
          var self = this;

          return [self.startPickerElem.val(), self.endPickerElem.val()].join(self.options.separator);
        }
      }
    );
  };

  // Define as an AMD module if possible
  if (typeof define === 'function' && define.amd) {
    define(['jquery', 'datatables-light-columnfilter', 'eonasdan-bootstrap-datetimepicker'], factory);
  } else if (typeof exports === 'object') {
    // Node/CommonJS
    factory(require('jquery'), require('datatables-light-columnfilter'), require('eonasdan-bootstrap-datetimepicker'));
  } else if (jQuery) {
    // Otherwise simply initialise as normal, stopping multiple evaluation
    factory(jQuery, jQuery.fn.dataTable.ColumnFilter);
  }
})(window, document);
