#!/bin/bash
. ./cmd.sh
[ -f path.sh ] && . ./path.sh
set -e


# Acoustic model parameters (copied from TIMIT)
numLeavesTri1=2500
numGaussTri1=15000
numLeavesMLLT=2500
numGaussMLLT=15000
numLeavesSAT=2500
numGaussSAT=15000
numGaussUBM=400
numLeavesSGMM=7000
numGaussSGMM=9000

feats_nj=8
train_nj=8
decode_nj=5

expname="expname"
exp_dir=$EXP_DIR_GLOBAL/$expname
exp_data_dir=$exp_dir/data
echo "Running experiment ${expname}, storing files in ${exp_dir}"

# Run once, then comment out these lines so they aren't run again
setup/compute_feats.sh
echo "Finished computing features; comment out these lines in run.sh now"
exit 1


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


# utils/mkgraph.sh $exp_data_dir/lang_test_bg $exp_dir/mono $exp_dir/mono/graph

# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  $exp_dir/mono/graph $exp_data_dir/val $exp_dir/mono/decode_val

# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  $exp_dir/mono/graph $exp_data_dir/test $exp_dir/mono/decode_test

echo ============================================================================
echo "           tri1 : Deltas + Delta-Deltas Training & Decoding               "
echo ============================================================================

# steps/align_si.sh --boost-silence 1.25 --nj "$train_nj" --cmd "$train_cmd" \
#  ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/mono ${exp_dir}/mono_ali

# Train tri1, which is deltas + delta-deltas, on train data.
# steps/train_deltas.sh --cmd "$train_cmd" \
#  $numLeavesTri1 $numGaussTri1 ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/mono_ali ${exp_dir}/tri1

# utils/mkgraph.sh ${exp_data_dir}/lang_test_bg ${exp_dir}/tri1 ${exp_dir}/tri1/graph

# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  ${exp_dir}/tri1/graph ${exp_data_dir}/val ${exp_dir}/tri1/decode_val

# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  ${exp_dir}/tri1/graph ${exp_data_dir}/test ${exp_dir}/tri1/decode_test

echo ============================================================================
echo "                 tri2 : LDA + MLLT Training & Decoding                    "
echo ============================================================================

# steps/align_si.sh --nj "$train_nj" --cmd "$train_cmd" \
#   ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/tri1 ${exp_dir}/tri1_ali

# steps/train_lda_mllt.sh --cmd "$train_cmd" \
#  --splice-opts "--left-context=3 --right-context=3" \
#  $numLeavesMLLT $numGaussMLLT ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/tri1_ali ${exp_dir}/tri2

# utils/mkgraph.sh ${exp_data_dir}/lang_test_bg ${exp_dir}/tri2 ${exp_dir}/tri2/graph

# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  ${exp_dir}/tri2/graph ${exp_data_dir}/val ${exp_dir}/tri2/decode_val

# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  ${exp_dir}/tri2/graph ${exp_data_dir}/test ${exp_dir}/tri2/decode_test

echo ============================================================================
echo "              tri3 : LDA + MLLT + SAT Training & Decoding                 "
echo ============================================================================

# Align tri2 system with train data.
# steps/align_si.sh --nj "$train_nj" --cmd "$train_cmd" \
#  --use-graphs true ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/tri2 ${exp_dir}/tri2_ali

# # From tri2 system, train tri3 which is LDA + MLLT + SAT.
# steps/train_sat.sh --cmd "$train_cmd" \
#  $numLeavesSAT $numGaussSAT ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/tri2_ali ${exp_dir}/tri3

# utils/mkgraph.sh ${exp_data_dir}/lang_test_bg ${exp_dir}/tri3 ${exp_dir}/tri3/graph

# steps/decode_fmllr.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  ${exp_dir}/tri3/graph ${exp_data_dir}/val ${exp_dir}/tri3/decode_val

# steps/decode_fmllr.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  ${exp_dir}/tri3/graph ${exp_data_dir}/test ${exp_dir}/tri3/decode_test