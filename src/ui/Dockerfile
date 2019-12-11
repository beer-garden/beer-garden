FROM nginx

COPY default.conf /etc/nginx/conf.d/default.conf
COPY dist /usr/share/nginx/html

# To enable SSL in Nginx
#RUN mkdir /etc/nginx/certs
#COPY server.crt /etc/nginx/certs/server.crt
#COPY server.key /etc/nginx/certs/server.key
#COPY ca.pem /etc/nginx/certs/ca.crt
