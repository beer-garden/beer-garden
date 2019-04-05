
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
        .attr('id', 'childContainer')
        .css('margin-right', '20px')
        .css('display', 'none')
        .append(
          $('<input>')
            .attr('id', 'childCheck')
            .attr('type', 'checkbox')
            .css('margin-top', '-4px')
            .change(() => { $('#requestIndexTable').dataTable().fnUpdate(); })
        )
        .append(
          $('<label>')
            .attr('for', 'childCheck')
            .css('padding-left', '4px')
            .text('Include Children')
        );
      $('.dataTables_filter').prepend(childContainer);

      let refreshButton = $('<button>')
        .attr('id', 'refreshButton')
        .attr('type', 'button')
        .addClass('btn')
        .addClass('btn-default')
        .addClass('fa')
        .addClass('fa-refresh')
        .css('margin-right', '20px')
        .css('margin-bottom', '5px')
        .css('display', 'none')
        .text(' Refresh')
        .click(() => { $('#requestIndexTable').dataTable().fnUpdate(); });
      $('.dataTables_length').prepend(refreshButton);

      let spinner = $('<span>')
        .attr('id', 'dtSpinner')
        .addClass('fa fa-spinner fa-pulse fa-lg')
        .css('margin-right', '20px')
        .css('margin-left', '20px')
        .css('visibility', 'hidden');
      $('.dataTables_length').append(spinner);

      // Register callback to show / hide spinner thingy
      let processingDelay = null;
      $('.dataTable').on('processing.dt', function(e, settings, processing) {
        // Regardless of whether this event is the start or end of processing
        // we want to clear the current timeout if one exists
        if (processingDelay) {
          clearTimeout(processingDelay);
        }

        if (!processing) {
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
