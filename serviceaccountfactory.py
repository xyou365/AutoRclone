from google.oauth2.service_account import Credentials
import googleapiclient.discovery, base64, json, progressbar, glob, sys, argparse, time
from os import mkdir

def get_project_details(project_input, project_count):
	passed_check = 0
	project_inputs = project_input.split(' ')
	
	while True:
		if passed_check == 0:
			if len(project_inputs) == 2:
				while True:
					try:
						int(project_inputs[1])
					except ValueError:
						print('Invalid input for number of accounts. Please try again.')
						new_input = input(str(project_count) + '. ')
						project_inputs = new_input.split(' ')
					else:
						passed_check = 1
						break
				
				if int(project_inputs[1]) > 0 and int(project_inputs[1]) < 101:
					pass
				else:
					passed_check = 0
					print('Invalid input for number of accounts. Please try again.')
					new_input = input(str(project_count) + '. ')
					project_inputs = new_input.split(' ')
			else:
				print('Invalid input. Please try again')
				new_input = input(str(project_count) + '. ')
				project_inputs = new_input.split(' ')

		else:
			break
			
	return {"project_id": project_inputs[0], "num_sa": int(project_inputs[1])}

def create_service_account_and_dump_key(project_id, service_account_name, service_account_filename):
	
	service_account = iam.projects().serviceAccounts().create(
		name="projects/" + project_id,
		body={
			"accountId": service_account_name,
			"serviceAccount": {
				"displayName": service_account_name
			}
		}
	).execute()

	key = iam.projects().serviceAccounts().keys().create(
		name="projects/" + project_id + "/serviceAccounts/" + service_account["uniqueId"],
		body={
			"privateKeyType": "TYPE_GOOGLE_CREDENTIALS_FILE",
			"keyAlgorithm": "KEY_ALG_RSA_2048"
		}
	).execute()
	
	f = open(service_account_filename, "w")
	f.write(base64.b64decode(key["privateKeyData"]).decode("utf-8"))
	f.close()

if __name__ == '__main__':
	stt = time.time()
	project_count = 0
	project_input = None
	projects = []
	project_details = {}
	prefix = ''
	
	parse = argparse.ArgumentParser(description='A tool to create Google service accounts.')
	parse.add_argument('--path','-p',default='accounts',help='Specify an alternate directory to output the credential files.')
	parse.add_argument('--controller','-c',default='controller/*.json',help='Specify the relative path for the controller file.')
	parse.add_argument('--no-autofill',default=False,action='store_true',help='Do not autofill the first project.')
	
	args = parse.parse_args()
	acc_dir = args.path
	contrs = glob.glob(args.controller)
	
	try:
		open(contrs[0],'r')
		print('Found controllers.')
	except IndexError:
		print('No controller found.')
		sys.exit(0)
		
	print('Add more projects:')
	print('[project id] [accounts to create]')

	if not args.no_autofill:
		project_count += 1
		project_input = json.loads(open(contrs[0],'r').read())['project_id'] + ' 99'
		project_details = get_project_details(project_input, project_count)
		print(str(project_count) + '. ' + project_details['project_id'] + ' ' + str(project_details['num_sa']))
		projects.append(project_details)
	
	while project_input != '':
		project_count += 1
		project_input = input(str(project_count) + '. ')
		if project_input != '':
			project_details = get_project_details(project_input, project_count)
			projects.append(project_details)

	while len(prefix) < 4:
		prefix = input('Custom email prefix? ').lower()
		if prefix == '':
			prefix = 'folderclone'
		if len(prefix) < 4:
			print('Email prefix must be 5 characters or longer!')

	print('Using ' + str(len(projects)) + ' projects...')
	
	credentials = Credentials.from_service_account_file(contrs[0], scopes=[
		"https://www.googleapis.com/auth/iam"
		])
	iam = googleapiclient.discovery.build("iam", "v1", credentials=credentials)
	
	try:
		mkdir(acc_dir)
	except FileExistsError:
		pass
	
	gc = 1

	for i in range(len(projects)):
		print('Creating accounts in ' + projects[i]['project_id'])
		for o in progressbar.progressbar(range(1, projects[i]['num_sa']+1)):
			create_service_account_and_dump_key(projects[i]['project_id'],prefix + str(o),acc_dir + "/" + str(gc) + '.json')
			gc += 1
	
	print('Complete.')
	hours, rem = divmod((time.time() - stt),3600)
	minutes, sec = divmod(rem,60)
	print("Elapsed Time:\n{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),sec))
