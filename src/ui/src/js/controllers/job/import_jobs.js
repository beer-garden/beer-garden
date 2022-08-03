import template from '../../../templates/import_jobs.html';

jobImportController.$inject = [
  '$scope',
  '$rootScope',
  '$uibModal',
  '$state',
  'JobService',
];

/**
 * jobImportController - Controller for job import.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $rootScope        Angular's $rootScope object.
 * @param  {Object} $uibModal         Angular UI's $uibModal object.
 * @param  {Object} $state
 * @param  {Object} JobService        Beer-Garden's job service.
 */
export function jobImportController(
    $scope,
    $rootScope,
    $uibModal,
    $state,
    JobService,
) {
  $scope.response = $rootScope.gardensResponse;
  $scope.data = $rootScope.systems;

  $scope.openImportJobsPopup = function() {
    const popupInstance = $uibModal.open({
      animation: true,
      controller: 'JobImportModalController',
      template: template,
    });

    popupInstance.result.then(function(resolvedResponse) {
      const jsonFileContents = resolvedResponse.jsonFileContents;
      JobService.importJobs(jsonFileContents).then(
          function(response) {
            $state.reload();
          },
          function(response) {
            alert('Failure! Server returned status ' + response.status);
          },
      );
    }, angular.noop);
  };
}

jobImportModalController.$inject = ['$scope', '$window', '$uibModalInstance'];

/**
 * jobImportModalController - Controller for the job import popup window.
 * @param {Object} $scope Angular's $scope object.
 * @param {Object} $window Object for the browser window.
 * @param {Object} $uibModalInstance Object for the modal popup window.
 */
export function jobImportModalController($scope, $window, $uibModalInstance) {
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
