import os, sys, re
from os.path import join, exists
sys.path.insert(1, join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper
from sklearn.preprocessing import OneHotEncoder
import numpy as np
from collections import OrderedDict


# Converts phonetic features from txt file to csv and txt file of what the articulatory feature vector is
# Done this way to avoid human error in copying down individually

# The file at txt filepath consists of the letter followed by its features 
# e.g. a vowel open front unrounded

# Returns dictionary of phones + features list
# e.g. phones["a"] = ["vowel", "open", "front", "unrounded"]
def read_phone_file(txt_filepath):
    with open(txt_filepath, "r") as f:
        lines = f.read().splitlines()
    phones = {}
    for line in lines:
        entry = line.split()
        phone = entry[0]
        features = entry[1:]
        phones[phone] = features
    return phones


# Reads phone map file and returns each line split up
def read_phone_map(phone_map):
    with open(phone_map, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    return [x.split() for x in lines]
    

# Checks if an IPA/X-SAMPA transcription exists
# Then checks if any of its phones do not occur in the universal phones list
def check_phone_map(phone_map, universal_phones, log_filepath):
    lang = os.path.basename(phone_map)[0:2]
    
    phones = read_phone_map(phone_map)
    missing_phones = []
  
    # Check if the first line after the Silence line has three items
    if len(phones[1]) != 3: # phone map is incomplete
        with open(log_filepath, "a") as f:
            f.write("Incomplete phone map for {}\n".format(lang))
        return None
    
    else:
        x_sampa_phones = [x[2] for x in phones if len(x) == 3]

        missing_phones = [x for x in x_sampa_phones if x not in universal_phones and x != "sil"]
        missing_phones = list(set(missing_phones)) # remove duplicates
        if len(missing_phones) > 0:
            with open(log_filepath, "a") as f:
                f.write("Lang {} is missing phones: {}\n".format(lang, str(missing_phones)))
        else:
            with open(log_filepath, "a") as f:
                f.write("Complete phone map for {}\n".format(lang))
        return x_sampa_phones


# Simple phone extender
def get_extended_phone_set(universal_phones):
    extensions = [":", "`" "_<", "_>", "_~", "_h", "_w", "_j", "_t", "_^", "_d"]
    extended_set = [x for x in universal_phones]
    for phone in universal_phones:
        extended_set += [phone + x for x in extensions]
    return extended_set

def get_all_features(universal_phones, extensions):
    all_features = []
    for feature in universal_phones.values():
        all_features += feature
    for feature in extensions.values():
        all_features += feature
    all_features = list(set(all_features))
    all_features.sort()
    return all_features

# 
def convert_to_features(all_phones, universal_phones, extensions, conf_dir):
    # Create dictionary with full features for each phone
    all_phones_dict = {}
    for phone in all_phones:
        if phone == "sil" or phone == "unk":
            all_phones_dict[phone] = []
            continue
        if phone in universal_phones:
            # Simply enter it if it's in the universal list already
            all_phones_dict[phone] = universal_phones[phone]
        else:
            phone_features = []
            # Stupid Python doesn't have a string copy function so we can modify it independently
            temp = (phone + '.')[:-1]
            # Check for extensions within e.g. _<, : etc.
            for extension in extensions:
                if extension in temp:
                    phone_features += extensions[extension]
                    temp = temp.replace(extension, "")
            n = len(temp)
            # If removing extensions is enough, will now find in universal phones list
            if temp in universal_phones:
                phone_features += universal_phones[temp]
            elif n <= 3: # Must be a dipthong/tripthong e.g. Ei
                for i in range(n):
                    phone_features += universal_phones[temp[i]]
            else:
                raise Exception("Unknown phone: {}".format(phone))
            # Remove any duplicate features
            phone_features = list(set(phone_features))
            all_phones_dict[phone] = phone_features
    # for phone, features in all_phones_dict.items():
    #     print("Phone: {}\tFeatures: {}".format(str(phone), str(features)))

    # Set up OneHotEncoder
    all_features = get_all_features(universal_phones, extensions)
    print("Total #features: {}".format(len(all_features)))
    arr = np.asarray(all_features)
    arr = arr.reshape(-1, 1)
    enc = OneHotEncoder()
    enc.fit(arr) #[all_features])

    write_to_txt_file(all_phones_dict, enc, conf_dir)

def write_to_txt_file(all_phones_dict, enc, conf_dir):
    filepath = join(conf_dir, "feature_vectors.txt")
    csv_filepath = join(conf_dir, "feature_vectors.csv")
    # Sort dictionary so that file is in a reasonable order
    od = OrderedDict(sorted(all_phones_dict.items()))

    # Get header line
    header = list(enc.categories_[0])
    # Get spacing list so that file is easy to read
    spacing = [len(x) for x in header]
    # Ignore spacing for phone; done separately since phone length is variable
    header.insert(0, "phone")

    with open(filepath, "w") as f:
        f.write(" ".join(header) + "\n")
        for phone, features in od.items():
            phone_spacing = len("phone") - len(phone) + 1
            if phone_spacing < 0:
                print("Spacing not good for: {}".format(phone))
                phone_spacing = 0
            phone += " "*phone_spacing
         
            # Fill silence phone with vector of 0s
            if phone.strip() == "sil":
                vector = np.zeros(len(header) - 1)
            # Fill unknown/noisy with vector of 1s
            elif phone.strip() == "unk":
                vector = np.ones(len(header) - 1)
            else:
                vector = convert_to_vector(features, enc)
            str_out = convert_vector_to_formatted_string(vector, spacing)

            f.write(phone + str_out + "\n")
            #print(phone)


# Converts from features to feature vector using OneHotEncoder
def convert_to_vector(features, encoder):
    out = encoder.transform(np.asarray(features).reshape(-1, 1)).toarray()
    return np.sum(out, axis=0)

def convert_vector_to_formatted_string(vector, spacing):
    vector = [str(int(x)) for x in list(vector)] # Convert from float array to string ints list
    assert len(vector) == len(spacing)
    str_out = ""

    for idx, number in enumerate(vector):
        space_added = spacing[idx]
        str_out += (number + " "*space_added)
    return str_out

    

def main():
    conf_dir = join(global_vars.conf_dir, "articulatory_features")
    phones_filepath =  join(conf_dir, "phone_attributes_vanilla.txt")
    extensions_filepath = join(conf_dir, "extensions.txt")
    if not exists(phones_filepath):
        print("Could not find phone file at: {}".format(phones_filepath))
        return
    if not exists(extensions_filepath):
        print("Could not find extensions file at: {}".format(extensions_filepath))
        return
    
    phone_maps_files = helper.listdir_fullpath(join(global_vars.conf_dir, "phone_maps"))
    universal_phones = read_phone_file(phones_filepath)
    extensions = read_phone_file(extensions_filepath)
    extended_u_phones = get_extended_phone_set(universal_phones)
    log_dir = join(global_vars.log_dir, "phonetic_features")
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    log_filepath = join(log_dir, "phone_map_check.txt")
    # Overwrite any existing file
    open(log_filepath, "w").close()

    all_phones = []

    for phone_map in phone_maps_files:
        x_sampa_phones = check_phone_map(phone_map, extended_u_phones, log_filepath)
        if x_sampa_phones is not None:
            all_phones += x_sampa_phones

    # Convert all_phones to unique ones
    all_phones = list(set(all_phones))

    print("Total #phones: {}".format(len(all_phones)))

    convert_to_features(all_phones, universal_phones, extensions, conf_dir)

if __name__ == "__main__":
    main()