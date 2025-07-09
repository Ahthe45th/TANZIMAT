#!/usr/bin/env python3
import subprocess
import os

script_dir = os.path.dirname(os.path.realpath(__file__))
kill_script_path = os.path.join(script_dir, 'kill_firefox.sh')

subprocess.run([kill_script_path])
