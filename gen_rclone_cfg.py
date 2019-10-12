# auto rclone
#
# Author Telegram https://t.me/CodyDoby
# Inbox  codyd@qq.com

import sys, os, glob
import argparse
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description="Generate rclone config file.")
    parser.add_argument('-t', '--team_drive_id', type=str, required=True,
                        help='the id of team dirve')
    parser.add_argument('-f', '--service_account_folder', type=str, default="accounts",
                        help='folder of service account files')
    parser.add_argument('-p', '--prefix', type=str, default="sa",
                        help='prefix of generated labels in rclone config file.')
    parser.add_argument('-o', '--output_of_config_file', type=str, default="./rclone.conf",
                        help='folder of service account files')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    sa_files = glob.glob(os.path.join(args.service_account_folder, '*.json'))

    output_of_config_file = args.output_of_config_file
    with open(output_of_config_file, 'w') as fp:

        for i, filename in enumerate(sa_files):
            filename = filename.replace(os.sep, '/')

            try:
                fp.write('[{}{:03d}]\n'
                         'type = drive\n'
                         'scope = drive\n'
                         'service_account_file = ./{}\n'
                         'team_drive = {}\n\n'.format(args.prefix, i, filename, args.team_drive_id))
            except:
                return print("failed to write to {}".format(output_of_config_file))

    print("Done. Generated rclone config file is successfully saved to {}\n".format(output_of_config_file))

    locate_cmd = 'rclone config file'
    try:
        output = subprocess.check_output(locate_cmd, shell=True).decode('utf-8')
    except:
        return print("\nExit. Please install rclone firstly: https://rclone.org/downloads/#script-download-and-install")

    default_rclone_config_file = output.replace('\0', '')
    print("Your default rclone {}\n"
          "You can\n"
          "* directly replace your default rclone config file with the generated file {} \n"
          "* or append content in generated config file to default "
          "config file\n".format(str(default_rclone_config_file), output_of_config_file))


if __name__ == "__main__":
    main()
