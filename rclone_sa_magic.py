# auto rclone
#
# Author Telegram https://t.me/CodyDoby
# Inbox  codyd@qq.com
#
# can copy from
# - [x] publicly shared folder to Team Drive
# - [x] Team Drive to Team Drive
# - [x] publicly shared folder to publicly shared folder
# - [x] Team Drive to publicly shared folder
# - [ ] private folder to any (think service accounts cannot do anything about private folder)
#
import argparse
import glob
import json
import os
import platform
import subprocess
import sys
import time
from signal import signal, SIGINT

# =================modify here=================
logfile = "log_rclone.txt"  # log file: tail -f log_rclone.txt
screen_name = "wrc"
# change it when u know what are u doing
SIZE_GB_MAX = 735
CNT_403_RETRY = 600
# =================modify here=================


def is_windows():
    return platform.system() == 'Windows'


def handler(signal_received, frame):
    if is_windows():
        kill_cmd = 'taskkill /IM "rclone.exe" /F'
    else:
        kill_cmd = "screen -r -S %s -X quit" % screen_name

    try:
        subprocess.check_call(kill_cmd, shell=True)
    except:
        pass
    sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser(description="Copy from source (publicly shared drive/Team Drive) "
                                                 "to destination (publicly shared drive/Team Drive).")
    parser.add_argument('-s', '--source_id', type=str, required=True,
                        help='the id of source')
    parser.add_argument('-d', '--destination_id', type=str, required=True,
                        help='the id of destination')

    parser.add_argument('-sf', '--source_folder', type=str, default="",
                        help='the folder path of source')
    parser.add_argument('-df', '--destination_folder', type=str, default="",
                        help='the folder path of destination')

    parser.add_argument('-start', '--start_sa_id', type=int, default=1,
                        help='the folder path of source')
    parser.add_argument('-end', '--end_sa_id', type=int, default=200,
                        help='the folder path of destination')

    parser.add_argument('-c', '--rclone_config_file', type=str,
                        help='rclone file path of rclone')
    parser.add_argument('-t', '--test_only', action="store_true",
                        help='rclone file path of rclone')

    args = parser.parse_args()
    return args


def gen_rclone_cfg(args):
    sa_files = glob.glob(os.path.join('accounts', '*.json'))
    output_of_config_file = './rclone.conf'

    with open(output_of_config_file, 'w') as fp:
        for i, filename in enumerate(sa_files):

            dir_path = os.path.dirname(os.path.realpath(__file__))
            filename = os.path.join(dir_path, filename)
            filename = filename.replace(os.sep, '/')

            if len(args.source_id) == 33:
                folder_or_team_drive = 'root_folder_id'
            elif len(args.source_id) == 19:
                folder_or_team_drive = 'team_drive'
            else:
                return print('Wrong length of team_drive_id or publicly shared root_folder_id')

            try:
                fp.write('[{}{:03d}]\n'
                         'type = drive\n'
                         'scope = drive\n'
                         'service_account_file = {}\n'
                         '{} = {}\n\n'.format('src', i, filename, folder_or_team_drive, args.source_id))
            except:
                return print("failed to write {} to {}".format(args.source_id, output_of_config_file))

            try:
                fp.write('[{}{:03d}]\n'
                         'type = drive\n'
                         'scope = drive\n'
                         'service_account_file = {}\n'
                         '{} = {}\n\n'.format('dst', i, filename, folder_or_team_drive, args.destination_id))
            except:
                return print("failed to write {} to {}".format(args.destination_id, output_of_config_file))

    return output_of_config_file, i


def main():
    signal(SIGINT, handler)

    args = parse_args()

    id = args.start_sa_id
    end_id = args.end_sa_id

    config_file = args.rclone_config_file
    if config_file is None:
        print('generating rclone config file.')
        config_file, end_id = gen_rclone_cfg(args)
        print('rclone config file generated.')
    else:
        return print('not supported yet.')
        pass
        # need parse labels from config files

    time_start = time.time()
    print("Start: " + str(time_start))

    while id <= end_id + 1:

        if id == end_id + 1:
            break
            # id = 1

        with open('current_sa.txt', 'w') as fp:
            fp.write(str(id) + '\n')

        src_label = "src" + "{0:03d}".format(id) + ":"
        dst_label = "dst" + "{0:03d}".format(id) + ":"

        open_cmd = "rclone --config {} copy ".format(config_file)
        if args.test_only:
            open_cmd += "--dry-run "

        open_cmd += "--drive-server-side-across-configs --rc -vv --ignore-existing " \
                    "--tpslimit 3 --transfers 3 --drive-chunk-size 32M --fast-list " \
                    "--log-file={} {} {}".format(logfile,
                                                src_label + args.source_folder,
                                                dst_label + args.destination_folder)

        if not is_windows():
            open_cmd = "screen -d -m -S {} ".format(screen_name) + open_cmd
        else:
            open_cmd = "start /b " + open_cmd

        print(open_cmd)

        try:
            subprocess.check_call(open_cmd, shell=True)
            print(">> Let us go %s" % dst_label)
            time.sleep(10)
        except subprocess.SubprocessError as error:
            return print("error: " + str(error))

        cnt_error = 0
        cnt_403_retry = 0
        size_GB_done_before = 0
        while True:
            cmd = 'rclone rc core/stats'
            try:
                response = subprocess.check_output(cmd, shell=True)
                cnt_error = 0
            except subprocess.SubprocessError as error:
                # continually ...
                cnt_error = cnt_error + 1
                if cnt_error >= 3:
                    print('No rclone task detected. Check your rclone cmd.')
                    return

                continue

            response_processed = response.decode('utf-8').replace('\0', '')
            response_processed_json = json.loads(response_processed)

            print(response_processed_json)

            size_GB_done = int(int(response_processed_json['bytes']) * 9.31322e-10)
            speed_now = float(int(response_processed_json['speed']) * 9.31322e-10 * 1024)

            print("%s %dGB Done @ %fMB/s" % (dst_label, size_GB_done, speed_now), end="\r")

            # continually no ...
            if size_GB_done - size_GB_done_before == 0:
                cnt_403_retry += 1
            else:
                cnt_403_retry = 0

            size_GB_done_before = size_GB_done

            # Stop by error (403) info
            if size_GB_done >= SIZE_GB_MAX or cnt_403_retry >= CNT_403_RETRY:

                if is_windows():
                    kill_cmd = 'taskkill /IM "rclone.exe" /F'
                else:
                    kill_cmd = "screen -r -S %s -X quit" % screen_name

                subprocess.check_call(kill_cmd, shell=True)
                print('\n')

                break

            time.sleep(2)
        id = id + 1

        time_stop = time.time()
        print(str((time_stop - time_start) / 60 / 60) + "小时")


if __name__ == "__main__":
    main()