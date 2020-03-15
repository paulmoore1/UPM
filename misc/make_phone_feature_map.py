import os, argparse, sys
from operator import itemgetter
import numpy as np

from os.path import join, basename, exists, dirname
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper

def get_args():
    parser = argparse.ArgumentParser(description="Making phone feature vector map")
    parser.add_argument('--phones-filepath', type=str, required=True,
        help="Filepath to phones.txt. Where the map file will be written")
    parser.add_argument('--feat-type', type=str, default="all", choices=["all", \
        "vc", "place", "manner", "backness", "height"],
        help="Feature type")
    return parser.parse_args()

def read_phones(phone_filepath):
    int_to_phone = {}
    with open(phone_filepath, "r") as f:
        lines = f.read().splitlines()
    for line in lines:
        entry = line.split()
        phone = entry[0]
        phone_int = entry[1]
        int_to_phone[phone_int] = phone
    return int_to_phone

def convert_phones_to_feats(int_to_phone, feat, feature_vector_filepath, write_path):
    with open(feature_vector_filepath, "r") as f:
        lines = f.read().splitlines()
    phone_to_feat = {}
    for idx, line in enumerate(lines):
        row = line.split()
        # First line is phone feat1 feat2 ...
        if idx == 0:
            header = row[1:]
        else: # Other lines are phone 1 0 0 1 ...
            phone = row[0]
            # Either take all the rows, or only ones at the appropriate index
            if feat == "all":
                feat_vec = row[1:]
            else:
                all_feats = row[1:]
                selected_feats = feat_to_cols(feat)
                col_idx = [header.index(feature) for feature in selected_feats]
                feat_vec = itemgetter(*col_idx)(all_feats)
                feat_vec = np.asarray([int(x) for x in feat_vec])
            # Used for adding unknown phones
            feat_length = len(feat_vec)
            phone_to_feat[phone] = feat_vec

    with open(write_path, "w") as f:
        print("IMPORTANT: inverting feature vectors right now")

        for i in range(len(int_to_phone)):
            write_line = [i]
            phone = int_to_phone[str(i)]
            if phone in phone_to_feat:
                feat_vec = phone_to_feat[phone]
                # TODO remove later


                feat_vec = 1 - feat_vec

            else: # Some phones like <eps> won't be in
                print("Phone not found: {}, setting to 1 (need to change)".format(phone))
                feat_vec = [1]*feat_length

            write_line += list(feat_vec)

            write_line = [str(x) for x in write_line]
            f.write(",".join(write_line) + "\n")
        print("Phones have {} features".format(feat_length))

def main():
    args = get_args()
    feat = args.feat_type
    feature_vector_filepath = join(global_vars.conf_dir, "articulatory_features",
                                    "feature_vectors.txt")
    if not exists(feature_vector_filepath):
        print("ERROR: feature vector file not found at {}".format(feature_vector_filepath))
        return

    if basename(args.phones_filepath) != "phones.txt":
        print("ERROR: filepath should end with \"phones.txt\"")
        return
    if not exists(args.phones_filepath):
        print("ERROR: phones.txt not found at {}".format(args.phones_filepath))
        return
    else:
        int_to_phone = read_phones(args.phones_filepath)

    write_path = join(dirname(args.phones_filepath), "phone_featmap.txt")

    convert_phones_to_feats(int_to_phone, feat, feature_vector_filepath, write_path)

# Values for appropriate columns depending on feature type (if not taking all)
def feat_to_cols(feat):
    if feat == "vc":
        return ["vowel", "consonant"]
    elif feat == "place":
        return ["alveolar", "alveolo-palatal", "bilabial", "coronal", "dental",
                "dorsal", "epiglottal", "glottal", "labial", "labial-palatal",
                "labial-velar", "labiodental", "lateral" "palatal", "palatal-velar",
                "pharyngeal", "postalveolar", "uvular", "velar"]
    elif feat == "manner":
        return ["nasal", "stop", "affricate", "approximant", "trill", "flap", "fricative"]
    elif feat == "backness":
        return ["front", "near-front", "central", "near-back", "back"]
    elif feat == "height":
        return ["close", "near-close", "close-mid", "mid", "open-mid", "near-open", "open"]
    else:
        print("Unknown feature type: {}".format(feat))
        raise Exception

if __name__ == "__main__":
    main()
