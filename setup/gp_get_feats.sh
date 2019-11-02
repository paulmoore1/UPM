#!/bin/bash
# Go up to main UPM directory
cd "/home/paul/UPM"

# Don't need since only using run.pl?
#[ -f cmd.sh ] && source cmd.sh || echo "cmd.sh not found. Jobs may not run properly"

. ./path.sh || { echo "Cannot source path.sh"; exit 1; }



GP_LANGUAGES="WU"
MFCC_DIR=$FEAT_DIR/mfcc

echo "Running with languages: ${GP_LANGUAGES}"

for L in $GP_LANGUAGES; do
    echo "Prepping language ${L}"
    lang_dir=$WAV_DIR/${L}/lists
    utils/fix_data_dir.sh $lang_dir

    # echo "Creating MFCC features."
    # steps/make_mfcc.sh \
    #     --write-utt2num-frames false \
    #     --mfcc-config $CONF_DIR/mfcc.conf \
    #     --nj 12 \
    #     --cmd run.pl \
    #     --compress true \
    #     $lang_dir \
    #     $LOG_DIR/make_mfcc/${L}

    #     $MFCC_DIR/${L}

done