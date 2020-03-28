import os, sys, argparse, shutil
from os.path import join, exists, isdir, basename, dirname
sys.path.insert(1, '/home/paul/UPM')
import global_vars
from py_helper_functions import listdir_fullpath


def get_args():
    parser = argparse.ArgumentParser(description="Organising data sets")
    parser.add_argument('--data-dir', type=str, required=True,
        help="Directory to output data files")
    parser.add_argument('--conf-dir', type=str, required=True,
        help="Directory of all configuration files")
    parser.add_argument('--train-languages', type=str, required=True,
        help="Which languages to use when training. Should be space-separated language codes")
    parser.add_argument('--val-languages', type=str, required=True,
        help="Which languages to use when training. Should be space-separated language codes")
    parser.add_argument('--test-languages', type=str, required=True,
        help="Which languages to use when training. Should be space-separated language codes")
    parser.add_argument('--feat-type', type=str, choices=["fbank", "mfcc"], default="mfcc")

    return parser.parse_args()


def read_spk_list(spk_filepath, lang):
    with open(spk_filepath, "r") as f:
        lines = f.read().splitlines()
    for line in lines:
        # Find list for that language
        if line.startswith(lang):
            # Return all speakers in the list
            return [lang + x for x in line.split()[1:]]
    # If no line found for the language
    raise AssertionError("No entry found in {} for {}".format(spk_filepath, lang))


def create_new_dir(set_dir, delete=True):
    # If directory is found, delete all content in it
    if isdir(set_dir):
        if delete:
            shutil.rmtree(set_dir)
        else:
            print("Blah")
    else:        
        os.makedirs(set_dir)


# Combine files for each train/val/test set for each language
# Writes to exp_data_dir/[train]
def combine_files(lang_codes, dataset, exp_data_dir, bad_tr, feat_type):
    assert dataset in ["train", "val", "test"], "ERROR: Dataset should be one of \"train\", \"val\" or \"test\""
    data_dir = global_vars.gp_data_dir

    write_dir = join(exp_data_dir, dataset)
    if not isdir(write_dir):
        os.makedirs(write_dir)
    
    # Gets transcription files
    for idx, lang_code in enumerate(lang_codes):
        if idx == 0:
            write_new = True
        else:
            write_new = False

        # Get list of speakers for filtering transcript
        spk_list = join(global_vars.conf_dir, "spk_lists", "{}_spk.list".format(dataset))
        assert exists(spk_list), "ERROR: Speaker list not found in {}".format(spk_list)

        speakers = read_spk_list(spk_list, lang_code)

        feat_filetypes = ["wav.scp", "spk2utt", "utt2spk", "utt2len", "feats_{}.scp".format(feat_type), "text"]
        feat_filepaths = [join(data_dir, lang_code, "lists", x)  for x in feat_filetypes]

        for read_filepath in feat_filepaths:
            if "feats" in read_filepath:
                filename = basename(read_filepath)
                filename = filename.replace("_{}".format(feat_type), "")
                write_filepath = join(write_dir, filename)
            else:
                write_filepath = join(write_dir, basename(read_filepath))
            # Write and filter the files
            write_and_filter(read_filepath, speakers, write_filepath, write_new, bad_tr)



def write_and_filter(original_filepath, spk_list, write_filepath, write_new, bad_tr):
    with open(original_filepath, "r") as f:
        lines = f.readlines()
    write_lines = []
    for line in lines:
        speaker = line[0:5]
        if basename(original_filepath) == "text":
            line = " ".join(line.split()) + "\n" # Ensure that there is only single spacing

        # If the file is not spk2utt, check the transcription id
        if "spk2utt" not in original_filepath:
            tr_id = line.split()[0]
            # Skip any bad transcriptions
            if tr_id in bad_tr:
                continue
        # Then check if the speaker matches
        if speaker in spk_list:
            write_lines.append(line)

    # If writing new file
    if write_new == True:
        with open(write_filepath, "w") as f:
            for line in write_lines:
                f.write(line)
    else:
        with open(write_filepath, "a") as f:
            for line in write_lines:
                f.write(line)

def get_blacklisted_transcriptions():
    blacklist_file = join(global_vars.conf_dir, "blacklisted_transcriptions.txt")
    transcriptions = []
    with open(blacklist_file, "r") as f:
        for line in f:
            entry = line.split()
            speaker = entry[0]
            transcriptions.append(speaker)
    return transcriptions

def main():
    bad_tr = get_blacklisted_transcriptions()

    args = get_args()

    data_splits = ["train", "val", "test"]

    data_dir = args.data_dir

    if not isdir(data_dir):
        os.makedirs(data_dir)
        for x in data_splits:
            os.makedirs(join(data_dir, x))


    for dataset in data_splits:
        if dataset == "train":
            langs = args.train_languages.split()
        elif dataset == "val":
            langs = args.val_languages.split()
        else:
            langs = args.test_languages.split()
        
        combine_files(langs, dataset, data_dir, bad_tr, args.feat_type)


if __name__ == "__main__":
    main()