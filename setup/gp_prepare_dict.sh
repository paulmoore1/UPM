#!/bin/bash

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
  --src-dir=DIR\tDirecory containing the data files e.g. ../data/local\n
";

if [ $# -ne 1 ]; then
  error_exit $usage;
fi

while [ $# -gt 0 ];
do
  case "$1" in
  --help) echo -e $usage; exit 0 ;;
  --src-dir=*)
  srcdir=`read_dirname $1`; shift ;;
  *)  echo "Unknown argument: $1, exiting"; echo -e $usage; exit 1 ;;
  esac
done

data_dir=$srcdir/data
dict_dir=$srcdir/dict
lm_dir=$srcdir/nist_lm
tmp_dir=$srcdir/lm_tmp

mkdir -p $dict_dir $lm_dir $tmp_dir

[ -f path.sh ] && . ./path.sh

#(1) Dictionary preparation:

# Make phones symbol-table (adding in silence and verbal and non-verbal noises at this point).
# We are adding suffixes _B, _E, _S for beginning, ending, and singleton phones.

# silence phones, one per line.
echo sil > $dict_dir/silence_phones.txt
echo sil > $dict_dir/optional_silence.txt

# nonsilence phones; on each line is a list of phones that correspond
# really to the same base phone.

# Create the lexicon, which is just an identity mapping
cut -d' ' -f2- $data_dir/train.text | tr ' ' '\n' | sort -u > $dict_dir/phones.txt
paste $dict_dir/phones.txt $dict_dir/phones.txt > $dict_dir/lexicon.txt || exit 1;
grep -v -F -f $dict_dir/silence_phones.txt $dict_dir/phones.txt > $dict_dir/nonsilence_phones.txt 

# A few extra questions that will be added to those obtained by automatically clustering
# the "real" phones.  These ask about stress; there's also one for silence.
cat $dict_dir/silence_phones.txt| awk '{printf("%s ", $1);} END{printf "\n";}' > $dict_dir/extra_questions.txt || exit 1;
cat $dict_dir/nonsilence_phones.txt | perl -e 'while(<>){ foreach $p (split(" ", $_)) {
  $p =~ m:^([^\d]+)(\d*)$: || die "Bad phone $_"; $q{$2} .= "$p "; } } foreach $l (values %q) {print "$l\n";}' \
 >> $dict_dir/extra_questions.txt || exit 1;

# (2) Create the phone bigram LM
if [ -z $IRSTLM ] ; then
  export IRSTLM=$KALDI_ROOT/tools/irstlm/
fi
export PATH=${PATH}:$IRSTLM/bin
if ! command -v prune-lm >/dev/null 2>&1 ; then
  echo "$0: Error: the IRSTLM is not available or compiled" >&2
  echo "$0: Error: We used to install it by default, but." >&2
  echo "$0: Error: this is no longer the case." >&2
  echo "$0: Error: To install it, go to $KALDI_ROOT/tools" >&2
  echo "$0: Error: and run extras/install_irstlm.sh" >&2
  exit 1
fi

cut -d' ' -f2- $data_dir/train.text | sed -e 's:^:<s> :' -e 's:$: </s>:' \
  > $data_dir/lm_train.text

build-lm.sh -i $data_dir/lm_train.text -n 2 \
  -o $tmp_dir/lm_phone_bg.ilm.gz

compile-lm $tmp_dir/lm_phone_bg.ilm.gz -t=yes /dev/stdout | \
grep -v unk | gzip -c > $lm_dir/lm_phone_bg.arpa.gz 

echo "Dictionary & language model preparation succeeded"
