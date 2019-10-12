#!/bin/bash

source ~/.bashrc

KALDI_ROOT=/home/paul/kaldi
KALDI_SRC=$KALDI_ROOT/src
KALDI_BIN=$KALDI_SRC/bin:$KALDI_SRC/featbin:$KALDI_SRC/fgmmbin:$KALDI_SRC/fstbin
KALDI_BIN=$KALDI_BIN$:$KALDI_SRC/gmmbin:$KALDI_SRC/latbin:$KALDI_SRC/nnetbin
export LC_ALL=C  # For expected sorting and joining behaviour

[ -d $PWD/local ] || { echo "Error: 'local' subdirectory not found."; }
[ -d $PWD/utils ] || { echo "Error: 'utils' subdirectory not found."; }
[ -d $PWD/steps ] || { echo "Error: 'steps' subdirectory not found."; }

export kaldi_local=$PWD/local
export kaldi_utils=$PWD/utils
export kaldi_steps=$PWD/steps

SCRIPTS=$kaldi_local:$kaldi_utils:$kaldi_steps
export PATH=$PATH:$SCRIPTS

SHORTEN_BIN=/home/paul/UPM/tools/shorten-3.6.1/bin
SOX_BIN=/usr/local/bin/sox

export PATH=$SHORTEN_BIN:$SOX_BIN:$PATH

export LOG_DIR=/home/paul/UPM/logs
export CONF_DIR=/home/paul/UPM/conf