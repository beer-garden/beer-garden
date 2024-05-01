commandIndexController.$inject = [
  '$rootScope',
  '$scope',
  '$stateParams',
  '$sce',
  'localStorageService',
  'DTOptionsBuilder',
  'SystemService',
];

/**
 * commandIndexController - Angular controller for all commands page.
 * @param  {Object} $rootScope       Angular's $rootScope object.
 * @param  {Object} $scope           Angular's $scope object.
 * @param  {Object} $stateParams
 * @param  {Object} $sce             Angular's $sce object.
 * @param  {Object} localStorageService  Storage service
 * @param  {Object} DTOptionsBuilder Data-tables' builder for options.
 * @param  {Object} SystemService
 */
export default function commandIndexController(
    $rootScope,
    $scope,
    $stateParams,
    $sce,
    localStorageService,
    DTOptionsBuilder,
    SystemService,
) {
  $scope.setWindowTitle('commands');
  $scope.filterHidden = false;
  $scope.template = '';
  $scope.dtInstance = {};
  $scope.dtOptions = DTOptionsBuilder.newOptions()
      .withOption('autoWidth', false)
      .withOption(
          'pageLength',
          localStorageService.get('_command_index_length') || 10,
      )
      .withOption('hiddenContainer', true)
      .withOption('order', [
        [0, 'asc'],
        [1, 'asc'],
        [2, 'asc'],
        [3, 'asc'],
      ])
      .withBootstrap();

  $scope.getTopicsHtml = function(topics) {
    if (topics === undefined || topics == null || topics.length == 0){
      return "''";
    }

    var htmlTopics = topics[0];

    for (var i = 1; i < topics.length; i++){
      htmlTopics = htmlTopics + "<br>" + topics[i];
    }

    return "'" + htmlTopics + "'";
  }

  $scope.instanceCreated = function(_instance) {
    $scope.dtInstance = _instance;

    $('#commandIndexTable').on('length.dt', (event, settings, len) => {
      localStorageService.set('_command_index_length', len);
    });
  }; 

  $scope.hiddenComparator = function(hidden, checkbox) {
    return checkbox || !hidden;
  };

  $scope.nodeMove = function(location) {
    const node = document.getElementById('filterHidden');
    const list = document.getElementById(location);
    list.append(node, list.childNodes[0]);
  };

  if (
    !(
      $stateParams.namespace ||
      $stateParams.systemName ||
      $stateParams.systemVersion
    )
  ) {
    $scope.dtOptions = $scope.dtOptions.withLightColumnFilter({
      0: {
        html: 'input',
        type: 'text',
        attr: {class: 'form-inline form-control', title: 'Namespace Filter'},
      },
      1: {
        html: 'input',
        type: 'text',
        attr: {class: 'form-inline form-control', title: 'System Filter'},
      },
      2: {
        html: 'input',
        type: 'text',
        attr: {class: 'form-inline form-control', title: 'Version Filter'},
      },
      3: {
        html: 'input',
        type: 'text',
        attr: {class: 'form-inline form-control', title: 'Command Filter'},
      },
      4: {
        html: 'input',
        type: 'text',
        attr: {
          class: 'form-inline form-control',
          title: 'Description Filter',
        },
      },
    });
  }

  $scope.successCallback = function(response, systems) {
    // Pull out what we care about
    let commands = [];
    const breadCrumbs = [];

    systems.forEach((system) => {
      if ($stateParams.namespace) {
        if (system.namespace != $stateParams.namespace){
          return;
        }
        if ($stateParams.systemName) {
          if ((system.display_name || system.name) != $stateParams.systemName){
            return;
          }

          if ($stateParams.systemVersion) {
            if (system.version != $stateParams.systemVersion) {
              return;
            }
          }
        }
      }
      system.commands.forEach((command) => {
        commands.push({
          id: command.id,
          hidden: command.hidden,
          namespace: system.namespace,
          name: command.name,
          command_type: command.command_type || 'ACTION',
          system: system.display_name || system.name,
          version: system.version,
          description: command.description || 'No Description Provided',
          topics: command.topics || [],
          tags: command.tags || [],
        });
      });
    });

    if ($stateParams.namespace) {
      breadCrumbs.push($stateParams.namespace);

      if ($stateParams.systemName) {
        breadCrumbs.push($stateParams.systemName);

        if ($stateParams.systemVersion) {
          breadCrumbs.push($stateParams.systemVersion);

          // If there's a fully specified system, and it has a template, show it
          const foundSystem = SystemService.findSystem(
            $stateParams.namespace,
            $stateParams.systemName,
            $stateParams.systemVersion,
          );
          if (foundSystem.template) {
            if ($scope.config.executeJavascript) {
              $scope.template = $sce.trustAsHtml(foundSystem.template);
            } else {
              $scope.template = foundSystem.template;
            }
          }
        }
      }
    }

    $scope.response = response;
    $scope.data = commands;

    $scope.userCanTask = $rootScope.hasCommandPermission(
        $rootScope.user,
        'request:create',
        commands[0],
    );
    $scope.dtOptions.withLanguage({
      info:
        'Showing _START_ to _END_ of _TOTAL_ entries (filtered from ' +
        $scope.data.length +
        ' total entries)',
      infoFiltered: '',
    });
    $scope.breadCrumbs = breadCrumbs;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  if ($rootScope.gardensResponse !== undefined){
    $scope.successCallback($rootScope.gardensResponse, $rootScope.systems);
  } 
  else {
    setTimeout(function delaySystemLoad() {
      if ($rootScope.gardensResponse !== undefined){
        $scope.successCallback($rootScope.gardensResponse, $rootScope.systems);
        $scope.$digest();
      } else {
        setTimeout(delaySystemLoad, 10);
      }
    }, 10);
  }


}
