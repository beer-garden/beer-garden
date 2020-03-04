'use strict';

// Javascript
// Utilities
import 'babel-polyfill';
import 'objectpath';
import 'tv4';
import 'jquery';

import moment from 'moment';
import 'moment-timezone';
moment.tz.setDefault('UTC');

// Angular
import angular from 'angular';
import 'angular-animate';
import 'angular-confirm';
import 'angular-filter';
import 'angular-sanitize';
import 'angular-websocket';
import 'angular-ui-ace';
import 'angular-ui-bootstrap';
import '@uirouter/angularjs';
import 'angular-bootstrap-switch';
import 'angular-strap';
import 'angular-local-storage';

import 'bootstrap';
import 'bootstrap-switch';
import 'eonasdan-bootstrap-datetimepicker';
import 'ui-select';
import 'metismenu';
import 'startbootstrap-sb-admin-2/js/sb-admin-2.js';
import 'datatables.net';
import 'datatables.net-bs';
import 'datatables-columnfilter';
import 'datatables-columnfilter/dist/dataTables.lcf.eonasdan.js';
import 'jwt-decode';
import 'angular-datatables/dist/angular-datatables.js';
import 'angular-datatables/dist/plugins/light-columnfilter/angular-datatables.light-columnfilter.js'; // eslint-disable-line max-len
import 'angular-datatables/dist/plugins/bootstrap/angular-datatables.bootstrap.js';
import 'angular-schema-form-bootstrap/dist/angular-schema-form-bootstrap-bundled.js';
import 'ace-builds/src-noconflict/ace.js';
import 'ace-builds/src-noconflict/mode-json.js';
import 'ace-builds/src-noconflict/theme-dawn.js';

// Our ASF addons and builder
import '@beer-garden/builder';
import '@beer-garden/addons';

// TODO - This needs to be served separately right now, something about WebWorkers?
// require('ace-builds/src-noconflict/worker-json.js');

// CSS
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/css/bootstrap-theme.css';
import 'bootstrap-switch/dist/css/bootstrap3/bootstrap-switch.css';
import 'metismenu/dist/metisMenu.css';
import 'startbootstrap-sb-admin-2/dist/css/sb-admin-2.css';
import 'datatables.net-bs/css/dataTables.bootstrap.css';
import 'ui-select/dist/select.css';
import 'font-awesome/css/font-awesome.css';
import './styles/custom.css';

// Now load our actual application components
import appRun from './js/run.js';
import runDTRenderer from './js/configs/dt_renderer.js';
import routeConfig from './js/configs/routes.js';
import {interceptorService, authInterceptorService, interceptorConfig}
  from './js/configs/http_interceptor.js';

import fetchDataDirective from './js/directives/fetch_data.js';
import bgStatusDirective from './js/directives/system_status.js';

import adminService from './js/services/admin_service.js';
import commandService from './js/services/command_service.js';
import instanceService from './js/services/instance_service.js';
import queueService from './js/services/queue_service.js';
import requestService from './js/services/request_service.js';
import systemService from './js/services/system_service.js';
import userService from './js/services/user_service.js';
import roleService from './js/services/role_service.js';
import permissionService from './js/services/permission_service.js';
import tokenService from './js/services/token_service.js';
import utilityService from './js/services/utility_service.js';
import jobService from './js/services/job_service.js';
import errorService from './js/services/error_service.js';
import eventService from './js/services/event_service.js';
import namespaceService from './js/services/namespace_service.js';

import aboutController from './js/controllers/about.js';
import adminQueueController from './js/controllers/admin_queue.js';
import adminSystemController from './js/controllers/admin_system.js';
import {adminUserController, newUserController} from './js/controllers/admin_user.js';
import {adminRoleController, newRoleController} from './js/controllers/admin_role.js';
import adminGardenController from './js/controllers/admin_garden.js';
import commandIndexController from './js/controllers/command_index.js';
import commandViewController from './js/controllers/command_view.js';
import requestIndexController from './js/controllers/request_index.js';
import requestViewController, {slideAnimation} from './js/controllers/request_view.js';
import systemIndexController from './js/controllers/system_index.js';
import systemViewController from './js/controllers/system_view.js';
import jobIndexController from './js/controllers/job_index.js';
import jobViewController from './js/controllers/job_view.js';
import jobCreateController from './js/controllers/job_create.js';
import loginController from './js/controllers/login.js';

// Partials
import './partials/about.html';
import './partials/admin_queue.html';
import './partials/admin_system.html';
import './partials/admin_user.html';
import './partials/admin_role.html';
import './partials/admin_garden.html';
import './partials/command_index.html';
import './partials/command_view.html';
import './partials/landing.html';
import './partials/request_index.html';
import './partials/request_view.html';
import './partials/system_index.html';
import './partials/system_view.html';
import './partials/job_index.html';
import './partials/job_view.html';
import './partials/job_create.html';

// Images
import './image/fa-beer.png';
import './image/fa-coffee.png';

// Finally, FINALLY, we have all our dependencies imported. Create the Angularness!
angular.module('bgApp',
[
  'ui.router',
  'ui.bootstrap',
  'ui.ace',
  'datatables',
  'datatables.bootstrap',
  'datatables.light-columnfilter',
  'schemaForm',
  'angular-confirm',
  'angular-websocket',
  'angular.filter',
  'ngAnimate',
  'frapontillo.bootstrap-switch',
  'mgcrea.ngStrap',
  'LocalStorageModule',
  'beer-garden.addons',
  'beer-garden.builder',
])
.run(appRun)
.run(runDTRenderer)
.config(routeConfig)
.config(interceptorConfig)
.config(['localStorageServiceProvider', function(localStorageServiceProvider) {
  localStorageServiceProvider.setStorageType('sessionStorage');
}])
.service('APIInterceptor', interceptorService)
.service('authInterceptorService', authInterceptorService)
.animation('.slide', slideAnimation)

.directive('fetchData', fetchDataDirective)
.directive('bgStatus', bgStatusDirective)

.factory('AdminService', adminService)
.factory('CommandService', commandService)
.factory('InstanceService', instanceService)
.factory('QueueService', queueService)
.factory('RequestService', requestService)
.factory('SystemService', systemService)
.factory('UserService', userService)
.factory('RoleService', roleService)
.factory('PermissionService', permissionService)
.factory('TokenService', tokenService)
.factory('UtilityService', utilityService)
.factory('JobService', jobService)
.factory('ErrorService', errorService)
.factory('EventService', eventService)
.factory('NamespaceService', namespaceService)

.controller('AboutController', aboutController)
.controller('AdminQueueController', adminQueueController)
.controller('AdminSystemController', adminSystemController)
.controller('AdminUserController', adminUserController)
.controller('NewUserController', newUserController)
.controller('AdminRoleController', adminRoleController)
.controller('NewRoleController', newRoleController)
.controller('AdminGardenController', adminGardenController)
.controller('CommandIndexController', commandIndexController)
.controller('CommandViewController', commandViewController)
.controller('RequestIndexController', requestIndexController)
.controller('RequestViewController', requestViewController)
.controller('SystemIndexController', systemIndexController)
.controller('SystemViewController', systemViewController)
.controller('JobIndexController', jobIndexController)
.controller('JobViewController', jobViewController)
.controller('JobCreateController', jobCreateController)
.controller('LoginController', loginController);
