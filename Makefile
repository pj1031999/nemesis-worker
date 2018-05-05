MAKE = make
INSTALL = install
CXX = g++
CXXFLAGS = -std=c++14 -O3 -Wall -Wextra -fno-exceptions -pthread

INCLUDE = -I$(CURDIR)/src/jail/src/include -I$(CURDIR)/src/proto/build
LIB = -lseccomp -lprotobuf

OBJ = build/sandbox.o $(CURDIR)/src/jail/build/process.o \
	  $(CURDIR)/src/jail/build/timer.o $(CURDIR)/src/proto/build/nemesis.pb.o

PREFIX = /usr/local

all: prepare build/sandbox

build/sandbox: build/sandbox.o
	$(CXX) $(CXXFLAGS) $(LIB) -o $(CURDIR)/build/sandbox $(OBJ)

build/sandbox.o: prepare jail proto
	$(CXX) $(CXXFLAGS) $(INCLUDE) -c -o $(CURDIR)/build/sandbox.o $(CURDIR)/src/sandbox.cc

jail:
	$(MAKE) -C $(CURDIR)/src/jail all

proto:
	$(MAKE) -C $(CURDIR)/src/proto all

test: jail
	$(MAKE) -C $(CURDIR)/src/jail all test

prepare:
	@mkdir -p build

clean:
	@rm -rf $(CURDIR)/build/*.o
	$(MAKE) -C $(CURDIR)/src/jail clean

distclean: clean
	@rm -rf $(CURDIR)/build
	$(MAKE) -C $(CURDIR)/src/jail distclean
	$(MAKE) -C $(CURDIR)/src/proto distclean

install: all
	@mkdir -p $(PREFIX)/sbin
	@mkdir -p $(PREFIX)/bin
	@mkdir -p $(PREFIX)/lib/nemesis/python
	@mkdir -p $(PREFIX)/lib/nemesis/ram2cpp
	$(INSTALL) -m 0755 $(CURDIR)/src/utilities/ram2cpp $(PREFIX)/bin
	$(INSTALL) -m 0755 $(CURDIR)/build/sandbox $(PREFIX)/sbin/sandbox
	$(INSTALL) -m 0755 $(CURDIR)/src/python/worker.py $(PREFIX)/sbin/worker
	$(INSTALL) -m 0755 $(CURDIR)/src/python/runner.py $(PREFIX)/sbin/runner
	$(INSTALL) -m 0644 $(CURDIR)/src/python/sandbox.py $(PREFIX)/lib/nemesis/python
	$(INSTALL) -m 0644 $(CURDIR)/src/python/runner.py $(PREFIX)/lib/nemesis/python
	$(INSTALL) -m 0644 $(CURDIR)/src/python/judger.py $(PREFIX)/lib/nemesis/python
	$(INSTALL) -m 0644 $(CURDIR)/src/python/compile_sandbox.py $(PREFIX)/lib/nemesis/python
	$(INSTALL) -m 0644 $(CURDIR)/src/proto/build/nemesis_pb2.py $(PREFIX)/lib/nemesis/python
	$(INSTALL) -m 0644 $(CURDIR)/src/proto/default_nemesis_proto.py $(PREFIX)/lib/nemesis/python

.PHONY: all jail test prepare clean install
