
module.exports = function(config) {

  config.set({

      // base path, that will be used to resolve files and exclude
      basePath: '../..',

      // frameworks to use
      frameworks: ['mocha', 'chai-sinon'],

      // list of files / patterns to load in the browser
      files: [
        // bower:js
        'brew_view/static/bower_components/jquery/jquery.js',
        'brew_view/static/bower_components/datatables.net/js/jquery.dataTables.js',
        'brew_view/static/bower_components/angular/angular.js',
        'brew_view/static/bower_components/angular-animate/angular-animate.js',
        'brew_view/static/bower_components/angular-sanitize/angular-sanitize.js',
        'brew_view/static/bower_components/bootstrap/dist/js/bootstrap.js',
        'brew_view/static/bower_components/bootstrap-switch/dist/js/bootstrap-switch.js',
        'brew_view/static/bower_components/angular-bootstrap-switch/dist/angular-bootstrap-switch.js',
        'brew_view/static/bower_components/angular-confirm-modal/angular-confirm.js',
        'brew_view/static/bower_components/angular-ui-router/release/angular-ui-router.js',
        'brew_view/static/bower_components/metisMenu/dist/metisMenu.js',
        'brew_view/static/bower_components/startbootstrap-sb-admin-2/dist/js/sb-admin-2.js',
        'brew_view/static/bower_components/datatables.net-bs/js/dataTables.bootstrap.js',
        'brew_view/static/bower_components/datatables-light-columnfilter/dist/dataTables.lightColumnFilter.min.js',
        'brew_view/static/bower_components/angular-datatables/dist/angular-datatables.js',
        'brew_view/static/bower_components/angular-datatables/dist/plugins/light-columnfilter/angular-datatables.light-columnfilter.js',
        'brew_view/static/bower_components/angular-datatables/dist/plugins/bootstrap/angular-datatables.bootstrap.js',
        'brew_view/static/bower_components/tv4/tv4.js',
        'brew_view/static/bower_components/objectpath/lib/ObjectPath.js',
        'brew_view/static/bower_components/angular-schema-form-bootstrap/dist/angular-schema-form-bootstrap-bundled.js',
        'brew_view/static/bower_components/angular-strap/dist/angular-strap.js',
        'brew_view/static/bower_components/angular-strap/dist/angular-strap.tpl.js',
        'brew_view/static/bower_components/angular-ui-select/dist/select.js',
        'brew_view/static/bower_components/angular-schema-form-addons/dist/addons.js',
        'brew_view/static/bower_components/angular-bootstrap/ui-bootstrap-tpls.js',
        'brew_view/static/bower_components/ace-builds/src-min-noconflict/ace.js',
        'brew_view/static/bower_components/ace-builds/src-min-noconflict/mode-json.js',
        'brew_view/static/bower_components/ace-builds/src-min-noconflict/worker-json.js',
        'brew_view/static/bower_components/ace-builds/src-min-noconflict/theme-dawn.js',
        'brew_view/static/bower_components/angular-ui-ace/ui-ace.js',
        'brew_view/static/bower_components/object-assign-shim/index.js',
        'brew_view/static/bower_components/angular-mocks/angular-mocks.js',
        // endbower

        'brew_view/static/js/*.js',
        'brew_view/static/js/**/*.js',
        'brew_view/static/index.html',
        'brew_view/static/partials/*.html',

        'tests/static/unit/**/*.js'
      ],

      // list of files to exclude
      exclude: [
        'brew_view/static/js/run.js',
      ],

      preprocessors: {
        'brew_view/static/partials/*.html': ['ng-html2js'],
        'brew_view/static/partials/**/*.html': ['ng-html2js']
      },

      ngHtml2JsPreprocessor: {
        stripPrefix: 'brew_view/static/',
        moduleName: 'templates'
      },

      coverageReporter: {
        reporters: [
            {type: 'lcov', subdir: 'lcov' },
            {type: 'cobertura', subdir: 'cobertura', file: 'cobertura.xml'}
        ],
        dir : 'output/js/coverage/'
      },

      junitReporter : {
        outputDir: 'output/js/junit/',
        outputFile: 'test-report.xml'
      }
  });
};
