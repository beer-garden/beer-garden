const webpack = require('webpack');
const merge = require('webpack-merge');
const common = require('./webpack.common.js');

module.exports = merge(common, {
  mode: 'production',

  // TODO - I THINK this is unnecessary with the change from
  // ExtractTextPlugin to MiniCssExtractPlugin
  //plugins: [
  //  new OptimizeCssAssetsPlugin(),
  //],
});
