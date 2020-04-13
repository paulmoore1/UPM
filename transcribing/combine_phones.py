import os, sys, argparse
from os.path import join, exists
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper

def get_args():
    parser = argparse.ArgumentParser(description="Combining phone sets")
    parser.add_argument("--write-dir", type=str, required=True, 
        help="Directory to write phonetic files to")
    parser.add_argument("--languages", type=str, required=True, 
        help="Languages to combine")
    return parser.parse_args()


def combine_phones(lang_codes, phone_map_dir, write_dir):
    phones_list = []
    for lang_code in lang_codes:
        phone_map = join(phone_map_dir, lang_code + "_phone_map.txt")
        with open(phone_map, "r") as f:
            lines = f.read().splitlines()
        for line in lines:
            entry = line.split()
            x_sampa_phone = entry[2]
            if x_sampa_phone not in phones_list:
                phones_list.append(x_sampa_phone)
    phones_list.sort()
    phones_list_no_sil = phones_list.copy()
    phones_list_no_sil.remove("sil")

    phones_file = join(write_dir, "phones.txt")
    silence_phones_file = join(write_dir, "silence_phones.txt")
    optional_silence_phones_file = join(write_dir, "optional_silence_phones.txt")
    non_silence_phones_file = join(write_dir, "nonsilence_phones.txt")
    extra_questions_file = join(write_dir, "extra_questions.txt")
    lexicon_file = join(write_dir, "lexicon.txt")
    lexiconp_file = join(write_dir, "lexiconp.txt")

    with open(phones_file, "w") as f:
        for phone in phones_list:
            f.write(phone + "\n")
    
    with open(silence_phones_file, "w") as f:
        f.write("sil\n")

    with open(optional_silence_phones_file, "w") as f:
        f.write("sil\n" )

    with open(non_silence_phones_file, "w") as f:
        for phone in phones_list_no_sil:
            f.write(phone + "\n")

    with open(extra_questions_file, "w") as f:
        f.write("sil\n")
        line = " ".join(phones_list_no_sil) + "\n"
        f.write(line)

    with open(lexicon_file, "w") as f:
        for phone in phones_list:
            f.write("{}\t{}\n".format(phone, phone))

    with open(lexiconp_file, "w") as f:
        for phone in phones_list:
            f.write("{}\t1.0\t{}\n".format(phone, phone))

def main():
    all_langs = os.listdir(global_vars.wav_dir)
    args = get_args()
    langs = args.languages.split()
    for lang in langs:
        if lang not in all_langs:
            print("ERROR: {} not found in languages list")
            return

    phone_map_dir = join(global_vars.conf_dir, "phone_maps")

    combine_phones(langs, phone_map_dir, args.write_dir)


if __name__ == "__main__":
    main()