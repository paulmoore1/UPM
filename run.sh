#!/bin/bash

[ -f path.sh ] && . ./path.sh

setup/gp_data_prep.sh $DATA_DIR_GLOBAL || exit 1