#!/bin/bash
# Run this from UPM as ./misc/fix_feats.sh
. ./path.sh

# Converts MFCC feats.scp to feats_mfcc.scp for all data folders.
for dir in ${DATA_DIR_GLOBAL}/*/; do
    lang_dir=${dir%*/}
    if [ -f ${lang_dir}/lists/feats.scp ]; then
        mv ${lang_dir}/lists/feats.scp ${lang_dir}/lists/feats_mfcc.scp
    fi
done

# Copy feats.scp (containing FBANK features) to data as feats_fbank.scp
for dir in ${WAV_DIR_GLOBAL}/*/; do
    lang_dir=${dir%*/}
    lang=`basename $lang_dir`
    
    if [ -f ${lang_dir}/feats.scp ]; then
        data_dir=$DATA_DIR_GLOBAL/$lang/lists
        cp ${lang_dir}/feats.scp $data_dir/feats_fbank.scp
    fi
done

