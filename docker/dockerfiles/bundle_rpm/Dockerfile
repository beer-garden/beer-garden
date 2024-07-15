ARG PYTHON_VERSION=3.7
ARG VERSION=unstable

FROM bgio/beer-garden:$VERSION-python$PYTHON_VERSION

RUN mkdir -p /source/rpm/dist 
ADD rpm/dist /source/rpm/dist

# RUN mkdir -p /source/ui/
# ADD src/ui/src /source/ui/src/