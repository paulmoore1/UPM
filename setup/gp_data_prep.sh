#!/bin/bash

# Based on timit_data_prep

if [ $# -ne 1 ]; then
   echo "Argument should be the ? directory, see ../run.sh for example."
   exit 1;
fi
expname="expname"

. ./path.sh

dir=$EXP_DIR_GLOBAL/$expname/data
lmdir=$EXP_DIR_GLOBAL/$expname/lm
mkdir -p $dir $lmdir
local=$UPM_DIR_GLOBAL/local
utils=$UPM_DIR_GLOBAL/utils
conf=$UPM_DIR_GLOBAL/conf

sph2pipe=$KALDI_ROOT/tools/sph2pipe_v2.5/sph2pipe

if [ ! -x $sph2pipe ]; then
   echo "Could not find (or execute) the sph2pipe program at $sph2pipe";
   exit 1;
fi

GP_LANGUAGES="SA UK"
MFCC_DIR=$FEAT_DIR_GLOBAL/mfcc
DATA_DIR=$dir

echo "Running with languages: ${GP_LANGUAGES}"

echo "Organising speakers into sets."

python ./setup/gp_data_organise.py \
    --wav-dir $WAV_DIR_GLOBAL \
    --data-dir $DATA_DIR \
    --conf-dir $CONF_DIR_GLOBAL \
    --train-languages "${GP_LANGUAGES}" \
    --val-languages "$GP_LANGUAGES" \
    --test-languages "$GP_LANGUAGES"


# for L in $GP_LANGUAGES; do
#   train_dirs+=($DATA_DIR/$L/train)
# done
# for L in $GP_LANGUAGES; do
#   val_dirs+=($DATA_DIR/$L/val)
# done
# for L in $GP_LANGUAGES; do
#   test_dirs+=($DATA_DIR/$L/test)
# done


# echo "Combining training directories: $(echo ${train_dirs[@]} | sed -e "s|${DATA_DIR}||g")"
# utils/combine_data.sh --extra-files 'utt2len' $DATA_DIR/train ${train_dirs[@]}

# echo "Combining validation directories: $(echo ${val_dirs[@]} | sed -e "s|${DATA_DIR}||g")"
# utils/combine_data.sh --extra-files 'utt2len' $DATA_DIR/val ${val_dirs[@]}

# echo "Combining testing directories: $(echo ${test_dirs[@]} | sed -e "s|${DATA_DIR}||g")"
# utils/combine_data.sh --extra-files 'utt2len' $DATA_DIR/test ${test_dirs[@]}

# for L in $GP_LANGUAGES; do
#     rm -rf $DATA_DIR/$L
# done

# cd $dir
# for x in train val test; do
# # Doing this currently to match TIMIT
#     cp $dir/$x/wav.scp $dir/${x}_wav.scp
#     cp $dir/$x/spk2utt $dir/${x}.spk2utt
#     cp $dir/$x/utt2spk $dir/${x}.utt2spk
#     cp $dir/$x/utt2len $dir/${x}_utt2len
#     cat ${x}.utt2spk | awk '{print $1}' > ${x}.uttids
# done