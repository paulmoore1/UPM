import os, sys
from os.path import join, exists
sys.path.insert(1, join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper
from collections import defaultdict
import numpy as np

def get_speakers(spk_dir, lang, dataset):
    spk_list = join(spk_dir, "{}_spk.list".format(dataset))
    with open(spk_list, "r") as f:
        spk_lines = f.read().splitlines()
        
    for line in spk_lines:
        if line.startswith(lang):
            entry = line.split()
            speakers = [lang + x + ".spk" for x in entry[1:]]
            return speakers
    print("ERROR: lang {} {} set not found!".format(lang, dataset))
    return None


def analyse_speakers(spk_list, data_dir, lang):
    def _get_info(spk_filepath):
        # In some cases have special converted version
        read_path = spk_filepath + ".utf8.converted"
        if not exists(read_path):
            # Try unconverted version
            read_path = spk_filepath
            if not exists(read_path):
                return None, None
        
        with open(read_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(";AGE:"):
                    if len(line) > 6:
                        age = line[5:-1]
                    else:
                        age = None
                if line.startswith(";SEX:"):
                    if len(line) > 6:
                        gender = line[5:-1]
                    else:
                        gender = None
        return age, gender
    
    n_spk = len(spk_list)
    ages = []
    genders = []
    missing_ages = 0
    missing_genders = 0
    for spk in spk_list:
        spk_filepath = join(data_dir, lang, "spk", spk)
        age, gender = _get_info(spk_filepath)
        if age is not None:
            ages.append(age)
        else:
            missing_ages += 1
        if gender is not None:
            genders.append(gender)
        else:
            missing_genders += 1

    if len(ages) >= 1:
        ages = np.asarray([int(x) for x in ages])
        mean_age = np.mean(ages)
        std_age = np.std(ages)
        age_line = "Age info for {0}/{1} speakers: {2:.1f}±{3:.1f}".format(
            len(ages), n_spk, mean_age, std_age)
        print(age_line)
        
    else:
        age_line = "No information for ages available"
        print(age_line)
    
    if len(genders) >= 1:
        males = [x for x in genders if x.startswith("m")]
        females = [x for x in genders if x.startswith("f")]
        n_m = len(males)
        n_f = len(females)
        total = n_m + n_f

        n_m_pct = round((n_m/total)*100)
        n_f_pct = round((n_f/total)*100)

        gender_line = "Gender ratio (m/f) for {0}/{1} speakers: {2}:{3}".format(
            len(genders), n_spk, n_m_pct, n_f_pct)
        print(gender_line)
    else:
        gender_line = "No information for genders available"
        print(gender_line)
    
    return age_line, gender_line


def analyse_spk_length(spk_list, exp_dir):
    utt2len_file = join(exp_dir, "utt2len")
    if not exists(utt2len_file):
        print("ERROR: utt2len file not found at {}".format(utt2len_file))
    # Faster lookup
    spk_set = set([x.replace(".spk", "") for x in spk_list])
    total_time = 0
    with open(utt2len_file, "r") as f:
        for line in f:
            spk = line[0:5]
            if spk in spk_set:
                entry = line.split()
                time = float(entry[1])
                total_time += time
    time_hrs = total_time / 60 / 60
    length_line = "Length: {0:.1f} hours".format(time_hrs)
    print(length_line)
    return length_line
 

def main():
    data_dir = global_vars.gp_data_dir
    spk_dir = join(global_vars.conf_dir, "spk_lists")
    results_dir = join(global_vars.results_dir, "spk_analysis")
    # Using speakers in this experiment as representative of actual amounts of data used
    root_exp_dir = join(global_vars.exp_dir, "baseline_mfcc", "data")

    if not os.path.isdir(results_dir):
        os.makedirs(results_dir)

    langs = ["BG", "CR", "HA", "PL", "SA", "SW", "TU", "UA"]
    datasets = ["train", "val", "test"]

    for dataset in datasets:
        dataset_lines = []
        for lang in langs:
            print("{}-{}".format(lang, dataset))
            spk_list = get_speakers(spk_dir, lang, dataset)
            age_line, gender_line = analyse_speakers(spk_list, data_dir, lang)
            exp_dir = join(root_exp_dir, dataset)
            length_line = analyse_spk_length(spk_list, exp_dir)
            lang_lines = "{}\n{}\n{}\n{}\n".format(lang, age_line, gender_line, length_line)
            lang_lines += ("-"*50 + "\n")
            dataset_lines.append(lang_lines)

        # Write results to file
        dataset_info_file = join(results_dir, dataset + "_info.txt")
        with open(dataset_info_file, "w") as f:
            for line in dataset_lines:
                f.write(line)

if __name__ == "__main__":
    main()