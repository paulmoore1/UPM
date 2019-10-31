import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import py_helper_functions as helper
import global_vars
import re
from os.path import join, exists

def get_all_phones(dict_file):
    with open(dict_file, "r") as f:
        lines = f.read().splitlines()
    phone_list = []
    for idx, line in enumerate(lines):
        # Splits on first occurrence of "} {" which is the dict split
        entry = line.split("} {", 1)
        word_phones = entry[1]
        # Sanity check - should end with double curly braces if it's the whole word
        if not word_phones.endswith("}}"):
            print("Error occured at line {} with word {}".format(idx, word_phones))
        # Remove curly braces, WB from string
        word_phones = word_phones.replace("{", "")
        word_phones = word_phones.replace("}", "")
        word_phones = word_phones.replace("WB", "")
        word_phone_list = word_phones.split()
        for phone in word_phone_list:
            if phone not in phone_list:
                phone_list.append(phone)
        # if idx > 4 and idx < 10:
        #     print(word_phone_list)
    phone_list.sort(key = lambda v: v.upper())
    return phone_list

def main():
    # Temp hard coded directory
    dict_dir = join(global_vars.wav_dir, "SA", "dict")
    assert exists(dict_dir), "Dictonary directory not found in " + dict_dir
    dict_file = join(dict_dir, "Swahili-GPDict.txt")
    phone_list = get_all_phones(dict_file)
    print("Phone list: ")
    for phone in phone_list:
        print(phone)

if __name__ == '__main__':
    main()
