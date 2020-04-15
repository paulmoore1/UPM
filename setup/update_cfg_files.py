import re, argparse, os, shutil
from os.path import dirname, join

def get_args():
    parser = argparse.ArgumentParser(description="Update configuration files")
    parser.add_argument('--cfg-filepath', type=str, required=True,
        help="Filepath to target configuration file")
    parser.add_argument('--lang-code', type=str, required=True, 
        help="Language code to update target configuration file with")
    return parser.parse_args()


def main():
    args = get_args()
    lang = args.lang_code

    with open(args.cfg_filepath, "r") as f:
        lines = f.read().splitlines()

    out_folder = None
    # Replaces all instances of 
    updating_test_lab_files = False
    for idx, line in enumerate(lines):
        # Update prediction folder
        if line.startswith("pred_folder"):
            lines[idx] = "pred_folder = pred_{}".format(lang)
        # Update output folder
        if line.startswith("out_folder"):
            pattern = re.compile(r'.*(exp.*)')
            print(line)
            m = pattern.match(line)
            root_exp_dir = m.group(1)

        # Only update lab_files for architecture 3
        if updating_test_lab_files:
            pattern = re.compile(r'.*\/(.*)_only\/')
            m = pattern.match(line)
            if m is not None:
                old_lang = m.group(1)
                old_str = "{}_only".format(old_lang)
                new_str = "{}_only".format(lang)
                lines[idx] = line.replace(old_str, new_str)
            # Stop updating at "n_chunks" which is at the end of the test lab files
            if line.startswith("n_chunks"):
                lines[idx] = "n_chunks = 10"
                updating_test_lab_files = False
        
        if "dataset3" in line:
            updating_test_lab_files = True

    with open(args.cfg_filepath, "w") as f:
        for line in lines:
            f.write(line + "\n")

    # Root pytorch_kaldi dir is e.g/ pytorch-kaldi/cfg/UPM/cfg_filepath
    pytorch_kaldi_dir = dirname(dirname(dirname(args.cfg_filepath)))
    exp_files_dir = join(pytorch_kaldi_dir, root_exp_dir, "exp_files")

    forward_files = [x for x in os.listdir(exp_files_dir) if x.startswith("forward")]
    # Delete any existing files for forwarding data
    for filename in forward_files:
        filepath = join(exp_files_dir, filename)
        os.remove(filepath)

if __name__ == "__main__":
    main()
