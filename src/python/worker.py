#!/usr/bin/python3

import argparse
import judger
import logging
import nemesis_pb2
import os
import threading
import time
import zmq

def heartbeat(data, addr, port):
    while True:
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect("tcp://%s:%s" % (addr, port))
        socket.send(data.SerializeToString())
        socket.close()
        time.sleep(2)


def worker(addr, port, logger):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://%s:%s" % (addr, port))

    while True:
        logger.info("worker(): waiting for a job")
        msg = socket.recv()
        job = nemesis_pb2.Job()
        job.ParseFromString(msg)
        if job.IsInitialized() == False:
            logger.error('worker(): job.IsInitialized() == False')
            continue
        logger.info("worker(): get job ({},{})".format(job.submit.id, job.custom_job.id))
        judge = judger.Judger(conf=job, logger=logger)
        status = judge.run()
        socket.send(status.SerializeToString())


def main_local():
    parser = argparse.ArgumentParser(description="Nemesis Worker")
    parser.add_argument('--addr', dest="addr", default="*", type=str, help="address")
    parser.add_argument('--port', dest="port", default=5556, type=str, help="port")
    parser.add_argument('--name', dest="name", default="WORKER_LOCALHOST_O1", type=str, help="worker name")
    parser.add_argument('--logic_addr', dest="logic_addr", default="localhost", type=str, help="logic address")
    parser.add_argument('--logic_port', dest="logic_port", default="5555", type=str, help="logic port")
    parser.add_argument('--id', dest="id", default=1, type=int, help="worker id")
    parser.add_argument('--heartbeat_port', dest="heartbeat_port", type=str, default="5550", help="heartbeat port")

    args = parser.parse_args()

    worker_data = nemesis_pb2.Heartbeat()
    worker_data.id = args.id
    worker_data.name = args.name
    worker_data.port = args.port
    worker_data.addr = args.addr

    thread_heartbeat = threading.Thread(target = heartbeat, args = (worker_data, args.logic_addr, args.heartbeat_port))
    thread_heartbeat.daemon = True
    thread_heartbeat.start()

    logging.basicConfig(level=logging.INFO)

    worker(args.addr, args.port, logging.getLogger(args.name))

def main():
    worker_data = nemesis_pb2.Heartbeat()

    worker_data.id =    int(os.getenv("WORKER_ID"))
    worker_data.name =  os.getenv("WORKER_NAME")
    worker_data.port =  os.getenv("WORKER_PORT")
    worker_data.addr =  os.getenv("WORKER_ADDR")

    name =              os.getenv("WORKER_NAME")
    port =              os.getenv("WORKER_PORT")
    logic_addr =        os.getenv("LOGIC_ADDR")
    addr =              os.getenv("WORKER_ADDR")
    heartbeat_port =    os.getenv("HEARTBEAT_PORT")

    thread_heartbeat = threading.Thread(target = heartbeat, args = (worker_data, logic_addr, heartbeat_port))
    thread_heartbeat.daemon = True
    thread_heartbeat.start()

    logging.basicConfig(level=logging.INFO)

    worker(addr, port, logging.getLogger(name))



if __name__ == "__main__":
    main()
