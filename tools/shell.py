# -*- coding: utf-8 -*-
#!/usr/bin/env python

import subprocess

def process(cmd=""):
    # print('start')
    completed_process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # print(f'returncode: {completed_process.returncode},stdout: {completed_process.stdout},stderr:{completed_process.stderr}')
    if b'' != completed_process.stderr:
        raise Exception(completed_process.stderr.decode('utf-8'))
    return completed_process.stdout.decode('utf-8')
