#!/bin/bash
docker-compose up -d --remove-orphans
docker-compose exec pflink pytest .
