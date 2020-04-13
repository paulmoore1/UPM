import os, epitran, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from os.path import join, exists
import global_vars
import py_helper_functions as helper

def get_transcript_files(language_code):
    lang_dir = join(global_vars.wav_dir, language_code)
    assert exists(lang_dir), lang_dir + " not found!"
    # First check if there is a "rmn" folder containing romanised transcripts
    if "rmn" in os.listdir(lang_dir):
        tr_dir = join(lang_dir, "rmn")
    # If not, use the "trl" folder which has special characters
    else:
        tr_dir = join(lang_dir, "trl")
    assert exists(tr_dir), tr_dir + " not found!"

    # Find dictionary directory, check exists
    dict_dir = join(lang_dir, "dict")
    assert exists(dict_dir), dict_dir + " not found!"
    # Find dictionary file (may be .dict or .txt)
    dict_files = [x for x in os.listdir(dict_dir) if x.endswith(".dict") or x.endswith(".txt")]
    if len(dict_files) > 1:
        print("WARNING: multiple dictionary files found: " + dict_files)
    dict_file = join(dict_dir, dict_files[0])

    return helper.listdir_fullpath(tr_dir), dict_file


def main():
    language_code = "HA"
    tr_files, dict_file = get_transcript_files(language_code)
    epi_dict = helper.read_epitran_codes()
    epi_code = epi_dict[language_code]
    assert epi_code != "None", "Language cannot be used with Epitran"
    if language_code in ["AR", "FR", "PO"]:
        print("WARNING: epitran quite inaccurate for " + language_code)


if __name__ == "__main__":
    main()