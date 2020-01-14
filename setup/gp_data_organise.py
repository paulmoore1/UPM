import os, sys, argparse, shutil
from os.path import join, exists, isdir, basename, dirname
sys.path.insert(1, '/home/paul/UPM')
import global_vars
from py_helper_functions import listdir_fullpath


def get_args():
    parser = argparse.ArgumentParser(description="Organising data sets")
    parser.add_argument('--wav-dir', type=str, required=True,
        help="Directory of all WAV files")
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

def filter_file_lines(speakers, read_filepath, write_filepath):
    with open(read_filepath, "r") as f:
        read_lines = f.readlines()
    write_lines = []
    for line in read_lines:
        # First 5 characters will be speaker 
        if line[0:5] in speakers:
            write_lines.append(line)

    with open(write_filepath, "w") as f:
        for line in write_lines:
            f.write(line)


def split_lang_codes(lang_codes_str):
    pass

def main():
    args = get_args()

    data_splits = ["train", "val", "test"]

    data_dir = args.data_dir
    wav_dir = args.wav_dir
    assert isdir(wav_dir), "WAV directory not found in {}".format(wav_dir)

    if not isdir(data_dir):
        os.makedirs(data_dir)
        for x in data_splits:
            os.makedirs(join(data_dir, x))


    conf_dir = join(args.conf_dir, "spk_lists")

    for dataset in data_splits:
        if dataset == "train":
            langs = args.train_languages.split()
        elif dataset == "val":
            langs = args.val_languages.split()
        else:
            langs = args.test_languages.split()
        spk_filepath = join(conf_dir, dataset + "_spk.list")
        
        for lang in langs:

            # General directories to read/write to
            read_dir = join(wav_dir, lang, "lists")
            write_dir = join(data_dir, lang, dataset)

            speakers = read_spk_list(spk_filepath, lang)

            if not isdir(write_dir):
                os.makedirs(join(data_dir, lang, dataset))
            for filetype in ["wav.scp", "spk2utt", "utt2spk", "utt2len"]:
                read_path = join(read_dir, filetype)
                write_path = join(write_dir, filetype)
                filter_file_lines(speakers, read_path, write_path)



if __name__ == "__main__":
    main()