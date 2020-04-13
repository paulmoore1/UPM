#!/bin/bash

exp_dir=""

. ./utils/parse_options.sh

for x in train val test; do
    data_dir=${exp_dir}/data/$x
    ali_dir=${exp_dir}/tri3_ali_${x}
    let num=1
    for dir in ${ali_dir}/ali.*.gz; do
        ali-to-phones --ctm-output $ali_dir/final.mdl "ark:gunzip -c $dir |" "${ali_dir}/${num}.ctm"
        let num++
    done
    python ./setup/filter_valid_alignments.py \
        --data-dir $data_dir \
        --ali-dir $ali_dir

    # Delete CTM files to save space
    find $ali_dir -name '*.ctm' -delete

    utils/fix_data_dir.sh $data_dir

done