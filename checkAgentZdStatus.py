import requests
# import logging
# from logging.handlers import RotatingFileHandler
import json
from creds import zdToken, zdEmail, baseUrl
from requestHandling import getResponse
from utils import initLogger, zendeskAuth, session
from globalVars import groupIds, managerEmails
import random

logging = initLogger()

from globalVars import runMode

class zdAgent():

	def __init__(self, *args, **kwargs):
		for attribute, value in kwargs.items():
			setattr(self, attribute, value)
		

	def attachNotificationGroup(self):

		for k,v in groupIds.items():
			if self.group in v:
				self.managerNotify = k
				break

		if getattr(self, 'managerNotify', None) is None:
			self.managerNotify = None
		else:
			self.managerEmails = [v for k,v in managerEmails.items() if k == self.managerNotify][0]
		
		return self



# Going to download all agents and return a list of objects.
def checkAgents(session):
	checkAgentFuncStatus = True
	agents = []

	devOOOchoices = [False, False, False, False, False, True]
	if runMode == 'DEV':
		logging.info('DEV MODE so agent.ooo is randomized ({} percent chance.)'.format(\
																			round((1/len(devOOOchoices))*100), 0))

	url = baseUrl + 'users.json?role[]=agent'
	while url is not None:
		r = getResponse(session, url, 'get').json()
		count = r['count']
		logging.info('results for ~100 out of {} agents.'.format(count))
		if 'next_page' in r and r['next_page'] is not None:
			url = str(r['next_page'])
		else:
			url = None
		
		for u in r['users']:

			if runMode == 'DEV':
				ooo = random.choice(devOOOchoices)
			else:
				ooo = u['user_fields']['agent_ooo']

			try:
				agents.append(zdAgent(zdId=u['id'], name=u['name'], email=u['email'], \
					timezone=u['time_zone'], locale=u['locale'], role=u['role_type'], \
					customRole=u['custom_role_id'], ooo=ooo, group=u['default_group_id']))
			except:
				logging.exception('Error establishing ZD agent objects.')
				checkAgentFuncStatus = False
	for agent in agents:
		agent = agent.attachNotificationGroup()
	return agents, checkAgentFuncStatus


# What agents are ooo?
def filterAgents(listOfAgents):

	return [agent for agent in listOfAgents if agent.ooo == True]


def getOOOAgents():
	agents, checkAgentFuncStatus = checkAgents(session)
	return filterAgents(agents), agents, checkAgentFuncStatus
