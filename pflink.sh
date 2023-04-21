#!/bin/bash
docker-compose up -d --build --remove-orphans
docker-compose exec pflink pytest .
