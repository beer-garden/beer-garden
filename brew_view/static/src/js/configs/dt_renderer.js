
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

      if (options.childContainer) {
        let childContainer = $('<span>')
          .attr('id', 'childContainer')
          .css('margin-right', '20px')
          .append(
            $('<input>')
              .attr('id', 'childCheck')
              .attr('type', 'checkbox')
              .css('margin-top', '-4px')
              .change(() => { $('.dataTable').dataTable().fnUpdate(); })
          )
          .append(
            $('<label>')
              .attr('for', 'childCheck')
              .css('padding-left', '4px')
              .text('Include Children')
          );
        $('.dataTables_filter').prepend(childContainer);
      }

      if (options.refreshButton) {
        let refreshButton = $('<button>')
          .attr('id', 'refreshButton')
          .attr('type', 'button')
          .addClass('btn')
          .addClass('btn-default')
          .css('margin-left', '20px')
          .css('margin-bottom', '5px')
          .click(() => { $('.dataTable').dataTable().fnUpdate(); })
          .append($('<span>')
            .addClass('fa')
            .addClass('fa-refresh')
            .css('padding-right', '5px')
          )
          .append($('<span>').text('Refresh'));
        $('.dataTables_length').append(refreshButton);
      }

      if (options.newData) {
        let newData = $('<span>')
          .attr('id', 'newData')
          .css('margin-left', '20px')
          .css('margin-bottom', '5px')
          .append($('<span>')
            .addClass('glyphicon')
            .addClass('glyphicon-info-sign')
            .css('padding-right', '5px')
          )
          .append($('<span>').text('Updated Info Detected'));
        $('.dataTables_length').append(newData);
      }

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
