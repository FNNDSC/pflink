#!/usr/bin/env bash
SYNOPSIS="
NAME
    PACS_Search.sh

SYNOPSIS
    PACS_Search.sh   [-h]                                   \\
                     [-S <startDate>]                       \\
                     [-E <endDate>]                         \\
                     [-K <searchKeyWordForStudy>]           \\
                     [-D <savingDir>]
DESC
    PACS_Search.sh is a script to query BCH PACS between a
    date range for a particular study and cross check the
    records with BCH ChRIS for auto-triggered feeds.

ARGS
    [-h]
    If specified, print this synapsis text of PACS_Search.sh.

    [-S <startDate>]
    Required field to specify a start date to search the PACS.

    [-E <endDate>]
    Required field to specify an end date to search the PACS.

    [-K <searchKeyWordForStudy>]
    If specified, use this string as a search keyword
    for studies found in PACS

    [-D <savingDir>]
    If specified, use this location to store px-find JSON
    files organized date-wise


EXAMPLES
    $ ./PACS_Search.sh -S 2024-08-01                           \\
                       -E 2024-08-09                           \\
                       -K 'XR HIPS TO ANKLES LEG MEASUREMENTS' \\
                       -D /home/sandip/PACS_results

"
FILE_NAME=""
NUM_PROC=8
DO_RUN="search"

while getopts "S:E:K:R:N:D:h" opt; do
    case $opt in
        h) printf "%s" "$SYNOPSIS"; exit 1              ;;

        S) START_DATE=$OPTARG                           ;;

        E) END_DATE=$OPTARG                             ;;

        K) KEYWORD=$OPTARG                              ;;

        D) FILE_NAME=$OPTARG                            ;;

        N) NUM_PROC=$OPTARG                             ;;

        *) exit 0                                       ;;

    esac
done
echo > varfile
while ! [[ "$START_DATE" > "$END_DATE" ]]; do
    curr_date=$(date -d "$START_DATE" +%Y%m%d)
    ((i=i%NUM_PROC)); ((i++==0)) && wait
    ./helperSearch.sh -S $curr_date -K "$KEYWORD" -F $FILE_NAME &
    START_DATE=$(date -d "$curr_date + 1 day" +%Y%m%d)
    END_DATE=$(date -d "$END_DATE" +%Y%m%d)
done
wait
date=$(date)
echo "[${date}] Search query executed successfully."
echo "$(grep -c 1 varfile) studies found."
rm varfile
