const path = require('path');
const merge = require('webpack-merge');
const common = require('./webpack.common.js');

module.exports = merge(common, {
  devtool: 'eval-source-map',
  devServer: {
    // Uncomment these to allow external (non-localhost) connections
    // host: '0.0.0.0',
    // disableHostCheck: true,

    contentBase: path.resolve(__dirname),
    stats: 'minimal',
    proxy: [{
      context: ['/api', '/config', '/version'],
      target: 'http://localhost:2337/',
    }],
  },
});
