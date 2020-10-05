#!/usr/bin/env bash

#copy token from env
touch config/frinx.license.cfg
echo "token=${TOKEN}" > config/frinx.license.cfg

#/opt/distribution-frinx/create-user.sh
/opt/uniconfig-frinx/run_uniconfig.sh || true
/opt/uniconfig-frinx/run-lighty-uniconfig-distribution.sh || true