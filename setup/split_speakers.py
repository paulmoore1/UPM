import os, sys, re
from os.path import join, exists
sys.path.insert(1, join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper


def get_all_transcript_filepaths(lang_code):
    lang_dir = join(global_vars.wav_dir, lang_code)
    if "rmn" in os.listdir(lang_dir):
        transcript_dir = join(lang_dir, "rmn")
    elif "trl" in os.listdir(lang_dir):
        transcript_dir = join(lang_dir, "trl")
    else:
        print("No transcript directories (rmn/trl) found in " + lang_dir)
        return None
    return helper.listdir_fullpath(transcript_dir)


def check_for_transcript_matches(lang_code, transcript_files, log_dir):
    transcript_files.sort()
    all_tr_dict = {}
    all_matches = []
    for transcript_file in transcript_files:
        if not exists(transcript_file):
            print("ERROR file not found: " + transcript_file)
            continue
        with open(transcript_file, "r") as f:
            try:
                lines = f.read().splitlines()
            except:
                print("Error reading file: {}".format(transcript_file))
                continue
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
                    match_str = spk_id + " " + spk_2_id
                    # if haven't seen this match, add a new tracker + counter
                    if not match_str in all_matches:
                        all_matches.append(match_str)
                        match_counter.append(1)
                    else:
                        match_idx = all_matches.index(match_str)
                        match_counter[match_idx] += 1
        already_checked.append(spk_id)
    
    with open(join(log_dir, "{}_logs.txt".format(lang_code.lower())), "w") as f:
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
            write_line_counts(f, v_bad_matches, "Very bad matches")
        if len(bad_matches) > 0:
            write_line_counts(f, bad_matches, "Bad matches")
        if len(minor_matches) > 0:
            write_line_counts(f, minor_matches, "Minor matches")

    return v_bad_matches, bad_matches, minor_matches

def write_line_counts(open_file, matches, label):
    open_file.write(label + ":\n")
    for match in matches:
        items = match.split()
        spk_1 = str(items[0])
        spk_2 = str(items[1])
        count = str(items[2])
        open_file.write("{} <--> {}: {}\n".format(spk_1, spk_2, count))

    
def get_spk_times(lang_code, log_dir):
    utt2len_filepath = join(global_vars.wav_dir, lang_code, "lists", "utt2len")
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
    all_times = []
    for spk_id, time in time_dict.items():
        all_times.append((spk_id, time))
    all_times.sort()
    total_len = sum(n for _, n in all_times)
    
    log_path = join(log_dir, "{}_times.txt".format(lang_code.lower()))

    with open(log_path, "w") as f:
        f.write("Time percent for each speaker\n")
        for spk_id, time in all_times:
            percent_time = round(time/total_len*100, 3)
            id_str = id_to_str(spk_id, space_before=False, lang_code=lang_code)
            f.write("{} {}\n".format(id_str, percent_time))

    return all_times

# Checks the percent split in time given a list of validation/test spk ids
def check_percent_split(ordered_times, val_ids, test_ids, v_bad, bad, minor, log_dir):
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

    assess_split(train_ids, v_bad, bad, minor, "Training", log_dir)
    assess_split(val_ids, v_bad, bad, minor, "Validation", log_dir)
    assess_split(test_ids, v_bad, bad, minor, "Testing", log_dir)
    

def print_percent(audio_len, total_len, data_subset):
    percent = audio_len/total_len*100
    print("{0} %: {1:.3f}".format(data_subset, percent))

def convert_to_tuples(matches):
    tuples = []
    for match in matches:
        items = match.split()
        # Convert e.g. UA001 --> 1
        spk_1_id = int(items[0][2:])
        spk_2_id = int(items[1][2:])
        tuples.append((spk_1_id, spk_2_id))
    return tuples


def assess_split(spk_ids, v_bad, bad, minor, label, log_dir):
    
    v_bad_count, v_bad_lines = get_counts_and_lines(v_bad, spk_ids)
    bad_count, bad_lines = get_counts_and_lines(bad, spk_ids)
    minor_count, minor_lines = get_counts_and_lines(minor, spk_ids)
    

    print("{}:\nVery bad count: {}\nBad count: {}\nMinor count: {}\n".format(
        label, str(v_bad_count), str(bad_count), str(minor_count)))

    log_file = join(log_dir, "{}_revised.txt".format(label.lower()))

    with open(log_file, "w") as f:
        write_line_counts(f, v_bad_lines, "Very bad matches")
        write_line_counts(f, bad_lines, "Bad matches")
        write_line_counts(f, minor_lines, "Minor matches")
    

# Get number of bad matches, and lines they occur on
def get_counts_and_lines(bad, spk_ids):
    matches = convert_to_tuples(bad)
    count = 0
    lines = []
    for idx, (id_1, id_2) in enumerate(matches):
        if id_1 in spk_ids and id_2 in spk_ids:
            count += 1
            lines.append(bad[idx])
    return count, lines
    

def print_percent_times(times):
    total_len = sum(n for _, n in times)
    percent_times = []
    for spk_id, time in times:
        percent_times.append((spk_id, round(time/total_len*100, 3)))
    print(percent_times)

def id_to_str(id, space_before=True, lang_code=None):
    if id < 10:
        id_str =  "00" + str(id)
    elif id < 100:
        id_str = "0" + str(id)
    else:
        id_str = str(id)

    if lang_code is not None:
        id_str = lang_code.upper() + id_str

    if space_before:
        id_str = " " + id_str

    return id_str    


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
                overwrite = helper.query_yes_no("IDs found for " + label + " already, overwrite? [y/n]", default="no")
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
    lang_code = "PO"
    log_dir = join(global_vars.log_dir, "splitting")
    if not exists(log_dir):
        os.makedirs(log_dir)
    transcript_files = get_all_transcript_filepaths(lang_code)
    v_bad, bad, minor = check_for_transcript_matches(lang_code, transcript_files, log_dir)
    
    times = get_spk_times(lang_code, log_dir)
    #print_percent_times(times)
    val_ids = [1, 2, 3, 4, 5, 7, 8, 9]
    test_ids = [6, 10]
    #
    check_percent_split(times, val_ids, test_ids, v_bad, bad, minor, log_dir)

    # spk_ids = [x[0] for x in times]
    # train_ids = [x for x in spk_ids if not (x in val_ids or x in test_ids)]

    # write_ids_to_conf(lang_code, train_ids, "Training")
    # write_ids_to_conf(lang_code, val_ids, "Validation")
    # write_ids_to_conf(lang_code, test_ids, "Testing")


if __name__ == "__main__":
    main()