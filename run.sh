#!/bin/bash
. ./cmd.sh
[ -f path.sh ] && . ./path.sh
set -e

feats_nj=8
train_nj=8
decode_nj=8

expname="expname"
exp_dir=$EXP_DIR_GLOBAL/$expname
exp_data_dir=$exp_dir/data
echo "Running experiment ${expname}, storing files in ${exp_dir}"

# setup/gp_data_prep.sh $DATA_DIR_GLOBAL || exit 1

# setup/gp_prepare_dict.sh --src-dir=$exp_dir || exit 1

# # Caution below: we remove optional silence by setting "--sil-prob 0.0",
# # in TIMIT the silence appears also as a word in the dictionary and is scored.
# utils/prepare_lang.sh --sil-prob 0.0 --position-dependent-phones false --num-sil-states 3 \
#   ${exp_dir}/data/dict "sil" ${exp_dir}/data/lang_tmp ${exp_dir}/data/lang

# setup/gp_format_data.sh

# mfccdir=$FEAT_DIR_GLOBAL/mfcc

# for x in train val test; do
#   steps/make_mfcc.sh --cmd "$train_cmd" --nj $feats_nj $exp_data_dir/$x $exp_dir/make_mfcc/$x $mfccdir
#   steps/compute_cmvn_stats.sh $exp_data_dir/$x $exp_dir/make_mfcc/$x $mfccdir
# done

echo ============================================================================
echo "                     MonoPhone Training & Decoding                        "
echo ============================================================================

#steps/train_mono.sh  --nj "$train_nj" --cmd "$train_cmd" $exp_data_dir/train $exp_data_dir/lang $exp_dir/mono


utils/mkgraph.sh $exp_data_dir/lang_test_bg $exp_dir/mono $exp_dir/mono/graph

steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
 $exp_dir/mono/graph $exp_data_dir/val $exp_dir/mono/decode_val

steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
 $exp_dir/mono/graph $exp_data_dir/test $exp_dir/mono/decode_test

