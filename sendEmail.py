

from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from email.mime.text import MIMEText
import base64
from base64 import b64encode, urlsafe_b64encode
import time
from google.oauth2 import service_account
from creds import gmailScopes, gmailTokenLocation, gmailCredsLocation, senderEmail



# If modifying these scopes, delete the file token.json.
SCOPES = gmailScopes

agentEmailBody = 'Hey there! \n\n[[This is an automated message.]] \n\n It looks like you may be on PTO tomorrow based on an event on the User Services calendar. \n\n Just a reminder to remember to mark yourself \'OOO\' in Zendesk before you leave. Otherwise, you will be assigned cases. \n\n Here\'s a link to the new PTO policy: LINK \n\n [[By the way, these emails may not always come, so please don\'t start to rely on them!]]'
agentEmailSubject = 'AUTOMATED MESSAGE: Upcoming PTO Reminder'

managerEmailSubject = 'AUTMATED MESSAGE: Possible PTO agent(s) not OOO in Zendesk.'



# def main(listOfObjects):
def googleAuth():
	store = file.Storage(gmailTokenLocation)
	creds = store.get()
	if not creds or creds.invalid:
		flow = client.flow_from_clientsecrets(gmailCredsLocation, SCOPES)
		creds = tools.run_flow(flow, store)
	service = build('gmail', 'v1', cache_discovery=False, http=creds.authorize(Http()))
	return service


def create_message(sender, to, subject, message_text):
	message = MIMEText(message_text)
	message['to'] = to
	message['from'] = sender
	message['subject'] = subject
	return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}


def send_message(service, user_id, message):
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print('Message Id: %s' % message['id'])
    return message
  except Exception as ex:
    print('An error occurred: {}'.format(ex))



def emailManagers(emailDict, count):

	service = googleAuth()
	for k, v in emailDict.items():
		if len(v['agents']) > 0 and len(v['managerEmails']) > 0 and len(v['managerEmails'][0]) > 0:
			managerEmailBody = 'Hi there! \n\n [[This is an automated message.]] \n\n It looks like these agents may be on PTO according to the User Services calendar but not marked OOO in Zendesk: \n\n {} \n\n They may be receiving cases while OOO.'.format(\
												[a for a in v['agents']])
			emails = [item for sublist in v['managerEmails'] for item in sublist]
			print(emails)
			for email in emails:
				if count < 5:
					message = create_message(senderEmail, email, managerEmailSubject, managerEmailBody)
					print(message)
					#send_message(service, 'me', message)
					count += 1
					time.sleep(1)
	
def emailAgents(listofEmails):
	print('The real list is: {}'.format(listofEmails))
	service = googleAuth()
	for email in listofEmails:
		message = create_message(senderEmail, email, agentEmailSubject, agentEmailBody)
		#send_message(service, 'me', message)
		print(message)




