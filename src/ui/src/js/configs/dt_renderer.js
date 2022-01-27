runDTRenderer.$inject = ['DTRendererService'];

/**
 * runDTRenderer - Tweak datatables rendering
 * @param  {Object} DTRendererService    Data-tables' rendering service.
 */
export default function runDTRenderer(DTRendererService) {
  DTRendererService.registerPlugin({
    postRender: function(options, result) {
      if (options && options.childContainer) {
        const childContainer = $('<span>')
            .attr('id', 'childContainer')
            .css('margin-right', '20px')
            .append(
                $('<input>')
                    .attr('id', 'childCheck')
                    .attr('type', 'checkbox')
                    .css('margin-top', '-4px')
                    .change(() => {
                      $('.dataTable').dataTable().fnUpdate();
                    }),
            )
            .append(
                $('<label>')
                    .attr('for', 'childCheck')
                    .css('padding-left', '4px')
                    .text('Show Children'),
            );
        $('.dataTables_filter').prepend(childContainer);
      }

      if (options && options.hiddenRequestContainer) {
        const hiddenRequestContainer = $('<span>')
            .attr('id', 'hiddenRequestContainer')
            .css('margin-right', '20px')
            .append(
                $('<input>')
                    .attr('id', 'hiddenRequestCheck')
                    .attr('type', 'checkbox')
                    .css('margin-top', '-4px')
                    .change(() => {
                      $('.dataTable').dataTable().fnUpdate();
                    }),
            )
            .append(
                $('<label>')
                    .attr('for', 'hiddenRequestCheck')
                    .css('padding-left', '4px')
                    .text('Show Hidden'),
            );
        $('.dataTables_filter').prepend(hiddenRequestContainer);
      }

      if (options && options.hiddenContainer) {
        const hiddenContainer = $('<ul>')
            .attr('id', 'hiddenList')
            .css('margin-right', '20px')
            .attr(
                'style',
                'list-style-type:none;margin-right:20px; display:inline; padding-left:0px;',
            )
            .append(
                $('<label>')
                    .attr('for', 'filterHidden')
                    .css('padding-left', '4px')
                    .text('Show Hidden'),
            );
        $('.dataTables_filter').prepend(hiddenContainer);
        const node = document.getElementById('filterHidden');
        const list = document.getElementById('hiddenList');
        list.insertBefore(node, list.childNodes[0]);
      }

      if (options && options.refreshButton) {
        const refreshButton = $('<button>')
            .attr('id', 'refreshButton')
            .attr('type', 'button')
            .addClass('btn')
            .addClass('btn-default')
            .addClass('btn-sm')
            .css('margin-left', '20px')
            .css('margin-bottom', '5px')
            .click(() => {
              $('.dataTable').dataTable().fnUpdate();
            })
            .append(
                $('<span>')
                    .addClass('fa')
                    .addClass('fa-refresh')
                    .css('padding-right', '5px'),
            )
            .append($('<span>').text('Refresh'));
        $('.dataTables_length').append(refreshButton);
      }

      if (options && options.newData) {
        const newData = $('<span>')
            .attr('id', 'newData')
            .css('margin-left', '20px')
            .css('margin-bottom', '5px')
            .css('visiblity', 'hidden')
            .append(
                $('<span>')
                    .addClass('glyphicon')
                    .addClass('glyphicon-info-sign')
                    .css('padding-right', '5px'),
            )
            .append(
                $('<span>').css('cursor', 'default').text('Updates Detected'),
            );
        $('.dataTables_length').append(newData);
      }

      const spinner = $('<span>')
          .attr('id', 'dtSpinner')
          .addClass('fa fa-spinner fa-pulse fa-lg')
          .css('margin-right', '20px')
          .css('margin-left', '20px')
          .css('visibility', 'hidden');
      $('.dataTables_filter').prepend(spinner);

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
          $('#refreshButton').prop('disabled', false);
        } else {
          processingDelay = setTimeout(function() {
            $('#dtSpinner').css('visibility', 'visible');
            $('#refreshButton').prop('disabled', true);
          }, 500);
        }
      });
    },
  });
}
