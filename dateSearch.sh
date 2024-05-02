#!/usr/bin/env bash

FILE_NAME="search_results.csv"

while getopts "S:E:K:F:h" opt; do
    case $opt in

        S) START_DATE=$OPTARG                           ;;

        E) END_DATE=$OPTARG                             ;;

        K) KEYWORD=$OPTARG                              ;;

        F) FILE_NAME=$OPTARG                            ;;

        *) exit 0                                       ;;

    esac
done

echo "PatientID,AccessionNumber,StudyDate,StudyDescription,SeriesDescription,Remarks,BodyPartExamined" > $FILE_NAME
while ! [[ "$START_DATE" > "$END_DATE" ]]; do
    curr_date=$(date -d "$START_DATE" +%Y%m%d)
    ./helperSearch.sh -S $curr_date -K $KEYWORD -F $FILE_NAME &
    START_DATE=$(date -d "$curr_date + 1 day" +%Y%m%d)
    END_DATE=$(date -d "$END_DATE" +%Y%m%d)
done
echo "Search query executed successfully."
wait