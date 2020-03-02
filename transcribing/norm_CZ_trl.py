import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from os.path import join, exists
import global_vars
import py_helper_functions as helper


map_long = {"Â¹": "¹e",
            "Ãž": "ø",
            "Ãœ": "ý"
            }

map_short = {"Ã­": "í"
            }


# Script to fix transcriptions after they're converted to utf-8

def normalise_file(transcript_file):
    pass

def main():
    transcriptions_dir = join(global_vars.wav_dir, "CZ", "trl")
    transcript_files = helper.listdir_fullpath(transcriptions_dir)
    for transcript_file in transcript_files:
        normalise_file(transcript_file)

if __name__ == "__main__":
    main()