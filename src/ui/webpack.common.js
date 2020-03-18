const path = require('path');
const webpack = require('webpack');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
  entry: {
    index: ['babel-polyfill', path.join(__dirname, 'src', 'index')],
    dark: path.join(__dirname, 'src/styles/dark', 'dark'),
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'dist'),
    publicPath: '/dist/',
  },
  plugins: [
    new webpack.ProvidePlugin({
      'tv4': 'tv4',
      '$': 'jquery',
      'jQuery': 'jquery',
      'window.jQuery': 'jquery',
      'moment': 'moment',
    }),
    new MiniCssExtractPlugin(),
    new CopyWebpackPlugin([
        {from: 'src/index.html'},
        {from: 'src/image', to: 'image'},
        {from: 'node_modules/swagger-ui-dist', to: 'swagger', ignore: ['*.map', '*.md']},
        {from: 'node_modules/ace-builds/src-noconflict/worker-json.js'},
    ]),
  ],
  resolve: {
    symlinks: false,
    alias: {
      'datatables': 'datatables.net',
      'datatables-columnfilter$': 'datatables-columnfilter/dist/dataTables.lightColumnFilter.js',
    },
    modules: [
      path.resolve(__dirname, 'node_modules'),
    ],
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /(node_modules)/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['env'],
          },
        },
      },
      {
        test: /\.html$/,
        use: ['ng-cache-loader?prefix=[dir]'],
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader'],
      },
      {
        test: /\.(eot|svg|ttf|woff|woff2|gif|png)$/,
        use: ['url-loader'],
      },
    ],
  },
};
