#!/bin/sh

function argumentsCheck {
  if [ $1 -eq 0 ]
  then
    execBackup=1
  fi

  if [ $1 -eq 1 ]
  then
    case $2 in
      --register-repo)
      registerRepo=1
      ;;

      *)
      exit
      ;;
    esac
  fi

  if [ $1 -gt 1 ]
  then
    exit
  fi
}

function register {
    curl -H 'Content-Type: application/json' -XPUT localhost:9200/_snapshot/es_backup -d '{"type": "fs","settings": {"location": "/usr/share/elasticsearch/backup"}}'
}

function backup {
    curl -X PUT "localhost:9200/_snapshot/es_backup/%3Csnapshot-%7Bnow%2Fd%7D%3E?wait_for_completion=true"
    tar -zcf /usr/share/elasticsearch/data/elasticsearch_snapshot-$(date +%Y-%m-%d).tar.gz /usr/share/elasticsearch/backup
    rm -rf /usr/share/elasticsearch/backup/*
}

# =======================================
# Program starts here
# =======================================
execBackup=0
registerRepo=0

argumentsCheck $# $@

if [ $registerRepo -eq 1 ]
then
    register
fi

if [ $execBackup -eq 1 ]
then
    backup
fi
