# Call from run.sh to compute features (once) for each language.
echo "Computing all MFCC features"
echo "WAV files in ${WAV_DIR_GLOBAL}; storing features in ${FEAT_DIR_GLOBAL}/mfcc"
lang_dirs=`find ${WAV_DIR_GLOBAL} -maxdepth 1 -mindepth 1 -type d`
feats_nj=8
mfccdir=${FEAT_DIR_GLOBAL}/mfcc
for lang_dir in ${lang_dirs}; do
    lang=`basename ${lang_dir}`
    echo "Computing MFCC features for language $lang"
    cp -r $lang_dir/lists/. $lang_dir # Do this so that the MFCC files will have the language suffix and can be distinguished
    utils/fix_data_dir.sh $lang_dir
    steps/make_mfcc.sh --cmd "$train_cmd" --nj $feats_nj $lang_dir $lang_dir/make_mfcc $mfccdir
    steps/compute_cmvn_stats.sh $lang_dir $lang_dir/make_mfcc $mfccdir
    # Fix again to update after extracting features
    utils/fix_data_dir.sh $lang_dir
done