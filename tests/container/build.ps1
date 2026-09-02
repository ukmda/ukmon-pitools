# build script for the docker container used for testing ukmon-pitools

# these parts of the build script wont work outside my network
scp ubunturms:source/Stations/UK0006/.config keys/
scp testpi4:.ssh/ukmon keys/testpi4

# the rest should work fine though
docker build . -t rmstestcont
docker tag rmstestcont:latest docker.io/markmac99/rmstestcont:latest
docker push docker.io/markmac99/rmstestcont:latest