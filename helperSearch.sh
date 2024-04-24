#!/usr/bin/env bash


while getopts "S:E" opt; do
    case $opt in

        S) START_DATE=$OPTARG                             ;;

        S) END_DATE=$OPTARG                             ;;


        *) exit 0                                   ;;

    esac
done

response=$(px-find --aet CHRISV3 \
              --serverIP 134.174.12.21  \
              --serverPort 104 \
              --db /neuro/users/chris/PACS/log \
              --verbosity 2 \
              --withFeedBack \
              --StudyDate $START_DATE \
              --Modality CT \
              --StudyOnly | grep -A 3 -B 9 Scanogram

)

list=$response
current=1
for item in "${list[@]}"; do
    list_values=$(echo "$item" | awk '{print $5}');
    ((current++))
done

values=$(echo "${list_values}" | sed '/^$/N;/^\n$/D')
test=$(echo "$values" | sed -e 's/^$/:/' )
IFS=':'; array=($test); unset IFS;

cmd=""
for i in "${array[@]}"; do
  R='\033[0m'
  k=$(echo $i | awk '{print $7}' | sed -e 's/\x1b\[[0-9;]*m//g');
  if [ "$k" == "" ]; then
    continue
  fi
  cmd+="./search.sh -L http://galena.tch.harvard.edu:30033/api/v1 -K $k  &"
  #cmd+="./search.sh -L http://galena.tch.harvard.edu:30033/api/v1 -K $k & "

done
echo "$cmd wait" | sh -v


