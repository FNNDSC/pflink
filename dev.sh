#!/bin/bash

if [ -f config.env ]; then
  export $(echo $(cat config.env | xargs))
fi

docker-compose up -d pflink-db
exec python app/main.py
