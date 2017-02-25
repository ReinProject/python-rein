import unittest

from rein.lib.bitcoinaddress import check_bitcoin_address, generate_sin

class TestBitcoinAddress(unittest.TestCase):
	def test_check_bitcoin_address(self):
		self.assertTrue(check_bitcoin_address('1CptxARjqcfkVwGFSjR82zmPT8YtRMubub'))
		self.assertTrue(check_bitcoin_address('3746f7fjJ6fG1pQXDjA8xy9WAzf4968WWv'))
		self.assertFalse(check_bitcoin_address('2746f7fjJ6fG1pQXDjA8xy9WAzf4968WWv'))

	def test_sin_generation(self):
		self.assertEqual(generate_sin('02F840A04114081690223B7069071A70D6DABB891763B638CC20C7EC3BD58E6C86'), 'TfG4ScDgysrSpodWD4Re5UtXmcLbY5CiUHA')