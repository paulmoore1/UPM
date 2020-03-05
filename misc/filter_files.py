import os, sys, argparse, shutil
from os.path import join, basename
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper

def get_args():
    parser = argparse.ArgumentParser(description="Filtering files based on transcripts")
    parser.add_argument('--list-dir', type=str, required=True,
        help="Directory of all list files")
    return parser.parse_args()


def get_tr_ids(transcript_filepath):
    ids = set()
    with open(transcript_filepath, "r") as f:
        lines = f.read().splitlines()
    for line in lines:
        tr_id = line.split()[0]
        ids.add(tr_id)
    return ids

def write_and_filter(original_filepath, id_list, write_filepath):
    with open(original_filepath, "r") as f:
        lines = f.readlines()
    write_lines = []
    for line in lines:
        line_id = line.split()[0]
        # Then check if the speaker matches
        if line_id in id_list:
            write_lines.append(line)
    
    with open(write_filepath, "w") as f:
        for line in write_lines:
            f.write(line)

def filter_all_files(list_dir, lang_code):
    transcripts_file = join(global_vars.all_tr_dir, lang_code + "_X-SAMPA_tr.txt")
    tr_ids = get_tr_ids(transcripts_file)

    feat_filetypes = ["wav.scp", "utt2spk", "utt2len", "feats.scp"]
    feat_filepaths = [join(list_dir, x)  for x in feat_filetypes]
    write_filepaths = [join(list_dir, x) for x in feat_filetypes]

    for idx, filepath in enumerate(feat_filepaths):
        write_and_filter(filepath, tr_ids, write_filepaths[idx])

def main():
    args = get_args()

    lang_code = args.list_dir.split('/')[-2]
    
    backup_dir = join(args.list_dir, "backup")
    if not os.path.exists(backup_dir):
        shutil.copytree(args.list_dir, backup_dir)
        shutil.rmtree(join(args.list_dir, "original"))

    #filter_all_files(args.list_dir, lang_code)

    transcripts_file = join(global_vars.all_tr_dir, lang_code + "_X-SAMPA_tr.txt")
    if os.path.exists(transcripts_file):
        shutil.copy2(transcripts_file, join(args.list_dir, "text"))

if __name__ == "__main__":
    main()