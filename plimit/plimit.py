"""Packet ratelimiting proxy implementation."""

__all__ = ("PacketLimiter",)

from collections import defaultdict
import time

MAX_RECV_BYTES = 4096

class PacketLimiter:
    blocked_ips = []


    def __init__(self, serveraddress):
        self._serveraddress = serveraddress
        self._count_recvd_from = defaultdict(int)
        self._send_rates_by_ip = {}
        self._time_of_first_recvd_from = {}


    def average_send_rate(self, ip):
        return self._send_rates_by_ip.get(ip, 0)


    def listen(self, at_socket):
        while True:

            data, server = at_socket.recvfrom(MAX_RECV_BYTES)
            if not data:
                break

            ip, port = server

            self._count_recvd_from[ip] += 1

            try:
                first_recvd_at = self._time_of_first_recvd_from[ip]
            except KeyError:
                first_recvd_at = time.time()
                self._time_of_first_recvd_from[ip] = time.time()
          
            time_elapsed = time.time() - first_recvd_at
            self._send_rates_by_ip[ip] = (
                time_elapsed / self._count_recvd_from[ip]
            )

            at_socket.sendto(data, self._serveraddress)

