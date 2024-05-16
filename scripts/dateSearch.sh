#!/usr/bin/env bash

FILE_NAME="search_results.csv"
NUM_PROC=8

while getopts "S:E:K:F:R:N:h" opt; do
    case $opt in

        S) START_DATE=$OPTARG                           ;;

        E) END_DATE=$OPTARG                             ;;

        K) KEYWORD=$OPTARG                              ;;

        F) FILE_NAME=$OPTARG                            ;;

        N) NUM_PROC=$OPTARG                             ;;

        *) exit 0                                       ;;

    esac
done
echo "Status,PatientID,AccessionNumber,StudyDate,StudyDescription,SeriesDescription,Remarks,BodyPartExamined,FieldOfViewDimensions" > $FILE_NAME
while ! [[ "$START_DATE" > "$END_DATE" ]]; do
    curr_date=$(date -d "$START_DATE" +%Y%m%d)
    ((i=i%NUM_PROC)); ((i++==0)) && wait
    ./helperSearch.sh -S $curr_date -K $KEYWORD -F $FILE_NAME &
    START_DATE=$(date -d "$curr_date + 1 day" +%Y%m%d)
    END_DATE=$(date -d "$END_DATE" +%Y%m%d)
done
wait
date=$(date)
echo "[${date}] Search query executed successfully."
