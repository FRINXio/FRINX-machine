#!/usr/bin/env bash

#/opt/distribution-frinx/create-user.sh
/opt/distribution-frinx/run_uniconfig.sh || true
/opt/distribution-frinx/run-lighty-uniconfig-distribution.sh || true