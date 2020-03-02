import os, sys
from os.path import join, exists
sys.path.insert(1, join(sys.path[0], '..'))
import global_vars
import py_helper_functions as helper

def main():
    expname = "new_exp"
    exp_dir = join(global_vars.exp_dir, expname)
    write_path = join(exp_dir, "results_summary.txt")
    with open(write_path, "w") as f:
            f.write("Results summary:\n")
    all_exps = os.listdir(exp_dir)
    all_results = []
    for exp in all_exps:
        wer_path = join(exp_dir, exp, "decode_val", "scoring_kaldi", "best_wer")
        if exists(wer_path):
            print("Found results for {}".format(exp))
            with open(wer_path, "r") as f:
                lines = f.read()
            all_results.append(exp + " " + lines)
    all_results.sort()
    for result in all_results:
        with open(write_path, "a") as f:
            f.write(result)


if __name__ == "__main__":
    main()