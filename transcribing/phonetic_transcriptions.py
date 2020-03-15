import os, re, sys, fnmatch, glob, string
from os.path import join, exists
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper
from collections import Counter

# Gets phone maps for a language.
# Needs the filename e.g. swahili_phone_mapping.txt
# Assumes map is in the form:
# dict_phone    ipa_phone   x_sampa_phone
# Returns two dictonaries mapping the particular dictionary phones to standardised IPA/X-SAMPA
# e.g. ipa_dict[SWA_th] = θ; x_sampa_dict[SWA_th] = T
def read_phone_map(map_file, return_x_sampa_phones=False):
    file_path = join(global_vars.conf_dir, "phone_maps", map_file)
    assert exists(file_path), "Could not find phone map in " + file_path
    with open(file_path, "r") as f:
        lines = f.read().splitlines()
    ipa_phone_map = {}
    x_sampa_phone_map = {}
    if not return_x_sampa_phones:
        for line in lines:
            #print(line)
            entry = line.split()
            dict_phone = entry[0]
            ipa_phone = entry[1]
            x_sampa_phone = entry[2]
            ipa_phone_map[dict_phone] = ipa_phone
            x_sampa_phone_map[dict_phone] = x_sampa_phone
        print("Finished reading phone maps")
        return ipa_phone_map, x_sampa_phone_map
    else:
        x_sampa_phones = set()
        for line in lines:
            entry = line.split()
            x_sampa_phone = entry[2]
            x_sampa_phones.add(x_sampa_phone)
        return x_sampa_phones

# Reads phonetic dictionary file and translates it into an IPA/X-SAMPA dictionary
# These files are stored as [lang_code]_IPA_dict.txt and ..X-SAMPA_dict.txt
def convert_phonetic_dict(lang_code, dict_file, ipa_phone_map, x_sampa_phone_map):
    with open(dict_file, "r") as f:
        print("Reading dictionary file: {}".format(dict_file))
        lines = f.read().splitlines()
    dict_dir = os.path.dirname(dict_file)
    words_dict = {}
    for idx, line in enumerate(lines):
        if lang_code in ["PL", "PO", "FR"]:
            entry = line.split("\t")
        elif lang_code in ["BG"]:
            entry = line.split(" ", 1)
        elif lang_code in ["KO"]:
            entry = line.split("}\t{")
        else:
            entry = line.split("} {", 1)
        word = entry[0].strip()
        word = word.replace("{", "")
        word = word.replace("}", "")

        word_phones = entry[1]
        

        # Remove curly braces, WB from string
        word_phones = word_phones.replace("{", "")
        word_phones = word_phones.replace("}", "")
        word_phones = word_phones.replace("WB", "")
        
        # Remove tonal information from Hausa (can't model)
        if lang_code == "HA":
            hausa_tones = [" L", " S", "T1", "T2", "T3"]
            for tone in hausa_tones:
                word_phones = word_phones.replace(tone, "")

        elif lang_code == "VN":
            viet_tones = ["T1", "T2", "T3", "T4", "T5", "T6"]
            for tone in viet_tones:
                word_phones = word_phones.replace(tone, "")

        word_phone_list = word_phones.split()
        #print("Word = {}\tPhone list =  {}".format(word, word_phone_list))
        words_dict[word] = word_phone_list
    print("Finished reading dictionary file")
    
    # Convert into IPA format
    ipa_file_path = join(dict_dir, lang_code + "_IPA_dict.txt")
    with open(ipa_file_path, "w") as f:
        for word in words_dict:
            # print(word)
            # print(words_dict[word])
            ipa_word = "".join((map(ipa_phone_map.get, words_dict[word])))
            f.write(word + " " + ipa_word + "\n")
    
    print("Wrote IPA dictionary in " + ipa_file_path)

    # Convert into X-SAMPA format
    x_sampa_file_path = join(dict_dir, lang_code + "_X-SAMPA_dict.txt")
    with open(x_sampa_file_path, "w") as f:
        for word in words_dict:
            #print(word)
            #print(words_dict[word])
            x_sampa_word = " ".join((map(x_sampa_phone_map.get, words_dict[word])))
            f.write(word + " " + x_sampa_word + "\n")

    print("Wrote X-SAMPA dictionary in " + x_sampa_file_path)


# Loads a ...IPA_dict.txt or _X-SAMPA_dict.txt file 
# Returns a dictonary where dict[word] = phonetic transcription
def load_dict_file(lang_code, dict_file):
    file_path = join(global_vars.gp_data_dir, lang_code, "dict", dict_file)
    with open(file_path, "r") as f:
        lines = f.read().splitlines()
    phonetic_dict = {}
    for line in lines:
        entry = line.split()
        # Check that it's just two items: word + phonetic pronunciation
        word = entry[0]
        phonetic_word = " ".join(entry[1:])
        uppercased_word = word[0].upper() + word[1:] # Can't capitalize as that lowers other letters
        phonetic_dict[word] = phonetic_word
        phonetic_dict[uppercased_word] = phonetic_word
    return phonetic_dict


# Gets all transcript filepaths for a language
# Checks for rmn (Romanized) first, failing that tries looking for trl
# If both fail, returns None, otherwise returns a list of full filepaths
def get_all_transcript_filepaths(lang_code, preferred_type="trl"):
    lang_dir = join(global_vars.gp_data_dir, lang_code)
    if "rmn" in os.listdir(lang_dir):
        if preferred_type == "rmn":
            transcript_dir = join(lang_dir, "rmn")
        else:
            if "trl" in os.listdir(lang_dir):
                transcript_dir = join(lang_dir, "trl")
    elif "trl" in os.listdir(lang_dir):
        transcript_dir = join(lang_dir, "trl")
    else:
        print("No transcript directories (rmn/trl) found in " + lang_dir)
        return None
    return helper.listdir_fullpath(transcript_dir)


# Reads all the transcript files, makes a txt file where each line looks like:
# SA001_1 phonetic_transcrption_of_sentence
# Optional arguments to filter utterances with stutters, uhms or OOV words from final list
def write_all_transcriptions(lang_code, transcript_files, ipa_dict, 
x_sampa_dict, trl_encoding, filter_sutters=True, filter_uhms=True, filter_oov=True):
    ipa_filepath = join(global_vars.all_tr_dir, lang_code + "_IPA_tr.txt")
    x_sampa_filepath = join(global_vars.gp_data_dir, lang_code, "lists", "text")
    ipa_lines = []
    x_sampa_lines = []
    transcript_files.sort()
    skipped_lines = 0
    oov_words = []
    for transcript_file in transcript_files:
        print("Writing for file: {}".format(os.path.basename(transcript_file)))
        if not exists(transcript_file):
            print("ERROR file not found: " + transcript_file)
            continue
        with open(transcript_file, "r", encoding=trl_encoding) as f:
            lines = f.read().splitlines()
        # Check speaker ID matches in file and filename
        header = lines[0]
        filename = os.path.splitext(os.path.basename(transcript_file))[0]
        header_ID = header.split()[-1]
        if lang_code != "FR":
            file_ID = filename[2:]
        else:
            file_ID = filename
        assert header_ID == file_ID, "File and header ID mismatch: {} vs {}".format(file_ID, header_ID)
        # Drop header line
        transcript_lines = lines[1:]
        # Ensure that the first line of the transcript file starts with ; [num]:
        assert re.match(";.*:", transcript_lines[0]) is not None, "Transcript lines should start with ; " + transcript_lines[0]
        curr_line_id = "1"
        for line in (transcript_lines):
            if line.startswith(";"):
                m = re.search("; (.+?):", line)
                assert m, "ERROR with line " + line
                curr_line_id = m.group(1)
            else:
                utt_id = filename + "_" + curr_line_id
                ipa_words, x_sampa_words = get_line(line, ipa_dict, x_sampa_dict, lang_code)
                # If Nis returned, something was wrong with one of the words
                if ipa_words is None:
                    print("ERROR with line {}".format(curr_line_id))
                    skipped_lines += 1
                    oov_words.append(x_sampa_words)
                    continue
                ipa_lines.append(utt_id + " " + ipa_words)
                x_sampa_lines.append(utt_id + " " + x_sampa_words)

    with open(ipa_filepath, "w") as f:
        for line in ipa_lines:
            f.write(line + "\n")
    
    with open(x_sampa_filepath, "w") as f:
        for line in x_sampa_lines:
            f.write(line + "\n")
                
    print("Finished writing transcriptions to {} and {}".format(ipa_filepath, x_sampa_filepath))
    counter = Counter(oov_words)
    print("OOV words: {}".format(str(counter)))
    print("Skipped {} lines".format(skipped_lines))

# Checks if the words in a line all occur in the dictionary
# If they all do, returns the dictionary values for the words
# Otherwise, returns None
def get_line(line, ipa_dict, x_sampa_dict, lang_code):
    # Remove punctuation for some languages
    basic_punctuation = [":", ";", "!", ".", ",", "?", "\""]
    if lang_code == "PL":
        # Can't simply replace all punctuation since hyphens are needed
        for punct in basic_punctuation:
            if punct in line:
                line = line.replace(punct, " ")
        polish_punct = ["”", "„", "`", "\ufeff", "\xad", "»", "«", "“", ")"]
        for punct in polish_punct:
            if punct in line:
                line = line.replace(punct, "")
        line = line.replace(" – ", " ")
        line = line.replace(" -", " ")
        line = line.replace("- ", " ")
        line = line.replace("ü", "u2")
        line = line.replace("ö", "o2")
        line = line.replace("ç", "c2")
    elif lang_code == "CZ":
        for punct in basic_punctuation:
            if punct in line:
                line = line.replace(punct, "")
        line = line.replace("- ", " ")
        line = line.replace("(", " ")
        line = line.replace(")", " ")
        line = line.replace("/", " ")
        line = line.replace("`", " ")
        line = line.replace("©", "¹")
        line = line.replace("®", "Ÿ")
        line = line.replace("«", "»")
    elif lang_code == "FR":
        for punct in basic_punctuation:
            if punct in line:
                line = line.replace(punct, "")
        line = line.replace("(", " ")
        line = line.replace(")", " ")
    elif lang_code == "KO":
        line = line.replace("#noise#", "")
    elif lang_code == "SW":
        line = re.sub(r'(<#[^<]*>)', " ", line)
    words = line.split()
    ipa_words = []
    x_sampa_words = []
    for word in words:
        #print(word)
        word = word.strip()
        word = word.replace(" ", "")
        found_oov = False
        if word in ipa_dict:
            ipa_word = ipa_dict[word]
            x_sampa_word = x_sampa_dict[word]
        # Try lowercasing if that's the problem
        else:
            
            lowercased_word = re.sub('[A-Z]+', lambda m: m.group(0).lower(), word)
            word_fragment = word.replace("<", "")
            word_fragment = word_fragment.replace(">", "")
            word_fragment = word_fragment.replace("-", "")
       
            if lowercased_word in ipa_dict:
                ipa_word = ipa_dict[lowercased_word]
                x_sampa_word = x_sampa_dict[lowercased_word]
            elif word.lower() in ipa_dict:
                ipa_word = ipa_dict[word.lower()]
                x_sampa_word = x_sampa_dict[word.lower()]
            elif word_fragment in ipa_dict:
                ipa_word = ipa_dict[word_fragment]
                x_sampa_word = x_sampa_dict[word_fragment]
            # Complicated logic to sort out the weird French words
            elif lang_code == "FR" and len(word) >= 2:
                word.lower()
                if word[1] == "\'": # If first bit is an apostrophe
                    prefix = word[0:2]
                    suffix = word[2:]

                    if "-" in suffix:
                        ipa_suffix, x_sampa_suffix = merge_punct(suffix, ipa_dict, x_sampa_dict, "-")
                        if ipa_suffix == None:
                            found_oov = True
                    else:
                        if suffix in ipa_dict:
                            ipa_suffix = ipa_dict[suffix]
                            x_sampa_suffix = x_sampa_dict[suffix]
                        else:
                            found_oov = True

                    if prefix in ipa_dict:
                        ipa_word = ipa_dict[prefix] + ipa_suffix
                        x_sampa_word = x_sampa_dict[prefix] + " " + x_sampa_suffix
                    else:
                        found_oov = True
                elif "-" in word:
                    ipa_word, x_sampa_word = merge_punct(word, ipa_dict, x_sampa_dict, "-")
                    if ipa_word == None:
                        found_oov = True

                elif "\'" in word:
                    ipa_word, x_sampa_word = merge_punct(word, ipa_dict, x_sampa_dict, "\'")
                    if ipa_word == None:
                        found_oov = True
                else:
                    found_oov = True
            
            elif lang_code == "VN" and "_" in word:
                words = word.split("_")
                first_word = words[0]
                second_word = words[1]
                if first_word in ipa_dict and second_word in ipa_dict:
                    ipa_word = ipa_dict[first_word] + " " + ipa_dict[second_word]
                    x_sampa_word = x_sampa_dict[first_word] + " " + x_sampa_dict[second_word]
                else:
                    found_oov = True
            elif lang_code == "SW":
                word.replace("<", "")
                word.replace(">", "")
                if word in ipa_dict:
                    ipa_word = ipa_dict[word]
                    x_sampa_word = x_sampa_dict[word]
                elif "_" in word:
                    
                    ipa_word, x_sampa_word = merge_punct(word, ipa_dict, x_sampa_dict, "_")
                    if ipa_word == None:
                        found_oov = True
                else:
                    found_oov = True
            else:
                found_oov = True
                
        if found_oov:
            #print("OOV word found: {} or {}".format(word, lowercased_word))
            return None, word
        ipa_words.append(ipa_word)
        x_sampa_words.append(x_sampa_word)
    ipa_words = " ".join(ipa_words)
    ipa_words = "sil " + ipa_words + " sil"
    x_sampa_words = " ".join(x_sampa_words)
    x_sampa_words = "sil " + x_sampa_words + " sil"
    return ipa_words, x_sampa_words

def merge_punct(word, ipa_dict, x_sampa_dict, punct):
    words = word.split(punct)
    all_words_in_dict =  True
    for word in words:
        if not word in ipa_dict:
            all_words_in_dict = False
    if all_words_in_dict:
        ipa_word = ""
        x_sampa_word = ""
        for word in words:
            ipa_word += ipa_dict[word]
            x_sampa_word += x_sampa_dict[word] + " "
        x_sampa_word[:-1] # Trim any trailing whitespace
        return ipa_word, x_sampa_word
    else:
        return None, None


def write_lang_transcriptions(lang_code, encoding, preferred_type):
    dict_dir = join(global_vars.gp_data_dir, lang_code, "dict")
    files = glob.glob(join(dict_dir, "*GPDict.txt"))
    assert len(files) == 1, "Multiple/no matches found in {}".format(dict_dir)
    dict_file = files[0]
    phone_map_file = lang_code + "_phone_map.txt"
    ipa_phone_map, x_sampa_phone_map = read_phone_map(phone_map_file)
    convert_phonetic_dict(lang_code, dict_file, ipa_phone_map, x_sampa_phone_map)
    ipa_dict = load_dict_file(lang_code, lang_code + "_IPA_dict.txt")
    x_sampa_dict = load_dict_file(lang_code, lang_code + "_X-SAMPA_dict.txt")
        
    transcript_files = get_all_transcript_filepaths(lang_code, preferred_type=preferred_type)
    write_all_transcriptions(lang_code, transcript_files, ipa_dict, x_sampa_dict, 
                                encoding)


def check_transcription(lang_code):
    map_file = join(global_vars.conf_dir, "phone_maps", "{}_phone_map.txt".format(lang_code))
    x_sampa_phones = read_phone_map(map_file, return_x_sampa_phones=True)

    transcript_file = join(global_vars.gp_data_dir, lang_code, "lists", "text")
    if not exists(transcript_file):
        print("File not found in {}".format(transcript_file))
        return

    with open(transcript_file, "r") as f:
        for idx, line in enumerate(f):
            entry = line.split()
            all_phones = entry[1:] # Since the ID is the first word
            for phone in all_phones:
                if phone not in x_sampa_phones:
                    print("ERROR at line {} with unknown phone {} for language {}".format(idx, phone, lang_code))
                    return
    print("Validated transcription successfully")

# Keep private so not imported
def _main():
    lang_codes = ["JA"] # FR needs iso-8859-15 and trl files
    #encoding="iso-8859-15"
    encoding="utf-8"

    for lang_code in lang_codes:
        write_lang_transcriptions(lang_code, encoding, "rmn")   
        check_transcription(lang_code)


if __name__ == "__main__":
    _main()