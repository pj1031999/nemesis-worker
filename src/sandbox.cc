#include <fstream>
#include <iostream>
#include <nemesis.pb.h>
#include <process.h>
#include <string>
#include <getopt.h>

struct globalArgs_t {
  std::string exe;
  std::string in;
  std::string out;
  std::string output_log;
  std::string config;
  unsigned long int time_limit;
  unsigned long int memory_limit;
  unsigned int id;
  int verbose_flag;
  int flags;

  globalArgs_t() :
    exe{"/dev/null"}, in{"/dev/null"}, out{"/dev/null"}, output_log{"dev/null"},
    config{"/dev/null"}, verbose_flag{0}, flags{0} {}

} globalArgs;


void display_usage(void) {
  std::cerr << "sandbox.cc " << std::endl;
  std::cerr << "usage:\tsandbox [--verbose] --exe ... --input/--in ... --output/--out ... --time_limit ... --memory_limit ... --id ... --log ..." << std::endl;
  exit(EXIT_FAILURE);
}

int main(int argc, char **argv) {

  int opt;
  while (true) {
    static struct option long_options[] =
    {
      {"verbose", no_argument,  &globalArgs.verbose_flag, 1},
      {"exe", required_argument,  NULL,  'e'},
      {"input", required_argument,  NULL,  'i'},
      {"in", required_argument,  NULL,  'i'},
      {"output",  required_argument,  NULL,  'o'},
      {"out", required_argument,  NULL,  'o'},
      {"time_limit", required_argument, NULL,  't'},
      {"memory_limit", required_argument, NULL,  'm'},
      {"log", required_argument,  NULL,  'l'},
      {"id", required_argument,  NULL,  'n'},
      {"help", no_argument, NULL, 'h'},
      {NULL,  NULL, NULL, NULL}
    };

    static const char *optString = "e:i:o:c:l:h:t:m:n";

    int option_index = 0;

    opt = getopt_long(argc, argv, optString, long_options, &option_index);

    if (opt == -1)
      break;

    switch (opt) {
      case 0:
        globalArgs.flags |= 1<<0;
        break;

      case 'h':
        display_usage();
        break;

      case 'e':
        globalArgs.exe = std::string(optarg);
        globalArgs.flags |= 1<<1;
        break;

      case 'i':
        globalArgs.in = std::string(optarg);
        globalArgs.flags |= 1<<2;
        break;

      case 'o':
        globalArgs.out = std::string(optarg);
        globalArgs.flags |= 1<<3;
        break;

      case 't':
        globalArgs.time_limit = std::atol(optarg);
        globalArgs.flags |= 1<<4;
        break;

      case 'm':
        globalArgs.memory_limit = std::atol(optarg);
        globalArgs.flags |= 1<<5;
        break;

      case 'l':
        globalArgs.output_log = std::string(optarg);
        globalArgs.flags |= 1<<6;
        break;

      case 'n':
        globalArgs.id = std::atoi(optarg);
        globalArgs.flags |= 1<<7;
        break;

      default:
        std::cerr << argv[0] << ": wrong args" << std::endl;
        abort();
    }
  }

  static const int good_flags[] = {
    ((1<<1) | (1<<2) | (1<<3) | (1<<4) | (1<<5) | (1<<6) | (1<<7)),
    ((1<<0) | (1<<1) | (1<<2) | (1<<3) | (1<<4) | (1<<5) | (1<<6) | (1<<7)),
    NULL
  };

  if (globalArgs.flags != good_flags[0] && globalArgs.flags != good_flags[1]) {
    std::cerr << argv[0] << ": wrong args" << std::endl;
    display_usage();
    return EXIT_FAILURE;
  }

  std::string exe = globalArgs.exe;
  std::string in = globalArgs.in;
  std::string out = globalArgs.out;
  std::string path_to_output = globalArgs.output_log;

  Nemesis::Status_Group_Test status;

  Nemesis::Process::Process proc;

  if (globalArgs.verbose_flag == true)
    proc.set_verbose();

  std::ofstream protobuff_output(path_to_output.c_str());

  if (protobuff_output.is_open() == false) {
    std::cerr << "protobuff_output.is_open() == false : path => "
              << path_to_output << std::endl;
    exit(EXIT_FAILURE);
  }

  Nemesis::Process::ReturnState state;

  proc.set_path(exe, in, out);
  proc.set_memory_limit(globalArgs.memory_limit);
  proc.set_time_limit(globalArgs.time_limit);

  proc.execute();
  state = proc.exit();

  status.set_id(globalArgs.id);
  status.set_verdict(false);
  status.set_time(proc.get_real_time());
  status.set_memory(proc.get_user_memory());


  if (state == Nemesis::Process::ReturnState::OK) {
    status.set_status(Nemesis::StatusCode::OK);
  } else if (state == Nemesis::Process::ReturnState::TLE) {
    status.set_status(Nemesis::StatusCode::TLE);
  } else if (state == Nemesis::Process::ReturnState::MLE) {
    status.set_status(Nemesis::StatusCode::MLE);
  } else if (state == Nemesis::Process::ReturnState::ILL) {
    status.set_status(Nemesis::StatusCode::ILL);
  } else if (state == Nemesis::Process::ReturnState::SEG) {
    status.set_status(Nemesis::StatusCode::SEG);
  } else if (state == Nemesis::Process::ReturnState::FPE) {
    status.set_status(Nemesis::StatusCode::FPE);
  } else if (state == Nemesis::Process::ReturnState::RE) {
    status.set_status(Nemesis::StatusCode::RE);
  } else if (state == Nemesis::Process::ReturnState::OE) {
    status.set_status(Nemesis::StatusCode::OE);
  } else if (state == Nemesis::Process::ReturnState::SYS) {
    status.set_status(Nemesis::StatusCode::SYS);
  } else if (state == Nemesis::Process::ReturnState::FSZ) {
    status.set_status(Nemesis::StatusCode::FSZ);
  } else {
    status.set_status(Nemesis::StatusCode::SYS);
  }

  if (status.IsInitialized() == false) {
    std::cerr << "status.IsInitialized() == false" << std::endl;
    std::cerr << status.DebugString() << std::endl;

    status.set_id(globalArgs.id);
    status.set_status(Nemesis::StatusCode::SYS);
    status.set_verdict(false);
    status.set_time(-1);
    status.set_memory(-1);

    status.SerializeToOstream(&protobuff_output);
    protobuff_output.close();

    exit(EXIT_FAILURE);
  }

  if (status.SerializeToOstream(&protobuff_output) == false) {
    std::cerr
        << "status.SerializeToOstream(protobuff_output) == false : path => "
        << path_to_output << std::endl;
    exit(EXIT_FAILURE);
  }

  protobuff_output.close();

  if (globalArgs.verbose_flag)
    std::cerr << status.DebugString() << std::endl;

  exit(EXIT_SUCCESS);
}
