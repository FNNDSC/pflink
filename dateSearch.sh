#!/usr/bin/env bash

start=2024-04-01
end=2024-04-10
cmd=""
while ! [[ $start > $end ]]; do
    cmd+="./helperSearch.sh -S $start &"
    start=$(date -d "$start + 1 day" +%Y%m%d)
done
echo "$cmd wait" | sh -v


    
