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
import time

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

print('Generating List')

for i in sa:
    ce = json.loads(open(i, 'r').read())['client_email']
    saList.append(ce)

print('List generated')
print('Deduping...')
saList = list(dict.fromkeys(saList))
if (sa_project != ""):
    print("Filtering email from %s." % sa_project)
    saList = [n for n in saList if sa_project in n]
print('Complete.')

hours, rem = divmod((time.time() - stt), 3600)
minutes, sec = divmod(rem, 60)
print("Elapsed Time:\n{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), sec))

with open(sa_file, 'w') as f:
    for i in range(len(saList)):
        if ((int(sp_num) <= len(saList) + 1) and (int(sp_num) != 0) and (i % int(sp_num) == 0)):
            print("", file=f)
        print(saList[i], file=f)
