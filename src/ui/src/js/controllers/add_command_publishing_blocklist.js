
addCommandPublishingBlocklistController.$inject = [
  '$scope',
  '$uibModalInstance',
  '$rootScope',
  'DTOptionsBuilder',
  'CommandPublishingBlocklistService',
  '$state',
  'commandBlocklist',
];

/**
 * addCommandPublishingBlocklistController - Controller for adding commands to publishing blocklist.
 * @param  {Object} $scope         Angular's $scope object.
 * @param {Object} $uibModalInstance Object for the modal popup window.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {Object} DTOptionsBuilder
 * @param  {Object} CommandPublishingBlocklistService command publishing blocklist service object
 * @param  {Object} $state,     Angular's $state, object.
 * @param {Object} commandBlocklist
 */
export default function addCommandPublishingBlocklistController(
    $scope,
    $uibModalInstance,
    $rootScope,
    DTOptionsBuilder,
    CommandPublishingBlocklistService,
    $state,
    commandBlocklist,
) {
  $scope.instanceCreated = function(_instance) {
    $scope.dtInstance = _instance;
  };

  $scope.dtOptions = DTOptionsBuilder.newOptions()
      .withOption('autoWidth', false)
      .withOption(
          'pageLength', 10,
      )
      .withOption('order', [
        [1, 'asc'],
        [2, 'asc'],
        [3, 'asc'],
      ])
      .withLightColumnFilter({
        0: {
          html: 'input',
          type: 'checkbox',
          attr: {
            'class': 'pull-right',
            'title': 'Select All',
            'id': 'select-all-checkbox',
            'style': 'width: 1%;',
            'onclick': 'document.getElementById("select-all-hidden-checkbox").click()',
          },
        },
        1: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'Namespace Filter', style: 'height: 1%'},
        },
        2: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'System Filter', style: 'height: 1%'},
        },
        3: {
          html: 'input',
          type: 'text',
          attr: {class: 'form-inline form-control', title: 'Commands Filter', style: 'height: 1%'},
        },
      })
      .withBootstrap();

  $scope.cancelSubmission = function() {
    $uibModalInstance.dismiss('cancel');
  };

  $scope.onCommandCheckChange = function(command) {
    command.isChecked = !command.isChecked;
    $scope.selectAllValue = false;
    document.getElementById('select-all-checkbox')['checked'] = false;
  };

  $scope.submitBlocklistEntries = function() {
    CommandPublishingBlocklistService.addToBlocklist(
        $scope.data.filter((item) => item.isChecked),
    ).then(
        (response) => {
          $uibModalInstance.close();
          $state.reload();
          alert('Successfully added commands to command publishing blocklist.');
        },
        (errorResponse) => {
          alert(`Failure! Server returned status ${errorResponse.statusText}`);
        },
    );
  };

  $scope.selectAllValue = false;

  $scope.selectAll = function() {
    const filteredData = $scope.dtInstance.DataTable.rows( {search: 'applied'} ).data();
    $scope.selectAllValue = !$scope.selectAllValue;
    for (let i = 0; i < filteredData.length; i++) {
      const command = $scope.data.find((item) => item.namespace === filteredData[i][1] &&
          item.system === filteredData[i][2] &&
          item.command === filteredData[i][3]);
      $scope.data[$scope.data.indexOf(command)].isChecked = $scope.selectAllValue;
    }
  };

  $scope.canSubmit = function() {
    return $scope.data.filter((item) => item.isChecked).length === 0;
  };

  $scope.formatSystemsToData = function(systems) {
    const data = [];
    systems.forEach((system) => {
      system.commands.forEach((command) => {
        const value = {
          'namespace': system.namespace,
          'system': system.name,
          'command': command.name,
          'isChecked': false,
        };
        if (
          !data.find((item) =>
            item.namespace === value.namespace &&
            item.system === value.system &&
            item.command === value.command) &&
          !commandBlocklist.find((item) =>
            item.namespace === value.namespace &&
            item.system === value.system &&
            item.command === value.command)
        ) {
          data.push(value);
        }
      });
    });
    return data;
  };
  $scope.response = $rootScope.sysResponse;
  $scope.data = $scope.formatSystemsToData($rootScope.systems);
}
