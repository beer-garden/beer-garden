FROM nginx:1.27-alpine
ARG VERSION=latest

# Defaults for the application proxy info
ENV BEERGARDEN_HOST=localhost \
    BEERGARDEN_PORT=2337

# Remove default config template
RUN rm /etc/nginx/conf.d/default.conf

# Nginx configuration template
ADD ./default.conf.template /etc/nginx/templates/

# Actual static resources
COPY ./dist /usr/share/nginx/html

# Using standard OCI (Open Container Initiative)
LABEL version="$VERSION" \
      description="Beer Garden React UI" \
      source="https://github.com/beer-garden/beer-garden" \
      maintainer="Beer Garden Maintainers" \
      org.opencontainers.image.title="Beer Garden React UI" \
      org.opencontainers.image.source="https://github.com/beer-garden/beer-garden" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.authors="Beer Garden Maintainers" \ 
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.url="https://beer-garden.io/" \
      org.opencontainers.image.documentation="https://beer-garden.io/"