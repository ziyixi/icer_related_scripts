#!/usr/bin/env python
"""
This script should be run with having set the SSH keys.
"""
import argparse
import sh
import sys
from loguru import logger
import click


class FLAG():
    """
    The class to store some global flags. These flags are used to control the output of the logs, or one log may appear multiple times.
    """
    gateway_flag = True
    notebook_flag = True
    url_flag = True


class Settings():
    """
    Store the global settings
    """
    NODE = ""
    USER = ""
    PORT = ""


@click.command()
@click.option('--user', required=True, type=str, help="ICER username")
@click.option('--port', required=True, type=str, help="the port of the jupyter notebook")
@click.option('--directory', required=True, type=str, help="the directory to start the jupyter notebook")
@click.option('--node', required=True, type=str, help="the developing node to use")
def main(user, port, directory, node):
    # output the log information
    logger.info(f"[user] {user}")
    Settings.USER = user
    logger.info(f"[port] {port}")
    Settings.PORT = port
    logger.info(f"[directory] {directory}")
    logger.info(f"[node] {node}")
    Settings.NODE = node

    logging_icer(user, port, directory, node)


def logging_icer(user, port, directory, node):
    """
    commands are strings arranged in a list.
    """
    ssh_develop_node = f"ssh {node}\n"
    handle_permission = f"export XDG_RUNTIME_DIR=''\n"
    cd_directory = f"cd {directory}\n"
    start_jupyter_notebook = f"jupyter notebook --NotebookApp.token='' --port={port}\n"
    to_sleep = f"sleep 1\n"
    logger.info(f"start to execute command on icer")

    stdin_list = [to_sleep, ssh_develop_node, to_sleep,
                  handle_permission, cd_directory, start_jupyter_notebook]

    sh.ssh(f"{user}@hpcc.msu.edu",
           _out=ssh_interact_jupyter,  _tty_in=True, _in=stdin_list)


def ssh_interact_jupyter(char, stdin):
    """
    handle standard output when starting to run the jupyter notebook.
    """
    if("Last login" in char and FLAG.gateway_flag):
        logger.info(f"success in logging on icer gateway")
        FLAG.gateway_flag = False
    if("@dev" in char):
        logger.info(f"success in logging on the developing node")
    if("Address already in use" in char):
        logger.error("choose another port to use!")
    if(Settings.NODE and FLAG.notebook_flag):
        if("NotebookApp" in char):
            logger.info(
                f"success in starting jupyter notebook using the developing node")
            handle_ssh_tunnel()
            FLAG.notebook_flag = False


def handle_ssh_tunnel():
    """
    set ssh tunnel when having started the jupyter notebook.
    """
    sh.ssh("-4", "-t", "-Y",
           f"{Settings.USER}@hpcc.msu.edu", "-L", f"{Settings.PORT}:localhost:{Settings.PORT}", "ssh", "-t", "-Y", Settings.NODE, "-L", f"{Settings.PORT}:localhost:{Settings.PORT}", _out=ssh_interact_tunnel, _tty_in=True)


def ssh_interact_tunnel(char, stdin):
    """
    handle standard output when setting up th essh tunnel.
    """
    if(FLAG.url_flag):
        logger.success(f"use http://localhost:{Settings.PORT}")
        FLAG.url_flag = False


if __name__ == "__main__":
    main()
