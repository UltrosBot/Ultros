#!/bin/bash

# Build and deploy on master branch
if [[ $TRAVIS_BRANCH == 'master' && $TRAVIS_PULL_REQUEST == 'false' ]]; then
    echo "Connecting to docker hub"
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

    echo "Building..."
    docker build -t gdude2002/ultros:latest -f docker/Dockerfile .

    echo "Pushing image to Docker Hub..."
    docker push gdude2002/ultros:latest
else
    echo "Skipping deploy"
fi
