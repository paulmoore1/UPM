#!/bin/bash -u

# Copyright 2012  Arnab Ghoshal, adapated by Paul Moore 2019

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
# WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
# MERCHANTABLITY OR NON-INFRINGEMENT.
# See the Apache 2 License for the specific language governing permissions and
# limitations under the License.

set -o errexit

function error_exit () {
  echo -e "$@" >&2; exit 1;
}

function read_dirname () {
  local dir_name=`expr "X$1" : '[^=]*=\(.*\)'`;
  [ -d "$dir_name" ] || mkdir -p "$dir_name" || error_exit "Directory '$dir_name' not found";
  local retval=`cd $dir_name 2>/dev/null && pwd || exit 1`
  echo $retval
}

PROG=`basename $0`;
usage="Usage: $PROG <arguments>\n
Prepare train, enroll, val and test file lists for a language.\n
e.g.: $PROG --config-dir=conf --corpus-dir=corpus --languages=\"GE PO SP\"\n\n
Required arguments:\n
  --config-dir=DIR\tDirectory containing the necessary config files\n
  --data-dir=DIR\tDirectory to copy the data to
  --wav-dir=DIR\tDirectory containing all wav files organised under language code folders
  --train-languages=STR\tSpace separated list of two letter language codes for training\n
  --val-languages=STR\tSpace separated list of two letter language codes for validation\n
  --test-languages=STR\tSpace separated list of two letter language codes for testing\n
";

if [ $# -ne 6 ]; then
  error_exit $usage;
fi

while [ $# -gt 0 ];
do
  case "$1" in
  --help) echo -e $usage; exit 0 ;;
  --config-dir=*)
  CONF_DIR=`read_dirname $1`; shift ;;
  --train-languages=*)
  TRAIN_LANGUAGES=`expr "X$1" : '[^=]*=\(.*\)'`; shift ;;
  --val-languages=*)
  VAL_LANGUAGES=`expr "X$1" : '[^=]*=\(.*\)'`; shift ;;
  --test-languages=*)
  TEST_LANGUAGES=`expr "X$1" : '[^=]*=\(.*\)'`; shift ;;
  --data-dir=*)
  DATA_DIR=`read_dirname $1`; shift ;;
  --wav-dir=*)
  WAV_DIR=`read_dirname $1`; shift ;;
  *)  echo "Unknown argument: $1, exiting"; echo -e $usage; exit 1 ;;
  esac
done

CONF_DIR=$CONF_DIR/spk_lists

# Check if the config files are in place:
pushd $CONF_DIR > /dev/null
if [ -f test_spk.list ]; then
  test_list=$CONF_DIR/test_spk.list
else
  echo "Test-set speaker list not found."; exit 1
fi
if [ -f val_spk.list ]; then
  val_list=$CONF_DIR/val_spk.list
else
  echo "Validation-set speaker list not found."; exit 1
fi
if [ -f train_spk.list ]; then
  train_list=$CONF_DIR/train_spk.list
fi
popd > /dev/null

[ -f path.sh ] && . ./path.sh  # Sets the PATH to contain necessary executables

# Make data folders to contain all the language files.
for x in train val test; do
  mkdir -p $DATA_DIR/${x}
done

tmpdir=$(mktemp -d /tmp/kaldi.XXXX);
trap 'rm -rf "$tmpdir"' EXIT

#testtmpdir=$DATA_DIR/testing
#mkdir -p $testtmpdir

# Create directories to contain files needed in training and testing:
echo "DATA_DIR is: $DATA_DIR"
echo "WAV_DIR is: $WAV_DIR"
for L in $TRAIN_LANGUAGES; do
  (
  mkdir -p $tmpdir/train/$L
  if [ -f $CONF_DIR/train_spk.list ]; then
    grep "^$L" $train_list | cut -f2- | tr ' ' '\n' \
      | sed -e "s?^?$L?" -e 's?$?_?' > $tmpdir/train/$L/train_spk
  else
    echo "Train-set speaker list not found. Skipping."
    #grep -v -f $tmpdir/$L/test_spk -f $tmpdir/$L/eval_spk -f $tmpdir/$L/enroll_spk \
    #  $WAVDIR/$L/lists/spk > $tmpdir/$L/train_spk || \
    #  echo "Could not find any training set speakers; \
    #  are you trying to use all of them for evaluation and testing?";
    continue
  fi

  echo "Language - ${L}: formatting train data."
  mkdir -p $DATA_DIR/$L/train
  rm -f $DATA_DIR/$L/train/wav.scp $DATA_DIR/$L/train/spk2utt \
        $DATA_DIR/$L/train/utt2spk $DATA_DIR/$L/train/utt2len

  for spk in `cat $tmpdir/train/$L/train_spk`; do
    grep -h "$spk" $WAV_DIR/$L/lists/wav.scp >> $DATA_DIR/$L/train/wav.scp
    grep -h "$spk" $WAV_DIR/$L/lists/spk2utt >> $DATA_DIR/$L/train/spk2utt
    grep -h "$spk" $WAV_DIR/$L/lists/utt2spk >> $DATA_DIR/$L/train/utt2spk
    grep -h "$spk" $WAV_DIR/$L/lists/utt2len >> $DATA_DIR/$L/train/utt2len
  done
  ) &
done
wait;
echo "Done"

for L in $VAL_LANGUAGES; do
  (
  mkdir -p $tmpdir/val/$L
  grep "^$L" $val_list | cut -f2- | tr ' ' '\n' \
    | sed -e "s?^?$L?" -e 's?$?_?' > $tmpdir/val/$L/val_spk

  echo "Language - ${L}: formatting val data."
  mkdir -p $DATA_DIR/$L/val
  rm -f $DATA_DIR/$L/val/wav.scp $DATA_DIR/$L/val/spk2utt \
        $DATA_DIR/$L/val/utt2spk $DATA_DIR/$L/val/utt2len

  for spk in `cat $tmpdir/val/$L/val_spk`; do
    grep -h "$spk" $WAV_DIR/$L/lists/wav.scp >> $DATA_DIR/$L/val/wav.scp
    grep -h "$spk" $WAV_DIR/$L/lists/spk2utt >> $DATA_DIR/$L/val/spk2utt
    grep -h "$spk" $WAV_DIR/$L/lists/utt2spk >> $DATA_DIR/$L/val/utt2spk
    grep -h "$spk" $WAV_DIR/$L/lists/utt2len >> $DATA_DIR/$L/val/utt2len
  done
  ) &
done
wait;
echo "Done"
for L in $TEST_LANGUAGES; do
  (
  mkdir -p $tmpdir/test/$L
  grep "^$L" $test_list | cut -f2- | tr ' ' '\n' \
    | sed -e "s?^?$L?" -e 's?$?_?' > $tmpdir/test/$L/test_spk

  echo "Language - ${L}: formatting test data."
  mkdir -p $DATA_DIR/$L/test
  rm -f $DATA_DIR/$L/test/wav.scp $DATA_DIR/$L/test/spk2utt \
        $DATA_DIR/$L/test/utt2spk $DATA_DIR/$L/test/utt2len
 
  for spk in `cat $tmpdir/test/$L/test_spk`; do
    grep -h "$spk" $WAV_DIR/$L/lists/wav.scp >> $DATA_DIR/$L/test/wav.scp
    grep -h "$spk" $WAV_DIR/$L/lists/spk2utt >> $DATA_DIR/$L/test/spk2utt
    grep -h "$spk" $WAV_DIR/$L/lists/utt2spk >> $DATA_DIR/$L/test/utt2spk
    grep -h "$spk" $WAV_DIR/$L/lists/utt2len >> $DATA_DIR/$L/test/utt2len
  done
  ) &
done
wait;
echo "Done"

# Combine data from all languages into big piles
train_dirs=()
val_dirs=()
test_dirs=()

for L in $TRAIN_LANGUAGES; do
  train_dirs+=($DATA_DIR/$L/train)
done
for L in $VAL_LANGUAGES; do
  val_dirs+=($DATA_DIR/$L/val)
done
for L in $TEST_LANGUAGES; do
  test_dirs+=($DATA_DIR/$L/test)
done


echo "Combining training directories: $(echo ${train_dirs[@]} | sed -e "s|${DATA_DIR}||g")"
utils/combine_data.sh --extra-files 'utt2len' $DATA_DIR/train ${train_dirs[@]}

echo "Combining validation directories: $(echo ${val_dirs[@]} | sed -e "s|${DATA_DIR}||g")"
utils/combine_data.sh --extra-files 'utt2len' $DATA_DIR/val ${val_dirs[@]}

echo "Combining testing directories: $(echo ${test_dirs[@]} | sed -e "s|${DATA_DIR}||g")"
utils/combine_data.sh --extra-files 'utt2len' $DATA_DIR/test ${test_dirs[@]}

echo "Finished data preparation."
