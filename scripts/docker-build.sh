VERSION=`cat version.txt`
docker build -t parallel-orchestrator:$VERSION -f Dockerfile .
