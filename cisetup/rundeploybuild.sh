#!/bin/bash

CI_RUN=${1}
BUILD_ID=${2}
CONF_VERSION=${3}
RELEASE=${4}
EmailId=${5}
projectid=${6}
deployjob=${7}
url="https://rio-api.pie.apple.com/v1/projects/${projectid}/pipeline_specs/${projectid}-${deployjob}/trigger"

echo $url

curl -k -X POST \
   $url \
  -H 'Cache-Control: no-cache' \
  -H "X-RIO-API-EMAIL: $EmailId" \
  -H 'Content-Type: application/json' \
  -H "X-RIO-API-TOKEN: $CI_RUN" \
  -d "{\"build_params\":{\"DOCKER_IMAGE_VERSION\":\"$BUILD_ID\",\"RELEASE_CONF_VERSION\":\"$CONF_VERSION\",\"RELEASE_VERSION\":\"$RELEASE\"}}"