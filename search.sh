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
cyan='\033[36m'
G='\033[32m'
R='\033[0m'
bold=$(tput bold)
normal=$(tput sgr0)
red='\033[31m'
cross='\u274c'
tick='\u2714'
while getopts "L:U:P:K:D:E:K:A:h" opt; do
    case $opt in
        h) printf "%s" "$SYNOPSIS"; exit 1                ;;

        L) URL=$OPTARG                                    ;;

        U) USERNAME=$OPTARG                               ;;

        P) PASSWORD=$OPTARG                               ;;

        D) DATE=$OPTARG                                   ;;
        
        E) END_DATE=$OPTARG                               ;;

        K) KEYWORD=$OPTARG                                ;;

        A) ANO=$OPTARG                                    ;;

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
l_study_id=()
l_series_id=()
count=$(echo "${#hash_key[@]}")
if [ $count == 0 ] ; then
  echo "No search results for $KEYWORD"
  exit
fi
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
      #echo "Internal server error occurred while searching for db_key: $i in pflink"
      continue
    fi
    study_id=$(echo $workflow_record | jq '.request.PACS_directive.StudyInstanceUID')
    series_id=$(echo $workflow_record | jq '.request.PACS_directive.SeriesInstanceUID')
    l_study_id+=("$study_id")
    l_series_id+=("$series_id")
    request_date=$(echo $workflow_record | jq '.creation_time' | awk '{print $1}')
    username=$(echo $workflow_record | jq '.request.cube_user_info.username')
done
uniques=($(for v in "${l_study_id[@]}"; do echo "$v";done| sort| uniq| xargs))
uniques_1=($(for v in "${l_series_id[@]}"; do echo "$v";done| sort| uniq| xargs))
current=1
search_count=$(echo "${#uniques[@]}")
remarks=""
if (( "$search_count" == 0 )) ; then
  remarks=$(echo ${red}No LLD records found.)
  # echo "No LLD analysis found for PatientID: $KEYWORD, AccessionNumber: $ANO in pflink for studies on $DATE"
else
  remarks="$search_count LLD records found."
fi
# for study in "${uniques[@]}"; do
    # =========================================================
    # Search PACS using px-find
    # =========================================================
    response=$(findscu -S -k QueryRetrieveLevel=IMAGE -k StudyInstanceUID=${uniques[0]} \
       -k SeriesInstanceUID=${uniques_1[0]} -k "BodyPartExamined" -k "SeriesNumber" \
       -aec PACSDCM -aet CHRISV3 134.174.12.21 104 2>&1 | strings)
    fmt_txt=$(echo $response | awk -v b=39 -v e=39 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | tr -d '[]')
    srs_no=$(echo $response | awk -v b=64 -v e=65 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | tr -d '[]IS#[:blank:]' | tr -s '[:blank:]')
    if [[ -z $(echo $srs_no | tr -s '[:blank:]') ]]; then
      srs_no=00
    fi
    resp_pacs=$(findscu -S -k QueryRetrieveLevel=SERIES -k StudyInstanceUID=${uniques[0]} \
        -k "SeriesDescription" -k SeriesNumber=$srs_no \
       -aec SYNAPSERESEARCH -aet SYNAPSERESEARCH 10.20.2.28 104 2>&1 | strings)
    srs_desc=$(echo $resp_pacs | awk -v b=38 -v e=40 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | tr -d '[]')
    echo $srs_desc


    status=$(px-find \
                                --aec 'SYNAPSERESEARCH' \
                                --aet 'SYNAPSERESEARCH' \
                                --serverIP '10.20.2.28' \
                                --serverPort '104' \
                                --AccessionNumber $ANO \
                                --withFeedBack)
                                #--StudyInstanceUID $study \

    #echo "Requested to synapse: $study, $KEYWORD, $ANO"
    #echo $status
    symbol=$(echo ${G}${bold}${tick}${R})
    StudyDate=$(echo $status | awk '{print $20}' );
    if [[ -z "$StudyDate" ]]; then
      StudyDate=$(echo ${bold}${red}$DATE${normal} )
      symbol=$cross
    fi
    AccessionNumber=$(echo $status | awk '{print $41}' );
    if [[ -z "$AccessionNumber" ]]; then
      AccessionNumber=$(echo ${bold}${red}$ANO${normal} )
    fi
    StudyDescription=$(echo $status | awk -v b=62 -v e=64 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}');
    if [[ -z $(echo $StudyDescription | tr -s '[:blank:]') ]]; then
      StudyDescription=$(echo ${bold}${red}NOT IN SYNAPSERESEARCH${normal} )
    fi
    SeriesDescription=$(echo $status | awk -v b=85 -v e=89 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | sed -e 's/\x1b\[[0-9;]*m//g');
    SeriesDescription=$(echo $srs_desc | sed 's/[^a-z A-Z 0-9]//g' | sed 's/["0xB"]//g' | sed 's/SeriesDescription//g')
    if [[ -z "$SeriesDescription" ]]; then
      SeriesDescription=$(echo ${bold}${red}NOT IN SYNAPSERESEARCH${normal} )
    fi
    echo -e "[${symbol}] ${G}PatientID:${bold}${KEYWORD}${R}${normal} ${G}AccessionNumber:${bold}${AccessionNumber}${R} ${G}StudyDate:${StudyDate}${R} ${G}StudyDescription:${StudyDescription}${R} ${G}SeriesDescription:${bold}${SeriesDescription}${R} ${G}Remarks:${bold}${remarks}${R} ${G}BodyPartExamined:${bold}[${fmt_txt}]${R} "

    ((current++))
#done
# =========================================================

