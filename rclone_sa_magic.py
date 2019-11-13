# auto rclone
#
# Author Telegram https://t.me/CodyDoby
# Inbox  codyd@qq.com
#
# can copy from
# - [x] publicly shared folder to Team Drive
# - [x] Team Drive to Team Drive
# - [ ] publicly shared folder to publicly shared folder (with write privilege)
# - [ ] Team Drive to publicly shared folder
#   `python3 .\rclone_sa_magic.py -s SourceID -d DestinationID -dp DestinationPathName -b 10`
#
# - [x] local to Team Drive
# - [ ] local to private folder
# - [ ] private folder to any (think service accounts cannot do anything about private folder)
#
from __future__ import print_function
import argparse
import glob
import json
import os, io
import platform
import subprocess
import sys
import time
import distutils.spawn
from signal import signal, SIGINT

# =================modify here=================
logfile = "log_rclone.txt"  # log file: tail -f log_rclone.txt
PID = 0

# parameters for this script
SIZE_GB_MAX = 735  # if one account has already copied 735GB, switch to next account
CNT_DEAD_RETRY = 100  # if there is no files be copied for 100 times, switch to next account
CNT_SA_EXIT = 3  # if continually switch account for 3 times stop script

# change it when u know what are u doing
# paramters for rclone.
# If TPSLIMITxTRANSFERS is too big, will cause 404 user rate limit error,
# especially for tasks with a lot of small files
TPSLIMIT = 3
TRANSFERS = 3
# =================modify here=================


def is_windows():
    return platform.system() == 'Windows'


def handler(signal_received, frame):
    global PID

    if is_windows():
        kill_cmd = 'taskkill /PID {} /F'.format(PID)
    else:
        kill_cmd = "kill -9 {}".format(PID)

    try:
        print("\n" + " " * 20 + " {}".format(time.strftime("%H:%M:%S")))
        subprocess.check_call(kill_cmd, shell=True)
    except:
        pass
    sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser(description="Copy from source (local/publicly shared drive/Team Drive/) "
                                                 "to destination (publicly shared drive/Team Drive).")
    parser.add_argument('-s', '--source_id', type=str,
                        help='the id of source. Team Drive id or publicly shared folder id')
    parser.add_argument('-d', '--destination_id', type=str, required=True,
                        help='the id of destination. Team Drive id or publicly shared folder id')

    parser.add_argument('-sp', '--source_path', type=str, default="",
                        help='the folder path of source. In Google Drive or local.')
    parser.add_argument('-dp', '--destination_path', type=str, default="",
                        help='the folder path of destination. In Google Drive.')

    # if there are some special symbols in source path, please use this
    # path id (publicly shared folder or folder inside team drive)
    parser.add_argument('-spi', '--source_path_id', type=str, default="",
                        help='the folder path id (rather than name) of source. In Google Drive.')

    parser.add_argument('-sa', '--service_account', type=str, default="accounts",
                        help='the folder path of json files for service accounts.')
    parser.add_argument('-cp', '--check_path', action="store_true",
                        help='if check src/dst path or not.')

    parser.add_argument('-p', '--port', type=int, default=5572,
                        help='the port to run rclone rc. set it to different one if you want to run other instance.')

    parser.add_argument('-b', '--begin_sa_id', type=int, default=1,
                        help='the begin id of sa for source')
    parser.add_argument('-e', '--end_sa_id', type=int, default=600,
                        help='the end id of sa for destination')

    parser.add_argument('-c', '--rclone_config_file', type=str,
                        help='config file path of rclone')
    parser.add_argument('-test', '--test_only', action="store_true",
                        help='for test: make rclone print some more information.')
    parser.add_argument('-t', '--dry_run', action="store_true",
                        help='for test: make rclone dry-run.')

    parser.add_argument('--disable_list_r', action="store_true",
                        help='for debug. do not use this.')

    parser.add_argument('--crypt', action="store_true",
                        help='for test: crypt remote destination.')

    parser.add_argument('--cache', action="store_true",
                        help="for test: cache the remote destination.")

    args = parser.parse_args()
    return args


def gen_rclone_cfg(args):
    sa_files = glob.glob(os.path.join(args.service_account, '*.json'))
    output_of_config_file = './rclone.conf'

    if len(sa_files) == 0:
        sys.exit('No json files found in ./{}'.format(args.service_account))

    with open(output_of_config_file, 'w') as fp:
        for i, filename in enumerate(sa_files):

            dir_path = os.path.dirname(os.path.realpath(__file__))
            filename = os.path.join(dir_path, filename)
            filename = filename.replace(os.sep, '/')

            # For source
            if args.source_id:
                if len(args.source_id) == 33:
                    folder_or_team_drive_src = 'root_folder_id'
                elif len(args.source_id) == 19:
                    folder_or_team_drive_src = 'team_drive'
                else:
                    sys.exit('Wrong length of team_drive_id or publicly shared root_folder_id')

                text_to_write = "[{}{:03d}]\n" \
                                "type = drive\n" \
                                "scope = drive\n" \
                                "service_account_file = {}\n" \
                                "{} = {}\n".format('src', i + 1, filename, folder_or_team_drive_src, args.source_id)

                # use path id instead path name
                if args.source_path_id:
                    # for team drive only
                    if len(args.source_id) == 19:
                        if len(args.source_path_id) == 33:
                            text_to_write += 'root_folder_id = {}\n'.format(args.source_path_id)
                        else:
                            sys.exit('Wrong length of source_path_id')
                    else:
                        sys.exit('For publicly shared folder please do not set -spi flag')

                text_to_write += "\n"

                try:
                    fp.write(text_to_write)
                except:
                    sys.exit("failed to write {} to {}".format(args.source_id, output_of_config_file))
            else:
                pass

            # For destination
            if len(args.destination_id) == 33:
                folder_or_team_drive_dst = 'root_folder_id'
            elif len(args.destination_id) == 19:
                folder_or_team_drive_dst = 'team_drive'
            else:
                sys.exit('Wrong length of team_drive_id or publicly shared root_folder_id')

            try:
                fp.write('[{}{:03d}]\n'
                         'type = drive\n'
                         'scope = drive\n'
                         'service_account_file = {}\n'
                         '{} = {}\n\n'.format('dst', i + 1, filename, folder_or_team_drive_dst, args.destination_id))
            except:
                sys.exit("failed to write {} to {}".format(args.destination_id, output_of_config_file))

            # For crypt destination
            if args.crypt:
                remote_name = '{}{:03d}'.format('dst', i + 1)
                try:
                    fp.write('[{}_crypt]\n'
                             'type = crypt\n'
                             'remote = {}:\n'
                             'filename_encryption = standard\n'
                             'password = hfSJiSRFrgyeQ_xNyx-rwOpsN2P2ZHZV\n'
                             'directory_name_encryption = true\n\n'.format(remote_name, remote_name))
                except:
                    sys.exit("failed to write {} to {}".format(args.destination_id, output_of_config_file))

            # For cache destination
            if args.cache:
                remote_name = '{}{:03d}'.format('dst', i + 1)
                try:
                    fp.write('[{}_cache]\n'
                             'type = cache\n'
                             'remote = {}:\n'
                             'chunk_total_size = 1G\n\n'.format(remote_name, remote_name))
                except:
                    sys.exit("failed to write {} to {}".format(args.destination_id, output_of_config_file))

    return output_of_config_file, i


def print_during(time_start):
    time_stop = time.time()
    hours, rem = divmod((time_stop - time_start), 3600)
    minutes, sec = divmod(rem, 60)
    print("Elapsed Time: {:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), sec))


def check_rclone_program():
    # promote if user has not install rclone
    rclone_prog = 'rclone'
    if is_windows():
        rclone_prog += ".exe"
    ret = distutils.spawn.find_executable(rclone_prog)
    if ret is None:
        sys.exit("Please install rclone firstly: https://rclone.org/downloads/")
    return ret


def check_path(path):
    try:
        ret = subprocess.check_output('rclone --config {} --disable ListR size \"{}\"'.format('rclone.conf', path),
                                      shell=True)
        print('It is okay:\n{}'.format(ret.decode('utf-8').replace('\0', '')))
    except subprocess.SubprocessError as error:
        sys.exit(str(error))


def main():
    signal(SIGINT, handler)

    # if rclone is not installed, quit directly
    ret = check_rclone_program()
    print("rclone is detected: {}".format(ret))
    args = parse_args()

    id = args.begin_sa_id
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
    print("Start: {}".format(time.strftime("%H:%M:%S")))

    cnt_acc_error = 0
    while id <= end_id + 1:

        if id == end_id + 1:
            break
            # id = 1

        with io.open('current_sa.txt', 'w', encoding='utf-8') as fp:
            fp.write(str(id) + '\n')

        src_label = "src" + "{0:03d}".format(id) + ":"
        dst_label = "dst" + "{0:03d}".format(id) + ":"
        if args.crypt:
            dst_label = "dst" + "{0:03d}_crypt".format(id) + ":"

        if args.cache:
            dst_label = "dst" + "{0:03d}_cache".format(id) + ":"

        src_full_path = src_label + args.source_path
        if args.source_id is None:
            src_full_path = args.source_path

        dst_full_path = dst_label + args.destination_path
        if args.destination_id is None:
            dst_full_path = args.destination_path

        if args.test_only:
            print('\nsrc full path\n', src_full_path)
            print('\ndst full path\n', dst_full_path, '\n')

        if args.check_path and id == args.begin_sa_id:
            print("Please wait. Checking source path...")
            check_path(src_full_path)

            print("Please wait. Checking destination path...")
            check_path(dst_full_path)

        # =================cmd to run=================
        rclone_cmd = "rclone --config {} copy ".format(config_file)
        if args.dry_run:
            rclone_cmd += "--dry-run "
        # --fast-list is default adopted in the latest rclone
        rclone_cmd += "--drive-server-side-across-configs --rc --rc-addr=\"localhost:{}\" -vv --ignore-existing ".format(args.port)
        rclone_cmd += "--tpslimit {} --transfers {} --drive-chunk-size 32M ".format(TPSLIMIT, TRANSFERS)
        if args.disable_list_r:
            rclone_cmd += "--disable ListR "
        rclone_cmd += "--drive-acknowledge-abuse --log-file={} \"{}\" \"{}\"".format(logfile, src_full_path,
                                                                                     dst_full_path)

        if not is_windows():
            rclone_cmd = rclone_cmd + " &"
        else:
            rclone_cmd = "start /b " + rclone_cmd
        # =================cmd to run=================

        print(rclone_cmd)

        try:
            subprocess.check_call(rclone_cmd, shell=True)
            print(">> Let us go {} {}".format(dst_label, time.strftime("%H:%M:%S")))
            time.sleep(10)
        except subprocess.SubprocessError as error:
            return print("error: " + str(error))

        cnt_error = 0
        cnt_dead_retry = 0
        size_bytes_done_before = 0
        cnt_acc_sucess = 0
        already_start = False

        try:
            response = subprocess.check_output('rclone rc --rc-addr="localhost:{}" core/pid'.format(args.port), shell=True)
            pid = json.loads(response.decode('utf-8').replace('\0', ''))['pid']
            if args.test_only: print('\npid is: {}\n'.format(pid))

            global PID
            PID = int(pid)

        except subprocess.SubprocessError as error:
            pass

        while True:
            rc_cmd = 'rclone rc --rc-addr="localhost:{}" core/stats'.format(format(args.port))
            try:
                response = subprocess.check_output(rc_cmd, shell=True)
                cnt_acc_sucess += 1
                cnt_error = 0
                # if there is a long time waiting, this will be easily satisfied, so check if it is started using
                # already_started flag
                if already_start and cnt_acc_sucess >= 9:
                    cnt_acc_error = 0
                    cnt_acc_sucess = 0
                    if args.test_only: print(
                        "total 9 times success. the cnt_acc_error is reset to {}\n".format(cnt_acc_error))

            except subprocess.SubprocessError as error:
                # continually ...
                cnt_error = cnt_error + 1
                cnt_acc_error = cnt_acc_error + 1
                if cnt_error >= 3:
                    cnt_acc_sucess = 0
                    if args.test_only: print(
                        "total 3 times failure. the cnt_acc_sucess is reset to {}\n".format(cnt_acc_sucess))

                    print('No rclone task detected (possibly done for this '
                          'account). ({}/3)'.format(int(cnt_acc_error / cnt_error)))
                    # Regard continually exit as *all done*.
                    if cnt_acc_error >= 9:
                        print('All done (3/3).')
                        print_during(time_start)
                        return
                    break
                continue

            response_processed = response.decode('utf-8').replace('\0', '')
            response_processed_json = json.loads(response_processed)
            size_bytes_done = int(response_processed_json['bytes'])
            checks_done = int(response_processed_json['checks'])
            size_GB_done = int(size_bytes_done * 9.31322e-10)
            speed_now = float(int(response_processed_json['speed']) * 9.31322e-10 * 1024)

            # try:
            #     print(json.loads(response.decode('utf-8')))
            # except:
            #     print("have some encoding problem to print info")
            if already_start:
                print("%s %dGB Done @ %fMB/s | checks: %d files" % (dst_label, size_GB_done, speed_now, checks_done), end="\r")
            else:
                print("%s reading source/destination | checks: %d files" % (dst_label, checks_done), end="\r")

            # continually no ...
            if size_bytes_done - size_bytes_done_before == 0:
                if already_start:
                    cnt_dead_retry += 1
                    if args.test_only:
                        print('\nsize_bytes_done', size_bytes_done)
                        print('size_bytes_done_before', size_bytes_done_before)
                        print("No. No size increase after job started.")
            else:
                cnt_dead_retry = 0
                if args.test_only: print("\nOk. I think the job has started")
                already_start = True

            size_bytes_done_before = size_bytes_done

            # Stop by error (403, etc) info
            if size_GB_done >= SIZE_GB_MAX or cnt_dead_retry >= CNT_DEAD_RETRY:

                if is_windows():
                    # kill_cmd = 'taskkill /IM "rclone.exe" /F'
                    kill_cmd = 'taskkill /PID {} /F'.format(PID)
                else:
                    kill_cmd = "kill -9 {}".format(PID)
                print("\n" + " " * 20 + " {}".format(time.strftime("%H:%M:%S")))
                try:
                    subprocess.check_call(kill_cmd, shell=True)
                    print('\n')
                except:
                    if args.test_only: print("\nFailed to kill.")
                    pass

                # =================Finish it=================
                if cnt_dead_retry >= CNT_DEAD_RETRY:
                    try:
                        cnt_exit += 1
                    except:
                        cnt_exit = 1
                    if args.test_only: print(
                        "1 more time for long time waiting. the cnt_exit is added to {}\n".format(cnt_exit))
                else:
                    # clear cnt if there is one time
                    cnt_exit = 0
                    if args.test_only: print("1 time sucess. the cnt_exit is reset to {}\n".format(cnt_exit))

                # Regard continually exit as *all done*.
                if cnt_exit >= CNT_SA_EXIT:
                    print_during(time_start)
                    # exit directly rather than switch to next account.
                    print('All Done.')
                    return
                # =================Finish it=================

                break

            time.sleep(2)
        id = id + 1

    print_during(time_start)


if __name__ == "__main__":
    main()