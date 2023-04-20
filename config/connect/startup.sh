#!/bin/bash

nohup /config/register_postgres.sh &

/docker-entrypoint.sh start