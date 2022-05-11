import template from '../../templates/add_command_publishing_blocklist.html';

CommandPublishingBlocklistController.$inject = [
  '$scope',
  '$rootScope',
  'DTOptionsBuilder',
  'CommandPublishingBlocklistService',
  '$uibModal',
];

/**
 * systemIndexController - Controller for the system index page.
 * @param  {Object} $scope         Angular's $scope object.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {Object} DTOptionsBuilder
 * @param  {Object} CommandPublishingBlocklistService command publishing blocklist service object
 * @param  {$scope} $uibModal     Angular UI's $uibModal object.
 */
export default function CommandPublishingBlocklistController(
    $scope,
    $rootScope,
    DTOptionsBuilder,
    CommandPublishingBlocklistService,
    $uibModal,
) {
  $scope.setWindowTitle();
  $scope.blockedList = false;

  $scope.data = [];

  $scope.dtOptions = DTOptionsBuilder.newOptions()
      .withOption('autoWidth', false)
      .withOption(
          'pageLength',
          10,
      )
      .withOption('order', [
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
      })
      .withBootstrap();

  $scope.deleteBlocklistEntry = function(blockedCommandId, index) {
    const promise = CommandPublishingBlocklistService.
        deleteCommandPublishingBlocklist(blockedCommandId);
    promise.then(
        (response) => {
          $scope.data.splice(index, 1);
        },
    );
  };

  $scope.instanceCreated = function(_instance) {
    $scope.dtInstance = _instance;
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

  const dataAddCheck = function(data, value) {
    for (let i = 0; i < data.length; i++) {
      if (data[i] === value) {
        return false;
      }
    }
    return true;
  };

  $scope.formatSystemsToData = function(systems) {
    const data = [];
    for (let i = 0; i < systems.length; i++) {
      const system = systems[i];
      for (let n = 0; n < system.commands.length; n++) {
        const command = system.commands[n];
        if (dataAddCheck(data, {
          'namespace': system.namespace,
          'system': system.name,
          'command': command.name,
        })) {
          data.push({'namespace': system.namespace,
            'system': system.name,
            'command': command.name,
            'status': '',
          });
        }
      }
    }
    return data;
  };

  $scope.response = $rootScope.sysResponse;

  function loadCommandPublishingBlocklist() {
    $scope.response = undefined;
    CommandPublishingBlocklistService.getCommandPublishingBlocklist()
        .then($scope.successCallback, $scope.failureCallback);
  }
  loadCommandPublishingBlocklist();
}
