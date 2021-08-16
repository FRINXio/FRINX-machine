#!/bin/sh

. /set_env_secrets.sh

yarn prisma migrate deploy --schema=prisma/schema.prisma 
MIGRATION_SUCCESS=$?
if [ ${MIGRATION_SUCCESS} -ne 0 ]; then
    exit 1
fi
node index.js