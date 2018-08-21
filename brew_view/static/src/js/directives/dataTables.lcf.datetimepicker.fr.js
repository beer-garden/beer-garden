
/**
 * function - Wrapper module for eonasdan-bootstrap-datetimepicker
 *
 * Based on dataTables.lcf.datetimepicker.fr.js:
 * @author Thomas <thansen@solire.fr>
 * @license CC BY-NC 4.0 http://creativecommons.org/licenses/by-nc/4.0/
 * @param  {window} window     JS Window Object.
 * @param  {document} document JS Location Object.
 */
(function(window, document) {
  let factory = function($, ColumnFilter) {
    'use strict';

    ColumnFilter.filter.range = {};
    ColumnFilter.filter.rangeBase = $.extend(true, {},
      ColumnFilter.filter.range);

    $.extend(
      ColumnFilter.filter.range,
      ColumnFilter.filter.rangeBase,
      {
        separator: '~',
        dom: function(th) {
          let self = this;

          // Picker widgets need to be inside a relative-positioned element
          th.css('position', 'relative');

          var element = $('<input>', {
            type: self.options.type || 'text',
            style: 'width: 50%;',
          });

          $.each(self.options.attr, function(key, value) {
            element.attr(key, value);
          });

          self.startElement = element.clone();
          $.each(self.options.startAttr, function(key, value) {
            self.startElement.attr(key, value);
          });

          self.endElement = element.clone();
          $.each(self.options.endAttr, function(key, value) {
            self.endElement.attr(key, value);
          });

          self.elements = self.startElement.datetimepicker(self.options.picker)
            .add(self.endElement.datetimepicker(self.options.picker))
            .appendTo(th);

          return self.elements;
        },
        bindEvents: function() {
          const self = this;

          self.startElement.on('dp.change', function() {
            self.search();
          });
          self.endElement.on('dp.change', function() {
            self.search();
          });
        },
        request: function() {
          const self = this;

          return [
            self.startElement.val(), self.endElement.val(),
          ].join(self.options.separator);
        },
      }
    );
  };

  // Define as an AMD module if possible
  if (typeof define === 'function' && define.amd) {
    define([
      'jquery',
      'datatables-columnfilter',
      'eonasdan-bootstrap-datetimepicker',
    ], factory);
  } else if (typeof exports === 'object') {
    // Node/CommonJS
    factory(
      require('jquery'),
      require('datatables-columnfilter'),
      require('eonasdan-bootstrap-datetimepicker')
    );
  } else if (jQuery) {
    // Otherwise simply initialise as normal, stopping multiple evaluation
    factory(jQuery, jQuery.fn.dataTable.ColumnFilter);
  }
})(window, document);
