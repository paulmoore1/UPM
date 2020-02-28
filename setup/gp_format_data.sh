#!/bin/bash

# Copyright 2013  (Author: Daniel Povey) (adapted by Paul Moore, 2020)
# Apache 2.0

# This script takes data prepared in a corpus-dependent way
# in data/local/, and converts it into the "canonical" form,
# in various subdirectories of data/, e.g. data/lang, data/train, etc.

expname="test"

. ./path.sh || exit 1;
. ./utils/parse_options.sh


# NOTE: need to pass as argument later

exp_dir=$EXP_DIR_GLOBAL/$expname


echo "Preparing train, dev and test data"
srcdir=$exp_dir/data
lmdir=$srcdir/nist_lm
tmpdir=$exp_dir/lm_tmp
lexicon=$exp_dir/dict/lexicon.txt
mkdir -p $tmpdir

for x in train val test; do
  mkdir -p $exp_dir/data/$x
  #utils/filter_scp.pl data/$x/spk2utt $srcdir/$x.spk2gender > data/$x/spk2gender || exit 1;
  #cp $srcdir/${x}.stm data/$x/stm
  #cp $srcdir/${x}.glm data/$x/glm
  utils/fix_data_dir.sh $exp_dir/data/$x
  #utils/validate_data_dir.sh --no-feats $exp_dir/data/$x || exit 1
done

# Next, for each type of language model, create the corresponding FST
# and the corresponding lang_test_* directory.

echo "Preparing language models for test"

for lm_suffix in bg; do
  test=$exp_dir/data/lang_test_${lm_suffix}
  mkdir -p $test
  cp -r $exp_dir/data/lang/* $test

  gunzip -c $lmdir/lm_phone_${lm_suffix}.arpa.gz | \
    arpa2fst --disambig-symbol=#0 \
             --read-symbol-table=$test/words.txt - $test/G.fst
  fstisstochastic $test/G.fst
 # The output is like:
 # 9.14233e-05 -0.259833
 # we do expect the first of these 2 numbers to be close to zero (the second is
 # nonzero because the backoff weights make the states sum to >1).
 # Because of the <s> fiasco for these particular LMs, the first number is not
 # as close to zero as it could be.

 # Everything below is only for diagnostic.
 # Checking that G has no cycles with empty words on them (e.g. <s>, </s>);
 # this might cause determinization failure of CLG.
 # #0 is treated as an empty word.
  mkdir -p $tmpdir/g
  awk '{if(NF==1){ printf("0 0 %s %s\n", $1,$1); }} END{print "0 0 #0 #0"; print "0";}' \
    < "$lexicon"  >$tmpdir/g/select_empty.fst.txt
  fstcompile --isymbols=$test/words.txt --osymbols=$test/words.txt $tmpdir/g/select_empty.fst.txt | \
   fstarcsort --sort_type=olabel | fstcompose - $test/G.fst > $tmpdir/g/empty_words.fst
  fstinfo $tmpdir/g/empty_words.fst | grep cyclic | grep -w 'y' &&
    echo "Language model has cycles with empty words" && exit 1
  rm -r $tmpdir/g
done

utils/validate_lang.pl $exp_dir/data/lang_test_bg || exit 1

echo "Succeeded in formatting data."
rm -r $tmpdir
