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
normal='' # $(tput sgr0)
red='' #\033[31m'
cross='\u274c'
tick='\u2714 '
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
l_srs_no=()
l_bd_part=()
l_fov=()
srs_no=00
BodyPartExamined="NOT FOUND"
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
    study_id=$(echo $workflow_record | jq '.request.PACS_directive.StudyInstanceUID' | tr '""' "\n")
    series_id=$(echo $workflow_record | jq '.request.PACS_directive.SeriesInstanceUID'| tr '""' "\n")

    # =================================================================
    # Query PACSDCM for accession_number, series_no, body_part_examined
    # =================================================================
    pacs_response=$(findscu -S -xi -k QueryRetrieveLevel=IMAGE -k StudyInstanceUID="$study_id" -k "FieldOfViewDimensions" \
       -k SeriesInstanceUID="$series_id" -k "BodyPartExamined" -k "SeriesNumber" -k "AccessionNumber" -k "StationName"\
       -aec PACSDCM -aet CHRISV3 134.174.12.21 104 2>&1 | strings)
    AccessionNumber=$(echo $pacs_response | awk -v b=21 -v e=21 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | tr -d '[]')
    StationName=$(echo $pacs_response | awk -v b=47 -v e=50 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | cut -d'[' -f 2 | cut -d']' -f 1)
    BodyPartExamined=$(echo $pacs_response | awk -v b=55 -v e=56 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | cut -d'[' -f 2 | cut -d']' -f 1)
    fov=$(echo $pacs_response | awk -v b=64 -v e=66 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | cut -d'[' -f 2 | cut -d']' -f 1)
    srs_no=$(echo $pacs_response | awk -v b=88 -v e=96 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | cut -d'[' -f 2 | cut -d']' -f 1 | tr -d '[:blank:]')

    if [[ ! "$AccessionNumber" == "$ANO" ]] ; then
      continue
    fi

    if [[ " ${l_series_id[*]} " = *"$series_id"*  ]] ; then
      continue
    fi


    l_study_id+=("$study_id")
    l_series_id+=("$series_id")
    l_srs_no+=("$srs_no")
    l_fov+=("$fov")
    l_bd_part+=("$BodyPartExamined")
    request_date=$(echo $workflow_record | jq '.creation_time' | awk '{print $1}')
    username=$(echo $workflow_record | jq '.request.cube_user_info.username')

    if  [[ -z "$srs_no" ]] ; then
      srs_no=00
#      continue
#    else
#      break
    fi


#done

uniques=($(for v in "${l_study_id[@]}"; do echo "$v";done| sort| uniq| xargs))
uniques_1=($(for v in "${l_series_id[@]}"; do echo "$v";done| sort| uniq| xargs))
current=1
search_count=$(echo "${#uniques_1[@]}")
remarks=""
if (( "$search_count" == 0 )) ; then
  remarks=$(echo ${red}No LLD records found.)
  # echo "No LLD analysis found for PatientID: $KEYWORD, AccessionNumber: $ANO in pflink for studies on $DATE"
else
  remarks="$search_count LLD records found."
fi

symbol=$(echo ${G}${bold}${tick}${R})
flag=VALID
    resp_pacs=$(findscu -S -k QueryRetrieveLevel=SERIES -k "AccessionNumber"\
        -k "SeriesDescription" -k "StudyInstanceUID=$study_id" -k "SeriesNumber=$srs_no" \
       -aec SYNAPSERESEARCH -aet SYNAPSERESEARCH 10.20.2.28 104 2>&1 | strings)
    synapse_acc_no=$(echo $resp_pacs | awk -v b=21 -v e=21 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | tr -d '[]')
    SeriesDescription=$(echo $resp_pacs | awk -v b=46 -v e=49 '{for (i=b;i<=e;i++) printf "%s%s", $i, (i<e ? OFS : ORS)}' | cut -d'[' -f 2 | cut -d']' -f 1 | sed 's/[#]//g' )

    #echo $SeriesDescription




    status=$(px-find \
                                --aec 'SYNAPSERESEARCH' \
                                --aet 'SYNAPSERESEARCH' \
                                --serverIP '10.20.2.28' \
                                --serverPort '104' \
                                --AccessionNumber $ANO \
                                --withFeedBack)

    #echo "Requested to synapse: $study, $KEYWORD, $ANO"
    #echo $status
    StudyDate=$(echo $status | awk '{print $20}' );
    #echo "$status"
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
     if [[ ! "$ANO" == "$synapse_acc_no" ]] ; then
      BodyPartExamined=$(echo ${bold}${red}NOT FOUND${normal} )
      SeriesDescription=$(echo ${bold}${red}NOT IN SYNAPSERESEARCH${normal} )
      StudyDate=$(echo ${bold}${red}$DATE${normal} )
      symbol=$cross
      AccessionNumber=$(echo ${bold}${red}$ANO${normal} )
      StudyDate=$(echo ${bold}${red}$DATE${normal} )
      flag=INVALID
      StudyDescription=$(echo ${bold}${red}NOT IN SYNAPSERESEARCH${normal} )
      fov="NOT FOUND"
      StationName="NOT FOUND"
    fi

    echo -e "[${symbol}] ${G}PatientID:${bold}${KEYWORD}${R}${normal} ${G}AccessionNumber:${bold}${AccessionNumber}${R} ${G}StudyDate:${StudyDate}${R} ${G}StudyDescription:${StudyDescription}${R} ${G}SeriesDescription:${bold}${SeriesDescription}${R} ${G}Remarks:${bold}${remarks}${R} ${G}BodyPartExamined:${bold}[${BodyPartExamined}]${R} ${G}FOV:${bold}[${fov}]${R} ${G}StationName:${bold}[${StationName}]${R}"
    echo "${flag},${KEYWORD},${AccessionNumber},${StudyDate},$StudyDescription,${SeriesDescription},${remarks},${BodyPartExamined},${fov}" | sed -e 's/\x1b\[[0-9;]*m//g' >> $FILE_NAME

    ((current++))
done
# =========================================================
uniques_1=($(for v in "${l_series_id[@]}"; do echo "$v";done| sort| uniq| xargs))
current=1
search_count=$(echo "${#uniques_1[@]}")
remarks="No LLD records found."
if (( "$search_count" == 0 )) ; then
  status=$(px-find \
                                --aec 'SYNAPSERESEARCH' \
                                --aet 'SYNAPSERESEARCH' \
                                --serverIP '10.20.2.28' \
                                --serverPort '104' \
                                --AccessionNumber $ANO \
                                --withFeedBack)

    #echo "Requested to synapse: $study, $KEYWORD, $ANO"
    #echo $status
    StudyDate=$(echo $status | awk '{print $20}' );
    #echo "$status"
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
     if [[ ! "$ANO" == "$synapse_acc_no" ]] ; then
      BodyPartExamined=$(echo ${bold}${red}NOT FOUND${normal} )
      SeriesDescription=$(echo ${bold}${red}NOT IN SYNAPSERESEARCH${normal} )
      StudyDate=$(echo ${bold}${red}$DATE${normal} )
      symbol=$cross
      AccessionNumber=$(echo ${bold}${red}$ANO${normal} )
      StudyDate=$(echo ${bold}${red}$DATE${normal} )
      flag=INVALID
      StudyDescription=$(echo ${bold}${red}NOT IN SYNAPSERESEARCH${normal} )
      fov="NOT FOUND"
      StationName="NOT FOUND"
    fi

    echo -e "[${symbol}] ${G}PatientID:${bold}${KEYWORD}${R}${normal} ${G}AccessionNumber:${bold}${AccessionNumber}${R} ${G}StudyDate:${StudyDate}${R} ${G}StudyDescription:${StudyDescription}${R} ${G}SeriesDescription:${bold}${SeriesDescription}${R} ${G}Remarks:${bold}${remarks}${R} ${G}BodyPartExamined:${bold}[${BodyPartExamined}]${R} ${G}FOV:${bold}[${fov}]${R} ${G}StationName:${bold}[${StationName}]${R}"
    echo "${flag},${KEYWORD},${AccessionNumber},${StudyDate},$StudyDescription,${SeriesDescription},${remarks},${BodyPartExamined},${fov}" | sed -e 's/\x1b\[[0-9;]*m//g' >> $FILE_NAME
fi
