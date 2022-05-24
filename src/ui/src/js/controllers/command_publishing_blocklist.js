import template from '../../templates/add_command_publishing_blocklist.html';

commandPublishingBlocklistController.$inject = [
  '$scope',
  '$rootScope',
  'DTOptionsBuilder',
  'CommandPublishingBlocklistService',
  '$uibModal',
];

/**
 * commandPublishingBlocklistController - Controller for viewing and
 * removing commands in the publishing blocklist.
 * @param  {Object} $scope         Angular's $scope object.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {Object} DTOptionsBuilder
 * @param  {Object} CommandPublishingBlocklistService command publishing blocklist service object
 * @param  {$scope} $uibModal     Angular UI's $uibModal object.
 */
export default function commandPublishingBlocklistController(
    $scope,
    $rootScope,
    DTOptionsBuilder,
    CommandPublishingBlocklistService,
    $uibModal,
) {
  $scope.data = [];
  $scope.alerts = [];

  $scope.dtOptions = DTOptionsBuilder.newOptions()
      .withOption('autoWidth', false)
      .withOption(
          'pageLength',
          10,
      )
      .withOption('order', [
        [0, 'asc'],
        [1, 'asc'],
        [2, 'asc'],
        [3, 'asc'],
      ])
      .withLightColumnFilter({
        0: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'Namespace Filter', style: 'height: 1%'},
        },
        1: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'System Filter', style: 'height: 1%'},
        },
        2: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'Commands Filter', style: 'height: 1%'},
        },
        3: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'Status Filter', style: 'height: 1%'},
        },
      })
      .withBootstrap();

  $scope.deleteBlocklistEntry = function(blockedCommandId, index) {
    CommandPublishingBlocklistService.
        deleteCommandPublishingBlocklist(blockedCommandId).then(
            (response) => {
              $scope.data[index].status = 'REMOVE_REQUESTED';
            },
            (errorResponse) => {
              $scope.alerts.push({
                type: 'danger',
                msg: `Failed to remove command! Server returned status ${errorResponse.statusText}`,
              });
            },
        );
  };

  function getData() {
    return $scope.data;
  }

  $scope.openPopup = function() {
    const popupInstance = $uibModal.open({
      template: template,
      resolve: {
        commandBlocklist: getData,
      },
      controller: 'AddCommandPublishingBlocklistController',
      windowClass: 'app-modal-window',
    });

    popupInstance.result.then(function(resolvedResponse) {
    }, angular.noop);
  };

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data.command_publishing_blocklist;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = [];
  };

  $scope.response = $rootScope.sysResponse;

  function loadCommandPublishingBlocklist() {
    $scope.response = undefined;
    CommandPublishingBlocklistService.getCommandPublishingBlocklist()
        .then($scope.successCallback, $scope.failureCallback);
  }
  loadCommandPublishingBlocklist();
}
