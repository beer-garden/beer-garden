
AddCommandPublishingBlocklistController.$inject = [
  '$scope',
  '$uibModalInstance',
  '$rootScope',
  'DTOptionsBuilder',
  'CommandPublishingBlocklistService',
  '$state',
  'commandBlocklist',
];

/**
 * systemIndexController - Controller for the system index page.
 * @param  {Object} $scope         Angular's $scope object.
 * @param {Object} $uibModalInstance Object for the modal popup window.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {Object} DTOptionsBuilder
 * @param  {Object} CommandPublishingBlocklistService command publishing blocklist service object
 * @param  {Object} $state,     Angular's $state, object.
 * @param {Object} commandBlocklist
 */
export default function AddCommandPublishingBlocklistController(
    $scope,
    $uibModalInstance,
    $rootScope,
    DTOptionsBuilder,
    CommandPublishingBlocklistService,
    $state,
    commandBlocklist,
) {
  $scope.dtOptions = DTOptionsBuilder.newOptions()
      .withOption('autoWidth', false)
      .withOption(
          'pageLength', 10,
      )
      .withOption('order', [
        [0, 'asc'],
        [1, 'asc'],
        [2, 'asc'],
      ])
      .withLightColumnFilter({
        1: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'Namespace Filter'},
        },
        2: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'System Filter'},
        },
        3: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'Commands Filter'},
        },
      })
      .withBootstrap();

  $scope.commandBlocklistAdd = [];

  $scope.onChangeCommandBlocklistAdd = function(command) {
    if (!$scope.commandBlocklistAdd.includes(command)) {
      $scope.commandBlocklistAdd.push(command);
    } else {
      const index = $scope.commandBlocklistAdd.indexOf(command);
      if (index > -1) {
        $scope.commandBlocklistAdd.splice(index, 1);
      }
    }
  };

  $scope.cancelSubmission = function() {
    $uibModalInstance.dismiss('cancel');
  };

  $scope.submitBlocklistEntries = function() {
    const promise = CommandPublishingBlocklistService.addToBlocklist(
        $scope.commandBlocklistAdd,
    );
    promise.then(
        (response) => {
          $uibModalInstance.close();
          $state.reload();
          alert('Successfully added commands to command publishing blocklist.');
        },
        (errorResponse) => {
          alert(`Failure! Server returned status ${errorResponse.status}`);
        },
    );
  };

  $scope.instanceCreated = function(_instance) {
    $scope.dtInstance = _instance;
  };

  function notInCommandBlocklist(value) {
    for (let i = 0; i < commandBlocklist.length; i++) {
      const blockedCommand = commandBlocklist[i];
      if (value.namespace===blockedCommand.namespace &&
          value.system===blockedCommand.system &&
          value.command===blockedCommand.command) {
        return false;
      }
    }
    return true;
  }

  $scope.formatSystemsToData = function(systems) {
    const data = [];
    for (let i = 0; i < systems.length; i++) {
      const system = systems[i];
      for (let n = 0; n < system.commands.length; n++) {
        const command = system.commands[n];
        const value = {
          'namespace': system.namespace,
          'system': system.name,
          'command': command.name,
        };
        if (!JSON.stringify(data).includes(JSON.stringify(value)) &&
            notInCommandBlocklist(value)) {
          data.push(value);
        }
      }
    }
    return data;
  };
  $scope.response = $rootScope.sysResponse;
  $scope.data = $scope.formatSystemsToData($rootScope.systems);
}
