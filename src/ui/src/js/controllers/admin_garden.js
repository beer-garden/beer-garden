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
    $scope.response = response;
    $scope.data = $scope.extractGardenChildren([response.data])
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
    return "<div class='panel-body' style='padding-bottom: 0px'>"+
    "<div class='list-group'>"+
    "	<div class='panel-heading' style='font-size: 22px'>"+
    "	  <span>Metrics</span>"+
    "	</div>"+
    "	<div class='list-group-item clearfix'>"+
    "	  <div>"+
    "		<span>Latency: 9s</span>"+
    "	  </div>"+
    "	</div>"+
    "	</div>"+
    "	<div class='list-group'>"+
    "	<div class='panel-heading' style='font-size: 22px'>"+
    "	  <span>Upstream</span>"+
    "	</div>"+
    "	<div class='list-group-item clearfix'>"+
    "	  <div>"+
    "		<ul>"+
    "		  <li>Parent</li>"+
    "		</ul>"+
    "	  </div>"+
    "	</div>"+
    "	</div>"+
    "	<div class='list-group'>"+
    "	<div class='panel-heading' style='font-size: 22px'>"+
    "	  <span>Downstream</span>"+
    "	</div>"+
    "	<div class='list-group-item clearfix'>"+
    "	  <div>"+
    "		<ul>"+
    "		  <li>Child A</li>"+
    "		  <li>Child B</li>"+
    "		  <li>Child C</li>"+
    "		</ul>"+
    "	  </div>"+
    "	</div>"+
    "	</div>"+
    "</div>";
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
    GardenService.getGarden($scope.config.gardenName ).then(
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
            $scope.data[i] = event.payload;
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
