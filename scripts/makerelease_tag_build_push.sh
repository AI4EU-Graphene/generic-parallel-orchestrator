#!/bin/bash

# this script 
# * takes the version tag from version.txt
# * fails if the working copy is dirty
# * tags the git repo with that tag (fails if a tag with that version already exists)
# * builds a docker image of the orchestrator with that tag
# * pushes it to the server

# this is the target repository including path, only the version tag will be appended
REMOTE_BASE_PATH="cicd.ai4eu-dev.eu:7444/generic-parallel-orchestrator/orchestrator_container"

VERSION=`cat version.txt`
echo "operating with target version '$VERSION'"

git diff --quiet || { echo "working copy is not clean!" ; git status ; exit -1; }

git tag $VERSION

docker build \
    -t parallel-orchestrator:$VERSION \
    -t $REMOTE_BASE_PATH:$VERSION \
    -f orchestrator_container/Dockerfile orchestrator_container

docker push $REMOTE_BASE_PATH:$VERSION

echo "successfully tagged, built, and pushed. do not forget to 'git push origin tag $VERSION' the tag"
