#!/usr/bin/env bash

while getopts "S:E:K:h" opt; do
    case $opt in

        S) START_DATE=$OPTARG                           ;;

        E) END_DATE=$OPTARG                             ;;

        K) KEYWORD=$OPTARG                              ;;

        *) exit 0                                       ;;

    esac
done
while ! [[ "$START_DATE" > "$END_DATE" ]]; do
    curr_date=$(date -d "$START_DATE" +%Y%m%d)
    ./helperSearch.sh -S $curr_date -K $KEYWORD &
    START_DATE=$(date -d "$curr_date + 1 day" +%Y%m%d)
    END_DATE=$(date -d "$END_DATE" +%Y%m%d)
done
echo "Search query executed successfully."
wait