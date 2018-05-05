import argparse
import compile_sandbox
import default_nemesis_proto
import logging
import nemesis_pb2
import os
import runner
import shutil
import tempfile


class Judger(object):
    def __init__(self, conf, logger):
        self.conf = conf
        self.logger = logger

        self.checker_path = None
        self.working_dir = None
        self.exe_path = None
        self.source_path = None
        self.solution_path = None

    def __return_custom_failure(self, conf):
        self.logger.error('Judger.__return_custom_failure()')

        result = default_nemesis_proto.default_CustomInvocationStatus()
        result.user_id = conf.user_id
        result.time = -1
        result.memory = -1
        result.compiled = False
        result.compile_log = b'internal Nemesis error'
        result.status = nemesis_pb2.SYS
        result.out = b'internal Nemesis error'
        
        job = default_nemesis_proto.default_JobReturn()
        job.custom = True
        job.custom_status.CopyFrom(result)
        job.system_error = True
        return job

    def __run__custom(self):
        self.logger.info('Judger.__run_custom()')
        try:
            self.working_dir = tempfile.mkdtemp()
            self.logger.info('Judger.__run__custom(): create')
            self.source_path = os.path.join(self.working_dir, 'source')
            self.exe_path = os.path.join(self.working_dir, 'bin')
        except:
            self.logger.error('Judger.__run__custom(): create working directory error')
            try:
                shutil.rmtree(self.working_dir)
            except:
                pass
            return self.__return_custom_failure(self.conf.custom_job)

        self.logger.info('Judger.__run__custom(): write source')
        try:
            with open(self.source_path, 'wb') as source_file:
                source_file.write(self.conf.custom_job.source)
        except:
            shutil.rmtree(self.working_dir)
            self.logger.error('Judger.__run__custom(): write source failure')
            return self.__return_custom_failure(self.conf.custom_job)

        compiler = compile_sandbox.Compiler(
            lang = self.conf.custom_job.lang,
            src_file = self.source_path,
            exe_file = self.exe_path,
            logger = self.logger)

        self.logger.info('Judger.__run__custom(): compilation started')

        try:
            compiler_exit_code, compiler_log = compiler.run()
        except:
            shutil.rmtree(self.working_dir)
            self.logger.error('Judger.__run__custom(): compilation sandbox failure')
            return self.__return_custom_failure(self.conf.custom_job)
        if compiler_exit_code != 0:
            self.logger.info('Judger.__run__custom(): compilation failure')

            result = default_nemesis_proto.default_CustomInvocationStatus()
            result.id = self.conf.custom_job.id
            result.user_id = self.conf.custom_job.user_id
            result.time = -1
            result.memory = -1
            result.compiled = False
            result.compile_log = compiler_log
            result.status = nemesis_pb2.OK
            result.out = b'0'

            status = default_nemesis_proto.default_JobReturn()
            status.custom_status.CopyFrom(result)
            status.custom = True
            status.system_error = False

            return status

        self.logger.info('Judger.__run__custom(): compilation success')

        try:
            self.logger.info('Judger.__run__custom(): run sandbox')
            proc = runner.Runner(
                logger = self.logger,
                exe_path = self.exe_path,
                conf = self.conf.custom_job.test,
                custom = True)

            status, time, memory, out = proc.run()

            self.logger.info('Judger.__run__custom(): sandbox exited')

            result = default_nemesis_proto.default_CustomInvocationStatus()
            result.id = self.conf.custom_job.id
            result.user_id = self.conf.custom_job.user_id
            result.time = time
            result.memory = memory
            result.compiled = True
            result.compile_log = compiler_log
            result.status = status
            result.out = out

            shutil.rmtree(self.working_dir)

            status = default_nemesis_proto.default_JobReturn()
            status.custom_status.CopyFrom(result)
            status.custom = True
            status.system_error = False

            return status
        except:
            shutil.rmtree(self.working_dir)
            self.logger.error('Judger.__run__custom(): run sandbox failure')
            return self.__return_custom_failure(self.conf.custom_job)

    def __return_failure(self, conf):
        self.logger.error('Judger.__return_failure()')
        result = default_nemesis_proto.default_Status()
        result.id = conf.submit.id
        result.task_id = conf.submit.task.task_id
        result.user_id = conf.submit.user_id
        result.lang = conf.submit.lang
        result.number_of_groups = 0
        result.points = 0
        result.acm = False
        result.compiled = False
        result.compile_log = b'Internal Nemesis error'
        result.status = nemesis_pb2.SYS
        result.rejudge = conf.submit.rejudge

        job = default_nemesis_proto.default_JobReturn()
        job.custom = False
        job.status.CopyFrom(result)
        job.system_error = True

        return job

    def __generate_outs(self):
        self.logger.info('Judger.__generate_outs()')
        compiler = compile_sandbox.Compiler(
            lang = nemesis_pb2.CXX,
            src_file = self.solution_source,
            exe_file = self.solution_path,
            logger = self.logger)

        self.logger.info('Judger.__generate_outs(): compile solution')

        try:
            compiler_exit_code, compiler_log = compiler.run()
        except:
            shutil.rmtree(self.working_dir)
            self.logger.error('Judger.__generate_outs(): solution compilation failure')
            return False

        if compiler_exit_code != 0:
            shutil.rmtree(self.working_dir)
            self.logger.error('Judger.__generate_outs(): solution compilation failure')
            self.logger.error(compiler_log)
            return False

        copy_of_task = nemesis_pb2.Task()
        copy_of_task.CopyFrom(self.conf.submit.task)

        for grp in self.conf.submit.task.groups:
            for test in grp.tests:
                self.logger.info('Judger.__generate_outs(): generate ({}, {})'.format(grp.id, test.id))
                conf = test
                run = runner.Runner(
                    exe_path = self.solution_path,
                    conf = conf,
                    custom = True,
                    logger = self.logger,
                    generator = True)
                status = run.run()
                if status[0] != nemesis_pb2.OK:
                    return False
                out = status[3]
                copy_of_task.groups[grp.id - 1].tests[test.id - 1].output = out

        self.conf.submit.task.CopyFrom(copy_of_task)
        return True

    def run(self):
        if self.conf.IsInitialized() == False:
            self.logger.error('Judger.run(): self.conf.IsInitialized() == False')
            raise RuntimeError('self.conf.IsInitialized() == False')
        if self.conf.custom:
            self.logger.info('Judger.run(): execute custom invocation')
            
            return self.__run__custom()

        self.logger.info('Judger.run(): run normal submit')

        try:
            self.working_dir = tempfile.mkdtemp()
            self.logger.info('Judger.run(): create {}'.format(self.working_dir))
            self.source_path = os.path.join(self.working_dir, 'source')
            self.exe_path = os.path.join(self.working_dir, 'bin')
            self.checker_path = os.path.join(self.working_dir, 'checker')
            self.checker_source = os.path.join(self.working_dir, 'checker.source')
            self.solution_path = os.path.join(self.working_dir, 'solution')
            self.solution_source = os.path.join(self.working_dir, 'solution.source')
        except:
            self.logger.error('Judger.run(): create working directory error')
            try:
                shutil.rmtree(self.working_dir)
            except:
                pass
            return self.__return_failure(self.conf)

        self.logger.info('Judger.run(): write source')
        try:
            with open(self.source_path, 'wb') as source_file:
                source_file.write(self.conf.submit.code)
            with open(self.checker_source, 'wb') as checker_file:
                checker_file.write(self.conf.submit.task.checker)
            self.logger.info('Judger.run(): write solution source')
            with open(self.solution_source, 'wb') as solution_file:
                solution_file.write(self.conf.submit.task.solution)
        except:
            shutil.rmtree(self.working_dir)
            self.logger.error('Judger.run(): write source failure')
            return self.__return_failure(self.conf)

        compiler = compile_sandbox.Compiler(
            lang=nemesis_pb2.CXX,
            src_file=self.checker_source,
            exe_file=self.checker_path,
            logger=self.logger)

        self.logger.info('Judger.run(): compile checker')

        try:
            compiler_exit_code, compiler_log = compiler.run()
        except:
            shutil.rmtree(self.working_dir)
            self.logger.error('Judger.run(): checker compilation failure')
            return self.__return_failure(self.conf)

        if compiler_exit_code != 0:
            shutil.rmtree(self.working_dir)
            self.logger.error('Judger.run(): checker compilation failure')
            self.logger.error(compiler_log)
            return self.__return_failure(self.conf)

        if self.__generate_outs() == False:
            self.logger.error('Judger.run(): outs generator failure')
            try:
                shutil.rmtree(self.working_dir)
            except:
                pass
            return self.__return_failure(self.conf)

        compiler = compile_sandbox.Compiler(
            lang=self.conf.submit.lang,
            src_file=self.source_path,
            exe_file=self.exe_path,
            logger=self.logger)

        self.logger.info('Judger.run(): compilation started')

        try:
            compiler_exit_code, compiler_log = compiler.run()
        except:
            shutil.rmtree(self.working_dir)
            self.logger.error('Judger.run(): compilation sandbox failure')
            return self.__return_failure(self.conf)

        if compiler_exit_code != 0:
            self.logger.info('Judger.run(): compilation failure')
            result = default_nemesis_proto.default_Status()
            result.id = self.conf.submit.id
            result.task_id = self.conf.submit.task.task_id
            result.user_id = self.conf.submit.user_id
            result.lang = self.conf.submit.lang
            result.number_of_groups = 0
            result.points = 0
            result.acm = False
            result.compiled = False
            result.compile_log = compiler_log
            result.status = nemesis_pb2.OK
            result.rejudge = self.conf.submit.rejudge
            shutil.rmtree(self.working_dir)

            job = default_nemesis_proto.default_JobReturn()
            job.custom = False
            job.status.CopyFrom(result)
            job.system_error = False

            return job

        self.logger.info('Judger.run(): compilation success')

        result = default_nemesis_proto.default_Status()
        result.id = self.conf.submit.id
        result.task_id = self.conf.submit.task.task_id
        result.user_id = self.conf.submit.user_id
        result.lang = self.conf.submit.lang
        result.number_of_groups = self.conf.submit.task.number_of_groups
        result.points = 0
        result.acm = False
        result.compiled = True
        result.compile_log = compiler_log
        result.status = nemesis_pb2.OK
        result.rejudge = self.conf.submit.rejudge

        correct_grp = 0

        for grp in self.conf.submit.task.groups:
            grp_status = default_nemesis_proto.default_Status_Group()
            grp_status.id = grp.id
            grp_status.number_of_tests = grp.number_of_tests

            verdict = True
            self.logger.info('Judger.run(): group number {}'.format(grp.id))
            for test in grp.tests:
                self.logger.info('Judger.run(): test number {}'.format(test.id))
                proc = runner.Runner(
                    logger = self.logger,
                    exe_path = self.exe_path,
                    conf = test,
                    src_path = self.source_path,
                    check_path = self.checker_path,
                    custom = False)
                try:
                    status = proc.run()
                except:
                    self.logger.error('Judgeer.run(): internal Nemesis error')
                    shutil.rmtree(self.working_dir)
                    return self.__return_failure(self.conf)
                if status.verdict == False:
                    verdict = False
                    grp_status.status = status.status
                if status.status != nemesis_pb2.OK:
                    grp_status.status = status.status
                grp_status.tests.extend([status])

            grp_status.verdict = verdict
            if verdict == True:
                correct_grp += 1
            if grp_status.status != nemesis_pb2.OK:
                result.status = grp_status.status
            result.groups.extend([grp_status])

        result.points = int(100 / result.number_of_groups * correct_grp)

        if correct_grp == result.number_of_groups:
            result.acm = True
            result.points = 100

        shutil.rmtree(self.working_dir)
        
        status = default_nemesis_proto.default_JobReturn()
        status.custom = False
        status.status.CopyFrom(result)
        return status


def main():
    parser = argparse.ArgumentParser(description="Nemesis Judger")
    parser.add_argument('--submit', dest="submit", required=True, help="submit file")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    conf = nemesis_pb2.Job()
    try:
        with open(args.submit, 'rb') as config_file:
            conf.ParseFromString(config_file.read())
    except:
        raise RuntimeError('read submit error')

    judge = Judger(conf=conf, logger=logging.getLogger('WORKER_LOCALHOST_01'))
    print(judge.run())


if __name__ == "__main__":
    main()
