from os.path import join, expanduser

home_dir = expanduser("~")
gp_dir = join(home_dir, "global_phone")
all_tr_dir = join(gp_dir, "all_transcripts")
exp_dir = join(home_dir, "upm_exp")
upm_dir = join(home_dir, "UPM")
wav_dir = join(home_dir, "gp_wav")
conf_dir = join(upm_dir, "conf")
log_dir = join(upm_dir, "logs")
