#!/bin/bash -u

set -o errexit
set -o pipefail

GPDIR=/home/paul/global_phone
WAVDIR=/home/paul/gp_wav
LANGMAP=/home/paul/UPM/conf/lang_codes.txt
LANGUAGES="UA"

echo "Languages: ${LANGUAGES}"
echo "Corpus dir: ${GPDIR}"
echo "Wav dir: ${WAVDIR}"

[ -f path.sh ] && . ./path.sh  # Sets the PATH to contain necessary executables

tmpdir=$(mktemp -d /tmp/kaldi.XXXX);
trap 'rm -rf "$tmpdir"' EXIT

for L in $LANGUAGES; do
  (
  LNAME=`awk '/'$L'/ {print $2}' $LANGMAP`;
  echo "Converting $L ($LNAME) data from SHN to WAV..."

  LISTDIR=$WAVDIR/$L/lists # Directory to write file lists
  FILEDIR=$WAVDIR/$L/files # Directory to write wav files
  mkdir -p $LISTDIR $FILEDIR

  shn_dir=$GPDIR/$LNAME/adc
  shn_file_pattern="${L}*\.adc\.shn"
  if [ $L = HA ]; then
    shn_dir=$GPDIR/Hausa/Hausa/Data/adc
    shn_file_pattern="${L}*\.adc"
  elif [ $L = SA ]; then
    shn_file_pattern="${L}*\.adc"
  elif [ $L = TA ]; then
    # shn_dir=$GPDIR/$LNAME/adc
    # File names are like taXXYYYd.wav.shn, e.g. ta02013d.wav.shn,
    # where XX is speaker number and YYY is utterance number
    shn_file_pattern="ta*\.wav\.shn"
  elif [ $L = UA ]; then
    shn_file_pattern="${L}*\.adc"
  elif [ $L = WU ]; then
    shn_dir=$GPDIR/Chinese-Shanghai/Wu/adc
  fi
  echo "$shn_dir"
  echo "$shn_file_pattern"
  # echo "$LISTDIR"
  #find $shn_dir -name "$shn_file_pattern" > $LISTDIR/shn.list
  #cat $LISTDIR/shn.list

  # If one of the languages with awkward adc format
  # if [ $L = HA ] || [ $L = SA ] || [ $L = UA ]; then
  #   echo "Language contains raw adc files"
  #   ./setup/gp_convert_audio_adc.sh \
  #     --input-list=$LISTDIR/shn.list \
  #     --output-dir=$FILEDIR \
  #     --output-list=$LISTDIR/wav.list
  # else 
  #   echo "Language files formatted with shn"
  #   ./setup/gp_convert_audio.sh \
  #   --input-list=$LISTDIR/shn.list \
  #   --output-dir=$FILEDIR \
  #   --output-list=$LISTDIR/wav.list
  # fi

  if [ "$L" = "TA" ]; then
    # from ta01007d.wav.shn.wav to TA007_01.wav
    for f in $FILEDIR/*.wav; do
      spk_id=$(echo $f | sed -E 's/.*ta[0-9]{2}([0-9]{3}).*/\1/')
      utt_id=$(echo $f | sed -E 's/.*ta([0-9]{2}).*/\1/')
      # echo "$FILEDIR/TA${spk_id}_${utt_id}.wav"
      mv $f "$FILEDIR/TA${spk_id}_${utt_id}.wav"

      mv $LISTDIR/wav.list $LISTDIR/wav.list.bak
      cat $LISTDIR/wav.list.bak | sed -E 's/(.*)ta([0-9]{2})([0-9]{3})d.wav.shn.wav/\1TA\3_\2.wav/g' |\
        sort | uniq > $LISTDIR/wav.list
    done
  fi

  # Get the utterance IDs for the audio files successfully converted to WAV
  sed -e "s?.*/??" -e 's?.wav$??' $LISTDIR/wav.list > $LISTDIR/basenames_wav

  paste $LISTDIR/basenames_wav $LISTDIR/wav.list | sort -k1,1 \
    > $LISTDIR/wav.scp

  (
    while read -r name; do
      utt=$(echo $name | grep -Po '([A-Z0-9_]+)(?=.wav)')
      echo $utt $(sox $name -n stat 2>&1 | grep -Po 'seconds.:\s+\K[0-9.]+');
    done < $LISTDIR/wav.list
  ) > $LISTDIR/utt2len

  sed -e 's?_.*$??' $LISTDIR/basenames_wav \
    | paste -d' ' $LISTDIR/basenames_wav - \
    > $LISTDIR/utt2spk

  utt2spk_to_spk2utt.pl $LISTDIR/utt2spk \
    > $LISTDIR/spk2utt || exit 1;

  grep -ohE "[A-Z]+[0-9]+ " $LISTDIR/spk2utt \
    | grep -ohE "[0-9]+" | sort | uniq -u > $LISTDIR/spk

  rm $LISTDIR/basenames_wav
  ) > $LOG_DIR_GLOBAL/wav/${L}_log &
done
wait;
exit
