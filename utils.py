import requests
import logging
import logging.handlers
from logging.handlers import RotatingFileHandler
import datetime

from creds import zdToken, zdEmail, baseUrl

# Convert a date string to a datetime date object.
def dateStringToDateObject(dateString):
    # Google Calendar date format: YYYY-MM-DD
    return datetime.datetime.strptime(dateString, '%Y-%m-%d').date()

# ZD session
def zendeskAuth():
	uname = '{}/token'.format(zdEmail)
	pw = zdToken
	headers = {'Content-Type': 'application/json'}
	auth = (uname, pw)
	session = requests.Session()
	session.auth = auth
	session.headers=headers
	if session is None:
		logging.critical('\tSession failed to establish')
		quit()
	else:
		logging.info('\tSession established.')
		return session

session = zendeskAuth()


# Generally the levels should be kept at ERROR but useful to switch to INFO for development.
# For troubleshooting, you can switch to DEBUG for more information.
def initLogger():
	logging.basicConfig(format='%(lineno)d - %(asctime)s - %(levelname)s - %(funcName)s - %(message)s', level=logging.DEBUG)
	handler = RotatingFileHandler('zendeskBackupVerboseAF.log', maxBytes=1000*1024,backupCount=5)
	handler.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(lineno)d - %(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
	handler.setFormatter(formatter)
	logging.getLogger('').addHandler(handler)
	logging.getLogger().setLevel(logging.DEBUG)

	return logging
