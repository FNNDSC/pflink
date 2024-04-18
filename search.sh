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

while getopts "L:U:P:K:S:E:K:h" opt; do
    case $opt in
        h) printf "%s" "$SYNOPSIS"; exit 1                ;;

        L) URL=$OPTARG                                    ;;

        U) USERNAME=$OPTARG                               ;;

        P) PASSWORD=$OPTARG                               ;;

        S) START_DATE=$OPTARG                             ;;
        
        E) END_DATE=$OPTARG                               ;;

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
#"$URL/workflow/date_search?start_date=$START_DATE&end_date=$END_DATE" \
hash_list=$(curl -s -X 'GET' \
  "$URL/workflow/search?keywords=$KEYWORD" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' | jq)

rem=$(echo $hash_list | tr '""' "\n" | sed "s/[][{}':,]//g")
list=$rem

for item in "${list[@]}"; do
    hash_key=$(echo "$item" | awk '{print $2}');
    #hash_key=$(echo "$item" | awk '!/_id/ {print}');
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

    study_id=$(echo $workflow_record | jq '.request.PACS_directive.StudyInstanceUID')

    # =========================================================
    # Search PACS using px-find
    # ========================================================= 
    echo "Searching PACS for StudyInstanceUID: $study_id ..."
    status=$(px-find \
                                --aec 'SYNAPSERESEARCH' \
                                --aet 'SYNAPSERESEARCH' \
                                --serverIP '10.20.2.28' \
                                --serverPort '104' \
                                --StudyInstanceUID $study_id \
                                --withFeedBack \
                                --StudyOnly)
                                # | awk '/NumberOfStudyRelatedInstances/ {print $41}'
                                present=$(echo $status );
                                echo $present
    RED_ON_GREEN='\033[31;42m'
    RESET='\033[0m'
    echo -e "${RED_ON_GREEN}${RESET}"

    ((current++))
done
# =========================================================

