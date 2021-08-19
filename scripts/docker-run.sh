VERSION=`cat version.txt`
#--publish=8061:8061 
docker run \
    -it \
    --name parallel-orchestrator \
    --network=host \
    parallel-orchestrator:$VERSION \
    $*
