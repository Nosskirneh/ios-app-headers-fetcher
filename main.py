#!/usr/bin/env python3

import sys
import os
import paramiko
from subprocess import run
import shutil
import re
import io
import plistlib
from pygit2 import Repository, RemoteCallbacks, Keypair
from pygit2 import GIT_SORT_TIME, GIT_SORT_REVERSE
from pathlib import Path

from config import *

def init_ssh():
    print("Setting up SSH connection...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(DEVICE_IP, username=DEVICE_USER, key_filename=os.path.expanduser('~/.ssh/id_rsa'))
    except:
        print("Client seems to be offline! Exiting...")
        sys.exit()
    return ssh


def run_clutch(ssh):
    print("Decrypting app...")
    _, stdout_, _ = ssh.exec_command('Clutch -b ' + bundle_identifier, get_pty=True)
    stdout_.channel.recv_exit_status()
    lines = stdout_.readlines()
    for line in lines:
        if "/var/tmp/clutch" in line:
            out_dir = '/' + line.split('/', 1)[1].rstrip() + '/'
            # Remove shitty escape char
            ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
            return ansi_escape.sub('', out_dir)
    return None


def copy_file(sftp):
    # Create local tmp directory if not already existing
    if not os.path.exists(TEMP_DIR):
        os.mkdir(TEMP_DIR)

    folder = out_dir + bundle_identifier
    file_name = sftp.listdir(folder)[0]
    sftp.get(folder + '/' + file_name, TEMP_DIR + '/' + file_name)
    return file_name


def extract_info(sftp):
    all_bundle_dir = "/var/containers/Bundle/Application/"
    bundles = sftp.listdir(all_bundle_dir)

    for bundle in bundles:
        sub_items = sftp.listdir(all_bundle_dir + bundle)
        app = [item for item in sub_items if item.endswith('.app')][0]

        with io.BytesIO() as fl:
            sftp.getfo(all_bundle_dir + bundle + '/' + app + '/' + "Info.plist", fl)
            fl.seek(0)

            contents = plistlib.load(fl)
            if contents['CFBundleIdentifier'] == bundle_identifier:
                return contents['CFBundleName'], contents['CFBundleShortVersionString'], contents['CFBundleVersion']
    return None


def push(repo, ref='refs/heads/master', remote_name='origin'):
    print("Pushing...")
    ssh_rsa_dir = str(Path.home()) + '/.ssh/'
    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.credentials = Keypair('git', ssh_rsa_dir + 'id_rsa.pub', ssh_rsa_dir + 'id_rsa', '')
            callbacks = RemoteCallbacks(credentials=remote.credentials)
            remote.push([ref], callbacks=callbacks)


def commit(name, version, bundle_version):
    print("Commiting...")
    repo = Repository('headers/.git')

    new_commit_message = name + ' ' + version + ' (' + bundle_version + ')'

    # Already commited this version?
    for commit in repo.walk(repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE):
        if commit.message == new_commit_message:
            return False

    index = repo.index
    index.add_all()
    index.write()
    user = repo.default_signature
    tree = index.write_tree()
    ref = 'refs/heads/master'
    repo.create_commit(ref, user, user, new_commit_message, tree, [repo.head.get_object().hex])

    push(repo, ref)
    return True



# Main
if len(sys.argv) < 2:
    print("You must specify a bundle identifier!")
    sys.exit()

bundle_identifier = sys.argv[1]

ssh = init_ssh()
out_dir = run_clutch(ssh)

if out_dir != None:
    sftp = ssh.open_sftp()
    file_name = copy_file(sftp)
    name, short_version, bundle_version = extract_info(sftp)

    ssh.close()
    print("Closed SSH session.")

    header_dir = "headers/" + bundle_identifier

    # Remove any previous header files to avoid old files
    if os.path.exists(header_dir):
        shutil.rmtree(header_dir)

    print("Starting class-dump...")
    run(["./class-dump", TEMP_DIR + '/' + file_name, "-H", "-o", header_dir])

    commit(name, short_version, bundle_version)

    print("Done! Cleaning up and exiting...")
    shutil.rmtree(TEMP_DIR)
