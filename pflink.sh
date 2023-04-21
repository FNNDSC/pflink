#!/bin/bash
docker build -t local/pflink .
docker-compose up -d --remove-orphans
docker-compose exec pflink pytest .
