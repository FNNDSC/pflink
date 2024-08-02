#!/usr/bin/env bash


while getopts "S:K:F:D:h" opt; do
    case $opt in

        S) STUDY_DATE=$OPTARG                             ;;

        K) KEYWORD=$OPTARG                                ;;

        F) FILE_NAME=$OPTARG                              ;;

        D) DO_RUN=$OPTARG                                 ;;

        *) exit 0                                         ;;

    esac
done

response=$(px-find --aet CHRISV3 \
              --serverIP 134.174.12.21  \
              --serverPort 104 \
              --db /neuro/users/chris/PACS/log \
              --verbosity 2 \
              --withFeedBack \
              --StudyDate $STUDY_DATE \
              --Modality CT \
              --StudyOnly | grep -i -A 3 -B 9 "$KEYWORD" & wait)

list=$response

current=1
for item in "${list[@]}"; do
    list_values=$(echo "$item" | awk '{print $5}');
    ((current++))
done

values=$(echo "${list_values}" | sed '/^$/N;/^\n$/D')
test=$(echo "$values" | sed -e 's/^$/:/' )
IFS=':'; array=($test); unset IFS;

study_hits=$(echo "${#array[@]}")
#if (( "$study_hits" == 1 )) ; then
#  echo "No $KEYWORD study found for Date: $STUDY_DATE in PACS"
#fi

for i in "${array[@]}"; do
  ANO=$(echo $i | awk '{print $6}' | sed -e 's/\x1b\[[0-9;]*m//g');
  k=$(echo $i | awk '{print $7}' | sed -e 's/\x1b\[[0-9;]*m//g');
  if [ "$k" == "" ]; then
    continue
  fi
  ./search.sh -L http://galena.tch.harvard.edu:30033/api/v1 -K $k -D $STUDY_DATE -A $ANO -F $FILE_NAME  &
done
wait


