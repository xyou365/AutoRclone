# auto rclone
# Print service account emails and store it into txt file
#
# Author Telegram https://t.me/szhu25
# Inbox  github@stevenz.net
# Version 0.3

from __future__ import print_function

import argparse
import glob
import json
import sys
import time


# Colored printing functions for strings that use universal ANSI escape sequences.
# fail: bold red, pass: bold green, warn: bold yellow,
# info: bold blue, bold: bold white

class ColorPrint:

    @staticmethod
    def print_fail(message, end='\n'):
        sys.stderr.write('\x1b[1;31m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_pass(message, end='\n'):
        sys.stdout.write('\x1b[1;32m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_warn(message, end='\n'):
        sys.stderr.write('\x1b[1;33m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_info(message, end='\n'):
        sys.stdout.write('\x1b[1;34m' + message.strip() + '\x1b[0m' + end)

    @staticmethod
    def print_bold(message, end='\n'):
        sys.stdout.write('\x1b[1;37m' + message.strip() + '\x1b[0m' + end)


stt = time.time()

parse = argparse.ArgumentParser(
    description='A tool to add service accounts to groups for your organization from a folder containing credential '
                'files.')
parse.add_argument('--path', '-p', default='accounts',
                   help='Specify an alternative path to the service accounts folder.')
parse.add_argument('--sa', '-sa', default='salist.txt',
                   help='Specify an alternative path to generate list of your service accounts.')
parse.add_argument('--seperator', '-sp', default='0',
                   help='Insert a empty line for every x lines to better seperate email adding process.')
parse.add_argument('--project', '-project', default='',
                   help='Project filter, specify this will only output emails that belong to the project you specified.')

args = parse.parse_args()
acc_dir = args.path
sa_file = args.sa
sp_num = args.seperator
sa_project = args.project

sa = glob.glob('%s/*.json' % acc_dir)

saList = []

ColorPrint.print_info('Generating List')

for i in sa:
    ce = json.loads(open(i, 'r').read())['client_email']
    saList.append(ce)

initSASize = len(saList)
if (initSASize == 0):
    raise ValueError('No Service Account json file found under %s directory' % acc_dir)
else:
    ColorPrint.print_info('List generated')

ColorPrint.print_info('Deduping...')
saList = list(dict.fromkeys(saList))
deduSASize = len(saList)

if (sa_project != ""):
    ColorPrint.print_info("Filtering email from %s." % sa_project)
    saList = [n for n in saList if sa_project in n]
    if (len(saList) == 0):
        raise ValueError('No Service Account json file matches %s' % sa_project)

print("Writing SA to file.")
with open(sa_file, 'w') as f:
    for i in range(len(saList)):
        if ((int(sp_num) <= len(saList) + 1) and (int(sp_num) != 0) and (i % int(sp_num) == 0)):
            print("", file=f)
        print(saList[i], file=f)

ColorPrint.print_pass('Complete.\n %i SA write to file' % len(saList))
ColorPrint.print_info('Your file is located at %s' % sa_file)

hours, rem = divmod((time.time() - stt), 3600)
minutes, sec = divmod(rem, 60)
ColorPrint.print_info("Elapsed Time: {:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), sec))

if (initSASize != deduSASize):
    ColorPrint.print_warn("Your SA directory contains %i duplicate." % (initSASize - deduSASize))
