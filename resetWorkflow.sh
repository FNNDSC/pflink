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
    resetWorkflow.sh is a helper script to authenticate into a
    'pflink' instance and re-run an existing workflow request by
    deleting it's existing record.

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

    [-K <searchKeyWord>]
    A comma separated list of keywords to search in an
    existing workflow record inside pflink-db.


EXAMPLES
    $ ./resetWorkflow.sh -L http://localhost:8050/api/v1   \\
                 -U pflink                                 \\
                 -P pflink1234                             \\
                 -K 120.11.34.7634334100

"
# =========================================================
# STEP 0:  CONFIGURATION
# =========================================================
URL='http://localhost:8050/api/v1'
USERNAME='pflink'
PASSWORD='pflink1234'

while getopts "L:U:P:K:h" opt; do
    case $opt in
        h) printf "%s" "$SYNOPSIS"; exit 1                ;;

        L) URL=$OPTARG                                    ;;

        U) USERNAME=$OPTARG                               ;;

        P) PASSWORD=$OPTARG                               ;;

        K) KEYWORD=$OPTARG                                ;;

        *) exit 0                                         ;;

    esac
done
# =========================================================
# AUTHENTICATION
# =========================================================
RESP=$(curl -s -X 'POST' \
  "$URL/auth-token" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "&username=$USERNAME&password=$PASSWORD" | jq)

token=$(echo $RESP | awk '{print $3}' | sed 's/[=",]//g')

# =========================================================
# STEP1: CURL request to get a hash key of a submitted request
# =========================================================  
hash_list=$(curl -s -X 'GET' \
  "$URL/workflow/search?keywords=$KEYWORD" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' | jq)
echo $hash_list | jq

rem=$(echo $hash_list | tr '""' "\n" | sed "s/[][{}':,]//g")
list=$rem

for item in "${list[@]}"; do 
    hash_key=$(echo "$item" | awk '{print $2}'); 
done
search_count=$(echo $hash_key | wc -w)
current=1
for i in $hash_key; do
    echo "[Showing $current of $search_count records]"
    echo "Current hash_key: $i"
    

    # =========================================================
    # STEP2: CURL request to get request stored in the db
    # =========================================================  
    workflow_record=$(curl -s -X 'GET' \
      "$URL/workflow?workflow_key=$i" \
      -H 'accept: application/json' \
      -H "Authorization: Bearer $token" \
      -H 'Content-Type: application/json')

    echo $workflow_record | jq

    workflow_request=$(echo $workflow_record | jq '.request')

    # =========================================================
    # Confirmation prompt to delete a record
    # ========================================================= 
    echo "Do you wish to redo this workflow record?"
    select ynx in "Yes" "No" "Exit"; do
        # =========================================================
        # STEP3: CURL request to delete and re-run an existing request
        # =========================================================
        case $ynx in
            Yes ) curl -s -X 'DELETE' \
                  "$URL/workflow?workflow_key=$i" \
                  -H 'accept: application/json' \
                  -H "Authorization: Bearer $token" \
                  -H 'Content-Type: application/json' | jq;
                  echo "Re-running the above workflow request."
                  # =========================================================
                  # STEP3a: CURL request to post a  request to pflink
                  # =========================================================
                  curl -s -X 'POST' \
                  "$URL/workflow" \
                  -H 'accept: application/json' \
                  -H "Authorization: Bearer $token" \
                  -H 'Content-Type: application/json' \
                  -d "$workflow_request" | jq
  
                  break;;
            No )  break;;
            Exit ) exit;;
        esac
    done
    ((current++))
done




# =========================================================
