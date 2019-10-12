from google.oauth2.service_account import Credentials
import googleapiclient.discovery, json, progress.bar, glob, sys, argparse, time

stt = time.time()

parse = argparse.ArgumentParser(description='A tool to add service accounts to a shared drive from a folder containing credential files.')
parse.add_argument('--path','-p',default='accounts',help='Specify an alternative path to the service accounts folder.')
parse.add_argument('--controller','-c',default='controller/*.json',help='Specify the relative path for the controller file.')
parse.add_argument('--yes','-y',default=False,action='store_true',help='Skips the sanity prompt.')
parsereq = parse.add_argument_group('required arguments')
parsereq.add_argument('--drive-id','-d',help='The ID of the Shared Drive.',required=True)

args = parse.parse_args()
acc_dir = args.path
did = args.drive_id
contrs = glob.glob(args.controller)

try:
	open(contrs[0],'r')
	print('Found controllers.')
except IndexError:
	print('No controller found.')
	sys.exit(0)
if not args.yes:
	input('Make sure the following email is added to the shared drive as Manager:\n' + json.loads((open(contrs[0],'r').read()))['client_email'])

credentials = Credentials.from_service_account_file(contrs[0], scopes=[
	"https://www.googleapis.com/auth/drive"
])

drive = googleapiclient.discovery.build("drive", "v3", credentials=credentials)
batch = drive.new_batch_http_request()

aa = glob.glob('%s/*.json' % acc_dir)
pbar = progress.bar.Bar("Readying accounts",max=len(aa))
for i in aa:
	ce = json.loads(open(i,'r').read())['client_email']
	batch.add(drive.permissions().create(fileId=did, supportsAllDrives=True, body={
		"role": "fileOrganizer",
		"type": "user",
		"emailAddress": ce
	}))
	pbar.next()
pbar.finish()
print('Adding...')
batch.execute()

print('Complete.')
hours, rem = divmod((time.time() - stt),3600)
minutes, sec = divmod(rem,60)
print("Elapsed Time:\n{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),sec))
