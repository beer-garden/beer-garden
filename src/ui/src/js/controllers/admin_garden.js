import gardenMetricsTemplate from '../../templates/admin_garden_metrics.html';

adminGardenController.$inject = [
  '$scope',
  '$uibModal',
  'GardenService',
  'EventService',
];

/**
 * adminGardenController - Garden management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} $uibModal
 * @param  {Object} GardenService    Beer-Garden's garden service object.
 * @param  {Object} EventService    Beer-Garden's event service object.
 */

export default function adminGardenController(
    $scope,
    $uibModal,
    GardenService,
    EventService,
) {
  $scope.setWindowTitle('gardens');
  $scope.alerts = [];
  $scope.gardenCreateSchema = GardenService.CreateSCHEMA;
  $scope.gardenCreateForm = GardenService.CreateFORM;

  $scope.successCallback = function(response) {
    for (let i = 0; i < response.data.length; i++){
      if (!response.data.has_parent){
        $scope.data = $scope.extractGardenChildren([response.data[i]]);
      }
    }
    $scope.response = response;
  };
  $scope.garden_name = null;
  $scope.createGardenFormHide = true;
  $scope.create_garden_name = null;
  $scope.createGardenFormHide = true;
  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = [];
  };
  $scope.is_unique_garden_name = true;
  $scope.create_garden_popover_message = null;
  $scope.create_garden_name_focus = false;

  $scope.getGardenInfo = function (garden) {

    $scope.routeMetrics = [];
    $scope.selectedGarden = garden;

    let keys = ["CREATE", "START", "COMPLETE"];

    for (let i = 0; i < $scope.data.length; i++) {
      let gardenMetrics = { "source": $scope.data[i].name };
      let foundMetrics = false;
      for (let x = 0; x < keys.length; x++) {
        if ($scope.data[i].metadata[keys[x] + "_DELTA_" + garden.name] !== undefined) {
          gardenMetrics[keys[x]] = {
            "DELTA": $scope.data[i].metadata[keys[x] + "_DELTA_" + garden.name],
            "AVG": $scope.data[i].metadata[keys[x] + "_AVG_" + garden.name],
            "COUNT": $scope.data[i].metadata[keys[x] + "_COUNT_" + garden.name],
          }
          foundMetrics = true;
        }
      }
      if (foundMetrics) {
        $scope.routeMetrics.push(gardenMetrics);
      }
    }

    $uibModal.open({
      template: gardenMetricsTemplate,
      scope: $scope,
      windowClass: 'app-modal-window',
    });

  }

  $scope.findGardenLabel = function(garden, gardenLabel) {
    if (garden.parent != null) {
      gardenLabel = garden.parent + "/" + gardenLabel;
      for (let i = 0; i < $scope.data.length; i++){
        if ($scope.data[i].name == garden.parent){
          gardenLabel = $scope.findGardenLabel($scope.data[i], gardenLabel)
        }
      }
    }
    return gardenLabel;

  }

  const loadGardens = function() {
    GardenService.getGardens().then(
        $scope.successCallback,
        $scope.failureCallback,
    );
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.syncGardens = function() {
    GardenService.syncGardens().then((resp)=>{}).catch((err) => {
      if (err.data && err.data.message) {
        $scope.alerts.push({
          type: 'danger',
          msg: err.data.message,
        });
        console.log('error', err.data.message);
      }
    });
  };


  $scope.rescan = function() {
    GardenService.rescanGardens();
  };
  $scope.syncGarden = function(garden) {
    GardenService.syncGarden(garden.name);
  };

  $scope.deleteGarden = function(garden) {
    GardenService.deleteGarden(garden.name);
  };

  $scope.startGarden = function(garden) {
    GardenService.updateStatus(garden.name, "RUNNING");
  };

  $scope.stopGarden = function(garden) {
    GardenService.updateStatus(garden.name, "STOPPED");
  };

  $scope.startReceivingConnection = function(garden, api) {
    GardenService.updateReceivingStatus(garden.name, "RECEIVING", api);
    for (let i = 0; i < garden.receiving_connections.length; i++) {
      if (garden.receiving_connections[i].api == api){
        if (garden.receiving_connections[i].status == "DISABLED") {
          GardenService.updateReceivingStatus(garden.name, "RECEIVING", api);
        }
      }
    }
  };

  $scope.stopReceivingConnection = function(garden, api) {
    for (let i = 0; i < garden.receiving_connections.length; i++) {
      if (garden.receiving_connections[i].api == api){
        if (["PUBLISHING","RECEIVING","UNREACHABLE","UNRESPONSIVE","ERROR","UNKNOWN"].includes(garden.receiving_connections[i].status)) {
          GardenService.updateReceivingStatus(garden.name, "DISABLED", api);
        }
      }
    }
  };

  $scope.startPublishingConnection = function(garden, api) {
    for (let i = 0; i < garden.publishing_connections.length; i++) {
      if (garden.publishing_connections[i].api == api){
        if (garden.publishing_connections[i].status == "DISABLED") {
          GardenService.updatePublisherStatus(garden.name, "PUBLISHING", api);
        }
      }
    }
  };

  $scope.stopPublishingConnection = function(garden, api) {
    for (let i = 0; i < garden.publishing_connections.length; i++) {
      if (garden.publishing_connections[i].api == api){
        if (["PUBLISHING","RECEIVING","UNREACHABLE","UNRESPONSIVE","ERROR","UNKNOWN"].includes(garden.publishing_connections[i].status)) {
          GardenService.updatePublisherStatus(garden.name, "DISABLED", api);
        }
      }
    }
  };

  $scope.isRemoteConfigured = function(garden) {
    if (garden.connection_type == "LOCAL"){
      return false;
    }
    if (garden.status == "MISSING_CONFIGURATION"){
      return false;
    }

    for (let i = 0; i < garden.publishing_connections.length; i++) {
      if (garden.publishing_connections[i].status == "MISSING_CONFIGURATION"){
        return false;
      }
    }
    return true;
  };

  $scope.isChild = function(garden) {
    if (garden.has_parent){
      return garden.parent == $scope.config.gardenName;
    }
    return false;
  };

  $scope.showUnconfigured = function(gardens){
    for (let i = 0; i < gardens.length; i++) {
      if ($scope.isRemoteUnconfigured(gardens[i])){
        return true;
      }
    }
    return false;
  }

  $scope.showUpstream = function(gardens){
    for (let i = 0; i < gardens.length; i++) {
      if (gardens[i].connection_type == "LOCAL" && gardens[i].name == $scope.config.gardenName){
        if (gardens[i].publishing_connections.length > 0){
          return true;
        }
      }
    }
    return false;
  }

  $scope.isLocal = function(garden) {
    return garden.name == $scope.config.gardenName && garden.connection_type == "LOCAL";
  }

  $scope.getConnectionUrl = function(connection, isReceiving) {
    let url = "";

    if (connection.config["host"] !== undefined){
      url = url + connection.config["host"];
    }
    if (connection.config["port"] !== undefined){
      url = url + ":" + connection.config["port"];
    }

    if (
      connection.config["url_prefix"] !== undefined &&
      connection.config["url_prefix"] != null &&
      connection.config["url_prefix"] != "" &&
      connection.config["url_prefix"] != "/"
    ) {
      url = url + "/" + connection.config["url_prefix"];
    }

    if (isReceiving){
      if (connection.config["subscribe_destination"] !== undefined){
        let sub_dest = connection.config["subscribe_destination"].replace(/^\/+/, "");
        url = url.replace(/\/+$/, "");
        url = url.concat("/", sub_dest);
      }
    } else {
      if (connection.config["send_destination"] !== undefined){
        let send_dest = connection.config["send_destination"].replace(/^\/+/, "");
        url = url.replace(/\/+$/, "");
        url = url.concat("/", send_dest);
      }
    }

    return url;
  }

  $scope.isRemoteUnconfigured = function(garden) {
    if (garden.connection_type == "LOCAL"){
      return false;
    }

    if (garden.parent != $scope.config.gardenName){
      return false;
    }

    if (garden.status == "MISSING_CONFIGURATION"){
      return true;
    }

    for (let i = 0; i < garden.publishing_connections.length; i++) {
      if (garden.publishing_connections[i].status == "MISSING_CONFIGURATION"){
        return true;
      }
    }
    return false;
  };

  const loadAll = function() {
    $scope.response = undefined;
    $scope.data = [];

    loadGardens();
  };

  $scope.removeGardenEventChildren = function(garden) {

    // Remove children
    for (let i = 0; i < garden.children.length; i++) {
      $scope.removeGardenEventChildren(garden.children[i])
    }

    // Remove source garden
    for (let i = 0; i < $scope.data.length; i++) {
      if ($scope.data[i].id == garden.id) {
        $scope.data.splice(i, 1);
      } else if ($scope.data[i].parent == garden.name){
        // Clean up any missing children
        $scope.data.splice(i, 1);
      }
    }


  }

  $scope.eventUpsetGarden = function (garden) {
    if (garden.connection_type != "LOCAL" && !garden.has_parent) {
      for (let i = 0; i < $scope.data.length; i++) {
        if ($scope.data[i].connection_type == "LOCAL") {
          garden.parent = $scope.data[i].name;
          break;
        }
      }
      garden.has_parent = true;
    }
    let gardenNotFound = true;
    for (let i = 0; i < $scope.data.length; i++) {
      if ($scope.data[i].id == garden.id) {
        // Min fields to update
        let updateValues = ["status", "receiving_connections", "publishing_connections", "metadata"];

        for (let x = 0; x < updateValues.length; x++) {
          $scope.data[i][updateValues[x]] = garden[updateValues[x]]
        }

        // Not all events include children, only update when children are provided or added
        if (
          garden.children !== undefined &&
          garden.children != null &&
          (
            garden.children.length > 0 ||
            $scope.data[i].children === undefined ||
            $scope.data[i].children == null ||
            $scope.data[i].children.length == 0
          )
        ) {
          $scope.data[i].children = garden.children;
        }
        gardenNotFound = false;
        break;
      }
    }

    if (gardenNotFound) {
      $scope.data.push(garden);
    }
    if (garden.children !== undefined && garden.children != null){
      for (let x = 0; x < garden.children.length; x++) {
        $scope.eventUpsetGarden(garden.children[x]);
      }
    }

  }

  EventService.addCallback('admin_garden', (event) => {
    switch (event.name) {
      case 'GARDEN_REMOVED':
        $scope.removeGardenEventChildren(event.payload)
        $scope.$digest();
        break;
      case 'GARDEN_CREATED':
      case 'GARDEN_CONFIGURED':
      case 'GARDEN_UPDATED':
        $scope.eventUpsetGarden(event.payload)
        $scope.$digest();
        break;
      case 'GARDEN_SYNC':
        if (event.payload.name != $scope.config.gardenName) {
          $scope.pushAlert('info', 'Garden sync event seen from ' + event.payload.name);
        }
    }
  });

  $scope.pushAlert = function (type, msg) {
    let newMessage = true;
    for (const alert of $scope.alerts) {
      if (alert.msg == msg) {
        newMessage = false;
      }
    }
    if (newMessage) {
      $scope.alerts.push({
        type: type,
        msg: msg,
      });
    }
  }

  $scope.$on('$destroy', function() {
    EventService.removeCallback('admin_garden');
  });

  $scope.$on('userChange', function() {
    loadAll();
  });

  loadAll();
}
