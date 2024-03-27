#!/bin/bash
docker-compose exec pflink coverage run -m pytest -vv  .
docker-compose exec pflink coverage report -m
