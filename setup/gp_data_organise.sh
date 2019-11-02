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
Prepare train, enroll, eval and test file lists for a language.\n
e.g.: $PROG --config-dir=conf --corpus-dir=corpus --languages=\"GE PO SP\"\n\n
Required arguments:\n
  --config-dir=DIR\tDirectory containing the necessary config files\n
  --data-dir=DIR\tDirectory to copy the data to
  --wav-dir=DIR\tDirectory containing all wav files organised under language code folders
  --train-languages=STR\tSpace separated list of two letter language codes for training\n
  --val-languages=STR\tSpace separated list of two letter language codes for evaluation\n
  --test-languages=STR\tSpace separated list of two letter language codes for testing\n
";

if [ $# -ne 4 ]; then
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

# Check if the config files are in place:
pushd $CONF_DIR > /dev/null
if [ -f test_spk.list ]; then
  test_list=$CONF_DIR/test_spk.list
else
  echo "Test-set speaker list not found."; exit 1
fi
if [ -f eval_spk.list ]; then
  eval_list=$CONF_DIR/eval_spk.list
else
  echo "Eval-set speaker list not found."; exit 1
fi
if [ -f train_spk.list ]; then
  train_list=$CONF_DIR/train_spk.list
fi
popd > /dev/null