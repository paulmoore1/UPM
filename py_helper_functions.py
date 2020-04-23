import os, sys, argparse, csv
from os.path import join, exists
import global_vars

""""
File containing various python functions which are commonly used
"""
def listdir_fullpath(d):
    return [join(d, f) for f in os.listdir(d)]

# Create 1:1 dict mapping e.g. dict[AR] = Arabic, dict[Arabic] = AR
def read_lang_codes():
    lang_dict = {}
    all_langs = []
    file_path = join(global_vars.conf_dir, "lang_codes.txt")
    assert exists(file_path), "Could not find lang_codes.txt under " + global_vars.conf_dir
    with open(file_path, "r") as f:
        lines = f.read().splitlines()
    for line in lines:
        entry = line.split()
        lang_code = entry[0]
        lang_word = entry[1]
        lang_dict[lang_code] = lang_word
        lang_dict[lang_word] = lang_code
        all_langs.append(lang_word)
    return lang_dict, all_langs

# Get dictionary mapping from lang code to epitran-code
# e.g. dict[HA] = "hau-Latn"
def read_epitran_codes():
    file_path = join(global_vars.conf_dir, "epitran_codes.txt")
    assert exists(file_path), "Could not find epitran_codes.txt under " + global_vars.conf_dir
    with open(file_path, "r") as f:
        lines = f.read().splitlines()
    epi_dict = {}
    for line in lines:
        entry = line.split()
        lang_code = entry[0]
        epitran_code = entry[1]
        epi_dict[lang_code] = epitran_code
    return epi_dict


def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def write_to_csv(filename, header, data, save_dir=None, overwrite=False):
    if save_dir is None:
        save_dir = os.getcwd()
    if ".csv" in filename:
        save_path = join(save_dir, filename)
    else:
        save_path = join(save_dir, filename + ".csv")
        
    # Sanity check on data
    for idx, row in enumerate(data):
        assert len(row) == len(header), "ERROR: mismatch between length of data ({}) and length of header ({})\n \
                                        This occurs at row {} containing: {}".format(len(row), len(header), idx, str(row))
    
    if exists(save_path) and overwrite == False:
        print("File exists already. Set overwrite=True to replace it")
    else:
        print("Writing to {}".format(save_path))
        with open(save_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)
    


