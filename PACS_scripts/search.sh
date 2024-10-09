#!/usr/bin/env bash
# =========================================================
SYNOPSIS="
NAME
    run_analysis.sh

SYNOPSIS
    run_analysis.sh [-h]                           \\
                     [-L <pflinkServiceURL>]       \\
                     [-U <pflinkUsername>]         \\
                     [-P <pflinkPassword>]         \\
                     [-K <searchKeyWord>]          \\
                     [-N <concurrent_no_of_days>]
DESC
    run_analysis.sh is a helper script to authenticate into a
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
C='\033[33m'
bold=$(tput bold)
normal='' # $(tput sgr0)
red='' #\033[31m'
cross='\u274c'
tick='\u2714 '
warning='\u26A0'
while getopts "L:U:P:K:D:E:K:A:F:h" opt; do
    case $opt in
        h) printf "%s" "$SYNOPSIS"; exit 1                ;;

        L) URL=$OPTARG                                    ;;

        U) USERNAME=$OPTARG                               ;;

        P) PASSWORD=$OPTARG                               ;;

        D) DATE=$OPTARG                                   ;;

        E) END_DATE=$OPTARG                               ;;

        K) KEYWORD=$OPTARG                                ;;

        A) ANO=$OPTARG                                    ;;

        F) FILE_NAME=$OPTARG                              ;;

        *) exit 0                                         ;;

    esac
done

status=$(px-find \
                                --aet CHRISV3 \
                                --serverIP 134.174.12.21  \
                                --serverPort 104 \
                                --AccessionNumber $ANO \
                                --json)
yyyy=$(date -d $DATE +%Y)
mm=$(date -d $DATE +%m)
dd=$(date -d $DATE +%d)
echo $status > "${FILE_NAME}/${yyyy}/${mm}/${dd}/${ANO}/status.json"
StudyDescription="Not available"
StudyDescription=$(echo $status | jq '.data[0].StudyDescription.value')
series=$(echo $status | jq '.data[0].series')
StationName=$(echo $status | jq '.data[0].series[0].StationName.value')
SeriesDescription="Not Applicable"
# =========================================================
# AUTHENTICATION
# =========================================================
RESP=$(curl -s -X 'GET' \
       -u radstar:radstar1234 \
       "http://rc-live.tch.harvard.edu:32222/api/v1/search/?name=$KEYWORD&min_creation_date=$DATE" | jq)
error=$(echo $RESP | jq '.collection.items[0].data[12].value' | tr '""' "\n")
feed_id=$(echo $RESP | jq '.collection.items[0].data[0].value' | tr '""' "\n")
feed_ui_link="http://chris-next.tch.harvard.edu:2222/feeds/${feed_id}?type=private"

total=$(echo $RESP | jq '.collection.total' | tr '""' "\n")
symbol=$cross
remarks="Not available in ChRIS"
if [[ $total>0 ]]; then
    symbol=$(echo ${G}${bold}${tick}${R})
    remarks="\e]8;;${feed_ui_link}\e\\${total} analysis found.\e]8;;\e\\"
fi

# read each item in the JSON array to an item in the Bash array
readarray -t my_array < <(echo $series | jq --compact-output '.[]')

# iterate through the Bash array
for item in "${my_array[@]}"; do
  sid=$(echo $item | jq '.SeriesInstanceUID.value' | tr '""' "\n")
  stid=$(echo $item | jq '.StudyInstanceUID.value' | tr '""' "\n")
  SeriesDescription=$(echo $item | jq '.SeriesDescription.value')
  pacs_response=$(findscu -S -xi -k QueryRetrieveLevel=IMAGE -k "StudyInstanceUID=$stid" -k "FieldOfViewDimensions" \
       -k "SeriesInstanceUID=$sid" -k "BodyPartExamined" -k "SeriesNumber" -k "AccessionNumber" -k "StationName"\
       -aec PACSDCM -aet CHRISV3 134.174.12.21 104 2>&1 | strings)

  StationName=$(echo $pacs_response | awk -v b=47 -v e=50 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | cut -d'[' -f 2 | cut -d']' -f 1)
  mark=""
  if [[ $StationName == *'EOS'* ]] && [[ $total == 0 ]]; then
    mark=$warning
  fi
  if [[ $SeriesDescription != *'SNAPSHOT'* ]] && [[ $SeriesDescription != *'ANNOTATIONS'* ]] && [[ $SeriesDescription != *'Information'* ]] && [[ $SeriesDescription != *'Report'* ]] && [[ $StationName != *'no value'* ]]; then
    echo -e "[${symbol}] ${G}PatientID:${bold}${KEYWORD}${R}${normal} ${G}AccessionNumber:${bold}${ANO}${R} ${G}StudyDate:${bold}${DATE}${R} ${G}StudyDescription:${bold}${StudyDescription}${R} ${G}SeriesDescription:[${bold}${SeriesDescription}]${R} ${G}Remarks:[${bold}${remarks}]${R} ${G}Error:[${bold}${error}]${R} ${G}StationName:[${bold}${StationName}]${R}${bold}${C}${mark}${R}"
  fi
done
echo 1 >> varfile



