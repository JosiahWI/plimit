import threading
import time
import unittest

from plimit import PacketLimiter

TEST_MSG = bytes("yay", "UTF-8")
TEST_LISTEN_ADDRESS = ("localhost", 30000)
TEST_SERVER_ADDRESS = ("localhost", 30001)

class MockSocket:


    def __init__(self):
        self._queue = []
        self._sent = []


    def recvfrom(self, bytes):
        while not self._queue:
            continue

        return self._queue.pop(0)


    def send(self, message, serveraddress):
        self._sent.append((message, serveraddress))


    def insert(self, packet):
        self._queue.append(packet)


    def pop(self, idx):
        return self._sent.pop(idx)


class TestPacketLimiter(unittest.TestCase):


    def setUp(self):
        self.limiter = PacketLimiter(TEST_SERVER_ADDRESS)
        self.mock_socket = MockSocket()
        self.proxy_thread = threading.Thread(
            target=self.limiter.listen,
            args=[self.mock_socket]
        )
        self.proxy_thread.start()


    def tearDown(self):
        self.wait_for_proxy_thread()


    def wait_for_proxy_thread(self):
        self.mock_socket.insert(("", TEST_LISTEN_ADDRESS))
        self.proxy_thread.join()


    def send_at_intervals(
            self,
            intervals,
            addr=TEST_SERVER_ADDRESS,
            message=TEST_MSG
        ):
        for sleep_time in intervals:
            time.sleep(sleep_time)
            self.mock_socket.insert((message, addr))


    def test_new_limiter_will_have_no_ips_blocked(self):
        self.assertCountEqual(self.limiter.blocked_ips, [])


    def test_when_limiter_has_recvd_no_packets_from_ip_rate_will_be_zero(self):
        self.assertEqual(self.limiter.average_send_rate("127.0.0.1"), 0)


    def test_when_limiter_recvs_packets_will_update_rate_correctly(self):
        first_addr, second_addr = (
            ("192.168.22.203", 30000),
            ("192.168.22.204", 30000)
        )

        first_intervals = [0, 0.01, 0.02, 0.04, 0.03]
        second_intervals = [0, 0.06, 0.07]

        first_average_rate = sum(first_intervals) / len(first_intervals)
        second_average_rate = sum(second_intervals) / len(second_intervals)

        self.send_at_intervals(first_intervals, addr=first_addr)
        self.send_at_intervals(second_intervals, addr=second_addr)

        self.wait_for_proxy_thread()

        self.assertAlmostEqual(
            self.limiter.average_send_rate(first_addr[0]),
            first_average_rate,
            2
        )
        self.assertAlmostEqual(
            self.limiter.average_send_rate(second_addr[0]),
            second_average_rate,
            2
        )


    def test_when_limiter_recvs_from_multiple_ips_will_distinguish_them(self):
        first_addr, second_addr = (
            ("192.168.22.203", 30000),
            ("192.168.22.204", 30000)
        )

        self.send_at_intervals([0], addr=first_addr)
        self.send_at_intervals([0, 0.1], addr=second_addr)

        self.wait_for_proxy_thread()
        self.assertGreater(
            self.limiter.average_send_rate(second_addr[0]),
            self.limiter.average_send_rate(first_addr[0])
        )


    def test_when_limiter_recvs_message_will_send_it_to_server(self):
        self.send_at_intervals([0], message=bytes("Hello, World!", "UTF-8"))
        
        expected = (b"Hello, World!", TEST_SERVER_ADDRESS)
        self.wait_for_proxy_thread()
        try:
            got = self.mock_socket.pop(-1)
        except IndexError:
            self.assertTrue(False, "listener did not send to socket")

        self.assertEqual(got, expected)


if __name__ == "__main__":
    unittest.main()

