#!/usr/bin/env bash
# =========================================================
SYNOPSIS="
NAME
    resetWorkflow.sh

SYNOPSIS
    resetWorkflow.sh [-h]                          \\
             [-L <pflinkServiceURL>]       \\
             [-U <pflinkUsername>]         \\
             [-P <pflinkPassword>]         \\
             [-K <searchKeyWord>]          \\
DESC
    setup.sh is a helper script to authenticate into a
    'pflink' instance and add a new 'pfdcm' service.

ARGS
    [-h]
    If specified, print this synapsis text of setup.sh.

    [-L <pflinkServiceURL>]
    If specified, uses this url (complete service address)
    as service address to submit curl requests to pflink.
    Default value is http://localhost:8050/api/v1.

    [-U <pflinkUsername>]
    If specified, use this string as pflink username.
    Default value is 'pflink'.

    [-P <pflinkPassword>]
    If specified, use this string as pflink password.
    Default value is 'pflink1234'.

    [-S <pfdcmServiceName>]
    If specified, use this string to add a new pfdcm instance.
    Default value is 'PFDCM'.

    [-A <pfdcmServiceAddress>]
    If specified, use this string as the service address of
    a new pfdcm instance.
    Default value is http://localhost:4005/api/v1.

EXAMPLES
    $ ./setup.sh -L http://localhost:8050/api/v1   \\
                 -U pflink                         \\
                 -P pflink1234                     \\
                 -S PFDCM                          \\
                 -A http://localhost:4005/api/v1

"
# =========================================================
# STEP 0:  CONFIGURATION
# =========================================================
URL='http://localhost:8050/api/v1'
USERNAME='pflink'
PASSWORD='pflink1234'
SERVICENAME='PFDCM'
SERVICEADDRESS='http://localhost:4005/api/v1'

while getopts "L:U:P:K:h" opt; do
    case $opt in
        h) printf "%s" "$SYNOPSIS"; exit 1                ;;

        L) URL=$OPTARG                                    ;;

        U) USERNAME=$OPTARG                               ;;

        P) PASSWORD=$OPTARG                               ;;

        K) KEYWORD=$OPTARG                            ;;

        *) exit 0                                         ;;

    esac
done
# =========================================================
# AUTHENTICATION
# =========================================================
RESP=$(curl -X 'POST' \
  "$URL/auth-token" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "&username=$USERNAME&password=$PASSWORD" | jq)


  
token=$(echo $RESP | awk '{print $3}' | sed 's/[=",]//g')



# =========================================================
# STEP1: CURL request to get a hash key of a submitted request
# =========================================================  
hash_list=$(curl -X 'GET' \
  "$URL/workflow/search?keywords=$KEYWORD" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' | jq )

hash_key=$(echo $hash_list | awk '{print $3}' | sed "s/['\",]//g")

echo $hash_key

# =========================================================
# STEP2: CURL reqest to get request stored in the db
# =========================================================  
workflow_record=$(curl -X 'GET' \
  "$URL/workflow?workflow_key=$hash_key" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' | jq )

echo $workflow_record
echo "Do you wish to delete this workflow record?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) delete_status=$(curl -X 'DELETE' \
  "$URL/workflow?workflow_key=$hash_key" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' | jq ); echo $delete_status; break;;
        No ) exit;;
    esac
done


# =========================================================
