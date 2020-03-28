##########################################################
# pytorch-kaldi v.0.1
# Mirco Ravanelli, Titouan Parcollet
# Mila, University of Montreal
# October 2018
##########################################################

import sys
import configparser
import os
from utils import is_sequential_dict, model_init, optimizer_init, forward_model, progress
from data_io import load_counts
import numpy as np
import random
import torch
from distutils.util import strtobool
import time
import threading
import torch

from data_io import read_lab_fea, open_or_fd, write_mat
from utils import shift
from tqdm import tqdm

def read_next_chunk_into_shared_list_with_subprocess(
    read_lab_fea, shared_list, cfg_file, is_production, output_folder, wait_for_process, articulatory_feats, articulatory_feat_dim
):
    p = threading.Thread(target=read_lab_fea, args=(cfg_file, is_production, shared_list, output_folder, articulatory_feats, articulatory_feat_dim))
    p.start()
    if wait_for_process:
        p.join()
        return None
    else:
        return p


def extract_data_from_shared_list(shared_list):
    data_name = shared_list[0]
    data_end_index_fea = shared_list[1]
    data_end_index_lab = shared_list[2]
    fea_dict = shared_list[3]
    lab_dict = shared_list[4]
    arch_dict = shared_list[5]
    data_set = shared_list[6]
    return data_name, data_end_index_fea, data_end_index_lab, fea_dict, lab_dict, arch_dict, data_set


def convert_numpy_to_torch(data_set_dict, save_gpumem, use_cuda):
    if not (save_gpumem) and use_cuda:
        data_set_inp = torch.from_numpy(data_set_dict["input"]).float().cuda()
        data_set_ref = torch.from_numpy(data_set_dict["ref"]).float().cuda()
    else:
        data_set_inp = torch.from_numpy(data_set_dict["input"]).float()
        data_set_ref = torch.from_numpy(data_set_dict["ref"]).float()
    data_set_ref = data_set_ref.view((data_set_ref.shape[0], 1))
    return data_set_inp, data_set_ref


def run_nn_refac01(
    data_name, data_set, data_end_index, fea_dict, lab_dict, arch_dict, cfg_file, processed_first, next_config_file
):
    def _read_chunk_specific_config(cfg_file):
        if not (os.path.exists(cfg_file)):
            sys.stderr.write("ERROR: The config file %s does not exist!\n" % (cfg_file))
            sys.exit(0)
        else:
            config = configparser.ConfigParser()
            config.read(cfg_file)
        return config

    def _get_batch_size_from_config(config, to_do):
        if to_do == "train":
            batch_size = int(config["batches"]["batch_size_train"])
        elif to_do == "valid":
            batch_size = int(config["batches"]["batch_size_valid"])
        elif to_do == "forward":
            batch_size = 1
        return batch_size

    def _initialize_random_seed(config):
        seed = int(config["exp"]["seed"])
        torch.manual_seed(seed)
        random.seed(seed)
        np.random.seed(seed)

    def _load_model_and_optimizer(fea_dict, model, config, arch_dict, use_cuda, multi_gpu, to_do):
        inp_out_dict = fea_dict
        nns, costs = model_init(inp_out_dict, model, config, arch_dict, use_cuda, multi_gpu, to_do)
        optimizers = optimizer_init(nns, config, arch_dict)
        for net in nns.keys():
            pt_file_arch = config[arch_dict[net][0]]["arch_pretrain_file"]
            if pt_file_arch != "none":
                if use_cuda:
                    checkpoint_load = torch.load(pt_file_arch)
                else:
                    checkpoint_load = torch.load(pt_file_arch, map_location="cpu")
                nns[net].load_state_dict(checkpoint_load["model_par"])
                if net in optimizers:
                    optimizers[net].load_state_dict(checkpoint_load["optimizer_par"])
                    optimizers[net].param_groups[0]["lr"] = float(
                        config[arch_dict[net][0]]["arch_lr"]
                    )  # loading lr of the cfg file for pt
            if multi_gpu:
                nns[net] = torch.nn.DataParallel(nns[net])
        return nns, costs, optimizers, inp_out_dict

    def _open_forward_output_files_and_get_file_handles(forward_outs, require_decodings, info_file, output_folder):
        post_file = {}
        for out_id in range(len(forward_outs)):
            if require_decodings[out_id]:
                out_file = info_file.replace(".info", "_" + forward_outs[out_id] + "_to_decode.ark")
            else:
                out_file = info_file.replace(".info", "_" + forward_outs[out_id] + ".ark")
            post_file[forward_outs[out_id]] = open_or_fd(out_file, output_folder, "wb")
        return post_file

    def _get_batch_config(data_set_input, seq_model, to_do, data_name, batch_size):
        N_snt = None
        N_ex_tr = None
        N_batches = None
        if seq_model or to_do == "forward":
            N_snt = len(data_name)
            N_batches = int(N_snt / batch_size)
        else:
            N_ex_tr = data_set_input.shape[0]
            N_batches = int(N_ex_tr / batch_size)
        return N_snt, N_ex_tr, N_batches

    def _prepare_input(
        snt_index,
        batch_size,
        inp_dim,
        ref_dim,
        beg_snt_fea,
        beg_snt_lab,
        data_end_index_fea,
        data_end_index_lab,
        beg_batch,
        end_batch,
        seq_model,
        arr_snt_len_fea,
        arr_snt_len_lab,
        data_set_inp,
        data_set_ref,
        use_cuda,
    ):
        def _zero_padding(
            inp,
            ref,
            max_len_fea,
            max_len_lab,
            data_end_index_fea,
            data_end_index_lab,
            data_set_inp,
            data_set_ref,
            beg_snt_fea,
            beg_snt_lab,
            snt_index,
            k,
        ):
            def _input_and_ref_have_same_time_dimension(N_zeros_fea, N_zeros_lab):
                if N_zeros_fea == N_zeros_lab:
                    return True
                return False

            snt_len_fea = data_end_index_fea[snt_index] - beg_snt_fea
            snt_len_lab = data_end_index_lab[snt_index] - beg_snt_lab
            N_zeros_fea = max_len_fea - snt_len_fea
            N_zeros_lab = max_len_lab - snt_len_lab
            if _input_and_ref_have_same_time_dimension(N_zeros_fea, N_zeros_lab):
                N_zeros_fea_left = random.randint(0, N_zeros_fea)
                N_zeros_lab_left = N_zeros_fea_left
            else:
                N_zeros_fea_left = 0
                N_zeros_lab_left = 0
            inp[N_zeros_fea_left : N_zeros_fea_left + snt_len_fea, k, :] = data_set_inp[
                beg_snt_fea : beg_snt_fea + snt_len_fea, :
            ]
            ref[N_zeros_lab_left : N_zeros_lab_left + snt_len_lab, k, :] = data_set_ref[
                beg_snt_lab : beg_snt_lab + snt_len_lab, :
            ]
            return inp, ref, snt_len_fea, snt_len_lab

        if len(data_set_ref.shape) == 1:
            data_set_ref = data_set_ref.shape.view((data_set_ref.shape[0], 1))
        max_len = 0
        if seq_model:
            max_len_fea = int(max(arr_snt_len_fea[snt_index : snt_index + batch_size]))
            max_len_lab = int(max(arr_snt_len_lab[snt_index : snt_index + batch_size]))
            inp = torch.zeros(max_len_fea, batch_size, inp_dim).contiguous()
            ref = torch.zeros(max_len_lab, batch_size, ref_dim).contiguous()
            for k in range(batch_size):
                inp, ref, snt_len_fea, snt_len_lab = _zero_padding(
                    inp,
                    ref,
                    max_len_fea,
                    max_len_lab,
                    data_end_index_fea,
                    data_end_index_lab,
                    data_set_inp,
                    data_set_ref,
                    beg_snt_fea,
                    beg_snt_lab,
                    snt_index,
                    k,
                )
                beg_snt_fea = data_end_index_fea[snt_index]
                beg_snt_lab = data_end_index_lab[snt_index]
                snt_index = snt_index + 1
        else:
            if to_do != "forward":
                inp = data_set[beg_batch:end_batch, :].contiguous()
            else:
                snt_len_fea = data_end_index_fea[snt_index] - beg_snt_fea
                snt_len_lab = data_end_index_lab[snt_index] - beg_snt_lab
                inp = data_set_inp[beg_snt_fea : beg_snt_fea + snt_len_fea, :].contiguous()
                ref = data_set_ref[beg_snt_lab : beg_snt_lab + snt_len_lab, :].contiguous()
                beg_snt_fea = data_end_index_fea[snt_index]
                beg_snt_lab = data_end_index_lab[snt_index]
                snt_index = snt_index + 1
        if use_cuda:
            inp = inp.cuda()
            ref = ref.cuda()
        return inp, ref, max_len_fea, max_len_lab, snt_len_fea, snt_len_lab, beg_snt_fea, beg_snt_lab, snt_index

    def _optimization_step(optimizers, outs_dict, config, arch_dict):
        for opt in optimizers.keys():
            optimizers[opt].zero_grad()
        outs_dict["loss_final"].backward()
        for opt in optimizers.keys():
            if not (strtobool(config[arch_dict[opt][0]]["arch_freeze"])):
                optimizers[opt].step()

    def _update_progress_bar(to_do, i, N_batches, loss_sum):
        if to_do == "train":
            status_string = (
                "Training | (Batch "
                + str(i + 1)
                + "/"
                + str(N_batches)
                + ")"
                + " | L:"
                + str(round(loss_sum.cpu().item() / (i + 1), 3))
            )
            if i == N_batches - 1:
                status_string = "Training | (Batch " + str(i + 1) + "/" + str(N_batches) + ")"
        if to_do == "valid":
            status_string = "Validating | (Batch " + str(i + 1) + "/" + str(N_batches) + ")"
        if to_do == "forward":
            status_string = "Forwarding | (Batch " + str(i + 1) + "/" + str(N_batches) + ")"
        progress(i, N_batches, status=status_string)

    def _write_info_file(info_file, to_do, loss_tot, err_tot, elapsed_time_chunk):
        with open(info_file, "w") as text_file:
            text_file.write("[results]\n")
            if to_do != "forward":
                text_file.write("loss=%s\n" % loss_tot.cpu().numpy())
                text_file.write("err=%s\n" % err_tot.cpu().numpy())
            text_file.write("elapsed_time_chunk=%f\n" % elapsed_time_chunk)
        text_file.close()

    def _save_model(to_do, nns, multi_gpu, optimizers, info_file, arch_dict):
        if to_do == "train":
            for net in nns.keys():
                checkpoint = {}
                if multi_gpu:
                    checkpoint["model_par"] = nns[net].module.state_dict()
                else:
                    checkpoint["model_par"] = nns[net].state_dict()
                if net in optimizers:
                    checkpoint["optimizer_par"] = optimizers[net].state_dict()
                else:
                    checkpoint["optimizer_par"] = dict()
                out_file = info_file.replace(".info", "_" + arch_dict[net][0] + ".pkl")
                torch.save(checkpoint, out_file)

    def _get_dim_from_data_set(data_set_inp, data_set_ref):
        inp_dim = data_set_inp.shape[1]
        ref_dim = 1
        if len(data_set_ref.shape) > 1:
            ref_dim = data_set_ref.shape[1]
        return inp_dim, ref_dim

    from data_io import read_lab_fea_refac01 as read_lab_fea
    from utils import forward_model_refac01 as forward_model

    config = _read_chunk_specific_config(cfg_file)
    _initialize_random_seed(config)

    output_folder = config["exp"]["out_folder"]
    use_cuda = strtobool(config["exp"]["use_cuda"])
    multi_gpu = strtobool(config["exp"]["multi_gpu"])
    to_do = config["exp"]["to_do"]
    info_file = config["exp"]["out_info"]
    model = config["model"]["model"].split("\n")
    forward_outs = config["forward"]["forward_out"].split(",")
    forward_normalize_post = list(map(strtobool, config["forward"]["normalize_posteriors"].split(",")))
    forward_count_files = config["forward"]["normalize_with_counts_from"].split(",")
    require_decodings = list(map(strtobool, config["forward"]["require_decoding"].split(",")))
    save_gpumem = strtobool(config["exp"]["save_gpumem"])
    is_production = strtobool(config["exp"]["production"])
    batch_size = _get_batch_size_from_config(config, to_do)

    if processed_first:
        shared_list = list()
        p = read_next_chunk_into_shared_list_with_subprocess(
            read_lab_fea, shared_list, cfg_file, is_production, output_folder, wait_for_process=True
        )
        data_name, data_end_index_fea, data_end_index_lab, fea_dict, lab_dict, arch_dict, data_set_dict = extract_data_from_shared_list(
            shared_list
        )
        data_set_inp, data_set_ref = convert_numpy_to_torch(data_set_dict, save_gpumem, use_cuda)
    else:
        data_set_inp = data_set["input"]
        data_set_ref = data_set["ref"]
        data_end_index_fea = data_end_index["fea"]
        data_end_index_lab = data_end_index["lab"]
    shared_list = list()
    data_loading_process = None
    if not next_config_file is None:
        data_loading_process = read_next_chunk_into_shared_list_with_subprocess(
            read_lab_fea, shared_list, next_config_file, is_production, output_folder, wait_for_process=False
        )
    nns, costs, optimizers, inp_out_dict = _load_model_and_optimizer(
        fea_dict, model, config, arch_dict, use_cuda, multi_gpu, to_do
    )
    if to_do == "forward":
        post_file = _open_forward_output_files_and_get_file_handles(
            forward_outs, require_decodings, info_file, output_folder
        )

    seq_model = is_sequential_dict(config, arch_dict)
    N_snt, N_ex_tr, N_batches = _get_batch_config(data_set_inp, seq_model, to_do, data_name, batch_size)
    beg_batch = 0
    end_batch = batch_size
    snt_index = 0
    beg_snt_fea = 0
    beg_snt_lab = 0
    arr_snt_len_fea = shift(shift(data_end_index_fea, -1, 0) - data_end_index_fea, 1, 0)
    arr_snt_len_lab = shift(shift(data_end_index_lab, -1, 0) - data_end_index_lab, 1, 0)
    arr_snt_len_fea[0] = data_end_index_fea[0]
    arr_snt_len_lab[0] = data_end_index_lab[0]
    data_set_inp_dim, data_set_ref_dim = _get_dim_from_data_set(data_set_inp, data_set_ref)
    inp_dim = data_set_inp_dim + data_set_ref_dim
    loss_sum = 0
    err_sum = 0
    start_time = time.time()
    for i in range(N_batches):
        inp, ref, max_len_fea, max_len_lab, snt_len_fea, snt_len_lab, beg_snt_fea, beg_snt_lab, snt_index = _prepare_input(
            snt_index,
            batch_size,
            data_set_inp_dim,
            data_set_ref_dim,
            beg_snt_fea,
            beg_snt_lab,
            data_end_index_fea,
            data_end_index_lab,
            beg_batch,
            end_batch,
            seq_model,
            arr_snt_len_fea,
            arr_snt_len_lab,
            data_set_inp,
            data_set_ref,
            use_cuda,
        )
        if to_do == "train":
            outs_dict = forward_model(
                fea_dict,
                lab_dict,
                arch_dict,
                model,
                nns,
                costs,
                inp,
                ref,
                inp_out_dict,
                max_len_fea,
                max_len_lab,
                batch_size,
                to_do,
                forward_outs,
            )
            _optimization_step(optimizers, outs_dict, config, arch_dict)
        else:
            with torch.no_grad():
                outs_dict = forward_model(
                    fea_dict,
                    lab_dict,
                    arch_dict,
                    model,
                    nns,
                    costs,
                    inp,
                    ref,
                    inp_out_dict,
                    max_len_fea,
                    max_len_lab,
                    batch_size,
                    to_do,
                    forward_outs,
                )
        if to_do == "forward":
            for out_id in range(len(forward_outs)):
                out_save = outs_dict[forward_outs[out_id]].data.cpu().numpy()
                if forward_normalize_post[out_id]:
                    counts = load_counts(forward_count_files[out_id])
                    out_save = out_save - np.log(counts / np.sum(counts))
                write_mat(output_folder, post_file[forward_outs[out_id]], out_save, data_name[i])
        else:
            loss_sum = loss_sum + outs_dict["loss_final"].detach()
            err_sum = err_sum + outs_dict["err_final"].detach()
        beg_batch = end_batch
        end_batch = beg_batch + batch_size
        _update_progress_bar(to_do, i, N_batches, loss_sum)
    elapsed_time_chunk = time.time() - start_time
    loss_tot = loss_sum / N_batches
    err_tot = err_sum / N_batches
    del inp, ref, outs_dict, data_set_inp_dim, data_set_ref_dim
    _save_model(to_do, nns, multi_gpu, optimizers, info_file, arch_dict)
    if to_do == "forward":
        for out_name in forward_outs:
            post_file[out_name].close()
    _write_info_file(info_file, to_do, loss_tot, err_tot, elapsed_time_chunk)
    if not data_loading_process is None:
        data_loading_process.join()
        data_name, data_end_index_fea, data_end_index_lab, fea_dict, lab_dict, arch_dict, data_set_dict = extract_data_from_shared_list(
            shared_list
        )
        data_set_inp, data_set_ref = convert_numpy_to_torch(data_set_dict, save_gpumem, use_cuda)
        data_set = {"input": data_set_inp, "ref": data_set_ref}
        data_end_index = {"fea": data_end_index_fea, "lab": data_end_index_lab}
        return [data_name, data_set, data_end_index, fea_dict, lab_dict, arch_dict]
    else:
        return [None, None, None, None, None, None]


def run_nn(
    data_name, data_set, data_end_index, fea_dict, lab_dict, arch_dict, cfg_file, processed_first, next_config_file,
    articulatory_feats, articulatory_feat_dim):

    # This function processes the current chunk using the information in cfg_file. In parallel, the next chunk is load into the CPU memory

    # Reading chunk-specific cfg file (first argument-mandatory file)
    if not (os.path.exists(cfg_file)):
        sys.stderr.write("ERROR: The config file %s does not exist!\n" % (cfg_file))
        sys.exit(0)
    else:
        config = configparser.ConfigParser()
        config.read(cfg_file)

    # Setting torch seed
    seed = int(config["exp"]["seed"])
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    # Reading config parameters
    output_folder = config["exp"]["out_folder"]
    use_cuda = strtobool(config["exp"]["use_cuda"])
    multi_gpu = strtobool(config["exp"]["multi_gpu"])

    to_do = config["exp"]["to_do"]
    info_file = config["exp"]["out_info"]

    model = config["model"]["model"].split("\n")

    forward_outs = config["forward"]["forward_out"].split(",")
    forward_normalize_post = list(map(strtobool, config["forward"]["normalize_posteriors"].split(",")))
    forward_count_files = config["forward"]["normalize_with_counts_from"].split(",")
    require_decodings = list(map(strtobool, config["forward"]["require_decoding"].split(",")))

    use_cuda = strtobool(config["exp"]["use_cuda"])
    save_gpumem = strtobool(config["exp"]["save_gpumem"])
    is_production = strtobool(config["exp"]["production"])

    if to_do == "train":
        batch_size = int(config["batches"]["batch_size_train"])

    if to_do == "valid":
        batch_size = int(config["batches"]["batch_size_valid"])

    if to_do == "forward":
        batch_size = 1

    # ***** Reading the Data********
    if processed_first:

        # Reading all the features and labels for this chunk
        shared_list = []

        p = threading.Thread(target=read_lab_fea, args=(cfg_file, is_production, shared_list, output_folder, articulatory_feats, articulatory_feat_dim))
        p.start()
        p.join()

        data_name = shared_list[0]
        data_end_index = shared_list[1]
        fea_dict = shared_list[2]
        lab_dict = shared_list[3]
        arch_dict = shared_list[4]
        data_set = shared_list[5]
        # fea_dict = e.g. {'mfcc': ['mfcc', 'exp/UPM_MLP_mfcc/exp_files/train_TIMIT_tr_ep00_ck0_mfcc.lst', 
        # 'apply-cmvn --utt2spk=ark:/home/paul/upm_exp/new_exp/data/train/utt2spk  
        # ark:/home/paul/gp_feats/mfcc/cmvn_train.ark ark:- ark:- 
        # | add-deltas --delta-order=2 ark:- ark:- |', '0', '0', 0, 69, 69]}

        # lab_dict = e.g. {'lab_mono': ['lab_mono', '/home/paul/upm_exp/new_exp/tri1_ali_train', 
        # 'ali-to-phones --per-frame=true', 69], 
        # 'lab_cd': ['lab_cd', '/home/paul/upm_exp/new_exp/tri1_ali_train', 'ali-to-pdf', 70]}

        # data_set = e.g. [[-2.42053270e+00 -1.84184778e+00  1.24067259e+00 ...  2.51362473e-01
        #    0.00000000e+00  9.60000000e+01]
        #  [-8.00050020e-01 -6.89594567e-01 -8.63680318e-02 ...  4.10112813e-02
        #    0.00000000e+00  9.50000000e+01]
        #  [ 9.68045533e-01  1.39045298e+00  4.92768027e-02 ... -7.87360191e-01
        #    6.10000000e+01  1.15600000e+03]
        #  ...
        #  [ 4.89345729e-01  6.06023490e-01  2.83024579e-01 ... -1.82384717e+00
        #    6.00000000e+00  4.14000000e+02]
        #  [ 4.45853412e-01  1.45813584e+00  1.52251995e+00 ...  9.27292585e-01
        #    8.30000000e+01  5.27000000e+02]
        #  [-2.57786417e+00 -8.25788319e-01 -1.24043882e+00 ... -8.90156806e-01
        #    0.00000000e+00  0.00000000e+00]]
        # shape = e.g. (2168739, 71)
        # second dim = #dimensions of features (usually 69) + #dimensions of targets e.g. 1 for single numbers
        
        # converting numpy tensors into pytorch tensors and put them on GPUs if specified
        if not (save_gpumem) and use_cuda:
            data_set = torch.from_numpy(data_set).float().cuda()
        else:
            data_set = torch.from_numpy(data_set).float()

    # Reading all the features and labels for the next chunk
    shared_list = []
    p = threading.Thread(target=read_lab_fea, args=(next_config_file, is_production, shared_list, output_folder, articulatory_feats, articulatory_feat_dim))
    p.start()

    # Reading model and initialize networks
    inp_out_dict = fea_dict

    [nns, costs] = model_init(inp_out_dict, model, config, arch_dict, use_cuda, multi_gpu, to_do)

    # optimizers initialization
    optimizers = optimizer_init(nns, config, arch_dict)

    # pre-training and multi-gpu init
    for net in nns.keys():
        pt_file_arch = config[arch_dict[net][0]]["arch_pretrain_file"]

        if pt_file_arch != "none":
            if use_cuda:
                checkpoint_load = torch.load(pt_file_arch)
            else:
                checkpoint_load = torch.load(pt_file_arch, map_location="cpu")
            nns[net].load_state_dict(checkpoint_load["model_par"])
            optimizers[net].load_state_dict(checkpoint_load["optimizer_par"])
            optimizers[net].param_groups[0]["lr"] = float(
                config[arch_dict[net][0]]["arch_lr"]
            )  # loading lr of the cfg file for pt

        if multi_gpu:
            nns[net] = torch.nn.DataParallel(nns[net])

    if to_do == "forward":

        post_file = {}
        for out_id in range(len(forward_outs)):
            if require_decodings[out_id]:
                out_file = info_file.replace(".info", "_" + forward_outs[out_id] + "_to_decode.ark")
            else:
                out_file = info_file.replace(".info", "_" + forward_outs[out_id] + ".ark")
            post_file[forward_outs[out_id]] = open_or_fd(out_file, output_folder, "wb")

    # check automatically if the model is sequential
    seq_model = is_sequential_dict(config, arch_dict)

    # ***** Minibatch Processing loop********
    if seq_model or to_do == "forward":
        N_snt = len(data_name)
        N_batches = int(N_snt / batch_size)
    else:
        N_ex_tr = data_set.shape[0]
        N_batches = int(N_ex_tr / batch_size)

    beg_batch = 0
    end_batch = batch_size

    snt_index = 0
    beg_snt = 0

    start_time = time.time()

    # array of sentence lengths
    arr_snt_len = shift(shift(data_end_index, -1, 0) - data_end_index, 1, 0)
    arr_snt_len[0] = data_end_index[0]

    loss_sum = 0
    err_sum = 0

    inp_dim = data_set.shape[1]

    for i in tqdm(range(N_batches)):

        max_len = 0

        if seq_model:

            max_len = int(max(arr_snt_len[snt_index : snt_index + batch_size]))
            inp = torch.zeros(max_len, batch_size, inp_dim).contiguous()

            for k in range(batch_size):

                snt_len = data_end_index[snt_index] - beg_snt

                # Removed since we have silence already
                N_zeros = max_len - snt_len

                # Appending a random number of initial zeros, tge others are at the end.
                N_zeros_left = random.randint(0, N_zeros)

                # randomizing could have a regularization effect
                inp[N_zeros_left : N_zeros_left + snt_len, k, :] = data_set[beg_snt : beg_snt + snt_len, :]
                

                beg_snt = data_end_index[snt_index]
                snt_index = snt_index + 1

        else:
            # features and labels for batch i
            if to_do != "forward":
                inp = data_set[beg_batch:end_batch, :].contiguous()
            else:
                snt_len = data_end_index[snt_index] - beg_snt
                inp = data_set[beg_snt : beg_snt + snt_len, :].contiguous()
                beg_snt = data_end_index[snt_index]
                snt_index = snt_index + 1

        # use cuda (this is working correctly)
        if use_cuda:
            inp = inp.cuda()

        if to_do == "train":
            # Forward input, with autograd graph active
            outs_dict = forward_model(
                fea_dict,
                lab_dict,
                arch_dict,
                model,
                nns,
                costs,
                inp,
                inp_out_dict,
                max_len,
                batch_size,
                to_do,
                forward_outs,
            )
            # Typical outs_dict:
            #         {'mfcc': tensor([[-2.4205, -1.8418,  1.2407,  ..., -0.0312,  0.9050,  0.2514],
            #     [-0.8001, -0.6896, -0.0864,  ...,  0.7128, -0.8012,  0.0410],
            #     [ 0.9680,  1.3905,  0.0493,  ...,  0.7868,  0.0306, -0.7874],
            #     ...,
            #     [ 1.3547,  0.8892,  0.5201,  ..., -0.1310, -0.2404,  2.5091],
            #     [-0.2628, -0.6329, -0.5910,  ...,  0.9764,  0.9203,  0.7786],
            #     [ 0.8450,  0.7046, -0.1917,  ...,  0.8781,  1.7115, -0.0939]],
            #    device='cuda:0'), 
            # 'out_dnn1': tensor([[0.0000, 0.1956, 0.1375,  ..., 0.0000, 0.3268, 0.0000],
            #     [0.0652, 0.4445, 2.3319,  ..., 0.0000, 0.0000, 0.0000],
            #     [0.0000, 0.0000, 0.0000,  ..., 0.0000, 0.0000, 0.0000],
            #     ...,
            #     [0.0000, 0.0896, 0.0000,  ..., 0.0000, 0.0000, 0.0000],
            #     [0.0000, 0.3323, 0.0000,  ..., 0.0000, 0.7390, 0.0000],
            #     [0.0643, 0.6104, 1.3655,  ..., 0.0000, 2.6829, 0.0000]],
            #    device='cuda:0', grad_fn=<FusedDropoutBackward>), 
            # 'out_dnn2': tensor([[-7.3100, -7.2961, -7.3049,  ..., -7.3618, -7.2981, -7.3452],
            #     [-7.3010, -7.3313, -7.3071,  ..., -7.3272, -7.3142, -7.3168],
            #     [-7.3519, -7.3171, -7.3098,  ..., -7.3399, -7.3214, -7.3125],
            #     ...,
            #     [-7.3620, -7.3274, -7.3316,  ..., -7.3163, -7.2775, -7.2797],
            #     [-7.3170, -7.2884, -7.3127,  ..., -7.3345, -7.3273, -7.3099],
            #     [-7.3273, -7.3018, -7.2763,  ..., -7.3198, -7.3555, -7.3646]],
            #    device='cuda:0', grad_fn=<LogSoftmaxBackward>), 
            # 'out_dnn3': tensor([[-4.5139, -4.5083, -4.5078,  ..., -4.5343, -4.5538, -4.6107],
            #     [-4.5301, -4.5042, -4.5536,  ..., -4.5492, -4.5570, -4.5964],
            #     [-4.5492, -4.5174, -4.5372,  ..., -4.5537, -4.5516, -4.5888],
            #     ...,
            #     [-4.4708, -4.4924, -4.6887,  ..., -4.5791, -4.5091, -4.5094],
            #     [-4.5106, -4.4888, -4.5453,  ..., -4.5565, -4.5538, -4.5629],
            #     [-4.5760, -4.4163, -4.6699,  ..., -4.5613, -4.5054, -4.5784]],
            #    device='cuda:0', grad_fn=<LogSoftmaxBackward>), 
            # 'loss_mono': tensor(4.5379, device='cuda:0', grad_fn=<NllLossBackward>), 
            # 'loss_mono_w': tensor(4.5379, device='cuda:0', grad_fn=<MulBackward0>), 
            # 'loss_cd': tensor(7.3148, device='cuda:0', grad_fn=<NllLossBackward>), 
            # 'loss_final': tensor(11.8528, device='cuda:0', grad_fn=<AddBackward0>), 
            # 'err_final': tensor(1., device='cuda:0')}

            for opt in optimizers.keys():
                optimizers[opt].zero_grad()

            outs_dict["loss_final"].backward()

            # Gradient Clipping (th 0.1)
            for net in nns.keys():
               torch.nn.utils.clip_grad_norm_(nns[net].parameters(), 0.1)

            for opt in optimizers.keys():
                if not (strtobool(config[arch_dict[opt][0]]["arch_freeze"])):
                    optimizers[opt].step()
        else:
            with torch.no_grad():  # Forward input without autograd graph (save memory)
                outs_dict = forward_model(
                    fea_dict,
                    lab_dict,
                    arch_dict,
                    model,
                    nns,
                    costs,
                    inp,
                    inp_out_dict,
                    max_len,
                    batch_size,
                    to_do,
                    forward_outs,
                )

        if to_do == "forward":
            for out_id in range(len(forward_outs)):

                out_save = outs_dict[forward_outs[out_id]].data.cpu().numpy()

                if forward_normalize_post[out_id]:
                    # read the config file
                    counts = load_counts(forward_count_files[out_id])
                    out_save = out_save - np.log(counts / np.sum(counts))

                # save the output
                write_mat(output_folder, post_file[forward_outs[out_id]], out_save, data_name[i])
        else:
            loss_sum = loss_sum + outs_dict["loss_final"].detach()
            err_sum = err_sum + outs_dict["err_final"].detach()

        # update it to the next batch
        beg_batch = end_batch
        end_batch = beg_batch + batch_size

        # Progress bar
        # if to_do == "train":
        #     status_string = (
        #         "Training | (Batch "
        #         + str(i + 1)
        #         + "/"
        #         + str(N_batches)
        #         + ")"
        #         + " | L:"
        #         + str(round(loss_sum.cpu().item() / (i + 1), 3))
        #     )
        #     if i == N_batches - 1:
        #         status_string = "Training | (Batch " + str(i + 1) + "/" + str(N_batches) + ")"

        # if to_do == "valid":
        #     status_string = "Validating | (Batch " + str(i + 1) + "/" + str(N_batches) + ")"
        # if to_do == "forward":
        #     status_string = "Forwarding | (Batch " + str(i + 1) + "/" + str(N_batches) + ")"

        # progress(i, N_batches, status=status_string)

    elapsed_time_chunk = time.time() - start_time

    loss_tot = loss_sum / N_batches
    err_tot = err_sum / N_batches

    # clearing memory
    del inp, outs_dict, data_set

    # save the model
    if to_do == "train":

        for net in nns.keys():
            checkpoint = {}
            if multi_gpu:
                checkpoint["model_par"] = nns[net].module.state_dict()
            else:
                checkpoint["model_par"] = nns[net].state_dict()

            checkpoint["optimizer_par"] = optimizers[net].state_dict()

            out_file = info_file.replace(".info", "_" + arch_dict[net][0] + ".pkl")
            torch.save(checkpoint, out_file)

    if to_do == "forward":
        for out_name in forward_outs:
            post_file[out_name].close()

    # Write info file
    with open(info_file, "w") as text_file:
        text_file.write("[results]\n")
        if to_do != "forward":
            text_file.write("loss=%s\n" % loss_tot.cpu().numpy())
            text_file.write("err=%s\n" % err_tot.cpu().numpy())
        text_file.write("elapsed_time_chunk=%f\n" % elapsed_time_chunk)

    text_file.close()

    # Getting the data for the next chunk (read in parallel)
    p.join()
    data_name = shared_list[0]
    data_end_index = shared_list[1]
    fea_dict = shared_list[2]
    lab_dict = shared_list[3]
    arch_dict = shared_list[4]
    data_set = shared_list[5]
    
    # converting numpy tensors into pytorch tensors and put them on GPUs if specified
    if not (save_gpumem) and use_cuda:
        data_set = torch.from_numpy(data_set).float().cuda()
    else:
        data_set = torch.from_numpy(data_set).float()

    return [data_name, data_set, data_end_index, fea_dict, lab_dict, arch_dict]
