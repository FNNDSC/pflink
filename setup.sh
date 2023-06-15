#!/usr/bin/env bash
# =========================================================
USERNAME='pflink'
PASSWORD='pflink1234'
SERVICENAME='PFDCM'
SERVICEADDRESS='http://localhost:4005'
# =========================================================
#
#
#
# =========================================================
RESP=$(curl -X 'POST' \
  'http://localhost:8050/api/v1/auth-token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d '&username=pflink&password=pflink1234' | jq)
  
token=$(echo $RESP | awk '{print $3}' | sed 's/[=",]//g')
  
curl -X 'POST' \
  'http://localhost:8050/api/v1/pfdcm' \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d '{
  "service_name": "PFDCM",
  "service_address": "http://localhost:4005"
}' | jq
