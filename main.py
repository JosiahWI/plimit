#!/usr/bin/env python3

from plimit import PacketLimiter

import socket

SERVER_ADDRESS = ("localhost", 30000)

if __name__ == "__main__":
    limiter = PacketLimiter()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SERVER_ADDRESS)
    print("Bound to {}:{}".format(*SERVER_ADDRESS))

    limiter.listen(sock)

