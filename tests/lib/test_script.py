import unittest

from rein.lib.script import parse_script, check_2_of_3, check_mandatory_multisig, build_2_of_3, build_mandatory_multisig

class TestScript(unittest.TestCase):
	def test_2_of_3(self):
		# primary payment 2-of-3 redeem script
		p = parse_script('5221029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb0052102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c4651921026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc53ae')
		self.assertTrue(check_2_of_3(p, ['029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
										 '02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
										 '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))
		# switch key order
		self.assertTrue(check_2_of_3(p, ['02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
										 '029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
										 '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))

	def test_mandatory_multisig(self):
		# mandatory multisig for mediator

		m = parse_script('2102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519ad5121029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb00521026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc52ae')
		self.assertTrue(check_mandatory_multisig(m, '02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
												   ['029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
													'026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))
		# switch non-mandatory key order
		self.assertTrue(check_mandatory_multisig(m, '02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
												   ['029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
													'026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))
		# mix up mandatory and non-mandatory keys
		self.assertFalse(check_mandatory_multisig(m, '029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
													['02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
													 '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))

	def test_build_redeem_scripts(self):
		self.assertEquals(build_2_of_3(['02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
										'029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
										'026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc'])[0], 
						  '522102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c4651921029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb00521026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc53ae')

		self.assertEquals(build_mandatory_multisig('02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
												  ['029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
												   '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc'])[0],
						  '2102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519ad5121029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb00521026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc52ae')