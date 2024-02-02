adminGardenController.$inject = [
  '$scope',
  '$state',
  'GardenService',
  'EventService',
];

/**
 * adminGardenController - Garden management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} GardenService    Beer-Garden's garden service object.
 * @param  {Object} EventService    Beer-Garden's event service object.
 */

export default function adminGardenController(
    $scope,
    $state,
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

  $scope.getGardenInsights = function(garden) {

    // Base Headers
    let tooltip = "<div class='panel-body' style='padding-bottom: 0px'>";

    // Add Metrics
    // TODO: Add metrics tags
    if (false){ 
      tooltip += "	<div class='panel-heading' style='font-size: 22px'>"+
      "	  <span>Metrics</span>"+
      "	</div>"+
      "	<div class='list-group-item clearfix'>"+
      "	  <div>"+
      "     <span>Latency: 9s</span>"+
      "	  </div>"+
      "	</div>";
    }

    // Upstream
    if (garden.has_parent){
      tooltip += "<div class='panel-heading' style='font-size: 22px'>"+
      "	  <span>Upstream</span>"+
      "	</div>"+
      "	<div class='list-group-item clearfix'>"+
      "	  <div>"+
      "		  <span>"+garden.parent+"</span>"+
      "	  </div>"+
      "	</div>";
    }

    // Downstream
    if (garden.children.length > 0){
      tooltip += "<div class='panel-heading' style='font-size: 22px'>"+
      " <span>Downstream</span>"+
      "</div>"+
      "<div class='list-group-item clearfix'>";
      
      for (let i = 0; i < garden.children.length; i++){
        tooltip += "<div><span>" + garden.children[i].name + "</span></div>";
      }

      tooltip += "  </div>"+
      "</div>";
    }

    tooltip += "</div>"
    return tooltip;
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
    GardenService.syncGardens().then((resp)=>{
      $scope.alerts.push({
        type: 'success',
        msg: 'Server accepted request to sync all gardens',
      });
    }).catch((err) => {
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
  };

  $scope.stopReceivingConnection = function(garden, api) {
    GardenService.updateReceivingStatus(garden.name, "DISABLED", api);
  };

  $scope.startPublishingConnection = function(garden, api) {
    GardenService.updatePublisherStatus(garden.name, "PUBLISHING", api);
  };

  $scope.stopPublishingConnection = function(garden, api) {
    GardenService.updatePublisherStatus(garden.name, "DISABLED", api);
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
      if (gardens[i].connection_type == "LOCAL"){
        if (gardens[i].publishing_connections.length > 0){
          return true;
        }
      }
    }
    return false;
  }

  $scope.isLocal = function(garden) {
    return garden.connection_type == "LOCAL";
  }

  $scope.getConnectionUrl = function(connection) {
    let url = "";

    if (connection.config["host"] !== undefined){
      url = url + connection.config["host"];
    }
    if (connection.config["port"] !== undefined){
      url = url + ":" + connection.config["port"];
    }

    if (connection.config["url_prefix"] !== undefined){
      url = url + "/" + connection.config["url_prefix"];
    }

    if (connection.config["send_destination"] !== undefined){
      url = url + "/" + connection.config["send_destination"];
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


  EventService.addCallback('admin_garden', (event) => {
    switch (event.name) {
      case 'GARDEN_CREATED':
        if (event.payload.connection_type != "LOCAL" && !event.payload.has_parent){
          for (let i = 0; i < $scope.data.length; i++) {
            if ($scope.data[i].connection_type == "LOCAL"){
              event.payload.parent = $scope.data[i].name;
            }
          }
          event.payload.has_parent = true;
        }
        $scope.data.push(event.payload);
        break;
      case 'GARDEN_REMOVED':
        for (let i = 0; i < $scope.data.length; i++) {
          if ($scope.data[i].id == event.payload.id) {
            $scope.data.splice(i, 1);
          }
        }
        break;
      case 'GARDEN_CONFIGURATION':
      case 'GARDEN_UPDATED':
        for (let i = 0; i < $scope.data.length; i++) {
          if ($scope.data[i].id == event.payload.id) {
            // Min fields to update
            let updateValues = ["status","receiving_connections","publishing_connections","children","metadata"];
            for (let x = 0; x < updateValues.length; x++){
              $scope.data[i][updateValues[x]] = event.payload[updateValues[x]]
            }
          }
        }
        break;
    }
  });

  $scope.$on('$destroy', function() {
    EventService.removeCallback('admin_garden');
  });

  $scope.$on('userChange', function() {
    loadAll();
  });

  loadAll();
}
