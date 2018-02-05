#!/usr/bin/env python

import os
import sys
import subprocess
import re

if len(sys.argv) > 2:
    PYLINT = sys.argv[2] + '/pylint'
else:
    PYLINT = 'pylint'

BASE_PATH             = sys.argv[1]
OUTPUT_FILE           = None
EXTRA_LIBS            = []
DISABLED_SETTINGS     = []
IGNORE_PATTERNS       = []
ADDITIONAL_PARAMETERS = ["--max-args=11", "--max-attributes=11", "--max-line-length=120",
                         "--disable=bad-builtin,locally-disabled,cyclic-import"]
CODE_RATING           = re.compile(r'Your code has been rated at ([-0-9].*)/10 \(previous run: ([-0-9.]*)/10,*')
FILE_NAME             = re.compile(r'[-a-zA-Z0-9_/]*\.py')





def setup_paths():
  old_pythonpath = None
  old_path       = os.environ['PATH']
  for path in EXTRA_LIBS:
    os.environ['PATH'] += os.pathsep + path
  if not os.environ.get("PYTHONPATH"):
    os.environ['PYTHONPATH'] = ''
  else:
    old_pythonpath = os.environ['PYTHONPATH']
  for path in EXTRA_LIBS:
    os.environ["PYTHONPATH"] += os.pathsep + path
  return old_path, old_pythonpath


def reset_paths(old_path, old_pythonpath=None):
  os.environ['PATH'] = old_path
  if old_pythonpath:
    os.environ['PYTHONPATH'] = old_pythonpath
  else:
    del os.environ['PYTHONPATH']


def construct_command():
  command = [PYLINT, BASE_PATH, '-f', 'parseable']
  if DISABLED_SETTINGS:
    command.append('--disable=%s' % ','.join(DISABLED_SETTINGS))
  if IGNORE_PATTERNS:
    command.append('--ignore=%s' % ','.join(IGNORE_PATTERNS))
  if ADDITIONAL_PARAMETERS:
    command.extend(ADDITIONAL_PARAMETERS)
  return command


def run_pylint():
  os.chdir(BASE_PATH)
  command = construct_command()
  try:
    output = subprocess.check_output(command, stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    output = e.output
  match = CODE_RATING.search(output)
  if not match or float(match.group(1)) < float(match.group(2)):
    exitcode = 1
  else:
    exitcode = 0
  if OUTPUT_FILE:
    with open(OUTPUT_FILE, 'w') as fd:
      fd.write(output)
  return exitcode, output


def add_file_paths(input):
  output = ''
  for line in input.split('\n'):
    if FILE_NAME.match(line):
      output += '%s/%s' % (BASE_PATH, line)
    else:
      output += line
    output += '\n'
  return output


def main():
  old_path, old_pythonpath = setup_paths()
  exitcode, output = run_pylint()
  output = add_file_paths(output)
  reset_paths(old_path, old_pythonpath)
  print output
  sys.exit(exitcode)

if __name__ == '__main__':
  main()
