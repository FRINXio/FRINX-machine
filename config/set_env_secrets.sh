#!/bin/sh

# set env variables from docker secret to service

set -a

FILES="/run/secrets/*"
for __filePath in $FILES
do
  if [ -f ${__filePath} ]; then
    . ${__filePath}
    cat ${__filePath} | while read line || [ -n "$line" ]; 
    do 
      case $line in
        '#'*) 
              ;; # ignore comments
        '')
              ;; # ignore empty spaces
        *)
            export $(echo "${line}" | cut -d '=' -f1) >/dev/null
            test="${test} $line";;
      esac
    done
  fi
done
${1}