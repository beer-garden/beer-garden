#!/bin/bash

# This requires you to have httpie (https://httpie.io/) installed
# You'll also need a GitHub Personal Access Token (https://github.com/settings/tokens)
# with the correct permissions to let you upload release artfacts
# Finally, you'll need an httpie session named "github" for both api.github.com
# and uploads.github.com that uses that token (https://httpie.io/docs#named-sessions)

VERSION=$1
ITERATION=$2
DIST_DIR="$(dirname $0)/../dist"

RAW_UPLOAD_URL=$(http -p b --session=github https://api.github.com/repos/beer-garden/beer-garden/releases/tags/${VERSION} | jq .upload_url)
# Because Github is SUPER ANNOYING this is horribly mangled:
# "https://uploads.github.com/repos/beer-garden/beer-garden/releases/34244733/assets{?name,label}"
# Seriously, that is crazypants
UNQUOTED=$(echo ${RAW_UPLOAD_URL} | cut -d '"' -f 2)
UPLOAD_URL=${UNQUOTED%\{*\}}

# OK, upload the thing
http \
	--session=github \
	"${UPLOAD_URL}" \
	"name==beer-garden-${VERSION}-${ITERATION}.el7.x86_64.rpm" \
	< "${DIST_DIR}/beer-garden-${VERSION}-${ITERATION}.el7.x86_64.rpm"

