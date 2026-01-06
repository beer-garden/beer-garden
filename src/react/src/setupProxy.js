const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:2337/api',
      changeOrigin: true, // Needed for virtual hosted sites
      onProxyReq: (proxyReq, req, res) => {
        // Forward custom headers from the original request or add new ones
        // Convert all header keys to lowercase
        Object.keys(req.headers).forEach(key => {
          proxyReq.setHeader(key, req.headers[key]);
        });
        // proxyReq.headers = req.headers;
        proxyReq.setHeader('X-Added-Header', 'my-custom-value');
        proxyReq.setHeader('start', '3');
        
      }
    })
  );
};