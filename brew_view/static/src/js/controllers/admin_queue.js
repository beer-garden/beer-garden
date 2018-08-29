import angular from 'angular';

adminQueueController.$inject = [
  '$rootScope',
  '$scope',
  '$q',
  '$compile',
  '$window',
  '$location',
  '$interval',
  '$http',
  'DTOptionsBuilder',
  'DTColumnBuilder',
  'QueueService',
];

/**
 * adminQueueController - Angular controller for queue index page.
 * @param  {$rootScope} $rootScope   Angular's $rootScope object.
 * @param  {$scope} $scope           Angular's $scope object.
 * @param  {$q} $q                   Angular's $q object.
 * @param  {$compile} $compile       Angular's $compile object.
 * @param  {$window} $window         Angular's $window object.
 * @param  {$location} $location     Angular's $location object.
 * @param  {$interval} $interval     Angular's $interval object.
 * @param  {$http} $http             Angular's $http object.
 * @param  {Object} DTOptionsBuilder Datatables' options builder object.
 * @param  {Object} DTColumnBuilder  Datatables' column builder object.
 * @param  {Object} QueueService     Beer-Garden's queue service object.
 */
export default function adminQueueController(
    $rootScope,
    $scope,
    $q,
    $compile,
    $window,
    $location,
    $interval,
    $http,
    DTOptionsBuilder,
    DTColumnBuilder,
    QueueService) {
  $scope.setWindowTitle('queues');

  let preconditionPromise;

  $scope.alerts = [];
  $scope.dtInstance = null;

  $scope.dtOptions = DTOptionsBuilder
    .fromFnPromise(
      () => {
        // Waiting for preconditionPromise ensures that the rootScope config
        // and systems are ready first
        return preconditionPromise.then(
          () => {
            return QueueService.getQueues().then(
              $scope.successCallback,
              $scope.failureCallback
            );
          },
          $scope.failureCallback
        );
      }
    )
    .withBootstrap()
    .withDisplayLength(50)
    .withDataProp('data')
    .withOption('order', [4, 'asc'])
    .withOption('autoWidth', false)
    .withOption('createdRow', function(row, data, dataIndex) {
      $compile(angular.element(row).contents())($scope);
    });

  $scope.dtColumns = [
    DTColumnBuilder
      .newColumn(null)
      .withTitle('')
      .withOption('width', '15px')
      .notSortable()
      .renderWith(function(data, type, full) {
        const baseUrl = 'http://{{queueHost}}:{{queueAdminPort}}';
        const path = '/#/queues/{{queueVirtualHost}}/' + full.name;
        const fullUrl = baseUrl + path;
        return '<a ng-href="' + fullUrl + '" target="_blank">' +
                 '<i class="fa fa-database fa-fw icon-color"></i>' +
               '</a>';
      }),
    DTColumnBuilder
      .newColumn('system')
      .withTitle('System')
      .renderWith(function(data, type, full) {
        let version = $rootScope.getVersionForUrl($rootScope.findSystemByID(full.system_id));
        return '<a ui-sref=' +
               '"system({name: \'' + full.system+ '\', version: \'' + version + '\'})">' +
               (full.display || data) + '</a>';
      }),
    DTColumnBuilder
      .newColumn('version')
      .withTitle('Version'),
    DTColumnBuilder
      .newColumn('instance')
      .withTitle('Instance Name'),
    DTColumnBuilder
      .newColumn('name')
      .withTitle('Queue Name'),
    DTColumnBuilder
      .newColumn('size')
      .withTitle('Queued Messages'),
    DTColumnBuilder
      .newColumn(null)
      .withTitle('Actions')
      .withOption('width', '10%')
      .notSortable()
      .renderWith(function(data, type, full) {
        return '<button class="btn btn-danger btn-block word-wrap-button" ' +
            'ng-click="clearQueue(\'' + full.name + '\')">Clear Queue</button>';
      }),
  ];

  $scope.instanceCreated = function(_instance) {
    $scope.dtInstance = _instance;
  };

  $scope.clearQueue = function(queueName) {
    QueueService.clearQueue(queueName).then(
      $scope.addSuccessAlert,
      $scope.addErrorAlert
    );
  };

  $scope.clearAllQueues = function() {
    QueueService.clearQueues().then(
      $scope.addSuccessAlert,
      $scope.addErrorAlert
    );
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.addSuccessAlert = function(response) {
    $scope.alerts.push({
      type: 'success',
      msg: 'Success! Please allow 5 seconds for the message counts to update.',
    });
  };

  $scope.addErrorAlert = function(response) {
    let msg = 'Uh oh! It looks like there was a problem clearing the queue.\n';
    if (response.data !== undefined && response.data !== null) {
      msg += response.data;
    }
    $scope.alerts.push({
      type: 'danger',
      msg: msg,
    });
  };

  let poller = $interval(function() {
    $scope.dtInstance.reloadData(() => {}, false);
  }, 5000);

  $scope.$on('$destroy', function() {
    if (angular.isDefined(poller)) {
      $interval.cancel(poller);
      poller = undefined;
    }
  });

  $scope.successCallback = function(response) {
    $scope.response = response;
    return response.data;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
  };

  const ensurePreconditions = function() {
    // The table is constructed from getQueues but we need to wait for the
    // application to have loaded systems and config first
    let configPromise = $rootScope.configPromise.then(
      () => {
        $scope.queueHost = $scope.config.amqHost;
        $scope.queuePort = $scope.config.amqPort;
        $scope.queueAdminPort = $scope.config.amqAdminPort;
        $scope.queueVirtualHost = encodeURIComponent($scope.config.amqVirtualHost);
      },
      $scope.failureCallback
    );

    preconditionPromise = $q.all({
      config: configPromise,
      systems: $rootScope.systemsPromise,
    });
  };

  $scope.$on('userChange', () => {
    $scope.response = undefined;

    // Make sure that preconditions are still good
    ensurePreconditions();

    // Then give the datatable a kick
    $scope.dtInstance.reloadData(() => {}, false);
  });

  ensurePreconditions();
};
