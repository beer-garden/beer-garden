FROM nginx:1.19-alpine

# Defaults for the application proxy info
ENV BEERGARDEN_HOST=localhost \
    BEERGARDEN_PORT=2337

# Remove default config template
RUN rm /etc/nginx/conf.d/default.conf

# Nginx configuration template
ADD ./default.conf.template /etc/nginx/templates/

# Actual static resources
COPY ./dist /usr/share/nginx/html

