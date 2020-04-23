import numpy as np
import re, os, sys, argparse
from os.path import join, exists
sys.path.insert(1, join(sys.path[0], '..'))
import global_vars
from collections import defaultdict
from py_helper_functions import write_to_csv, listdir_fullpath

def get_args():
    parser = argparse.ArgumentParser(description="Getting loss info from exp files")
    parser.add_argument('--info-dir', type=str, required=True,
        help="Directory to exp files")
    parser.add_argument('--savename', type=str, required=True,
        help="What to save the CSV file as")
    return parser.parse_args()


def analyse_info_files(info_dir, savename=None):
    def _read_loss(info_file):
        with open(info_file, "r") as f:
            for line in f:
                if line.startswith("loss"):
                    return float(line[5:])
                
    def _get_mean_loss(info_dir, dataset):
        relevant_info = [x for x in listdir_fullpath(info_dir) if os.path.basename(x).startswith(dataset)]

        pattern = re.compile(r'.*ep(.{2})')
        d = defaultdict(list)
        for info in relevant_info:
            m = pattern.match(info)
            epoch = m.group(1)
            loss = _read_loss(info)
            d[epoch].append(loss)
        
        all_eps = []
        all_losses = []
        for key, losses in d.items():
            avg_loss = np.mean(losses)
            #print("Epoch: {} Mean loss: {}".format(key, avg_loss))
            all_eps.append(key)
            all_losses.append(avg_loss)
        
        return all_eps, all_losses
    
    def _join_lists(list_of_lists):
        list_start = list_of_lists[0]
        n = len(list_start)
        for list_i in list_of_lists[1:]:
            assert len(list_i) == n
            list_start = [str(a) +"," +str(b) for a, b in zip(list_start, list_i)]
            
        for idx, list_i in enumerate(list_start):
            list_start[idx] = list_i.split(",")
        return list_start
    
    eps, tr_losses = _get_mean_loss(info_dir, "train")
    val_eps, val_losses = _get_mean_loss(info_dir, "val")
    n = min(len(eps), len(val_eps))
    eps = eps[:n]
    val_eps = val_eps[:n]
    tr_losses = tr_losses[:n]
    val_losses = val_losses[:n]
    data = _join_lists([eps, tr_losses, val_losses])
    if savename is not None:
        header = ["ep", "tr_loss", "val_loss"]
        write_to_csv(savename, header, data, overwrite="True")

def main():
    args = get_args()
    analyse_info_files(args.info_dir, args.savename)

if __name__ == "__main__":
    main()