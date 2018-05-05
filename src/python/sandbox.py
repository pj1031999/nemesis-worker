#!/usr/bin/env python3

import logging
import os
import pwd
import resource
import subprocess
import sys


class Sandbox(object):
    def __init__(self,
                 command,
                 args,
                 logger,
                 stdin = None,
                 stdout = None,
                 stderr = None,
                 memory_limit = None,
                 time_limit = None,
                 output_limit = None,
                 nobody = None):
        self.command = command
        self.args = args
        self.stdin_file = stdin
        self.stdout_file = stdout
        self.stderr_file = stderr
        self.memory_limit = memory_limit
        self.time_limit = time_limit
        self.output_limit = output_limit
        self.process = None
        self.stdout = None
        self.stderr = None
        self.exit_code = None
        self.nobody = nobody
        self.logger = logger

    def __setlimits__(self):
        if self.stdin_file != None:
            stdin_fd = os.open(self.stdin_file, os.O_RDONLY)
            os.dup2(stdin_fd, sys.stdin.fileno())
            os.close(stdin_fd)

        if self.stdout_file != None:
            stdout_fd = os.open(self.stdout_file,
                                os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            os.dup2(stdout_fd, sys.stdout.fileno())
            os.close(stdout_fd)

        if self.stderr_file != None:
            stderr_fd = os.open(self.stderr_file, os.O_WRONLY | os.O_CREAT)
            os.dup2(stderr_fd, sys.stderr.fileno())
            os.close(stderr_fd)

        if self.nobody != None:
            passwd = pwd.getpwnam('nobody')

            os.initgroups(passwd.pw_name, passwd.pw_gid)
            os.setgid(passwd.pw_gid)
            os.setuid(passwd.pw_uid)

        if self.memory_limit != None:
            resource.setrlimit(resource.RLIMIT_AS,
                               (self.memory_limit, self.memory_limit))

        if self.time_limit != None:
            resource.setrlimit(resource.RLIMIT_CPU,
                               (self.time_limit, self.time_limit))

        if self.output_limit != None:
            resource.setrlimit(resource.RLIMIT_FSIZE,
                               (self.output_limit, self.output_limit))

    def run(self):
        self.logger.info('Sandobx.run():' + ' '.join(([self.command] + self.args)))

        proc = subprocess.Popen(
            [self.command] + self.args,
            preexec_fn=self.__setlimits__,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
        self.exit_code = proc.wait(self.time_limit + 1)
        self.stdout, self.stderr = proc.communicate()

        self.logger.info('Sandbox.run(): exit code: {}'.format(self.exit_code))

        return self.exit_code, self.stdout, self.stderr
