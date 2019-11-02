import os, sys, re
from os.path import join, exists
sys.path.insert(1, join(sys.path[0], '..'))
import global_vars
from phonetic_transcriptions import get_all_transcript_filepaths
from py_helper_functions import query_yes_no


def check_for_transcript_matches(transcript_files):
    transcript_files.sort()
    all_tr_dict = {}
    all_matches = []
    for transcript_file in transcript_files:
        if not exists(transcript_file):
            print("ERROR file not found: " + transcript_file)
            continue
        with open(transcript_file, "r") as f:
            lines = f.read().splitlines()
        # Filter non-speech lines and set to lower-case
        lines = [x.lower() for x in lines if not x.startswith(";")]
        filename = os.path.splitext(os.path.basename(transcript_file))[0]
        all_tr_dict[filename] = lines
    already_checked = []
    match_counter = []
    # Iterate through speakers in the transcription dictionary
    for spk_id in all_tr_dict:
        spk_lines = all_tr_dict[spk_id]
        # Iterate through lines, checking if it exists in any other speaker
        for line in spk_lines:
            for spk_2_id in all_tr_dict:
                # Skip if it's the same speaker
                if spk_id == spk_2_id or spk_2_id in already_checked:
                    continue
                spk_2_lines = all_tr_dict[spk_2_id]
                if line in spk_2_lines:
                    match_str = spk_id + " <--> " + spk_2_id
                    # if haven't seen this match, add a new tracker + counter
                    if not match_str in all_matches:
                        all_matches.append(match_str)
                        match_counter.append(1)
                    else:
                        match_idx = all_matches.index(match_str)
                        match_counter[match_idx] += 1
        already_checked.append(spk_id)
    log_path = join(global_vars.log_dir, "sa_tr")
    if not exists(log_path):
        os.makedirs(log_path)
    with open(join(log_path, "sa_logs.txt"), "w") as f:
        v_bad_matches = []
        bad_matches = []
        minor_matches = []
        for idx, line in enumerate(all_matches):
            match_count = match_counter[idx]
            match_line = line + " " + str(match_count) + " \n"
            if match_count > 10:
                v_bad_matches.append(match_line)
            elif match_count > 1:
                bad_matches.append(match_line)
            else:
                minor_matches.append(match_line)
        if len(v_bad_matches) > 0:
            f.write("Very bad matches:\n")
            for line in v_bad_matches:
                f.write(line)
        if len(bad_matches) > 0:
            f.write("Bad matches: \n")
            for line in bad_matches:
                f.write(line)
        if len(minor_matches) > 0:
            f.write("Minor matches: \n")
            for line in minor_matches:
                f.write(line)

    
def get_spk_times(utt2len_filepath):
    with open(utt2len_filepath, "r") as f:
        lines = f.read().splitlines()
    time_dict = {}
    for line in lines:
        entry = line.split()
        spk_id = int(entry[0].split("_")[0][2:])
        time = float(entry[1])
        if spk_id in time_dict:
            time_dict[spk_id] += time
        else:
            time_dict[spk_id] = time
    ordered_tuples = []
    for spk_id, time in time_dict.items():
        ordered_tuples.append((spk_id, time))
    ordered_tuples.sort()
    return ordered_tuples

# Checks the percent split in time given a list of validation/test spk ids
def check_percent_split(ordered_times, val_ids, test_ids):
    spk_ids = [x[0] for x in ordered_times]
    train_ids = [x for x in spk_ids if not (x in val_ids or x in test_ids)]
    
    if any(x in val_ids for x in test_ids):
        print("ERROR: validation ids in test ids")
        return
    if any(not x in spk_ids for x in val_ids):
        print("ERROR: validation id not found in spk ids")
        return
    if any(not x in spk_ids for x in test_ids):
        print("ERROR: test id not found in spk ids")
        return

    total_len = sum(n for _, n in ordered_times)
    val_len = sum(n for i, n in ordered_times if i in val_ids)
    test_len = sum(n for i, n in ordered_times if i in test_ids)
    training_len = total_len - val_len - test_len

    print_percent(training_len, total_len, "Training")
    print_percent(val_len, total_len, "Validation")
    print_percent(test_len, total_len, "Testing")

    v_bad_matches = [(4, 5), (15, 81), (17, 20), (20, 23), (29, 73), (32, 33), (33, 36), (48, 61)]
    bad_matches = [(12, 13), (20, 21), (33, 38), (36, 38), (39, 40), (44, 45), (50, 51), (56, 57), (66, 67)]

    assess_split(train_ids, v_bad_matches, bad_matches, "Training")
    assess_split(val_ids, v_bad_matches, bad_matches, "Validation")
    assess_split(test_ids, v_bad_matches, bad_matches, "Testing")
    

def print_percent(audio_len, total_len, data_subset):
    percent = audio_len/total_len*100
    print("{0} %: {1:.3f}".format(data_subset, percent))


def assess_split(spk_ids, v_bad_matches, bad_matches, label):
    v_bad = 0
    for id_1, id_2 in v_bad_matches:
        if id_1 in spk_ids and id_2 in spk_ids:
            v_bad += 1
    bad = 0
    for id_1, id_2 in bad_matches:
        if id_1 in spk_ids and id_2 in spk_ids:
            bad += 1
    #print("{}:\nVery bad count: {}\nBad count: {}\n".format(label, str(v_bad), str(bad)))


def print_percent_times(times):
    total_len = sum(n for _, n in times)
    percent_times = []
    for spk_id, time in times:
        percent_times.append((spk_id, round(time/total_len*100, 3)))
    print(percent_times)


def write_ids_to_conf(lang_code, ids, label, overwrite=False):
    ids.sort()
    id_str = lang_code
    for spk_id in ids:
        if spk_id < 10:
            id_str += (" 00" + str(spk_id))
        elif spk_id < 100:
            id_str += (" 0" + str(spk_id))
        else:
            id_str += (" " + str(spk_id))
    data_subset_str = normalise_data_subset_string(label)
    conf_file = join(global_vars.conf_dir, "spk_lists", data_subset_str + "_spk.list")

    # If doesn't exist, create a new file
    if not exists(conf_file):
        with open(conf_file, "w") as f:
            f.write(id_str + "\n")
    else:
        # If does exist, check if it's in the file or not
        with open(conf_file, "r") as f:
            lines = f.read().splitlines()
        # If ID string isn't already in the file for the language, append it 
        if not any(x.startswith(lang_code) for x in lines):
            lines.append(id_str)
            lines.sort()
            with open(conf_file, "w") as f:
                for line in lines:
                    f.write(line + "\n")
        # ID string is in file, decide if to overwrite or not
        else:
            old_line_list = [x for x in lines if lang_code in x]
            if len(old_line_list) != 1:
                print("ERROR: multiple lines found with same language code")
                return
            old_line = old_line_list[0]
            # If the old line was different, check whether or not to override
            if old_line != id_str:
                overwrite = query_yes_no("IDs found for " + label + " already, overwrite? [y/n]", default="no")
                if not overwrite:
                    print("Did not overwrite")
                    return
                else:
                    print("Overwriting old values")
                    lines.remove(old_line)
                    lines.append(id_str)
                    lines.sort()
                    with open(conf_file, "w") as f:
                        for line in lines:
                            f.write(line + "\n")
            

# Converts training/validation/test strings into a 
# standard lowercase format
def normalise_data_subset_string(data_str):
    data_str = data_str.lower()
    if data_str.startswith("train"):
        return "train"
    elif data_str.startswith("val") or data_str.startswith("eval"):
        return "val"
    elif data_str.startswith("test"):
        return "test"
    else:
        return "UNK"


def main():
    lang_code = "SA"
    transcript_files = get_all_transcript_filepaths(lang_code)
    #check_for_transcript_matches(transcript_files)
    utt2len_filepath = join(global_vars.wav_dir, lang_code, "lists", "utt2len")
    times = get_spk_times(utt2len_filepath)
    #print_percent_times(times)
    val_ids = [4, 12, 20, 25, 29, 33, 44, 48, 55, 56, 82]
    test_ids = [6, 10, 15, 21, 32, 36, 39, 50, 66, 79, 95]
    check_percent_split(times, val_ids, test_ids)

    spk_ids = [x[0] for x in times]
    train_ids = [x for x in spk_ids if not (x in val_ids or x in test_ids)]

    write_ids_to_conf(lang_code, train_ids, "Training")
    write_ids_to_conf(lang_code, val_ids, "Validation")
    write_ids_to_conf(lang_code, test_ids, "Testing")


if __name__ == "__main__":
    main()