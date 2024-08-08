#!/usr/bin/env bash

FILE_NAME="search_results.csv"
NUM_PROC=8
DO_RUN="search"

while getopts "S:E:K:F:R:N:D:h" opt; do
    case $opt in

        S) START_DATE=$OPTARG                           ;;

        E) END_DATE=$OPTARG                             ;;

        K) KEYWORD=$OPTARG                              ;;

        F) FILE_NAME=$OPTARG                            ;;

        N) NUM_PROC=$OPTARG                             ;;

        D) DO_RUN=$OPTARG                               ;;

        *) exit 0                                       ;;

    esac
done
echo "Status,PatientID,AccessionNumber,StudyDate,StudyDescription,SeriesDescription,Remarks,BodyPartExamined,FieldOfViewDimensions" > $FILE_NAME
while ! [[ "$START_DATE" > "$END_DATE" ]]; do
    curr_date=$(date -d "$START_DATE" +%Y%m%d)
    yyyy=$(date -d $curr_date +%Y)
    mm=$(date -d $curr_date +%m)
    dd=$(date -d $curr_date +%d)
    mkdir -p "${yyyy}/${mm}/${dd}"
    ((i=i%NUM_PROC)); ((i++==0)) && wait
    ./helperSearch.sh -S $curr_date -K "$KEYWORD" -F $FILE_NAME -D $DO_RUN &
    START_DATE=$(date -d "$curr_date + 1 day" +%Y%m%d)
    END_DATE=$(date -d "$END_DATE" +%Y%m%d)
done
wait
date=$(date)
echo "[${date}] Search query executed successfully."
