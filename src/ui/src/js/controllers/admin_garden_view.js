import _ from 'lodash';

adminGardenViewController.$inject = [
  '$scope',
  'GardenService',
  'EventService',
  '$stateParams',
];

/**
 * adminGardenController - Garden management controller.
 * @param  {Object} $scope           Angular's $scope object.
 * @param  {Object} GardenService    Beer-Garden's garden service object.
 * @param  {Object} EventService     Beer-Garden's event service.
 * @param  {Object} $stateParams     State params
 */
export default function adminGardenViewController(
    $scope,
    GardenService,
    EventService,
    $stateParams,
) {
  $scope.setWindowTitle('Configure Garden');
  $scope.alerts = [];
  $scope.formErrors = [];

  $scope.isLocal = false;
  $scope.gardenSchema = null;
  $scope.gardenForm = null;
  $scope.gardenModel = {};

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  const generateGardenSF = function() {
    $scope.gardenSchema = GardenService.SCHEMA;
    $scope.gardenForm = GardenService.FORM;
    $scope.gardenModel = GardenService.serverModelToForm($scope.data);

    $scope.$broadcast('schemaFormRedraw');
  };

  $scope.updateModelFromImport = (newGardenDefinition) => {
    const existingData = $scope.data;
    const newConnType = newGardenDefinition['connection_type'];
    const newConnParams = newGardenDefinition['connection_params'];

    const newData = {...existingData,
      connection_type: newConnType,
      connection_params: newConnParams};

    $scope.data = newData;

    generateGardenSF();
  };

  $scope.successCallback = function(response) {
    console.log('response', response);
    $scope.response = response;
    $scope.data = response.data;

    if ($scope.data.id == null || $scope.data.connection_type == 'LOCAL') {
      $scope.isLocal = true;
      $scope.alerts.push({
        type: 'info',
        msg: 'Since this is the local Garden it\'s not possible to modify ' +
        'connection information',
      });
    }

    generateGardenSF();
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = [];
  };

  const loadGarden = function() {
    GardenService.getGarden($stateParams.name).then(
        $scope.successCallback,
        $scope.failureCallback,
    );
  };

  const loadAll = function() {
    $scope.response = undefined;
    $scope.data = [];

    loadGarden();
  };

  const errorPlaceholder = 'errorPlaceholder';

  const resetAllValidationErrors = () => {
    const updater = (field) => {
      $scope.$broadcast(
          `schemaForm.error.${field}`,
          errorPlaceholder,
          true,
      );
    };

    // this is brittle because it's a copy/paste from the form code,
    // but will suffice for now because we expect the form won't
    // ever be updated in this version of the UI
    const httpFlds = [
      'http.host',
      'http.port',
      'http.url_prefix',
      'http.ssl',
      'http.ca_cert',
      'http.ca_verify',
      'http.client_cert',
    ];
    const stompFlds = [
      'stomp.host',
      'stomp.port',
      'stomp.send_destination',
      'stomp.subscribe_destination',
      'stomp.username',
      'stomp.password',
      'stomp.ssl',
      'stomp.headers',
    ];

    httpFlds.map(updater);
    stompFlds.map(updater);
  };

  const fieldErrorName =
    (entryPoint, fieldName) => `schemaForm.error.${entryPoint}.${fieldName}`;

  const fieldErrorMessage =
    (errorObject) => {
      const error = typeof errorObject === 'string' ?
        Array(errorObject) : errorObject;
      return error[0];
    };

  const updateValidationMessages = (entryPoint, errorsObject) => {
    for (const fieldName in errorsObject) {
      if (errorsObject.hasOwnProperty(fieldName)) {
        $scope.$broadcast(
            fieldErrorName(entryPoint, fieldName),
            errorPlaceholder,
            fieldErrorMessage(errorsObject[fieldName]),
        );
      }
    }
  };

  $scope.addErrorAlert = function(response) {
    /* If we have an error response that indicates that the connection
     * parameters are incorrect, display a warning alert specifying which of the
     * entry points are wrong. Then update the validation of the individual
     * schema fields.
     *
     * NOTE: individual field validation is not currently used
     */
    if (response['data'] && response['data']['message']) {
      const messageData = String(response['data']['message']);
      const singleQuoteRegExp = new RegExp('\'', 'g');
      const cleanedMessages = messageData.replace(singleQuoteRegExp, '"');
      const messages = JSON.parse(cleanedMessages);

      if ('connection_params' in messages) {
        const connParamErrors = messages['connection_params'];

        for (const entryPoint in connParamErrors) {
          if (connParamErrors.hasOwnProperty(entryPoint)) {
            updateValidationMessages(entryPoint, connParamErrors[entryPoint]);

            $scope.alerts.push({
              type: 'warning',
              msg: `Errors found in ${entryPoint} connection`,
            });
          }
        }
      }
    } else {
      $scope.alerts.push({
        type: 'danger',
        msg:
          'Something went wrong on the backend: ' +
          _.get(response, 'data.message', 'Please check the server logs'),
      });
    }
  };

  const clearScopeAlerts = () => {
    while ($scope.alerts.length) {
      $scope.alerts.pop();
    }
  };

  $scope.submitImport = (data) => {
    GardenService.updateGardenConfig(data).then(
        () => console.log('Garden updated from import successfully'),
        $scope.addErrorAlert,
    );
  };

  $scope.submitGardenForm = function(form, model) {
    clearScopeAlerts();
    resetAllValidationErrors();
    $scope.$broadcast('schemaFormValidate');

    if (form.$valid) {
      let updatedGarden = undefined;

      try {
        updatedGarden =
          GardenService.formToServerModel($scope.data, model);
      } catch (e) {
        console.log(e);

        $scope.alerts.push({
          type: 'warning',
          msg: e,
        });
      }

      if (updatedGarden) {
        GardenService.updateGardenConfig(updatedGarden).then(
            () => console.log('Garden update saved successfully'),
            $scope.addErrorAlert,
        );
      }
    } else {
      $scope.alerts.push(
          'There was an error validating the Garden.',
      );
    }
  };

  $scope.syncGarden = function() {
    GardenService.syncGarden($scope.data.name);
  };

  EventService.addCallback('admin_garden_view', (event) => {
    switch (event.name) {
      case 'GARDEN_UPDATED':
        if ($scope.data.id == event.payload.id) {
          $scope.data = event.payload;
        }
        break;
    }
  });

  $scope.$on('$destroy', function() {
    EventService.removeCallback('admin_garden_view');
  });

  $scope.$on('userChange', function() {
    loadAll();
  });

  loadAll();
}
