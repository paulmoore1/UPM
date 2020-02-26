import os, sys, re
from os.path import join, exists
sys.path.insert(1, join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper

# Converts phonetic features from txt file to csv and txt file of what the articulatory feature vector is
# Done this way to avoid human error in copying down individually

# The file at txt filepath consists of the letter followed by its features 
# e.g. a vowel open front unrounded

def main():
    txt_filepath = join(global_vars.conf_dir, "articulatory_features", "phone_attributes_vanilla.txt")
    if not exists(txt_filepath):
        print("Could not find txt file at: {}".format(txt_filepath))



if __name__ == "__main__":
    main()