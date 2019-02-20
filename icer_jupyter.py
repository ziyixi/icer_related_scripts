#!/usr/bin/env python
import argparse
import sh
import sys
from loguru import logger


class FLAG():
    gateway_flag = True
    notebook_flag = True
    url_flag = True


def check_args(args=None):
    parser = argparse.ArgumentParser(
        description='A python script to run jupyter notebook on icer computing node and open it on localhost',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-u', '--user',
                        help='icer user name',
                        required=True,
                        default='xiziyi')
    parser.add_argument('-t', '--time',
                        help='time to use (not necessary when use computing node)',
                        required=False,
                        default='02:00:00')
    parser.add_argument('-m', '--memory',
                        help='memory per core (not necessary when use computing node)',
                        required=False,
                        default='1G')
    parser.add_argument('-c', '--cores',
                        help='number of cores (not necessary when use computing node)',
                        required=False,
                        default='1')
    parser.add_argument('-p', '--port',
                        help='port of the notebook',
                        required=False,
                        default='8789')
    parser.add_argument('-d', '--directory',
                        help='directory to open the notebook',
                        required=False,
                        default='/mnt/home/xiziyi/')
    parser.add_argument('-n', '--node',
                        help='whether just use developing node',
                        required=False,
                        default=True)
    parser.add_argument('--develop_login',
                        help="developing node to use salloc command",
                        required=False,
                        default="dev-intel14-k20")
    results = parser.parse_args(args)
    return results


def ssh_interact_jupyter(char, stdin):
    # sys.stdout.write(char)
    # sys.stdout.flush()
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
    # sys.stdout.write(char)
    # sys.stdout.flush()
    if(FLAG.url_flag):
        logger.success(f"use http://localhost:{parsed_args.port}")
        FLAG.url_flag = False


def handle_ssh_tunnel():
    sh.ssh("-4", "-t", "-Y",
           f"{parsed_args.user}@hpcc.msu.edu", "-L", f"{parsed_args.port}:localhost:{parsed_args.port}", "ssh", "-t", "-Y", global_status["hostname"], "-L", f"{parsed_args.port}:localhost:{parsed_args.port}", _out=ssh_interact_tunnel, _tty_in=True)


def logging_icer(parsed_args):
    ssh_develop_node = f"ssh {parsed_args.develop_login}\n"
    salloc_job = f"salloc --time={parsed_args.time} -c {parsed_args.cores} --mem-per-cpu={parsed_args.memory}\n"
    handle_permission = f"export XDG_RUNTIME_DIR=''\n"
    start_jupyter_notebook = f"jupyter notebook --NotebookApp.token='' --port={parsed_args.port} --notebook-dir={parsed_args.directory}\n"
    to_sleep = f"sleep 1\n"
    logger.info(f"start to execute command on icer")

    if(not parsed_args.node):
        stdin_list = [to_sleep, ssh_develop_node, to_sleep, salloc_job,
                      handle_permission, start_jupyter_notebook]
    else:
        stdin_list = [to_sleep, ssh_develop_node, to_sleep,
                      handle_permission, start_jupyter_notebook]

    sh.ssh(f"{parsed_args.user}@hpcc.msu.edu",
           _out=ssh_interact_jupyter,  _tty_in=True, _in=stdin_list)


if __name__ == "__main__":
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
    global_status = {}
    global_status["use_compute_node"] = parsed_args.node
    global_status["hostname"] = ''
    if(global_status["use_compute_node"]):
        global_status["hostname"] = parsed_args.develop_login
    logger.info(f"[develop_login] {parsed_args.develop_login}")
    logger.success("success in parsing arguments!")

    # * submit job and run jupyter notebook on the computing node
    logging_icer(parsed_args)
