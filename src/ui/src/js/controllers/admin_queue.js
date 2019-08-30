import angular from 'angular';

adminQueueController.$inject = [
  '$rootScope',
  '$scope',
  '$q',
  '$compile',
  '$interval',
  'DTOptionsBuilder',
  'DTColumnBuilder',
  'SystemService',
  'QueueService',
];

/**
 * adminQueueController - Angular controller for queue index page.
 * @param  {Object} $rootScope        Angular's $rootScope object.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $q                Angular's $q object.
 * @param  {Object} $compile          Angular's $compile object.
 * @param  {Object} $interval         Angular's $interval object.
 * @param  {Object} DTOptionsBuilder  Datatables' options builder object.
 * @param  {Object} DTColumnBuilder   Datatables' column builder object.
 * @param  {Object} SystemService     Beer-Garden's system service object.
 * @param  {Object} QueueService      Beer-Garden's queue service object.
 */
export default function adminQueueController(
    $rootScope,
    $scope,
    $q,
    $compile,
    $interval,
    DTOptionsBuilder,
    DTColumnBuilder,
    SystemService,
    QueueService) {
  $scope.setWindowTitle('queues');

  $scope.alerts = [];
  $scope.dtInstance = null;

  $scope.dtOptions = DTOptionsBuilder
    .fromFnPromise(
      () => {
        return QueueService.getQueues().then(
          $scope.successCallback,
          $scope.failureCallback
        );
        // return $q.all({
        //   systems: SystemService.promise(),
        //   queues: QueueService.getQueues(),
        // }).then(
        //   $scope.successCallback,
        //   $scope.failureCallback
        // );
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
      .newColumn('system')
      .withTitle('System')
      .renderWith(function(data, type, full) {
        let version = SystemService.getVersionForUrl(SystemService.findSystemByID(full.system_id));
        return '<a ui-sref=' +
               '"base.namespace.system({systemName: \'' + full.system+ '\', systemVersion: \'' + version + '\'})">' +
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
    // $scope.response = response.queues;
    $scope.response = response;
    return $scope.response.data;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
  };

  // $scope.$on('userChange', () => {
  //   $scope.response = undefined;

  //   // Then give the datatable a kick
  //   $scope.dtInstance.reloadData(() => {}, false);
  // });

  // // Force reloading so switching namespaces works
  // SystemService.loadSystems();
};
