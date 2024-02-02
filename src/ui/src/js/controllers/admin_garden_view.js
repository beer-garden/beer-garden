import _ from 'lodash';

adminGardenViewController.$inject = [
  '$scope',
  '$window',
  '$timeout',
  'GardenService',
  'EventService',
  '$stateParams',
];

/**
 * adminGardenController - Garden management controller.
 * @param  {Object} $scope           Angular's $scope object.
 * @param  {Object} $window          Angular's $window object
 * @param  {Object} $timeout         Angular's $timeout object
 * @param  {Object} GardenService    Beer-Garden's garden service object.
 * @param  {Object} EventService     Beer-Garden's event service.
 * @param  {Object} $stateParams     State params
 */
export default function adminGardenViewController(
    $scope,
    $window,
    $timeout,
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

  /**
   * Display an alert on the screen that will eventually disappear on its own
   * if it is not an error alert
   *
   * @param {Object} alert - bootstrap UI alert object
   */
  const addAlert = (alert) => {
    $scope.alerts.push(alert);
    if (alert.type !== 'danger') {
      // make informational alerts disappear on their own after 30 seconds
      $timeout(()=> {
        const index = $scope.alerts.indexOf(alert);
        if (index > -1) {
          $scope.closeAlert(index);
        }
      }, 30000);
    }
  };

  /**
   * Move the window up so that the alerts are visible
   */
  const scrollToAlerts = () => {
    $window.scrollTo(0,
        document.getElementById('garden-view-alert-list').offsetTop - 120);
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
    $scope.response = response;
    $scope.data = response.data;

    if ($scope.data.id == null || $scope.data.connection_type == 'LOCAL') {
      $scope.isLocal = true;
      addAlert({
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
      'http.username',
      'http.password',
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

            addAlert({
              type: 'warning',
              msg: `Errors found in ${entryPoint} connection`,
            });
          }
        }
      }
    } else {
      addAlert({
        type: 'danger',
        msg:
          'Something went wrong on the backend: ' +
          _.get(response, 'data.message', 'Please check the server logs'),
      });
    }
    scrollToAlerts();
  };

  $scope.submitImport = (data) => {
    GardenService.updateGardenConfig(data).then(
        () => console.log('Garden updated from import successfully'),
        $scope.addErrorAlert,
    );
  };

  $scope.submitGardenForm = function(form, model) {
    resetAllValidationErrors();
    $scope.$broadcast('schemaFormValidate');

    if (form.$valid) {
      let updatedGarden = undefined;

      try {
        updatedGarden =
          GardenService.formToServerModel($scope.data, model);
      } catch (e) {
        console.log(e);

        addAlert({
          type: 'warning',
          msg: e,
        });
      }

      if (updatedGarden) {
        GardenService.updateGardenConfig(updatedGarden).then(
            () => {
              addAlert({
                type: 'success',
                msg: 'Garden update saved successfully',
              });
            },
            $scope.addErrorAlert,
        );
      }
    } else {
      addAlert({
        type: 'danger',
        msg: 'There was an error validating the Garden.',
      });
    }
    scrollToAlerts();
  };

  $scope.syncGarden = function() {
    GardenService.syncGarden($scope.data.name).then((r)=>{
      addAlert({
        type: 'success',
        msg: 'Server accepted sync command',
      });
      scrollToAlerts();
    }).catch((e)=>{
      if (e.data && e.data.message) {
        addAlert({
          type: 'danger',
          msg:
          'Garden sync failed!',
        });
        addAlert({
          type: 'danger',
          msg: String(e.data.message),
        });
        $scope.data.status = 'ERROR';
      } else {
        addAlert({
          type: 'danger',
          msg:
          'Garden sync failed! Please check the server logs.',
        });
      }
      scrollToAlerts();
    });
  };

  EventService.addCallback('admin_garden_view', (event) => {
    switch (event.name) {
      case 'GARDEN_SYNC':
        console.log('event', event);
      case 'GARDEN_UPDATED':
        if (event.payload.id && $scope.data.id === event.payload.id) {
          $scope.$apply(() => {
            $scope.data = event.payload;
          });
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
