#!/usr/bin/env sh
set -e
cd deploy
docker-compose up -d --build
