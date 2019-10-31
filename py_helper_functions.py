import os
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



