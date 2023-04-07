#!/bin/bash

cp app/config.py app/processes

docker-compose up -d pflink-db
exec python app/main.py
