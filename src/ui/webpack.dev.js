const path = require('path');
const merge = require('webpack-merge');
const common = require('./webpack.common.js');

const proxyHost = 'localhost';
const proxyPort = '2337';
const fs = require('fs');

module.exports = merge(common, {
  mode: 'development',
  devtool: 'eval-source-map',

  devServer: {
    // Uncomment this to allow external (non-localhost) connections
    // host: '0.0.0.0',

    /// This seemed to cause issues with the live reloading
    disableHostCheck: true,

    // Compress responses with gzip
    compress: true,

    // Disable serving non-webpack generated assets
    contentBase: false,
    publicPath: '/',

    // Control the verbosity
    stats: 'minimal',

    // Uncomment below for SSL
//    https: true,
//    key: fs.readFileSync('/home/gnburch/PycharmProjects/nginx-casport/localhost-key.pem'),
//    cert: fs.readFileSync('/home/gnburch/PycharmProjects/nginx-casport/localhost-crt.pem'),
//    ca: fs.readFileSync('/home/gnburch/PycharmProjects/nginx-casport/AllTrustedPartners.ca-bundle'),

    proxy: [
// Switch comment lines for target to enable SSL
      {
        context: ['/api', '/config', '/login', '/logout', '/version'],
        target: `http://${proxyHost}:${proxyPort}/`,
        // Uncomment below for SSL
        //Secure is set to false if using self signed certs
//        target: `https://${proxyHost}:${proxyPort}/`,
//        secure: false
        // Uncomment for simulated proxy headers
//        headers: {
//            'X-Username': 'admin',
//            'X-Secret': 'IAMSUPERSECRET'
//        },
      },
      {
        context: ['/api/v1/socket/events'],
        target: `ws://${proxyHost}:${proxyPort}/`,
        ws: true,
        // Uncomment below for SSL
        //Secure is set to false if using self signed certs
//        target: `wss://${proxyHost}:${proxyPort}/`,
//        secure: false

        // Uncomment for simulated proxy headers
//        headers: {
//            'X-Username': 'admin',
//            'X-Secret': 'IAMSUPERSECRET'
//        },
      },
    ],
  },
});
