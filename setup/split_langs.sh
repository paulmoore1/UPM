#!/bin/bash

exp_dir="exp_test"
langs=""
mfccdir="mfcc"
# Based on timit_data_prep
. ./path.sh

. ./utils/parse_options.sh

exp_data_dir=$exp_dir/data
train_dir=$exp_data_dir/train
val_dir=$exp_data_dir/val
test_dir=$exp_data_dir/test

for lang in $langs; do
  #new_train=${train_dir}_no_$lang
  new_val=${val_dir}_$lang
  #new_val_2=${val_dir}_no_$lang
  new_test=${test_dir}_$lang
  #new_test_2=${test_dir}_no_$lang
  #cp -r $train_dir $new_train
  cp -r $val_dir $new_val
  cp -r $test_dir $new_test
  #cp -r $val_dir $new_val_2
  #cp -r $test_dir $new_test_2
  # Delete all lines in training utt2spk starting with the language
  #sed "/^${lang}/ d" < $new_train/utt2spk > $new_train/utt2spk.filt
  #sed "/^${lang}/ d" < $new_val_2/utt2spk > $new_val_2/utt2spk.filt
  #sed "/^${lang}/ d" < $new_test_2/utt2spk > $new_test_2/utt2spk.filt

  # Keep only the lines that match the language in val/test utt2spk
  awk "/^${lang}/{print}" < $new_val/utt2spk > $new_val/utt2spk.filt
  awk "/^${lang}/{print}" < $new_test/utt2spk > $new_test/utt2spk.filt

  for x in $new_val $new_test; do
  #for x in $new_train $new_val $new_test $new_val_2 $new_test_2; do
    mv $x/utt2spk.filt $x/utt2spk
    utils/fix_data_dir.sh $x
    steps/compute_cmvn_stats.sh $x $exp_dir/make_cmvn/$x $mfccdir
    #steps/compute_cmvn_stats.sh $exp_data_dir/$x $exp_dir/make_cmvn/$x $fbankdir
  done

  #new_tr_ali=tri3_ali_train_no_$lang
  new_val_ali=tri3_ali_val_$lang
  new_test_ali=tri3_ali_test_$lang
  #new_val_2_ali=tri3_ali_val_no_$lang
  #new_test_2_ali=tri3_ali_test_no_$lang

  # Do alignments
  # steps/align_fmllr.sh --nj 8  \
  #  $new_train ${exp_data_dir}/lang ${exp_dir}/tri3 ${exp_dir}/${new_tr_ali}

  # steps/align_fmllr.sh --nj 8  \
  #   $new_val ${exp_data_dir}/lang ${exp_dir}/tri3 ${exp_dir}/${new_val_ali}

  # steps/align_fmllr.sh --nj 8  \
  #   $new_test ${exp_data_dir}/lang ${exp_dir}/tri3 ${exp_dir}/${new_test_ali}

  # steps/align_fmllr.sh --nj 8  \
  #   $new_val_2 ${exp_data_dir}/lang ${exp_dir}/tri3 ${exp_dir}/${new_val_2_ali}

  # steps/align_fmllr.sh --nj 8  \
  #     $new_test_2 ${exp_data_dir}/lang ${exp_dir}/tri3 ${exp_dir}/${new_test_2_ali}

done
