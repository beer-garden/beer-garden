const path = require('path');
const webpack = require('webpack');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const VisualizerPlugin = require('webpack-visualizer-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  entry: {
    index: ['babel-polyfill', path.join(__dirname, 'src', 'index')],
    dark: path.join(__dirname, 'src/styles/dark', 'dark')
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'dist'),
    publicPath: '/dist/'
  },
  plugins: [
    new webpack.ProvidePlugin({
      'tv4': 'tv4',
      '$': 'jquery',
      'jQuery': 'jquery',
      'window.jQuery': 'jquery',
      'moment': 'moment'
    }),
    new webpack.optimize.CommonsChunkPlugin({
      name: 'vendor',
      minChunks: function(module) {
        return module.context
          && module.context.indexOf('node_modules') !== -1
          && module.context.indexOf('bootswatch') === -1;
      }
    }),
    new ExtractTextPlugin("[name].css")
    // new VisualizerPlugin()
    // new BundleAnalyzerPlugin({openAnalyzer: false})
  ],
  resolve: {
    symlinks: false,
    alias: {
      'datatables': 'datatables.net',
      'datatables-light-columnfilter$': 'datatables-light-columnfilter/dist/dataTables.lightColumnFilter.js'
    },
    modules: [
      path.resolve(__dirname, 'node_modules'),
      path.resolve(__dirname, 'bower_components'),
      'node_modules'
    ]
  },
  module: {
    rules: [
      {
        test: /\.html$/,
        use: ['ng-cache-loader?prefix=[dir]']
      },
      {
        test: /\.css$/,
        use: ExtractTextPlugin.extract({
          fallback: 'style-loader',
          use: 'css-loader?sourceMap'
        })
      },
      {
        test: /\.(eot|svg|ttf|woff|woff2|gif|png)$/,
        use: ['url-loader']
      }
    ]
  }
};
