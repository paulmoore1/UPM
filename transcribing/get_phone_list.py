import os, sys, glob
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import py_helper_functions as helper
import global_vars
import re
from os.path import join, exists

def get_all_phones(dict_file, lang_code):
    with open(dict_file, "r") as f:
        lines = f.read().splitlines()
    phone_list = []
    exceptions = ["PO", "PL", "FR", "BG"]
    if lang_code not in exceptions:
        for idx, line in enumerate(lines):
            if lang_code != "KO":
                # Splits on first occurrence of "} {" which is the dict split
                entry = line.split("} {", 1)
            else:
                entry = line.split("}\t{")
            #print(entry)
            word_phones = entry[1]
            # Sanity check - should end with double curly braces if it's the whole word
            if not word_phones.endswith("}}"):
                print("Error occured at line {} with word {}".format(idx, word_phones))
            # Remove curly braces, WB from string
            word_phones = word_phones.replace("{", "")
            word_phones = word_phones.replace("}", "")
            word_phones = word_phones.replace("WB", "")
            phone_list = update_phone_list(word_phones, phone_list)
            # if idx > 4 and idx < 10:
            #     print(word_phone_list)
    elif lang_code in ["PO", "FR"]:
        # Words are separated by tabs
        for idx, line in enumerate(lines):
            entry = line.split("\t")
            word_phones = entry[1]
            phone_list = update_phone_list(word_phones, phone_list)
    
    elif lang_code in ["PL", "BG"]:
        # Words are separated by tabs, but separated by curly braces
        for idx, line in enumerate(lines):
            if lang_code != "BG":
                entry = line.split("\t")
            else:
                entry = line.split(" ", 1)
            word_phones = entry[1]
            word_phones = word_phones.replace("{", "")
            word_phones = word_phones.replace("}", "")
            word_phones = word_phones.replace("WB", "")
            phone_list = update_phone_list(word_phones, phone_list)
            
    phone_list.sort(key = lambda v: v.upper())
    # Put the SIL token first if it exists
    if "SIL" in phone_list:
        phone_list.remove("SIL")
        phone_list.insert(0, "SIL")
    return phone_list

def update_phone_list(word_phones, phone_list):
    word_phone_list = word_phones.split()
    for phone in word_phone_list:
        if phone not in phone_list:
            phone_list.append(phone)
    return phone_list

def main():
    lang_code = "CR"
    dict_dir = join(global_vars.wav_dir, lang_code, "dict")
    files = glob.glob(join(dict_dir, "*GPDict.txt"))
    assert len(files) == 1, "Multiple/no matches found in {}".format(dict_dir)
    dict_file = files[0]
    print("Reading from : {}".format(dict_file))
    phone_list = get_all_phones(dict_file, lang_code)
    print("Phone list: ")
    for phone in phone_list:
        print(phone)

if __name__ == '__main__':
    main()
