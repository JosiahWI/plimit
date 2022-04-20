#!/usr/bin/env python3

from plimit import PacketLimiter

import argparse
import socket

DEFAULT_LISTEN_ADDRESS = ("localhost", 30000)
DEFAULT_SERVER_ADDRESS = ("localhost", 30001)

parser = argparse.ArgumentParser()
parser.add_argument(
    "-l",
    "--listen_addr",
    default=DEFAULT_LISTEN_ADDRESS,
    help="listen address in format addr:port"
)
parser.add_argument(
    "-t",
    "--target_addr",
    default=DEFAULT_SERVER_ADDRESS,
    help="server address in format addr:port"
)


def parse_addr(addr):
    ip, port = addr.split(":")
    return ip, int(port)


if __name__ == "__main__":
    args = parser.parse_args()
    
    target_addr = parse_addr(args.target_addr)
    listen_addr = parse_addr(args.listen_addr)
    
    limiter = PacketLimiter(target_addr)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(listen_addr)
    print("Bound to {}\nRelaying to {}".format(
        args.listen_addr,
        args.target_addr
    ))

    limiter.listen(sock)

