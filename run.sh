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
decode_nj=8

expname="new_exp"
GP_LANGUAGES="SA UA GE"
exp_dir=$EXP_DIR_GLOBAL/$expname
exp_data_dir=$exp_dir/data
echo "Running experiment ${expname}, storing files in ${exp_dir}"

# Run once, then comment out these lines so they aren't run again
# setup/compute_feats.sh
# echo "Finished computing features; comment out these lines in run.sh now"
# exit 1

# setup/gp_data_prep.sh \
#     --expname $expname \
#     --langs "${GP_LANGUAGES}"


# setup/gp_prepare_dict.sh --src-dir=$exp_dir || exit 1

# # # Caution below: we remove optional silence by setting "--sil-prob 0.0",
# # # in TIMIT the silence appears also as a word in the dictionary and is scored.
# utils/prepare_lang.sh --sil-prob 0.0 --position-dependent-phones false --num-sil-states 3 \
#    ${exp_dir}/data/dict "sil" ${exp_dir}/data/lang_tmp ${exp_dir}/data/lang

# setup/gp_format_data.sh \
#     --expname $expname

mfccdir=$FEAT_DIR_GLOBAL/mfcc

# for x in train val test; do
# ##   steps/make_mfcc.sh --cmd "$train_cmd" --nj $feats_nj $exp_data_dir/$x $exp_dir/make_mfcc/$x $mfccdir
#     steps/compute_cmvn_stats.sh $exp_data_dir/$x $exp_dir/make_cmvn/$x $mfccdir
# done

echo ============================================================================
echo "                     MonoPhone Training & Decoding                        "
echo ============================================================================

# gaussians=(1000 2000)
# for gaussian in ${gaussians[@]}; do
#     mono_exp=mono_${gaussian}
#     echo "Training monophone model with ${gaussian} target number of Gaussians"
        
#     steps/train_mono.sh  \
#         --nj "$train_nj" \
#         --totgauss $gaussian \
#         --cmd "$train_cmd" \
#         $exp_data_dir/train \
#         $exp_data_dir/lang \
#         $exp_dir/${mono_exp}

#     echo "Building graph"
#     utils/mkgraph.sh \
#         $exp_data_dir/lang_test_bg \
#         $exp_dir/${mono_exp} \
#         $exp_dir/${mono_exp}/graph

#     echo "Decoding model with ${gaussian} Gaussians"
#     steps/decode.sh \
#         --nj "$decode_nj" \
#         --cmd "$decode_cmd" \
#         $exp_dir/${mono_exp}/graph \
#         $exp_data_dir/val \
#         $exp_dir/${mono_exp}/decode_val
    
# done

# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  $exp_dir/mono/graph $exp_data_dir/test $exp_dir/mono/decode_test


echo ============================================================================
echo "           tri1 : Deltas + Delta-Deltas Training & Decoding               "
echo ============================================================================
numLeavesTri1=(2000 2500 3000)
numGaussTri1=(10000 15000 20000)
numLeavesMLLT=(2000 2500 3000)
numGaussMLLT=(10000 15000 20000)
numLeavesSAT=(2000 2500 3000)
numGaussSAT=(10000 15000 20000)

# steps/align_si.sh \
#     --boost-silence 1.25 \
#     --nj "$train_nj" \
#     --cmd "$train_cmd" \
#     ${exp_data_dir}/train \
#     ${exp_data_dir}/lang \
#     ${exp_dir}/mono_2000 \
#     ${exp_dir}/mono_ali

for numLeaves in ${numLeavesTri1[@]}; do
    for numGauss in ${numGaussTri1[@]}; do
    echo "Training triphone with ${numLeaves} leaves and ${numGauss} Gaussians"
        tri_exp=tri1_leaves_${numLeaves}_gauss_${numGauss}
        
        # Train tri1, which is deltas + delta-deltas, on train data.
        steps/train_deltas.sh \
            --cmd "$train_cmd" \
            $numLeaves \
            $numGauss \
            ${exp_data_dir}/train \
            ${exp_data_dir}/lang \
            ${exp_dir}/mono_ali \
            ${exp_dir}/${tri_exp}

        utils/mkgraph.sh \
            ${exp_data_dir}/lang_test_bg \
            ${exp_dir}/${tri_exp} \
            ${exp_dir}/${tri_exp}/graph

        steps/decode.sh \
            --nj "$decode_nj" \
            --cmd "$decode_cmd" \
            ${exp_dir}/${tri_exp}/graph \
            ${exp_data_dir}/val \
            ${exp_dir}/${tri_exp}/decode_val
    done
done




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