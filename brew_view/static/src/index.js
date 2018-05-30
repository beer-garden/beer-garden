'use strict';

// Javascript
// Utilities
import 'babel-polyfill';
import 'objectpath';
import 'tv4';
import 'jquery';

// Angular
import angular from 'angular';
import 'angular-animate';
import 'angular-cookies';
import 'angular-confirm';
import 'angular-filter';
import 'angular-sanitize';
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
import {appRun, dtLoadingTemplate} from './js/run.js';
import routeConfig from './js/configs/routes.js';
import {interceptorService, interceptorConfig} from './js/configs/http_interceptor.js';

import emptyDirective from './js/directives/empty.js';
import loadingDirective from './js/directives/loading.js';
import serverErrorDirective from './js/directives/server_error.js';
import bgStatusDirective from './js/directives/system_status.js';
import './js/directives/dataTables.lcf.datetimepicker.fr.js';

import adminService from './js/services/admin_service.js';
import commandService from './js/services/command_service.js';
import instanceService from './js/services/instance_service.js';
import queueService from './js/services/queue_service.js';
import requestService from './js/services/request_service.js';
import systemService from './js/services/system_service.js';
import utilityService from './js/services/utility_service.js';
import versionService from './js/services/version_service.js';

import aboutController from './js/controllers/about.js';
import adminQueueController from './js/controllers/admin_queue.js';
import adminSystemController from './js/controllers/admin_system.js';
import applicationController from './js/controllers/application.js';
import commandIndexController from './js/controllers/command_index.js';
import commandViewController from './js/controllers/command_view.js';
import landingController from './js/controllers/landing.js';
import requestIndexController from './js/controllers/request_index.js';
import requestViewController, {slideAnimation} from './js/controllers/request_view.js';
import systemViewController from './js/controllers/system_view.js';

// Partials
import './partials/about.html';
import './partials/admin_queue.html';
import './partials/admin_system.html';
import './partials/command_index.html';
import './partials/command_view.html';
import './partials/landing.html';
import './partials/request_index.html';
import './partials/request_view.html';
import './partials/system_view.html';

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
  'angular.filter',
  'ngAnimate',
  'frapontillo.bootstrap-switch',
  'mgcrea.ngStrap',
  'ngCookies',
  'LocalStorageModule',
  'beer-garden.addons',
  'beer-garden.builder',
])
.run(appRun)
.run(dtLoadingTemplate)
.config(routeConfig)
.config(interceptorConfig)
.service('APIInterceptor', interceptorService)
.animation('.slide', slideAnimation)

.directive('empty', emptyDirective)
.directive('loading', loadingDirective)
.directive('serverError', serverErrorDirective)
.directive('bgStatus', bgStatusDirective)

.factory('AdminService', adminService)
.factory('CommandService', commandService)
.factory('InstanceService', instanceService)
.factory('QueueService', queueService)
.factory('RequestService', requestService)
.factory('SystemService', systemService)
.factory('UtilityService', utilityService)
.factory('VersionService', versionService)

.controller('AboutController', aboutController)
.controller('QueueIndexController', adminQueueController)
.controller('SystemAdminController', adminSystemController)
.controller('ApplicationController', applicationController)
.controller('CommandIndexController', commandIndexController)
.controller('CommandViewController', commandViewController)
.controller('LandingController', landingController)
.controller('RequestIndexController', requestIndexController)
.controller('RequestViewController', requestViewController)
.controller('SystemViewController', systemViewController);
