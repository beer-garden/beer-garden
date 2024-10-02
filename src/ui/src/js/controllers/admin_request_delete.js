import angular from 'angular';

adminRequestDeleteController.$inject = [
  '$scope',
  '$uibModalInstance',
  'RequestService',
  'system',
  'instance',
];

/**
 * adminRequestDeleteController - Angular controller for queue index page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $uibModalInstance Modal instance.
 * @param  {Object} $interval         Angular's $interval object.
 * @param  {Object} RequestService      Beer-Garden's request service object.
 * @param  {Object} system
 * @param  {Object} instance
 */
export default function adminRequestDeleteController(
  $scope,
  $uibModalInstance,
  RequestService,
  system,
  instance,
) {
  $scope.alerts = [];
  $scope.system = system;
  $scope.instance = instance;
  $scope.queues = [];

  $scope.success_count = 0;
  $scope.cancelled_count = 0;
  $scope.error_count = 0;
  $scope.created_count = 0;
  $scope.received_count = 0;
  $scope.in_progress_count = 0;
  $scope.all_count = 0;

  $scope.deleteCancelRequests = function (status, is_cancel = false) {
    let deleteParams = {
      "namespace": $scope.system.namespace,
      "system": $scope.system.name,
      "system_version": $scope.system.version,
      "instance_name": $scope.instance.name
    };

    if (is_cancel){
      deleteParams["is_cancel"] = true
    }

    if (status != "ALL") {
      deleteParams["status"] = status;
    }

    RequestService.deleteRequests(deleteParams).then($scope.addSuccessAlert, $scope.addDeleteErrorAlert);

  };

  $scope.closeAlert = function (index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.addSuccessAlert = function (response) {
    $scope.alerts.push({
      type: 'success',
      msg: 'Success! Requests have been deleted.',
    });
    $scope.loadRequests();
  };

  $scope.closeDialog = function () {
    $uibModalInstance.close();
  };

  $scope.addDeleteErrorAlert = function (response) {
    let msg = 'Uh oh! It looks like there was a problem deleted the Requests.\n';
    if (response.data !== undefined && response.data !== null) {
      msg += response.data;
    }
    $scope.alerts.push({
      type: 'danger',
      msg: msg,
    });
  };

  $scope.buildFilter = function (status) {
    return {
      "include_children": true,
      "length": 1,
      "columns": [
        {
          "data": "namespace__exact",
          "name": "",
          "searchable": true,
          "orderable": true,
          "search": {
            "value": $scope.system.namespace,
            "regex": false
          }
        },
        {
          "data": "system__exact",
          "name": "",
          "searchable": true,
          "orderable": true,
          "search": {
            "value": $scope.system.name,
            "regex": false
          }
        },
        {
          "data": "system_version__exact",
          "name": "",
          "searchable": true,
          "orderable": true,
          "search": {
            "value": $scope.system.version,
            "regex": false
          }
        },
        {
          "data": "instance_name__exact",
          "name": "",
          "searchable": true,
          "orderable": true,
          "search": {
            "value": $scope.instance.name,
            "regex": false
          }
        },
        {
          "data": "status",
          "name": "",
          "searchable": true,
          "orderable": true,
          "search": {
            "value": ((status == "ALL") ? "" : status),
            "regex": false
          }
        },
      ]
    };
  }

  $scope.loadRequests = function () {

    $scope.all_count = 0;
    $scope.success_count = 0;
    $scope.cancelled_count = 0;
    $scope.error_count = 0;
    $scope.created_count = 0;
    $scope.received_count = 0;
    $scope.in_progress_count = 0;

    RequestService.getRequests($scope.buildFilter("SUCCESS")).then(
      (response) => {
        $scope.success_count = parseInt(response.headers('recordsFiltered'));
        $scope.all_count += $scope.success_count;
      },
      (response) => {
        let msg = 'Uh oh! It looks like there was a problem counting the SUCCESS Requests.\n';
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        $scope.alerts.push({
          type: 'danger',
          msg: msg,
        });
      }
    );

    RequestService.getRequests($scope.buildFilter("CANCELED")).then(
      (response) => {
        $scope.cancelled_count = parseInt(response.headers('recordsFiltered'));
        $scope.all_count += $scope.cancelled_count;
      },
      (response) => {
        let msg = 'Uh oh! It looks like there was a problem counting the CANCELED Requests.\n';
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        $scope.alerts.push({
          type: 'danger',
          msg: msg,
        });
      }
    );

    RequestService.getRequests($scope.buildFilter("ERROR")).then(
      (response) => {
        $scope.error_count = parseInt(response.headers('recordsFiltered'));
        $scope.all_count += $scope.error_count;
      },
      (response) => {
        let msg = 'Uh oh! It looks like there was a problem counting the ERROR Requests.\n';
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        $scope.alerts.push({
          type: 'danger',
          msg: msg,
        });
      }
    );

    RequestService.getRequests($scope.buildFilter("CREATED")).then(
      (response) => {
        $scope.created_count = parseInt(response.headers('recordsFiltered'));
        $scope.all_count += $scope.created_count;
      },
      (response) => {
        let msg = 'Uh oh! It looks like there was a problem counting the CREATED Requests.\n';
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        $scope.alerts.push({
          type: 'danger',
          msg: msg,
        });
      }
    );

    RequestService.getRequests($scope.buildFilter("RECEIVED")).then(
      (response) => {
        $scope.received_count = parseInt(response.headers('recordsFiltered'));
        $scope.all_count += $scope.received_count;
      },
      (response) => {
        let msg = 'Uh oh! It looks like there was a problem counting the RECEIVED Requests.\n';
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        $scope.alerts.push({
          type: 'danger',
          msg: msg,
        });
      }
    );

    RequestService.getRequests($scope.buildFilter("IN_PROGRESS")).then(
      (response) => {
        $scope.in_progress_count = parseInt(response.headers('recordsFiltered'));
        $scope.all_count += $scope.in_progress_count;
      },
      (response) => {
        let msg = 'Uh oh! It looks like there was a problem counting the IN PROGRESS Requests.\n';
        if (response.data !== undefined && response.data !== null) {
          msg += response.data;
        }
        $scope.alerts.push({
          type: 'danger',
          msg: msg,
        });
      }
    );


  };

  $scope.loadRequests();
}
