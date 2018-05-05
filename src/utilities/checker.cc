#include <cstdlib>
#include <cstdio>
#include <getopt.h>

struct globalArgs_t {
  char *src;
  char *input;
  char *output;
  char *answer;
  int verbose_flag;

  int flags;

  globalArgs_t() {
    src = NULL;
    input = NULL;
    output = NULL;
    answer = NULL;
    verbose_flag = 0;
    flags = 0;
  }

} globalArgs;


int check(FILE *src, FILE *input, FILE *output, FILE *answer, int verbose);

int main(int argc, char **argv) {
  int opt;
  
  while (true) {
    static struct option long_options[] = 
    {
      {"verbose", no_argument,  &globalArgs.verbose_flag, 1},
      {"src", required_argument,  NULL, 's'},
      {"input", required_argument,  NULL, 'i'},
      {"output",  required_argument,  NULL, 'o'},
      {"answer",  required_argument,  NULL, 'a'},
      {NULL,  NULL, NULL, NULL}
    };

    static const char *optString = "s:i:o:a:";
    int option_index = 0;

    opt = getopt_long(argc, argv, optString, long_options, &option_index);
    
    if (opt == -1)
      break;

    switch (opt) {
      case 0:
        globalArgs.flags |= 1<<0;
        break;

      case 's':
        globalArgs.src = optarg;
        globalArgs.flags |= 1<<1;
        break;

      case 'i':
        globalArgs.input = optarg;
        globalArgs.flags |= 1<<2;
        break;

      case 'o':
        globalArgs.output = optarg;
        globalArgs.flags |= 1<<3;
        break;

      case 'a':
        globalArgs.answer = optarg;
        globalArgs.flags |= 1<<4;
        break;

      default:
        fprintf(stderr, "%s: wrong args\n", argv[0]);
        abort();
    }
  }

  static const int good_flags[] = { 
    ((1<<1) | (1<<2) | (1<<3) | (1<<4)),
    ((1<<0) | (1<<1) | (1<<2) | (1<<3) | (1<<4)),
    NULL
  };

  if (globalArgs.flags != good_flags[0] && globalArgs.flags != good_flags[1]) {
    fprintf(stderr, "%s: wrong args\n", argv[0]);
    abort();
  }

  FILE *src = fopen(globalArgs.src, "r");
  FILE *input = fopen(globalArgs.input, "r");
  FILE *output = fopen(globalArgs.output, "r");
  FILE *answer = fopen(globalArgs.answer, "r");

  if (src == NULL || input == NULL || output == NULL || answer == NULL) {
    if (src) 
      fclose(src);
    if (input)
      fclose(input);
    if (output)
      fclose(output);
    if (answer)
      fclose(answer);
    abort();
  }

  int status = check(src, input, output, answer, globalArgs.verbose_flag);

  fclose(src); 
  fclose(input); 
  fclose(output); 
  fclose(answer);

  return status;
}



int check(FILE *src, FILE *in, FILE *out, FILE *ans, int verbose) {
}
