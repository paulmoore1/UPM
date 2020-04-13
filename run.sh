#!/bin/bash
. ./cmd.sh
[ -f path.sh ] && . ./path.sh
set -e


# Acoustic model parameters (copied from TIMIT)
numGaussMono=2000
numLeavesTri1=2500
numGaussTri1=20000
numLeavesMLLT=2500
numGaussMLLT=20000
numLeavesSAT=3000
numGaussSAT=20000
numGaussUBM=400
numLeavesSGMM=7000
numGaussSGMM=9000

feats_nj=8
train_nj=8
decode_nj=8

#expname="sa_only"
expname="baseline_slavic"
#expname="all_no_bg"
cfgname="UPM_RNN_mfcc_slavic_base.cfg"
#cfgname="UPM_RNN_fbank_base.cfg"
feattype="mfcc"

#GP_LANGUAGES="BG SA UA SW CR HA PL TU"
GP_LANGUAGES="BG"
exp_dir=$EXP_DIR_GLOBAL/$expname
exp_data_dir=$exp_dir/data
baseline_dir=$EXP_DIR_GLOBAL/baseline_mfcc
mfccdir=$FEAT_DIR_GLOBAL/mfcc
fbankdir=$FEAT_DIR_GLOBAL/fbank
echo "Running experiment ${expname}, storing files in ${exp_dir}"
echo "Pytorch experiment files are ${cfgname}"

# Run once, then comment out these lines so they aren't run again
# setup/compute_feats.sh
# echo "Finished computing features; comment out these lines in run.sh now"
# exit 1

# setup/split_langs.sh --exp_dir $exp_dir --langs "$GP_LANGUAGES" --mfccdir $mfccdir
# exit

# setup/gp_data_prep.sh \
#     --expname $expname \
#     --langs "${GP_LANGUAGES}" \
#     --feattype "$feattype"

# setup/gp_prepare_dict.sh --src-dir=$exp_dir || exit 1

# # # # # # Caution below: we remove optional silence by setting "--sil-prob 0.0",
# # # # # # in TIMIT the silence appears also as a word in the dictionary and is scored.
# utils/prepare_lang.sh --sil-prob 0.0 --position-dependent-phones false --num-sil-states 3 \
#    ${exp_dir}/data/dict "sil" ${exp_dir}/data/lang_tmp ${exp_dir}/data/lang

# setup/gp_format_data.sh \
#     --expname $expname

# for x in train val test; do
#   steps/compute_cmvn_stats.sh $exp_data_dir/$x $exp_dir/make_cmvn/$x $mfccdir
#   #steps/compute_cmvn_stats.sh $exp_data_dir/$x $exp_dir/make_cmvn/$x $fbankdir
# done
# #
# # exit
# #For removing invalid utterances after aligning
# setup/filter_valid_alignments.sh \
#     --exp-dir $exp_dir

#Get phone feature maps for each item
ali_dir=${exp_dir}/tri3_ali
feat=all
for x in train val test; do
  echo "Making phone feature map for ${ali_dir}_${x}"
  phones=${ali_dir}_${x}/phones.txt
  python misc/make_phone_feature_map.py \
    --phones-filepath $phones \
    --feat $feat \
    --print-info True
done

# Adapted for hold-one-out
# tr_ali_dir=${exp_dir}/tri3_ali_train_no_BG
# val_ali_dir=${exp_dir}/tri3_ali_val_no_BG
# test_ali_dir=${exp_dir}/tri3_ali_test_BG

# feat=all
# for x in $tr_ali_dir $val_ali_dir $test_ali_dir; do
#   echo "Making phone feature map for ${x}"
#   phones=${x}/phones.txt
#   python misc/make_phone_feature_map.py \
#     --phones-filepath $phones \
#     --feat $feat \
#     --print-info True
# done

python misc/set_chunks.py \
  --cfg-filename $cfgname \
  --exp-data-dir $exp_data_dir


root_dir=$PWD
cd pytorch-kaldi
python run_exp.py cfg/UPM/$cfgname

cd $root_dir


local/score.sh $exp_data_dir/val $exp_data_dir/lang $PWD/pytorch-kaldi/exp/UPM_RNN_mfcc_base_5_layers/decode_UPM_val_out_dnn2

exit


# steps/align_si.sh \
#     --boost-silence 1.25 \
#     --nj "$train_nj" \
#     --cmd "$train_cmd" \
#     ${exp_data_dir}/test_TU \
#     ${exp_data_dir}/lang \
#     ${exp_dir}/mono \
#     ${exp_dir}/mono_ali_test_TU

# exit


echo ============================================================================
echo "                     MonoPhone Training & Decoding                        "
echo ============================================================================


mono_exp=mono
# steps/train_mono.sh  \
#     --nj "$train_nj" \
#     --totgauss $numGaussMono \
#     --cmd "$train_cmd" \
#     $exp_data_dir/train \
#     $exp_data_dir/lang \
#     $exp_dir/${mono_exp}

# utils/mkgraph.sh \
#     $exp_data_dir/lang_test_bg \
#     $exp_dir/${mono_exp} \
#     $exp_dir/${mono_exp}/graph

# steps/decode.sh \
#     --nj "$decode_nj" \
#     --cmd "$decode_cmd" \
#     $exp_dir/${mono_exp}/graph \
#     $exp_data_dir/val \
#     $exp_dir/${mono_exp}/decode_val

# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  $exp_dir/mono/graph $exp_data_dir/test $exp_dir/mono/decode_test


echo ============================================================================
echo "           tri1 : Deltas + Delta-Deltas Training & Decoding               "
echo ============================================================================
# # Train tri1, which is deltas + delta-deltas, on train data.
tri_exp=tri1

# steps/align_si.sh \
#     --boost-silence 1.25 \
#     --nj "$train_nj" \
#     --cmd "$train_cmd" \
#     ${exp_data_dir}/train \
#     ${exp_data_dir}/lang \
#     ${exp_dir}/mono \
#     ${exp_dir}/mono_ali


# steps/train_deltas.sh \
#     --cmd "$train_cmd" \
#     $numLeavesTri1 \
#     $numGaussTri1 \
#     ${exp_data_dir}/train \
#     ${exp_data_dir}/lang \
#     ${exp_dir}/mono_ali \
#     ${exp_dir}/${tri_exp}

# utils/mkgraph.sh \
#     ${exp_data_dir}/lang_test_bg \
#     ${exp_dir}/${tri_exp} \
#     ${exp_dir}/${tri_exp}/graph

# steps/decode.sh \
#     --nj "$decode_nj" \
#     --cmd "$decode_cmd" \
#     ${exp_dir}/${tri_exp}/graph \
#     ${exp_data_dir}/val \
#     ${exp_dir}/${tri_exp}/decode_val

# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  ${exp_dir}/${tri_exp}/graph ${exp_data_dir}/test ${exp_dir}/${tri_exp}/decode_test


echo ============================================================================
echo "                 tri2 : LDA + MLLT Training & Decoding                    "
echo ============================================================================

tri2_exp=tri2

# steps/align_si.sh --nj "$train_nj" --cmd "$train_cmd" \
#    ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/tri1 ${exp_dir}/tri1_ali


# steps/train_lda_mllt.sh --cmd "$train_cmd" \
#     --splice-opts "--left-context=3 --right-context=3" \
#     $numLeavesMLLT $numGaussMLLT ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/tri1_ali ${exp_dir}/${tri2_exp}

# utils/mkgraph.sh \
#     ${exp_data_dir}/lang_test_bg \
#     ${exp_dir}/${tri2_exp} \
#     ${exp_dir}/${tri2_exp}/graph

# steps/decode.sh \
#     --nj "$decode_nj" \
#     --cmd "$decode_cmd" \
#     ${exp_dir}/${tri2_exp}/graph \
#     ${exp_data_dir}/val \
#     ${exp_dir}/${tri2_exp}/decode_val


# steps/decode.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  ${exp_dir}/${tri2_exp}/graph ${exp_data_dir}/test ${exp_dir}/${tri2_exp}/decode_test

echo ============================================================================
echo "              tri3 : LDA + MLLT + SAT Training & Decoding                 "
echo ============================================================================

tri3_exp=tri3
# #Align tri2 system with train data.
# steps/align_si.sh --nj "$train_nj" --cmd "$train_cmd" \
#  --use-graphs true ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/${tri2_exp} ${exp_dir}/tri2_ali_train

# # From tri2 system, train tri3 which is LDA + MLLT + SAT.

# steps/train_sat.sh --cmd "$train_cmd" \
#     $numLeavesSAT $numGaussSAT ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/tri2_ali_train ${exp_dir}/${tri3_exp}

# utils/mkgraph.sh \
#     ${exp_data_dir}/lang_test_bg \
#     ${exp_dir}/${tri3_exp} \
#     ${exp_dir}/${tri3_exp}/graph

# steps/align_fmllr.sh --nj "$train_nj" --cmd "$train_cmd" \
#  ${exp_data_dir}/train ${exp_data_dir}/lang ${exp_dir}/${tri3_exp} ${exp_dir}/tri3_ali_train

# steps/align_fmllr.sh --nj "$train_nj" --cmd "$train_cmd" \
#  ${exp_data_dir}/val ${exp_data_dir}/lang ${exp_dir}/${tri3_exp} ${exp_dir}/tri3_ali_val

#  steps/align_fmllr.sh --nj "$train_nj" --cmd "$train_cmd" \
#  ${exp_data_dir}/test ${exp_data_dir}/lang ${exp_dir}/${tri3_exp} ${exp_dir}/tri3_ali_test


# steps/decode_fmllr.sh \
#     --nj "$decode_nj" \
#     --cmd "$decode_cmd" \
#     ${exp_dir}/${tri3_exp}/graph \
#     ${exp_data_dir}/val \
#     ${exp_dir}/${tri3_exp}/decode_val

# steps/decode_fmllr.sh --nj "$decode_nj" --cmd "$decode_cmd" \
#  ${exp_dir}/${tri3_exp}/graph ${exp_data_dir}/test ${exp_dir}/${tri3_exp}/decode_test

