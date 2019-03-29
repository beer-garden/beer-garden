
runDTRenderer.$inject = [
  'DTRendererService',
];

/**
 * runDTRenderer - Tweak datatables rendering
 * @param  {Object} DTRendererService    Data-tables' rendering service.
 */
export default function runDTRenderer(DTRendererService) {
  DTRendererService.registerPlugin({
    postRender: function(options, result) {

      let childContainer = $('<span>')
        .append(
          $('<input>')
            .attr('id', 'childCheck')
            .attr('type', 'checkbox')
            .css('margin', '0')
            .change(() => { $('#requestIndexTable').dataTable().fnUpdate(); })
        )
        .append(
          $('<label>')
            .attr('for', 'childCheck')
            .css('vertical-align', 'text-top')
            .css('padding-right', '15px')
            .css('padding-left', '4px')
            .css('margin', '0')
            .text('Include Children')
        );
      $('.dataTables_filter').prepend(childContainer);

      // Insert a spinner thingy
      let spinner = $('<span>')
        .attr('id', 'dtSpinner')
        .addClass('fa fa-spinner fa-pulse')
        .css('margin-right', '5px')
        .css('visibility', 'hidden');
      $('.dataTables_filter').prepend(spinner);

      // Register callback to show / hide spinner thingy
      let processingDelay = null;
      $('.dataTable').on('processing.dt', function(e, settings, processing) {
        if (!processing) {
          clearTimeout(processingDelay);
          $('#dtSpinner').css('visibility', 'hidden');
        } else {
          processingDelay = setTimeout(function() {
            $('#dtSpinner').css('visibility', 'visible');
          }, 500);
        }
      });
    },
  });
};
