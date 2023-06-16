#!/usr/bin/env bash
# =========================================================
SYNOPSIS="
NAME
    setup.sh

SYNOPSIS
    setup.sh [-h]                          \\
             [-U <pflinkUsername>]         \\
             [-P <pflinkPassword>]         \\
             [-S <pfdcmServiceName>]       \\
             [-A <pfdcmServiceAddress>]    \\

EXAMPLES
    $ ./setup.sh -U pflink                         \\
                 -P pflink1234                     \\
                 -S PFDCM                          \\
                 -A http://localhost:4005

"
# =========================================================
# STEP 0:  CONFIGURATION
# =========================================================
USERNAME='pflink'
PASSWORD='pflink1234'
SERVICENAME='PFDCM'
SERVICEADDRESS='http://localhost:4005'

while getopts "U:P:S:A:h" opt; do
    case $opt in
        h) printf "%s" "$SYNOPSIS"; exit 1                ;;

        U) USERNAME=$2                                    ;;

        P) PASSWORD=$OPTARG                               ;;

        S) SERVICENAME=$OPTARG                            ;;

        A) SERVICEADDRESS=$OPTARG                         ;;

        *) exit 0                                         ;;

    esac
done
# =========================================================
#
#
#
# =========================================================
RESP=$(curl -X 'POST' \
  'http://localhost:8050/api/v1/auth-token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "&username=$USERNAME&password=$PASSWORD" | jq)
  
token=$(echo $RESP | awk '{print $3}' | sed 's/[=",]//g')

# =========================================================
# STEP : CURL request to add a new `pfdcm` service instance
# =========================================================  
curl -X 'POST' \
  'http://localhost:8050/api/v1/pfdcm' \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d '{
  "service_name": "'$SERVICENAME'",
  "service_address": "'$SERVICEADDRESS'"
}' | jq
# =========================================================
