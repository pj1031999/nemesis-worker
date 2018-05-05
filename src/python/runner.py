#!/usr/bin/python3

import argparse
import default_nemesis_proto
import logging
import nemesis_pb2
import os
import sandbox
import shutil
import subprocess
import sys
import tempfile


class Runner(object):
    def __init__(self,
                 logger,
                 exe_path,
                 conf,
                 src_path = None,
                 check_path = None,
                 custom = False,
                 sandbox_path = None,
                 generator = False):

        self.exe_path = exe_path
        self.conf = conf
        self.src_path = src_path
        self.check_path = check_path
        self.custom = custom
        self.logger = logger
        self.generator = generator

        self.run_dir = None
        self.run_exe = None
        self.run_conf = None
        self.run_in = None
        self.run_src = None
        self.run_out = None
        self.run_check = None
        self.run_log = None
        self.run_ans = None

        self.sandbox_path = '/usr/local/sbin/sandbox'

        if sandbox_path:
            self.sandbox_path = sandbox_path

    def __init_self_var__(self):
        self.logger.info('Runner.__init_self_var__()')
        self.run_exe = os.path.join(self.run_dir, 'bin')
        self.run_in = os.path.join(self.run_dir, 'in')
        self.run_src = os.path.join(self.run_dir, 'src')
        self.run_out = os.path.join(self.run_dir, 'out')
        self.run_check = os.path.join(self.run_dir, 'check')
        self.run_log = os.path.join(self.run_dir, 'log')
        self.run_conf = os.path.join(self.run_dir, 'conf')
        self.run_ans = os.path.join(self.run_dir, 'ans')

    def __run_custom__(self):
        self.logger.info('Runner.__run_custom__()')
        status = None
        time = None
        memory = None
        out = None

        try:
            self.run_dir = tempfile.mkdtemp()
            self.logger.info('Runner.__run_custom__(): create {}'.format(self.run_dir))
            shutil.chown(self.run_dir, user='nobody', group='nogroup')

            self.__init_self_var__()

            self.logger.info('Runner.__run_custom__(): copy {} => {}'.format(self.exe_path, self.run_exe))

            shutil.copyfile(self.exe_path, self.run_exe)
            shutil.chown(self.run_exe, user='nobody', group='nogroup')
            os.chmod(self.run_exe, 0o744)

            self.logger.info('Runner.__run_custom__(): write input {}'.format(self.run_in))

            try:
                with open(self.run_in, "wb") as run_input:
                    run_input.write(self.conf.input)
            except:
                raise RuntimeError('write input error')

            shutil.chown(self.run_in, user='nobody', group='nogroup')
        except:
            self.logger.error('Runner.__run_custom__(): shutil exception')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('shutil exception')

        try:
            self.logger.info('Runner.__run_custom__(): subprocess run sandbox')
            self.logger.info('{}'.format([
                self.sandbox_path, '--exe', self.run_exe, '--input',
                self.run_in, '--output', self.run_ans, '--time_limit',
                str(self.conf.time_limit), '--memory_limit',
                str(self.conf.memory_limit), '--id',
                str(self.conf.id), '--log', self.run_log
            ]))
            proc = subprocess.run([
                self.sandbox_path, '--exe', self.run_exe, '--input',
                self.run_in, '--output', self.run_ans, '--time_limit',
                str(self.conf.time_limit), '--memory_limit',
                str(self.conf.memory_limit), '--id',
                str(self.conf.id), '--log', self.run_log
            ])
        except:
            self.logger.error('Runner.__run_custom__(): sandbox subprocess exception')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('sandbox subprocess exception')

        if proc.returncode != 0:
            self.logger.error('Runner.__run_custom__(): sandbox returncode: {}'.format(proc.returncode))
            shutil.rmtree(self.run_dir)
            raise RuntimeError('sandobx returncode != 0')

        result = default_nemesis_proto.default_Status_Group_Test()
        #result = nemesis_pb2.Status.Group.Test()

        try:
            with open(self.run_log, "rb") as result_file:
                result.ParseFromString(result_file.read())
        except:
            self.logger.error('Runner.__run_custom__(): parse log file exception')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('parse log file exception')

        status = result.status
        time = result.time
        memory = result.memory

        try:
            with open(self.run_ans, "rb") as answer_file:
                if self.generator == True:
                    out = answer_file.read()
                else:
                    out = answer_file.read(256)
        except:
            self.logger.error('Runner.__run_custom__(): read answer file error')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('read answer file error')

        shutil.rmtree(self.run_dir)

        return (status, time, memory, out)

    def __run_submit__(self):
        self.logger.info('Runner.__run_submit__()')
        try:
            self.run_dir = tempfile.mkdtemp()
            self.logger.info('Runner.__run_submit__(): create {}'.format(self.run_dir))
            shutil.chown(self.run_dir, user='nobody', group='nogroup')

            self.__init_self_var__()

            self.logger.info('Runner.__run_submit__(): copy {} => {}'.format(self.exe_path, self.run_exe))

            shutil.copyfile(self.exe_path, self.run_exe)
            shutil.chown(self.run_exe, user='nobody', group='nogroup')
            os.chmod(self.run_exe, 0o744)

            self.logger.info('Runner.__run_submit__(): write input: {}'.format(self.run_in))

            try:
                with open(self.run_in, 'wb') as run_input:
                    run_input.write(self.conf.input)
            except:
                raise RuntimeError('write input error')

            shutil.chown(self.run_in, user='nobody', group='nogroup')

            self.logger.info('Runner.__run_submit__(): copy {} => {}'.format(self.src_path, self.run_src))

            shutil.copyfile(self.src_path, self.run_src)
            shutil.chown(self.run_src, user='nobody', group='nogroup')
        except:
            self.logger.error('Runner.__run_submit__(): shutil exception')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('shutil exception')

        try:
            self.logger.info('Runner.__run_submit__(): subprocess run sandbox')
            proc = subprocess.run([
                self.sandbox_path, '--exe', self.run_exe, '--input',
                self.run_in, '--output', self.run_ans, '--time_limit',
                str(self.conf.time_limit), '--memory_limit',
                str(self.conf.memory_limit), '--id',
                str(self.conf.id), '--log', self.run_log
            ])
        except:
            self.logger.error('Runner.__run_submit__(): sandbox subprocess exception')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('sandbox subprocess exception')

        self.logger.info('Runner.__run_submit__(): sandbox returncode: {}'.format(proc.returncode))
        if proc.returncode != 0:
            self.logger.error('Runner.__run_submit__(): sandbox returncode error: {}'.format(proc.returncode))
            shutil.rmtree(self.run_dir)
            raise RuntimeError('sandobx returncode != 0')

        result = default_nemesis_proto.default_Status_Group_Test()
        #result = nemesis_pb2.Status.Group.Test()

        try:
            with open(self.run_log, "rb") as result_file:
                result.ParseFromString(result_file.read())
        except:
            self.logger.error('Runner.__run_submit__(): parse log file exception')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('parse log file exception')

        try:
            self.logger.info('Runner.__run_submit__(): write output => {}'.format(self.run_out))

            try:
                with open(self.run_out, "wb") as run_output:
                    run_output.write(self.conf.output)
            except:
                raise RuntimeError('write output error')

            shutil.chown(self.run_out, user='nobody', group='nogroup')

            self.logger.info('Runner.__run_submit__(): copy {} => {}'.format(self.check_path, self.run_check))

            shutil.copyfile(self.check_path, self.run_check)
            shutil.chown(self.run_check, user='nobody', group='nogroup')
            os.chmod(self.run_check, 0o744)
        except:
            self.logger.error('Runner.__run_submit__(): shutil exception')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('shutil exception')

        check_exit_code = None
        check_stdout = None
        check_stderr = None

        try:
            self.logger.info('Runner.__run_submit__(): sandbox run check')
            proc = sandbox.Sandbox(
                self.run_check, [
                    '--src', self.run_src, '--input', self.run_in, '--output',
                    self.run_out, '--answer', self.run_ans
                ],
                memory_limit = 1024 * 1024 * 1024,
                time_limit = 120,
                nobody = True,
                logger = self.logger)
            check_exit_code, check_stdout, check_stderr = proc.run()
        except:
            self.logger.error('Runner.__run_submit__(): sandbox run check error')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('sandbox error')

        if check_exit_code == 0:
            result.verdict = True
        elif check_exit_code == 1:
            result.verdict = False
        else:
            self.logger.error('Runner.__run_submit__(): checker internal error')
            shutil.rmtree(self.run_dir)
            raise RuntimeError('checker error')

        shutil.rmtree(self.run_dir)
        result.id = self.conf.id
        return result

    def run(self):
        self.logger.info('Runner.run()')
        if self.conf.IsInitialized() == False:
            self.logger.error('Runner.run(): self.conf.IsInitialized() == False')
            raise RuntimeError('self.conf.IsInitialized() == False')
        if self.custom:
            return self.__run_custom__()
        return self.__run_submit__()


def main():
    parser = argparse.ArgumentParser(description="Nemesis code runner")
    parser.add_argument('--exe', dest="exe_path", default="/dev/null", help="exe file")
    parser.add_argument('--input', dest="input_path", default="/dev/null", help="input file")
    parser.add_argument('--memory', dest="memory_limit", type=int, default=1024 * 32, help="memory limit")
    parser.add_argument('--time', dest="time_limit", type=int, default=1, help="time limit")
    parser.add_argument('--src', dest="src_path", default=None, help="source path")
    parser.add_argument('--output', dest="output_path", default=None, help="output path")
    parser.add_argument('--check', dest="check_path", default=None, help="check path")
    parser.add_argument('--custom', dest="custom", default=False, help="custom invocation", action='store_true')
    parser.add_argument('--sandbox', dest="sandbox_path", default=None, help="sandbox path")

    args = parser.parse_args()
    
    conf = default_nemesis_proto.default_Task_Group_Test()
    conf.id = 1
    conf.time_limit = args.time_limit
    conf.memory_limit = args.memory_limit

    try:
        with open(args.input_path, 'rb') as input_file:
            conf.input = input_file.read()
    except:
        raise RuntimeError('read input error')

    if args.output_path:
        try:
            with open(args.output_path, 'rb') as output_file:
                conf.output = output_file.read()
        except:
            raise RuntimeError('read correct output error')

    logging.basicConfig(level = logging.INFO)

    logger = logging.getLogger('runner_logger')

    runner = Runner(
        exe_path = args.exe_path,
        conf = conf,
        src_path = args.src_path,
        check_path = args.check_path,
        custom = args.custom,
        sandbox_path = args.sandbox_path,
        logger = logger)

    print(runner.run())


if __name__ == "__main__":
    main()
