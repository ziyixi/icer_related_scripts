#!/usr/bin/env python
"""
This script should be run with having set the SSH keys.
"""
import argparse
import sh
import sys
from loguru import logger


class FLAG():
    """
    The class to store some global flags. These flags are used to control the output of the logs, or one log may appear multiple times.
    """
    gateway_flag = True
    notebook_flag = True
    url_flag = True


def check_args(args=None):
    """
    This function is used to parse the script args.
    """
    # ArgumentDefaultsHelpFormatter: display the default value.
    parser = argparse.ArgumentParser(
        description='A python script to run jupyter notebook on icer computing node and open it on localhost',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # specify the user, should be <user>@hpcc.msu.edu
    parser.add_argument('-u', '--user',
                        help='icer user name',
                        required=True,
                        default='xiziyi')
    # specify the time that will be used. Notice in developing node the time could only be 2 hours.
    parser.add_argument('-t', '--time',
                        help='time to use (not necessary when use computing node)',
                        required=False,
                        default='02:00:00')
    # specify the memory that will be used.
    parser.add_argument('-m', '--memory',
                        help='memory per core (not necessary when use computing node)',
                        required=False,
                        default='1G')
    # specify how many cores you want to use. (mainly for ipython parallel, which I will find a way to configure)
    # TODO ipython parallel
    parser.add_argument('-c', '--cores',
                        help='number of cores (not necessary when use computing node)',
                        required=False,
                        default='1')
    # which port you will use as the local port. (the same with the remote port at icer, and it's also the port jupyter notebook runs)
    parser.add_argument('-p', '--port',
                        help='port of the notebook',
                        required=False,
                        default='8789')
    # which directory the jupyter notebook will run. COULDN'T INCLUDE ~! (stupid shell's property)
    parser.add_argument('-d', '--directory',
                        help='directory to open the notebook',
                        required=False,
                        default='/mnt/home/xiziyi/')
    # whether to use the developing node or submit a job.
    parser.add_argument('-n', '--devnode',
                        help='just use the developing node without submitting a job',
                        dest='node',
                        action='store_true',
                        required=False)
    parser.add_argument('--no-devnode',
                        help='submit a job through salloc',
                        dest='node',
                        action='store_false',
                        required=False)
    parser.set_defaults(node=True)
    # whether use gpu or not.
    parser.add_argument('-g', '--gpu',
                        help='use gpu (should use dev-intel14-k20 or dev-intel16-k80)',
                        dest='gpu',
                        action='store_true',
                        required=False)
    parser.add_argument('--no-gpu',
                        help='not use gpu',
                        dest='gpu',
                        action='store_false',
                        required=False)
    parser.set_defaults(gpu=True)
    # which develop node you want to login.
    parser.add_argument('--develop_login',
                        help="developing node to use salloc command",
                        required=False,
                        default="dev-intel14-k20")
    results = parser.parse_args(args)
    return results


def ssh_interact_jupyter(char, stdin):
    """
    handle standard output when starting to run the jupyter notebook.
    """
    global global_status, parsed_args

    if("Last login" in char and FLAG.gateway_flag):
        logger.info(f"success in logging on icer gateway")
        FLAG.gateway_flag = False
    if("@dev" in char):
        logger.info(f"success in logging on the developing node")
    if("Address already in use" in char):
        logger.error("choose another port to use!")
    if(global_status["hostname"] and FLAG.notebook_flag):
        if("NotebookApp" in char):
            logger.info(
                f"success in starting jupyter notebook using the developing node")
            handle_ssh_tunnel()
            FLAG.notebook_flag = False


def ssh_interact_tunnel(char, stdin):
    """
    handle standard output when setting up th essh tunnel.
    """
    global global_status, parsed_args

    if(FLAG.url_flag):
        logger.success(f"use http://localhost:{parsed_args.port}")
        FLAG.url_flag = False


def handle_ssh_tunnel():
    """
    set ssh tunnel when having started the jupyter notebook.
    """
    global global_status, parsed_args

    sh.ssh("-4", "-t", "-Y",
           f"{parsed_args.user}@hpcc.msu.edu", "-L", f"{parsed_args.port}:localhost:{parsed_args.port}", "ssh", "-t", "-Y", global_status["hostname"], "-L", f"{parsed_args.port}:localhost:{parsed_args.port}", _out=ssh_interact_tunnel, _tty_in=True)


def logging_icer():
    """
    start jupyter notebook. (tasks to do after logging on the icer)
    """
    global global_status, parsed_args

    ssh_develop_node = f"ssh {parsed_args.develop_login}\n"
    salloc_job = f"salloc --time={parsed_args.time} -c {parsed_args.cores} --mem-per-cpu={parsed_args.memory}\n"
    handle_permission = f"export XDG_RUNTIME_DIR=''\n"
    cd_directory = f"cd {parsed_args.directory}\n"
    start_jupyter_notebook = f"jupyter notebook --NotebookApp.token='' --port={parsed_args.port}\n"
    load_gpu_module = f"module purge;module load CUDA/9.0.176 cuDNN/7.0.2-CUDA-9.0.176;module load GCC/5.4.0-2.26 OpenMPI/1.10.3;"
    to_sleep = f"sleep 1\n"
    logger.info(f"start to execute command on icer")
    if(parsed_args.gpu):
        if(not parsed_args.node):
            stdin_list = [to_sleep, ssh_develop_node, to_sleep, salloc_job,
                          handle_permission, load_gpu_module, cd_directory, start_jupyter_notebook]
        else:
            stdin_list = [to_sleep, ssh_develop_node, to_sleep,
                          handle_permission, load_gpu_module, cd_directory, start_jupyter_notebook]
    else:
        if(not parsed_args.node):
            stdin_list = [to_sleep, ssh_develop_node, to_sleep, salloc_job,
                          handle_permission, cd_directory, start_jupyter_notebook]
        else:
            stdin_list = [to_sleep, ssh_develop_node, to_sleep,
                          handle_permission, cd_directory, start_jupyter_notebook]

    sh.ssh(f"{parsed_args.user}@hpcc.msu.edu",
           _out=ssh_interact_jupyter,  _tty_in=True, _in=stdin_list)


def init():
    """
    log output and set global status.
    """
    global global_status, parsed_args

    logger.info("start to parse arguments")
    parsed_args = check_args(sys.argv[1:])
    logger.info(f"[user] {parsed_args.user}")
    if(not parsed_args.node):
        logger.info(f"[time] {parsed_args.time}")
        logger.info(f"[memory] {parsed_args.memory}")
        logger.info(f"[cores] {parsed_args.cores}")
    else:
        logger.info("[time] 02:00:00")
        logger.info("memory and cores depend on the node you are using")
    logger.info(f"[port] {parsed_args.port}")
    logger.info(f"[directory] {parsed_args.directory}")
    logger.info(f"[node] {parsed_args.node}")
    logger.info(f"[gpu] {parsed_args.gpu}")
    global_status = {}
    global_status["use_compute_node"] = parsed_args.node
    global_status["hostname"] = ''
    if(global_status["use_compute_node"]):
        global_status["hostname"] = parsed_args.develop_login
    if(parsed_args.gpu and (parsed_args.develop_login != "dev-intel14-k20" and parsed_args.develop_login != "dev-intel16-k80")):
        logger.error("the developing node you are using is not gpu node!")
        exit()
    logger.info(f"[develop_login] {parsed_args.develop_login}")
    logger.success("success in parsing arguments!")


if __name__ == "__main__":
    init()
    logging_icer()
