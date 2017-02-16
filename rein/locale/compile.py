import os
import subprocess

for f in os.listdir(os.getcwd()):
	if f.endswith('.po'):
		subprocess.call("msgfmt {} -o {}".format(f, f.replace('.po', '.mo')))
		print('Compiling {} to .mo format'.format(f))