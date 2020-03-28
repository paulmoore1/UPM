import os, sys, argparse, shutil, glob
from os.path import join, exists, isdir, basename, dirname
sys.path.insert(1, '/home/paul/UPM')
import global_vars
from py_helper_functions import listdir_fullpath


def get_args():
    parser = argparse.ArgumentParser(description="Organising data sets")
    parser.add_argument('--data-dir', type=str, required=True,
        help="Directory to output data files")
    parser.add_argument('--ali-dir', type=str, required=True,
        help="Alignment directory folder")
    return parser.parse_args()

def get_unique_utts(ctm_filepath):
    utts = set()
    with open(ctm_filepath, "r") as f:
        for line in f:
            utt = line.split()[0]
            utts.add(utt)
    return utts

def utts_to_utt2spk(all_utts):
    for idx, utt in enumerate(all_utts):
        speaker = utt.split("_")[0]
        all_utts[idx] = utt + " " + speaker
    return all_utts

def main():
    args = get_args()
    print("Filtering valid alignments in {}, writing to {}".format(args.ali_dir, args.data_dir))
    all_utts = set()
    ctm_files = glob.glob(join(args.ali_dir, "*.ctm"))
    for ctm_file in ctm_files:
        utts = get_unique_utts(ctm_file)
        all_utts = all_utts.union(all_utts, utts)

    all_utts = list(all_utts)
    all_utts.sort()

    all_utts = utts_to_utt2spk(all_utts)

    with open(join(args.data_dir, "utt2spk"), "w") as f:
        for utt in all_utts:
            f.write(utt + "\n")


if __name__ == "__main__":
    main()