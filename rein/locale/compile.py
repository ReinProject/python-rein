import os
import subprocess

# Compile all .po files within the current working directory to .mo format
for f in os.listdir(os.getcwd()):
	if f.endswith('.po'):
		subprocess.call("msgfmt {} -o {}".format(f, f.replace('.po', '.mo')))
		print('Compiling {} to .mo format'.format(f))