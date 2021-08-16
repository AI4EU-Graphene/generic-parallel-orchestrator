VERSION=`cat version.txt`
docker run \
    -it \
    --name parallel-orchestrator \
    --publish=8061:8061 \
    parallel-orchestrator:$VERSION \
    $*
