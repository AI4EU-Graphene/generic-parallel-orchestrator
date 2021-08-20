VERSION=`cat version.txt`
docker build -t parallel-orchestrator:$VERSION -f orchestrator_container/Dockerfile orchestrator_container/
