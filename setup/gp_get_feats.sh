#!/bin/bash
# Go up to main UPM directory
cd "/home/paul/UPM"

# Don't need since only using run.pl?
#[ -f cmd.sh ] && source cmd.sh || echo "cmd.sh not found. Jobs may not run properly"

. ./path.sh || { echo "Cannot source path.sh"; exit 1; }

apply_cmvn=true

GP_LANGUAGES="SA"
MFCC_DIR=$FEAT_DIR_GLOBAL/mfcc
DATA_DIR=$DATA_DIR_GLOBAL

echo "Running with languages: ${GP_LANGUAGES}"

echo "Organising speakers into sets."

python ./setup/gp_data_organise.py \
    --wav-dir $WAV_DIR_GLOBAL \
    --data-dir $DATA_DIR \
    --conf-dir $CONF_DIR_GLOBAL \
    --train-languages $GP_LANGUAGES \
    --val-languages $GP_LANGUAGES \
    --test-languages $GP_LANGUAGES


for L in $GP_LANGUAGES; do
  train_dirs+=($DATA_DIR/$L/train)
done
for L in $GP_LANGUAGES; do
  val_dirs+=($DATA_DIR/$L/val)
done
for L in $GP_LANGUAGES; do
  test_dirs+=($DATA_DIR/$L/test)
done


echo "Combining training directories: $(echo ${train_dirs[@]} | sed -e "s|${DATA_DIR}||g")"
utils/combine_data.sh --extra-files 'utt2len' $DATA_DIR/train ${train_dirs[@]}

echo "Combining validation directories: $(echo ${val_dirs[@]} | sed -e "s|${DATA_DIR}||g")"
utils/combine_data.sh --extra-files 'utt2len' $DATA_DIR/val ${val_dirs[@]}

echo "Combining testing directories: $(echo ${test_dirs[@]} | sed -e "s|${DATA_DIR}||g")"
utils/combine_data.sh --extra-files 'utt2len' $DATA_DIR/test ${test_dirs[@]}

for L in $GP_LANGUAGES; do
    rm -rf $DATA_DIR/$L
done

echo "Finished data preparation."

for x in train val test; do
    steps/make_mfcc.sh \
        --write-utt2num-frames false \
        --mfcc-config $CONF_DIR_GLOBAL/mfcc.conf \
        --nj 12 \
        --cmd run.pl \
        --compress true \
        $DATA_DIR/${x} \
        $LOG_DIR_GLOBAL/make_mfcc/${x} \
        $MFCC_DIR/${x}

    # Can maybe apply CMVN later

    # if [ apply_cmvn ]; then
    #   setup/prepare_feats_for_egs.sh \
    #     --nj 4 \
    #     --cmd run.pl \
    #     $DATA_DIR/${x} \
    #     $DATA_DIR/${x}_cmvn \
    #     $MFCC_DIR/${x}
    #
    #     # Clean up directories
    #     rm -rf $DATADIR/${x}
    #     mv $DATA_DIR/${x}_cmvn $DATA_DIR/${x}
    #
    #
    #
    # fi



done
