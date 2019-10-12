import os
from os.path import join, exists, basename
import sys
sys.path.insert(1, '/home/paul/UPM')
import global_vars

def listdir_fullpath(d):
    return [join(d, f) for f in os.listdir(d)]


def read_lang_codes(conf_dir):
    lang_dict = {}
    all_langs = []
    file_path = join(conf_dir, "lang_codes.txt")
    assert exists(file_path), "Could not find lang_codes.txt under " + conf_dir
    with open(file_path, "r") as f:
        lines = f.read().splitlines()
    for line in lines:
        entry = line.split()
        lang_code = entry[0]
        lang_word = entry[1]
        # Create 1:1 dict mapping e.g. dict[AR] = Arabic, dict[Arabic] = AR
        lang_dict[lang_code] = lang_word
        lang_dict[lang_word] = lang_code
        all_langs.append(lang_word)
    return lang_dict, all_langs


# Gets all speaker files in the path
def get_speaker_files(gp_path, lang):
    if lang == "Tamil":
        return listdir_fullpath(gp_path)
    else:
        speaker_files = []
        for speaker in os.listdir(gp_path):
            spk_path = join(gp_path, speaker)
            for spk_file in os.listdir(spk_path):
                speaker_files.append(join(spk_path, spk_file))
        return speaker_files


# Removes any files in the speaker file list if they exist in the wav file list
def compare_and_remove_file_lists(speaker_files, wav_files, lang):
    if len(wav_files) == 0:
        print("No wav files found for " + lang)
        return
    for spk_file in speaker_files:
        spk_id = basename(spk_file).split(".")[0]
        wav_id = spk_id + ".wav"
        # If file exists, then remove
        if wav_id in wav_files:
            os.remove(spk_file)

def clean_empty_speaker_folders(gp_path, lang):
    if lang == "Tamil":
        # Tamil has no separate speaker folders
        return
    for spk_folder in listdir_fullpath(join(gp_path)):
        if len(os.listdir(spk_folder)) == 0:
            os.rmdir(spk_folder)
        

def main():
    lang_dict, all_langs = read_lang_codes(global_vars.conf_dir)
    for lang in all_langs:
        if lang == "Hausa":
            gp_path = join(global_vars.gp_dir, lang, "Hausa", "Data", "adc")
        elif lang == "Chinese-Shanghai":
            gp_path = join(global_vars.gp_dir, lang, "Wu", "adc")
        else:
            gp_path = join(global_vars.gp_dir, lang, "adc")
        try:
            assert exists(gp_path)
        except:
            print("Language directory not found in " + gp_path)
            continue
        speaker_files = get_speaker_files(gp_path, lang)
        lang_code = lang_dict[lang]
        wav_files = os.listdir(join(global_vars.wav_dir, lang_code, "files"))
        compare_and_remove_file_lists(speaker_files, wav_files, lang)
        clean_empty_speaker_folders(gp_path, lang)
  

if __name__ == "__main__":
    main()