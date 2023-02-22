#!/bin/bash

docker compose up mongodb -d --remove-orphans 


exec python app/main.py
