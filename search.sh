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
    current_hash=$i
    

    # =========================================================
    # STEP2: CURL request to get request stored in the db
    # =========================================================  
    workflow_record=$(curl -s -X 'GET' \
      "$URL/workflow?workflow_key=$i" \
      -H 'accept: application/json' \
      -H "Authorization: Bearer $token" \
      -H 'Content-Type: application/json')

    response_count=$(echo $workflow_record | wc -w)

    if [ $response_count == 3 ]; then
      continue
    fi
    study_id=$(echo $workflow_record | jq '.request.PACS_directive.StudyInstanceUID')
    if [ $study_id == "" ]; then
      continue
    fi
    request_date=$(echo $workflow_record | jq '.creation_time' | awk '{print $1}')
    username=$(echo $workflow_record | jq '.request.cube_user_info.username')

    # =========================================================
    # Search PACS using px-find
    # =========================================================
    status=$(px-find \
                                --aec 'SYNAPSERESEARCH' \
                                --aet 'SYNAPSERESEARCH' \
                                --serverIP '10.20.2.28' \
                                --serverPort '104' \
                                --StudyInstanceUID $study_id \
                                --withFeedBack \
                                --StudyOnly)

    G='\033[32m'
    R='\033[0m'
    StudyDate=$(echo $status | awk '{print $20}' );
    AccessionNumber=$(echo $status | awk '{print $41}' );
    StudyDescription=$(echo $status | awk -v b=62 -v e=64 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' );
    echo -e "[$current/$search_count] ${G}StudyID:${study_id}${R} ${G}RequestedOn:${request_date}${R}  ${G}RequestedBy:${username}${R}  ${G}StudyDate:${StudyDate}${R} ${G}AccessionNumber:${AccessionNumber}${R} ${G}StudyDescription:${StudyDescription}${R}"

    ((current++))
done
# =========================================================

