import logging
import nemesis_pb2
import sandbox
import sys


class Compiler(object):
    def __init__(self, lang, src_file, exe_file, logger):
        self.lang = lang
        self.src_file = src_file
        self.exe_file = exe_file
        self.exit_code = None
        self.stdout = None
        self.stderr = None
        self.logger = logger

    def run(self):
        self.logger.info('Compiler.run(): {} {} {}'.format(self.lang, self.src_file, self.exe_file))
        
        compiler_dictionary_command = {
            nemesis_pb2.CC: '/usr/bin/gcc',
            nemesis_pb2.CXX: '/usr/bin/g++',
            nemesis_pb2.RAM: '/usr/local/bin/ram2cpp'
        }
        compiler_dictionary_args = {
            nemesis_pb2.CC: ['-x', 'c', '-O2', '-std=c89', '-lm', '-o'],
            nemesis_pb2.CXX: ['-x', 'c++', '-O2', '-std=c++11', '-o'],
            nemesis_pb2.RAM: []
        }

        proc = sandbox.Sandbox(
            command=compiler_dictionary_command[self.lang],
            args=compiler_dictionary_args[self.lang] + [self.exe_file] +
            [self.src_file],
            memory_limit=1024 * 1024 * 256,
            time_limit=60,
            output_limit=1024 * 1024 * 10,
            logger=self.logger)

        self.exit_code, self.stdout, self.stderr = proc.run()

        self.logger.info('Compiler.run(): exit code:{}'.format(self.exit_code))

        return self.exit_code, str(self.stderr.decode('UTF-8'))
