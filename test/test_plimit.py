import threading
import time
import unittest

from plimit import PacketLimiter


class MockSocket:


    def __init__(self):
        self._queue = []


    def recvfrom(self, bytes):
        while not self._queue:
            continue

        return self._queue.pop(0)


    def insert(self, packet):
        self._queue.append(packet)


class TestPacketLimiter(unittest.TestCase):


    def setUp(self):
        self.limiter = PacketLimiter()
        self.mock_socket = MockSocket()
        self.proxy_thread = threading.Thread(
            target=self.limiter.listen,
            args=[self.mock_socket]
        )
        self.proxy_thread.start()


    def tearDown(self):
        self.wait_for_proxy_thread()


    def wait_for_proxy_thread(self):
        self.mock_socket.insert(("", "127.0.0.1"))
        self.proxy_thread.join()


    def send_at_intervals(self, intervals, ip="127.0.0.1", message="yay"):
        for sleep_time in intervals:
            time.sleep(sleep_time)
            self.mock_socket.insert((message, ip))


    def test_new_limiter_will_have_no_ips_blocked(self):
        self.assertCountEqual(self.limiter.blocked_ips, [])


    def test_when_limiter_has_recvd_no_packets_from_ip_rate_will_be_zero(self):
        self.assertEqual(self.limiter.average_send_rate("127.0.0.1"), 0)


    def test_when_limiter_recvs_packets_will_update_rate_correctly(self):
        first_ip, second_ip = ("192.168.22.203", "192.168.22.204")

        first_intervals = [0, 0.01, 0.02, 0.04, 0.03]
        second_intervals = [0, 0.06, 0.07]

        first_average_rate = sum(first_intervals) / len(first_intervals)
        second_average_rate = sum(second_intervals) / len(second_intervals)

        self.send_at_intervals(first_intervals, ip=first_ip)
        self.send_at_intervals(second_intervals, ip=second_ip)

        self.wait_for_proxy_thread()

        self.assertAlmostEqual(
            self.limiter.average_send_rate(first_ip),
            first_average_rate,
            2
        )
        self.assertAlmostEqual(
            self.limiter.average_send_rate(second_ip),
            second_average_rate,
            2
        )


    def test_when_limiter_recvs_from_multiple_ips_will_distinguish_them(self):
        first_ip, second_ip = ("192.168.22.203", "192.168.22.204")
        self.send_at_intervals([0], ip=first_ip, message="huh")
        self.send_at_intervals([0, 0.1], ip=second_ip)

        self.wait_for_proxy_thread()
        self.assertGreater(
            self.limiter.average_send_rate(second_ip),
            self.limiter.average_send_rate(first_ip)
        )


if __name__ == "__main__":
    unittest.main()

