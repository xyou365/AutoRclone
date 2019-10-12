# AutoRclone: rclone copy/move/sync (automatically) with service accounts (still in the beta stage)
Many thanks for [rclone](https://rclone.org/) and [folderclone](https://github.com/Spazzlo/folderclone).

- [x] create service accounts using script
- [x] add massive service accounts into rclone config file
- [x] add massive service accounts into groups for your organization
- [x] automatically switch accounts when rclone copy/move/sync 

Step 1. Copy code to your VPS or local machine
---------------------------------
Run command 
`sudo git clone https://github.com/xyou365/AutoRclone 
&& cd AutoRclone 
&& sudo pip3 install -r requirements.txt`

Step 2. Generate service accounts (sa) required
---------------------------------
Let us create as many service accounts as possible following [official steps of folderclone](https://github.com/Spazzlo/folderclone/blob/master/README_multifolderclone.md#steps-to-setup-multifactorypy). 

After you finished, there will be many json files in folder `accounts`.

[What is service account](https://cloud.google.com/iam/docs/service-accounts).

[How to use service account in rclone](https://rclone.org/drive/#service-account-support).


Step 3. Add service accounts into rclone config file
---------------------------------
For convenient, we use script to write (directly) the service accounts generated in **Step 2** into rclone config file.

To set source Team Drive, run command `python3 gen_rclone_cfg.py -p tdsrc -t SharedTeamDriveSrcID`
```
Done. Generated rclone config file is successfully saved to ./rclone.conf

Your default rclone Configuration file is stored at:
C:\Vim\Neovim\share\rclone\rclone.conf

You can
* directly replace your default rclone config file with the generated file ./rclone.conf
* or append content in generated config file to default config file
```
To set destination Team Drive, run again with different parameters: `python3 gen_rclone_cfg.py -p tddst -t SharedTeamDriveDstID`

Step 4. Add service accounts to groups for your organization (Optional)
---------------------------------
_Support that you are GSuite admin (domain admin or normal admin)_

Here we use Google Groups to manager our service accounts considering the  
[Official limits to the members of Team Drive](https://support.google.com/a/answer/7338880?hl=en) (Limit for individuals and groups directly added as members: 600).

1. Turn on the Directory API following [official steps](https://developers.google.com/admin-sdk/directory/v1/quickstart/python) (save the generated json file to folder `credentials`).

2. Create groups for your organization [in the Admin console](https://support.google.com/a/answer/33343?hl=en). After create a group, you will have an address for example`sa@yourdomain.com`.

3. Run `python3 massadd.py -p ./accounts -c credentials/*.json -g sa@yourdomain.com`

_For meaning of above flags, please run `python3 massadd.py -h`_

Step 5. Add service accounts or google groups (created in Step 4) into both of your Team Drive
---------------------------------
Add the group address `sa@yourdomain.com` to your source Team Drive (tdsrc) and destination Team Drive (tddst). 
 
If you are not Gsuite admin or do not care about the member limitation of Team Drive, 
just use script of folderclone to add sa accounts into Team Drive.

- Add service accounts into your source Team Drive: 
`python3 masshare.py -d SharedTeamDriveSrcID`

- Add service accounts into your destination Team Drive:
And run `python3 masshare.py -d SharedTeamDriveDstID`

Step 6. Start your task (copy from Team Drive tdsrc to tddst)
---------------------------------
_Please check in this way `rclone lsd tdsrc001:` and `rclone lsd tddst001:`). Make sure it is okay._

Edit the `rclone_sa.py` using your editor `vim rclone_sa.py`.

Let us `rclone copy` hundreds of TB resource using service accounts from source Team Drive `tdsrc` into you destination Team Drive `tddst` using sa accounts 1 to 1000
`python3 rclone_sa.py 1 1000`

Run this command `tail -f log_rclone.txt` to see what happens in details.

![](AutoRclone.jpg)

Let's talk about this project in Telegram Group [AutoRclone](https://t.me/AutoRclone)

[Blog（中文）](https://www.gfan.loan/?p=235) | [Google Drive Group](https://t.me/google_drive) | [Google Drive Channel](https://t.me/gdurl)  



