import os, re, sys, fnmatch, glob
from os.path import join, exists
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper

# Gets phone maps for a language.
# Needs the filename e.g. swahili_phone_mapping.txt
# Assumes map is in the form:
# dict_phone    ipa_phone   x_sampa_phone
# Returns two dictonaries mapping the particular dictionary phones to standardised IPA/X-SAMPA
# e.g. ipa_dict[SWA_th] = θ; x_sampa_dict[SWA_th] = T
def read_phone_map(map_file):
    file_path = join(global_vars.conf_dir, "phone_maps", map_file)
    assert exists(file_path), "Could not find phone map in " + file_path
    with open(file_path, "r") as f:
        lines = f.read().splitlines()
    ipa_phone_map = {}
    x_sampa_phone_map = {}

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


# Reads phonetic dictionary file and translates it into an IPA/X-SAMPA dictionary
# These files are stored as [lang_code]_IPA_dict.txt and ..X-SAMPA_dict.txt
def convert_phonetic_dict(lang_code, dict_file, ipa_phone_map, x_sampa_phone_map):
    with open(dict_file, "r") as f:
        lines = f.read().splitlines()
    dict_dir = os.path.dirname(dict_file)
    words_dict = {}
    for idx, line in enumerate(lines):
        entry = line.split("} {", 1)
        word = entry[0]
        # Word entries should start with a {, and not have a } after the split
        try:
            
            assert word.startswith("{")
            assert not word.endswith("}")
        except:
            print(entry)
            print(word.startswith("{"))
            print(not word.endswith("}"))
            print("Error at line {} with {}; skipping".format(idx, word))
            continue
        # Trim the { off the front
        word = word[1:]
        word_phones = entry[1]
        # Should end with double curly braces if split correctly
        try:
            assert word_phones.endswith("}}")
        except:
            print("Error at line {} with word phones {}".format(idx, word_phones))
            continue
        # Remove curly braces, WB from string
        word_phones = word_phones.replace("{", "")
        word_phones = word_phones.replace("}", "")
        word_phones = word_phones.replace("WB", "")
        word_phone_list = word_phones.split()
        words_dict[word] = word_phone_list
    print("Finished reading dictionary file")
    
    # Convert into IPA format
    ipa_file_path = join(dict_dir, lang_code + "_IPA_dict.txt")
    with open(ipa_file_path, "w") as f:
        for word in words_dict:
            ipa_word = "".join((map(ipa_phone_map.get, words_dict[word])))
            f.write(word + " " + ipa_word + "\n")
    
    print("Wrote IPA dictionary in " + ipa_file_path)

    # Convert into X-SAMPA format
    x_sampa_file_path = join(dict_dir, lang_code + "_X-SAMPA_dict.txt")
    with open(x_sampa_file_path, "w") as f:
        for word in words_dict:
            x_sampa_word = " ".join((map(x_sampa_phone_map.get, words_dict[word])))
            f.write(word + " " + x_sampa_word + "\n")

    print("Wrote X-SAMPA dictionary in " + x_sampa_file_path)


# Loads a ...IPA_dict.txt or _X-SAMPA_dict.txt file 
# Returns a dictonary where dict[word] = phonetic transcription
def load_dict_file(lang_code, dict_file):
    file_path = join(global_vars.gp_dir, "dict", lang_code, dict_file)
    with open(file_path, "r") as f:
        lines = f.read().splitlines()
    phonetic_dict = {}
    for line in lines:
        entry = line.split()
        # Check that it's just two items: word + phonetic pronunciation
        word = entry[0]
        phonetic_word = " ".join(entry[1:])
        phonetic_dict[word] = phonetic_word
    return phonetic_dict


# Gets all transcript filepaths for a language
# Checks for rmn (Romanized) first, failing that tries looking for trl
# If both fail, returns None, otherwise returns a list of full filepaths
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


# Reads all the transcript files, makes a txt file where each line looks like:
# SA001_1 phonetic_transcrption_of_sentence
# Optional arguments to filter utterances with stutters, uhms or OOV words from final list
def write_all_transcriptions(lang_code, transcript_files, ipa_dict, x_sampa_dict, filter_sutters=True, filter_uhms=True, filter_oov=True):
    ipa_filepath = join(global_vars.all_tr_dir, lang_code + "_IPA_tr.txt")
    x_sampa_filepath = join(global_vars.all_tr_dir, lang_code + "_X-SAMPA_tr.txt")
    ipa_lines = []
    x_sampa_lines = []
    transcript_files.sort()
    for transcript_file in transcript_files:
        if not exists(transcript_file):
            print("ERROR file not found: " + transcript_file)
            continue
        with open(transcript_file, "r") as f:
            lines = f.read().splitlines()
        # Check speaker ID matches in file and filename
        header = lines[0]
        filename = os.path.splitext(os.path.basename(transcript_file))[0]
        header_ID = header.split()[-1]
        file_ID = filename[2:]
        assert header_ID == file_ID, "File and header ID mismatch: {} vs {}".format(header_ID, file_ID)
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
                ipa_words, x_sampa_words = get_line(line, ipa_dict, x_sampa_dict, filter_oov)
                # If Nis returned, something was wrong with one of the words
                if ipa_words is None:
                    print("ERROR with line " + line)
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


# Checks if the words in a line all occur in the dictionary
# If they all do, returns the dictionary values for the words
# Otherwise, returns None
def get_line(line, ipa_dict, x_sampa_dict, filter_oov):
    words = line.split()
    ipa_words = []
    x_sampa_words = []
    for word in words:
        try:
            ipa_word = ipa_dict[word]
            x_sampa_word = x_sampa_dict[word]
        except:
            # If filtering OOV words, stop here
            if filter_oov:
                raise Exception("OOV word found: {}".format(word))
                return None, None
        ipa_words.append(ipa_word)
        x_sampa_words.append(x_sampa_word)
    ipa_words = " ".join(ipa_words)
    ipa_words = "sil " + ipa_words + " sil"
    x_sampa_words = " ".join(x_sampa_words)
    x_sampa_words = "sil " + x_sampa_words + " sil"
    return ipa_words, x_sampa_words

def write_lang_transcriptions(lang_code):
    dict_dir = join(global_vars.gp_dir, "dict", lang_code)
    files = glob.glob(join(dict_dir, "*GPDict.txt"))
    assert len(files) == 1, "Multiple/no matches found in {}".format(dict_dir)
    dict_file = files[0]
    phone_map_file = lang_code + "_phone_map.txt"
    ipa_phone_map, x_sampa_phone_map = read_phone_map(phone_map_file)
    convert_phonetic_dict(lang_code, dict_file, ipa_phone_map, x_sampa_phone_map)
    ipa_dict = load_dict_file(lang_code, lang_code + "_IPA_dict.txt")
    x_sampa_dict = load_dict_file(lang_code, lang_code + "_X-SAMPA_dict.txt")
        
    transcript_files = get_all_transcript_filepaths(lang_code)
    write_all_transcriptions(lang_code, transcript_files, ipa_dict, x_sampa_dict)
    
def combine_phones(lang_codes, phone_map_dir, write_dir):
    phones_list = []
    for lang_code in lang_codes:
        phone_map = join(phone_map_dir, lang_code + "_phone_map.txt")
        with open(phone_map, "r") as f:
            lines = f.read().splitlines()
        for line in lines:
            entry = line.split()
            x_sampa_phone = entry[2]
            if x_sampa_phone not in phones_list:
                phones_list.append(x_sampa_phone)
    phones_list.sort()
    phones_list_no_sil = phones_list.copy()
    phones_list_no_sil.remove("sil")

    phones_file = join(write_dir, "phones.txt")
    silence_phones_file = join(write_dir, "silence_phones.txt")
    optional_silence_phones_file = join(write_dir, "optional_silence_phones.txt")
    non_silence_phones_file = join(write_dir, "nonsilence_phones.txt")
    extra_questions_file = join(write_dir, "extra_questions.txt")
    lexicon_file = join(write_dir, "lexicon.txt")
    lexiconp_file = join(write_dir, "lexiconp.txt")

    with open(phones_file, "w") as f:
        for phone in phones_list:
            f.write(phone + "\n")
    
    with open(silence_phones_file, "w") as f:
        f.write("sil\n")

    with open(optional_silence_phones_file, "w") as f:
        f.write("sil\n" )

    with open(non_silence_phones_file, "w") as f:
        for phone in phones_list_no_sil:
            f.write(phone + "\n")

    with open(extra_questions_file, "w") as f:
        f.write("sil\n")
        line = " ".join(phones_list_no_sil) + "\n"
        f.write(line)

    with open(lexicon_file, "w") as f:
        for phone in phones_list:
            f.write("{}\t{}\n".format(phone, phone))

    with open(lexiconp_file, "w") as f:
        for phone in phones_list:
            f.write("{}\t1.0\t{}\n".format(phone, phone))

# Keep private so not imported
def _main():
    lang_codes = ["SA", "UK"]
    phone_map_dir = join(global_vars.conf_dir, "phone_maps")
    dict_dir = join(global_vars.exp_dir, "dict")
    if not os.path.isdir(dict_dir):
        os.mkdir(dict_dir)
    #for lang_code in lang_codes:
    #    write_lang_transcriptions(lang_code)
    combine_phones(lang_codes, phone_map_dir, dict_dir)    
    

if __name__ == "__main__":
    _main()