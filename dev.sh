#!/bin/bash
export PFLINK_MONGODB=mongodb://localhost:27017
export PFLINK_PFDCM=http://localhost:4005
export PFLINK_PORT=8050

docker-compose up -d pflink-db
exec python app/main.py
