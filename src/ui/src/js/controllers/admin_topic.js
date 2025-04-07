import newTopicTemplate from '../../templates/new_topic.html';

adminTopicController.$inject = [
  '$rootScope',
  '$scope',
  '$compile',
  '$uibModal',
  'localStorageService',
  'DTOptionsBuilder',
  'DTColumnBuilder',
  'TopicService',
];

/**
 * adminTopicController - Angular controller for viewing all topics.
 * @param  {Object} $rootScope        Angular's $rootScope object.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $compile          Angular's $compile object.
 * @param  {Object} $uibModal          Angular's $uibModal object.
 * @param  {Object} localStorageService  Storage service
 * @param  {Object} DTOptionsBuilder  Data-tables' options builder object.
 * @param  {Object} DTColumnBuilder   Data-tables' column builder object.
 * @param  {Object} TopicService    Beer-Garden Topic Service.
 */
export default function adminTopicController(
    $rootScope,
    $scope,
    $compile,
    $uibModal,
    localStorageService,
    DTOptionsBuilder,
    DTColumnBuilder,
    TopicService,
) {
  $scope.setWindowTitle('topics');

  $scope.topics = {};

  $scope.dtOptions = DTOptionsBuilder.newOptions()
      .withOption('autoWidth', false)
      .withOption(
          'pageLength',
          localStorageService.get('_topic_index_length') || 10,
      )
      .withOption('ajax', function(data, callback, settings) {
      // Need to also request ID for the href
        data.columns.push({data: 'id'});

        if ($('#hiddenTopicCheck').is(':checked')) {
          data.include_generated = true;
        }

        // Not urlencoding semicolons in the search values breaks the backend
        for (const column of data.columns) {
          if (column.search && column.search.value) {
            column.search.value = column.search.value.replace(/;/g, '%3B');
          }
        }

        TopicService.getTopics(data).then(
            (response) => {
              $scope.response = response;

              callback({
                data: response.data,
                draw: response.headers('draw'),
                recordsFiltered: response.headers('recordsFiltered'),
                recordsTotal: response.headers('recordsTotal'),
              });
            },
            (response) => {
              $scope.response = response;
            },
        );
      })
      .withLightColumnFilter({})
      .withDataProp('data')
      .withOption('serverSide', true)
      .withOption('hiddenTopicContainer', true)
      .withPaginationType('full_numbers')
      .withBootstrap()
      .withOption('createdRow', function(row, data, dataIndex) {
        $compile(angular.element(row).contents())($scope);
      });

  $scope.dtColumns = [
    DTColumnBuilder.newColumn('name').withTitle('Topic').withOption('width', '20%'),
    DTColumnBuilder.newColumn('publisher_count').withTitle('Publisher Count').withOption('width', '7%')
        .renderWith(function(data, type, full) {
          let publisher_count = data;
          console.log(publisher_count);
          var div = document.createElement('div');
          var itemText = document.createTextNode(publisher_count);
          div.append(itemText);
          if (publisher_count > 0) {
            var button = document.createElement('button')
            button.setAttribute("class", "fa fa-0 pull-right");
            button.style.fontSize="20px";
            button.setAttribute("ng-click", "doResetCount(" + JSON.stringify(full.id) + ")");
            button.setAttribute("ng-if", "hasPermission('GARDEN_ADMIN', true)");
            button.setAttribute("confirm","Are you sure you want to reset the publisher count?");
            button.setAttribute("title","Reset Count");
            div.append(button);
          }
          return div.outerHTML;
        }),
    DTColumnBuilder.newColumn('subscribers')
        .withTitle('Subscribers')
        .renderWith(function(data, type, full) {
          let subscribers = data;
          if (subscribers.length > 0) {
            var tbl = document.createElement("table");
            tbl.style.width = '100%';
            tbl.setAttribute("class", "table table-bordered")
            var thd = document.createElement('thead')
            let columns = ["Garden", "Namespace", "System", "Version", "Instance", "Command", "Consumer Count", "Type"]
            var tr = document.createElement('tr');
              columns.forEach((column) => {
                var th = document.createElement('th');
                if (column == "Consumer Count"){ th.style.cssText = "min-width: 100px;"}
                if (column == "Type"){ th.style.cssText = "min-width: 125px;"}
                var columnText = document.createTextNode(column);
                th.append(columnText);
                tr.append(th);
              });           
              thd.append(tr);
            tbl.appendChild(thd);
            var tbdy = document.createElement('tbody')
            subscribers.forEach((subscriber) => {
              let items = [subscriber.garden, subscriber.namespace, subscriber.system, subscriber.version, subscriber.instance, subscriber.command]
              var tr = document.createElement('tr');
              items.forEach((item) => {
                var td = document.createElement('td');
                var itemText = document.createTextNode((item) ? item : '*');
                td.append(itemText);
                tr.append(td);
              });
              // Add button(s) to tr
              // Consumer count
              var td = document.createElement('td');
              var itemText = document.createTextNode(subscriber.consumer_count);
              td.append(itemText);
              if (subscriber.consumer_count > 0) {
                var button = document.createElement('button')
                button.setAttribute("class", "fa fa-0 pull-right");
                button.style.fontSize="20px";
                button.setAttribute("ng-click", "doResetCount(" + JSON.stringify(full.id) + "," + JSON.stringify(subscriber) + ")");
                button.setAttribute("ng-if", "hasPermission('GARDEN_ADMIN', true)");
                button.setAttribute("confirm","Are you sure you want to reset the consumer count?");
                button.setAttribute("title","Reset Count");
                td.append(button);
              }
              tr.append(td);
              tbdy.append(tr);
              // Subscriber Type
              var td = document.createElement('td');
              var itemText = document.createTextNode(subscriber.subscriber_type);
              td.append(itemText);
              if (subscriber.subscriber_type == 'DYNAMIC') {
                var button = document.createElement('button')
                button.setAttribute("class", "fa fa-square-xmark pull-right");
                button.style.fontSize="20px";
                button.setAttribute("ng-click", "doRemoveSubscriber(" + JSON.stringify(full.id) + "," + JSON.stringify(subscriber) + ")");
                button.setAttribute("ng-if", "hasPermission('GARDEN_ADMIN', true)");
                button.setAttribute("confirm","Are you sure you want to delete Subscriber? " + JSON.stringify(subscriber, null, '\n'));
                button.setAttribute("title","Delete Subscriber");
                td.append(button);
              }
              tr.append(td);
              tbdy.append(tr);
            });
            tbl.appendChild(tbdy);
            return '<div style="overflow: auto;">' + tbl.outerHTML + '</div>';
          } else {
            return "";
          }
        }),
    DTColumnBuilder.newColumn(null).withTitle('').withOption('sortable', false).withOption('width', '70px')
        .renderWith(function(data, type, full) {
          let subscribers = full.subscribers;
          const has_only_dynamic_subscribers = subscribers.every((subscriber) => subscriber.subscriber_type == "DYNAMIC");

          var deleteTopicButton = null;
          if (has_only_dynamic_subscribers){
            deleteTopicButton = document.createElement('button')
            deleteTopicButton.setAttribute("class", "fa fa-trash pull-right");
            deleteTopicButton.style.fontSize="20px";
            deleteTopicButton.setAttribute("ng-click", "doDelete(" + JSON.stringify(full.id) + ")");
            deleteTopicButton.setAttribute("ng-if", "hasPermission('GARDEN_ADMIN', true)");
            deleteTopicButton.setAttribute("confirm","Are you sure you want to delete Topic \"" + full.name + "\"?");
            deleteTopicButton.setAttribute("title","Delete Topic");
          }
          var addSubscriberButton = document.createElement('button')
          addSubscriberButton.setAttribute("class", "fa fa-square-plus pull-right");
          addSubscriberButton.style.fontSize="20px";
          addSubscriberButton.setAttribute("ng-click", "doAddSubscriber(" + JSON.stringify(full, ["id", "name"]) + ")");
          addSubscriberButton.setAttribute("ng-if", "hasPermission('GARDEN_ADMIN', true)");
          addSubscriberButton.setAttribute("title","Add Subscriber(s)");
          if (deleteTopicButton){
            return deleteTopicButton.outerHTML + addSubscriberButton.outerHTML;
          } else {
            return addSubscriberButton.outerHTML;
          }
        }),
  ];

  $scope.instanceCreated = function(_instance) {
    $scope.dtInstance = _instance;

    $('#topicIndexTable').on('length.dt', (event, settings, len) => {
      localStorageService.set('_topic_index_length', len);
    });
  };

  const lightColumnFilterOptions = {
    name: {
      html: 'input',
      type: 'text',
      attr: {class: 'form-inline form-control', title: 'Topic Filter'},
    },
    publisher_count: {
      html: 'input',
      type: 'text',
      attr: {class: 'form-inline form-control', title: 'Publisher Count Filter'},
    },
    subscribers: {
      html: 'input',
      type: 'text',
      attr: {class: 'form-inline form-control', title: 'Subscribers Filter'},
    },
    null: {}
  };

  $scope.dtColumns.forEach((column, i) => {
    $scope.dtOptions.lightColumnFilterOptions[i] = lightColumnFilterOptions[column.mData];
  });

  $scope.$on('userChange', function() {
    $scope.response = undefined;

    if ($scope.dtInstance) {
      $scope.dtInstance.reloadData(() => {}, false);
    }
  });

  $scope.doDelete = function(topic_id) {
    TopicService.deleteTopic(topic_id).then(() => {
      if ($scope.dtInstance) {
        $scope.dtInstance.reloadData();
      }
    });
  };

  $scope.doRemoveSubscriber = function(topic_id, subscriber) {
    TopicService.removeSubscriber(topic_id, subscriber).then(() => {
      if ($scope.dtInstance) {
        $scope.dtInstance.reloadData();
      }
    });
  };

  $scope.doResetCount = function(topic_id, subscriber = null) {
    TopicService.resetCount(topic_id, subscriber).then(() => {
      if ($scope.dtInstance) {
        $scope.dtInstance.reloadData();
      }
    });
  };

  $scope.doSync = function() {
    TopicService.syncTopics().then(() => {
      if ($scope.dtInstance) {
        $scope.dtInstance.reloadData();
      }
    });
  };

  $scope.doAddSubscriber = function(topic) {
    const modalInstance = $uibModal.open({
      controller: 'NewTopicController',
      template: newTopicTemplate,
      resolve: {
        isNew: false,
        editTopic: topic,
      },
    });
    modalInstance.result.then(
        (create) => { 
          TopicService.createTopic(create).then(() => {
            if ($scope.dtInstance) {
              $scope.dtInstance.reloadData();
            }
          });
        },
        // We don't really need to do anything if canceled
        () => {},
    );
  };

  $scope.doCreate = function(topic) {
    const modalInstance = $uibModal.open({
      controller: 'NewTopicController',
      template: newTopicTemplate,
      resolve: {
        isNew: true,
        editTopic: topic,
      },
    });
    modalInstance.result.then(
        (create) => { 
          TopicService.createTopic(create).then(() => {
            if ($scope.dtInstance) {
              $scope.dtInstance.reloadData();
            }
          });
        },
        // We don't really need to do anything if canceled
        () => {},
    );
  };
}
