import os, csv
""""
File for mapping phonemes to description
"""
def parse_csv(filename):
    all_phonemes = []
    phoneme_attributes = {}
    with open(filename, "r") as f:
        data = csv.reader(f, delimiter=",")
        next(data) #Skip header line
        for row in data:
            all_phonemes.append(row[0])
            phoneme_attributes[row[0]] = set(row[1].split())
            # e.g. {"a": {'vowel', 'open', 'front', 'unrounded'}}
    return all_phonemes, phoneme_attributes


# Matches the longest possible suffix for a given phoneme
# e.g. ts_< --> matches to _<
def match_longest_suffix(search_phoneme, all_phonemes):
    candidates = []
    for phoneme in all_phonemes:
        if search_phoneme.endswith(phoneme):
            candidates.append(phoneme)
    # If no matching phonemes were found, return error
    if not candidates:
        return "ERR"
    else:
        # Return the longest phoneme found
        return max(candidates, key=len)


def get_all_suffixes(search_phoneme, all_phonemes):
    suffixes = []
    # Keep munching the suffixes off the string until it's empty
    while len(search_phoneme) > 0:
        suffix = match_longest_suffix(search_phoneme, all_phonemes)
        if suffix != "ERR":
            print("Found suffix: " + suffix)
            suffixes.append(suffix)
            # Remove suffix from string so search continues
            search_phoneme = search_phoneme[:-len(suffix)]
        else:
            return ["ERR"]
    return suffixes


# Gets the union of all attributes for each phoneme suffix
def combine_attributes(suffixes, phoneme_attributes):
    full_set = set()
    for suffix in suffixes:
        full_set  = full_set.union(phoneme_attributes[suffix])
    return list(full_set)

def main():
    all_phonemes, phoneme_attributes = parse_csv("phonemes.csv")
    suffixes = get_all_suffixes("ts_>tK", all_phonemes)
    for suffix in suffixes:
        print(phoneme_attributes[suffix])
    full_set = combine_attributes(suffixes, phoneme_attributes)
    print(full_set)

if __name__ == "__main__":
    main()
