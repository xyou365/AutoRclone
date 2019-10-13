# auto rclone
#
# Author Telegram https://t.me/CodyDoby
# Inbox  codyd@qq.com

import os, re, sys, io, subprocess
from signal import signal, SIGINT
import json, time

# =================modify here=================
screen_name = "wrc" # watch rc
# please check the prefix which set before in your rclone config file
src_prefix_string = 'tdsrc'
dst_prefix_string = 'tddst'

L_src = "%s:path_to_your_src_folder" # your src dir, if you are in root folder, change directly to "%s:"
L_dst = "%s:path_to_your_dst_folder" # your dst dir

logfile = "log_rclone.txt"           # log file: tail -f log_rclone.txt
START = 1
END = 399

# change it when u know what are u doing
SIZE_GB_MAX = 735
CNT_403_RETRY = 600
# =================modify here=================

if len(sys.argv)==3:
    _,s1,s2 = sys.argv
    START,END = int(s1),int(s2)
elif len(sys.argv)==2:
    _,s1 = sys.argv
    START = int(s1)


def handler(signal_received, frame):

    kill_cmd = "screen -r -S %s -X quit" % screen_name 
    try:
        subprocess.check_call(kill_cmd, shell=True)
    except:
        pass
    sys.exit(0)


def main():

    signal(SIGINT, handler)

    id = START

    start = time.time()
    print("Start: " + str(start))

    while id<=END+1:

        if id == END+1:
            break 
            # id = 1
        
        with open('current_sa.txt', 'w') as fp:
            fp.write(str(id)+'\n')

        acc_src = src_prefix_string + "{0:03d}".format(id)
        acc_dst = dst_prefix_string + "{0:03d}".format(id)
        open_cmd = "screen -d -m -S %s " \
                   "rclone copy --drive-server-side-across-configs --rc -vv --ignore-existing " \
                   "--tpslimit 6 --transfers 6 --drive-chunk-size 32M --fast-list " \
                   "--log-file=%s %s %s" % (screen_name, logfile, L_src%acc_src, L_dst%acc_dst)
        print(open_cmd)

        try:
            subprocess.check_call(open_cmd, shell=True)
            print(">> Let us go %s" % acc_dst)
            time.sleep(10)
        except subprocess.CalledProcessError as error:
            return print("error: " + str(error.output))

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
                print('3 times over')
                return

            response_processed = response.decode('utf-8').replace('\0', '')
            response_processed_json = json.loads(response_processed)

            # print(json.dumps(response_processed_json, indent=4, sort_keys=True, ensure_ascii=False).encode('utf8'))
            # print(response_processed_json)

            size_GB_done = int(int(response_processed_json['bytes']) * 9.31322e-10)
            speed_now = float(int(response_processed_json['speed']) * 9.31322e-10 * 1024)

            print("%s: %dGB Done @ %fMB/s" % (acc_dst, size_GB_done, speed_now), end="\r")

            # continually no ...
            if size_GB_done - size_GB_done_before == 0:
                cnt_403_retry += 1
            else:
                cnt_403_retry = 0

            size_GB_done_before = size_GB_done

            # Todo Stop by error info
            if size_GB_done >= SIZE_GB_MAX or cnt_403_retry >= CNT_403_RETRY:

                kill_cmd = "screen -r -S %s -X quit" % screen_name
                subprocess.check_call(kill_cmd, shell=True)
                print('\n')

                break

            time.sleep(2)
        id = id + 1

        stop = time.time()
        print(str((stop - start) / 60 / 60) + "小时")


if __name__ == "__main__":
    main()