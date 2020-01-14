import os, argparse, sys
from os.path import expanduser, join, isdir, exists
home = expanduser("~")
upm_dir = os.path.join(home, "UPM")
sys.path.insert(1, upm_dir)

from py_helper_functions import str2bool

def get_args():
    parser = argparse.ArgumentParser(description='UPM transcription')
    parser.add_argument("--conf-dir", type=str, required=True, 
                        help="Directory for configuration files")
    parser.add_argument("--lang-codes", type=str, required=True, 
                        help="Language codes")
    parser.add_argument("--dataset", required=True, choices=["train", "val", "test"])
    parser.add_argument("--write-dir", type=str, required=True,
                        help="Directory to write output to")
    parser.add_argument("--create-phone-files", type=str2bool, default=False)
    return parser.parse_args()

def main():
    args = get_args()
    


def get_args():
    parser = argparse.ArgumentParser(description='UPM transcription')
    parser.add_argument("--conf-dir", type=str, required=True, 
                        help="Directory for configuration files")
    parser.add_argument("--lang-codes", type=str, required=True, 
                        help="Language codes")
    parser.add_argument("--dataset", required=True, choices=["train", "val", "test"])
    parser.add_argument("--write-dir", type=str, required=True,
                        help="Directory to write output to")
    parser.add_argument("--create-phone-files", type=str2bool, default=False)
    return parser.parse_args()

if __name__ == "__main__":
    main()