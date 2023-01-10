#!/bin/bash

docker-compose up -d
exec python app/main.py
