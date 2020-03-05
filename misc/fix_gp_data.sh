#!/bin/bash
# Run this from UPM as ./misc/fix_gp_data.sh
. ./path.sh

for dir in ${DATA_DIR_GLOBAL}/*/; do
    lists_dir=${dir%*/}/lists

    python misc/filter_files.py \
        --list-dir $lists_dir
    
    utils/fix_data_dir.sh $lists_dir

    utils/validate_data_dir.sh $lists_dir

done