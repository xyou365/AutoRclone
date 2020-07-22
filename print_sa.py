# auto rclone
# Print service account emails and store it into txt file
#
# Author Telegram https://t.me/szhu25
# Inbox  github@stevenz.net

from __future__ import print_function

import os, argparse, time, json, glob

stt = time.time()

parse = argparse.ArgumentParser(
    description='A tool to add service accounts to groups for your organization from a folder containing credential '
                'files.')
parse.add_argument('--path', '-p', default='accounts',
                   help='Specify an alternative path to the service accounts folder.')
# service-account@googlegroups.com

args = parse.parse_args()
acc_dir = args.path

sa = glob.glob('%s/*.json' % acc_dir)

saList = []

print('Generating List')
for i in sa:
    ce = json.loads(open(i, 'r').read())['client_email']
    saList.append(ce)

print('List generated')
print('Deduping...')
saList1 = list(dict.fromkeys(saList))
print('Complete.')

hours, rem = divmod((time.time() - stt), 3600)
minutes, sec = divmod(rem, 60)
print("Elapsed Time:\n{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), sec))

with open('salist.txt', 'w') as f:
    for i in saList1:
        print(i, file=f)
