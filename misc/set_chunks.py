import os, sys, argparse, math
from os.path import join, basename, exists, dirname
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper

def get_args():
    parser = argparse.ArgumentParser(description="Making phone feature vector map")
    parser.add_argument('--cfg-filename', type=str, required=True,
        help="Filepath to UPM_xxx_.cfg.")
    parser.add_argument('--exp-data-dir', type=str, required=True,
        help="Path to directory containing \"train\", \"val\" and \"test\" data folders")
    return parser.parse_args()

# Get indices for where to write n_chunks lines for train/val/test
def get_writing_indices(cfg_filepath):
    idx_dict = {}
    with open(cfg_filepath, "r") as f:
        lines = f.read().splitlines()
        for dataset in [("train", "1"), ("val", "2"), ("test", "3")]:
            for idx, line in enumerate(lines):
                # Dataset should be labelled as [dataset1] for training etc
                if line == "[dataset{}]".format(dataset[1]):
                    # Search for next occurence of "n_chunks"
                    for idx2, line2 in enumerate(lines[idx+1:]):
                        if "n_chunks" in line2:
                            idx_dict[dataset[0]] = idx2 + idx + 1
                            break
    return idx_dict

def get_n_chunks(datapath, hours_per_chunk=1.0):
    
    total_length = 0
    num_lines = 0
    with open(datapath, "r") as f:
        for line in f:
            # Lines are of the format: utt_ID time
            time = float(line.split()[1])
            total_length += time
            num_lines += 1

    n_hours = total_length / 3600
    # Divide by 10 (to allow rounding up), then divide by hours_per_chunk and multiply the ceiling by 10 for a round number
    rounded = str(int(math.ceil(n_hours / 10.0 / hours_per_chunk) * 10))

    return rounded


def write_to_cfg_file(cfg_filepath, chunks_dict, idx_dict):
    with open(cfg_filepath, "r") as f:
        lines = f.readlines()
    
    for dataset, n_chunks in chunks_dict.items():
        line_idx = idx_dict[dataset]
        lines[line_idx] = "n_chunks = {}\n".format(n_chunks)
        print("Wrote {} chunks for {}".format(n_chunks, dataset))

    with open(cfg_filepath, "w") as f:
        f.writelines(lines)


def main():
    
    # Parse arguments and check all filepaths exist as expected
    #----------------------------------------------------
    args = get_args()
    cfg_filepath = join(global_vars.pytorch_kaldi_dir, "cfg", "UPM", args.cfg_filename)
    assert exists(cfg_filepath), "Configuration file not found at {}".format(cfg_filepath)

    datasets = ["train", "val", "test"]
    # Datapaths are tuples of ("train", "path/to/train/utt2len") etc.
    datapaths = [(x, join(args.exp_data_dir, x, "utt2len")) for x in datasets]

    for datapath in datapaths:
        assert(exists(datapath[1])), "Error: could not find{}".format(datapath[1])
    #----------------------------------------------------

    chunks_dict = {}
    for datapath in datapaths:
        n_chunks = get_n_chunks(datapath[1])
        chunks_dict[datapath[0]] = n_chunks

    idx_dict = get_writing_indices(cfg_filepath)
    

    write_to_cfg_file(cfg_filepath, chunks_dict, idx_dict)



    
    

if __name__ == "__main__":
    main()