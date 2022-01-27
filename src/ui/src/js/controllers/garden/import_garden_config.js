import template from '../../../templates/import_garden_config.html';

gardenConfigImportController.$inject = [
  '$scope',
  '$rootScope',
  '$uibModal',
  '$state',
];

/**
 * gardenConfigImportController - Controller for garden config import.
 * @param  {Object} $scope                     Angular's $scope object.
 * @param  {Object} $rootScope                 Angular's $rootScope object.
 * @param  {Object} $uibModal                  Angular UI's $uibModal object.
 * @param  {Object} $state                     State
 */
export function gardenConfigImportController(
    $scope,
    $rootScope,
    $uibModal,
    $state,
) {
  $scope.response = $rootScope.sysResponse;

  $scope.openImportGardenConfigPopup = () => {
    const popupInstance = $uibModal.open({
      animation: true,
      controller: 'GardenConfigImportModalController',
      template: template,
    });

    popupInstance.result.then((resolvedResponse) => {
      const jsonFileContents = resolvedResponse.jsonFileContents;
      const newConfig = JSON.parse(jsonFileContents);

      $scope.updateModelFromImport(newConfig);
      $scope.submitImport($scope.data);
      $state.reload();
    }, () => console.log('Garden import cancelled'));
  };
}

gardenConfigImportModalController.$inject =
    ['$scope', '$window', '$uibModalInstance'];

/**
 * gardenConfigImportModalController - Controller for the garden config import
 * popup window.
 *
 * @param {Object} $scope Angular's $scope object.
 * @param {Object} $window Object for the browser window.
 * @param {Object} $uibModalInstance Object for the modal popup window.
 */
export function gardenConfigImportModalController(
    $scope, $window, $uibModalInstance) {
  $scope.import = {};
  $scope.fileName = undefined;
  $scope.fileContents = undefined;
  $scope.fileIsGoodJson = true;

  $scope.inputClicker = function() {
    $window.document.getElementById('fileSelectHiddenControl').click();
  };

  $scope.doImport = function() {
    $scope.import['jsonFileContents'] = $scope.fileContents;
    $uibModalInstance.close($scope.import);
  };

  $scope.cancelImport = function() {
    $uibModalInstance.dismiss('cancel');
  };

  function isParsableJson(string) {
    try {
      JSON.parse(string);
    } catch (e) {
      return false;
    }
    return true;
  }

  $scope.onFileSelected = function(event) {
    const theFile = event.target.files[0];
    $scope.fileName = theFile.name;

    const reader = new FileReader();
    reader.onload = function(e) {
      $scope.$apply(function() {
        const result = reader.result;
        const isGoodJson = isParsableJson(result);

        if (isGoodJson) {
          $scope.fileContents = result;
          $scope.fileIsGoodJson = true;
        } else {
          $scope.fileIsGoodJson = false;
        }
      });
    };
    reader.readAsText(theFile);
  };
}
