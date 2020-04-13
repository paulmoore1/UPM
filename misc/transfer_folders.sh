#!/bin/bash
# Run this from UPM as ./misc/transfer_folders.sh
. ./path.sh

for dir in ${WAV_DIR_GLOBAL}/*/; do
    lang_dir=${dir%*/}
    lang=`basename $lang_dir`
    for folder in ${lang_dir}/*; do
        folder_name=`basename $folder`
    # Transfers all folders apart from "files" (which contains WAV files)
        if [ $folder_name == "files" ]; then 
            continue
        else
            new_dir=${DATA_DIR_GLOBAL}/$lang/$folder_name
            mkdir -p $new_dir
            mv -v $folder/*  $new_dir
        fi
    done
done