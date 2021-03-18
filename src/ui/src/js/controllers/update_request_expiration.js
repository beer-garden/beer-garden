updateRequestExpirationController.$inject = [
  '$scope',
  '$uibModalInstance',
  'RequestService',
  'model',
  'request',
];

/**
 * newUserController - New User controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export default function updateRequestExpirationController(
  $scope,
  $uibModalInstance,
  RequestService,
  model,
  request,
  ) {
  $scope.schema =  {
                    'type': 'object',
                    'properties': {
                                'expiration_date': {
                                  'title': 'Expiration Date',
                                  'type': ['integer', 'null'],
                                  'format': 'datetime',
                                },
                              },
                    };
  $scope.form = [
                    {
                      'type': 'section',
                      'items': [
                        'expiration_date',
                      ],
                    },
                    {
                      'type': 'section',
                      'htmlClass': 'row',
                      'items': [
                        {
                          'type': 'button', 'style': 'btn-warning w-100 ', 'title': 'Reset',
                          'onClick': 'reset(form, model)', 'htmlClass': 'col-md-2',
                        },
                        {
                          'type': 'submit', 'style': 'btn-primary w-100',
                          'title': 'Update Expiration', 'htmlClass': 'col-md-10',
                        },
                      ],
                    },
                ];
  $scope.request = request;
  $scope.model = model;
  $scope.showAlert = false;

  $scope.failureCallback = function(response) {
      $scope.showAlert = true;
      if (response.statusText == "Not Found"){
        $scope.errorMsg = "Request has been removed";
      }
      else {
        $scope.errorMsg = response.data.message;
      }
   };

   $scope.successCallback = function(data) {
           $uibModalInstance.close(data);
      };
  $scope.requestCheck = false;
  $scope.result = RequestService.getRequest($scope.request.id).then(
        (response) => {
          $scope.requestCheck = true;
        },
        $scope.failureCallback,
  );

  $scope.ok = function(form, model) {
    let result = RequestService.updateRequestExpiration($scope.request, model['expiration_date']).then(
      (response) => {
        $scope.successCallback(response.data);
      },
      $scope.failureCallback,
    );

  };
  $scope.reset = function(form, model) {
      $scope.showAlert = false;
      $scope.model = {};

      $scope.$broadcast('schemaFormRedraw');
    };

  $scope.close = function() {
    $uibModalInstance.dismiss('cancel');
  };
};