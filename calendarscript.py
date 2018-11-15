from __future__ import print_function
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from checkAgentZdStatus import getOOOAgents
from globalVars import oooStringList, partialDayKeyWords, now, today, todayWeekday, noEmailList
from globalVars import groupIds, managerEmails, devAgentEmails, runMode, devManagerEmails, notifyAgentsThisCycle
from utils import dateStringToDateObject, initLogger
from sendEmail import emailManagers, emailAgents
from creds import SCOPES, calendarId, alreadyNotifiedFile, gCalTokenLocation, gCalCredsLocation

import logging



# Taken and slighly modified from the Google Python API documentation.
def googleCalAuth():
    store = file.Storage(gCalTokenLocation)
    creds = store.get()
    if not creds or creds.invalid:
        logging.info('Refreshing token for Google Calendar.')
        flow = client.flow_from_clientsecrets(gCalCredsLocation, SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', cache_discovery=False, http=creds.authorize(Http()))
    return service.events().list(calendarId=calendarId,
                                            timeMin=now).execute()


# We're keeping a persistent list of event IDs that we've already sent a reminder to the
# agent for so we don't send multiple.
def retrieveCalendarEventsAlreadyNotified():
    try:
        with open (alreadyNotifiedFile, 'r') as f:
            return [line.rstrip('\n') for line in f], True
    except Exception as ex:
        logging.exception('Exception attempting to load previously notified event IDs: {}'.format(ex))
        return [], False


# Creating lists of event objects from the Google Calendar results. For more info check
# the Events class.
def initEvents(incomingEvents, calendarEventsAlreadyNotified, oooStringList):
    
    initEventsFuncManagerStatus, initEventsFuncAgentStatus = True, True

    # Using the proceedToEmailAgents var to not send emails of an exception occurs.
    outgoingEvents = []
    try:
        for e in incomingEvents['items']:
            outgoingEvents.append(Event(calendarEventsAlreadyNotified, id=e['id'], status=e['status'], \
                created=e['created'], updated=e['updated'], summary=e['summary'].lower(), \
                creator=e['creator']['email'], start=e['start'], end=e['end']))
        
    except Exception as ex:
        logging.exception('Exception initialing list of Events: {}'.format(ex))
        initEventsFuncManagerStatus, initEventsFuncAgentStatus = False, False

    # returns attr notifyToday (bool). Whether or not to email the agent today.
    try:
        for oe in outgoingEvents:
            oe = oe.ifNotifyToday(today, calendarEventsAlreadyNotified)
    except:
        logging.exception('Exception determining if notify agent today: {}'.format(ex))
        initEventsFuncAgentStatus = False
    
    oooEvents = []
    for a in outgoingEvents:
        # Checking to see if the event description contains a string associated with OOO.
        # The list of OOO strings is in globalVars and can be edited.
        if any(ostring in a.summary for ostring in oooStringList):
            if a.creator not in noEmailList:
                oooEvents.append(a)
        else:
            pass
    return outgoingEvents, oooEvents, initEventsFuncManagerStatus, initEventsFuncAgentStatus

# Finding out which agents are OOO today according to the User Services calendar.
def whichAgentsOffToday(events, today):
    
    # Is today with the start and end dates of the PTO event?
    def ifCalendarOOOToday(event, today):
        start = dateStringToDateObject(event.start['date'])
        end = dateStringToDateObject(event.end['date'])
        if start <= today <= end:
            event.oooToday = True
        else:
            event.oooToday = False
        return event

    agentsOOOOnCalendar = []
    for a in events:
        # Confirm the event has a start date.
        if getattr(a, 'start'):
            # append oooToday attr.
            a = ifCalendarOOOToday(a, today)
        else:
            a.oooToday = False
        if a.oooToday == True:
            agentsOOOOnCalendar.append(a)
    return agentsOOOOnCalendar



# Returns of list of email addresses to remind to go OOO in zd and a list
# of the event ids so we can record it.
def getAgentWarnedEmails(events, runMode=runMode):
    emailAddressesToNotify, notifiedEventIds = [], []
    for e in events:
        if e.notifyToday == True:
            emailAddressesToNotify.append(e.creator)
            notifiedEventIds.append(e.id)
    if runMode == 'DEV':
        logging.info('Replacing actual agent email list with dev list.')
        logging.info('Replacing notifiedEventIds list with an empty list.')
        logging.info('Would have proceeded with agent emails: '.format(emailAddressesToNotify))
        return devAgentEmails, []
    else:
        return emailAddressesToNotify, notifiedEventIds



class Event():
    def __init__(self, calendarEventsAlreadyNotified, *args, **kwargs):
        # Just create an attr for everything passed.
        for attribute, value in kwargs.items():
            setattr(self, attribute, value)
        # creating a dt object for comparison.
        self.startDateObj = (dateStringToDateObject(self.start['date']))
        
        
    # For the event, is today the business day before the start of PTO? If so, we'll go on to
    # email the agent (the creator of the event).
    def ifNotifyToday(self, today, calendarEventsAlreadyNotified):
    
        # Filter out events already notified for.
        if self.id not in calendarEventsAlreadyNotified:
            startDate = self.startDateObj
            logging.debug('\tEvent {} is not in the list of previously notified events.'.format(self.summary))
            
            # mon 0, tues 1, wed 2, thurs 3, fri 4, sat 5, sun 6 
            weekdayStartDay = startDate.weekday()
            weekdayToday = today.weekday()
            logging.debug('weekdayStartDay and weekdayToday are {} and {} respectively.'.format(\
                weekdayStartDay, weekdayToday))

            # If PTO start day is on weekend, make the start day a monday since they
            # will be treated the same.
            if weekdayStartDay > 4:
                weekdayStartDay = 0
                logging.debug('\tMoved the weekday to Monday because it was on the weekend.')
               
            # For PTO start days on Monday (or the weekend), we'll notify the Friday before.
            if weekdayStartDay == 0:
                notifyDate = startDate - datetime.timedelta(days=3)
                logging.debug('\tSince startday is Monday, setting notifyDate to {}'.format(\
                    notifyDate))
            else:
            # For Tues-Fri PTO start days, we'll notify the day before.
                notifyDate = startDate - datetime.timedelta(days=1)
                logging.debug('\tNotifydate is {}'.format(notifyDate))

            # All that really matters that we return from this is if we need to send a 
            # notification today.
            if today == notifyDate:
                self.notifyToday = True
            else:
                self.notifyToday = False
        else:
            # If already notified, don't notify.
            self.notifyToday = False
            logging.info('Removing event {} - {} from list because it has already been notified.'.format(\
                self.summary, self.start))
        logging.info('notifyToday for event {} is {}'.format(self.summary, self.notifyToday))
        return self

# If we emailed the agent, write the event ID to a persistent file so we don't do it again.
def recordEventsThatWereNotified(listOfEventIds):
    try:
        with open(alreadyNotifiedFile, 'a') as f:
            for x in listOfEventIds:
                f.write(x + '\n')
        logging.debug('alreadyNotifiedFile loaded.')
        return True
    except Exception as ex:
        logging.exception('Exception writing to already-notified file: {}'.format(ex))
        return False

# For every OOO event on the calendar, is the event creator marked as OOO in ZD?
# If not, make the needToNotifyManager attribute True.
def getAgentsNeedManagerNotification(calendarObjects, zdOOOAgents, zdAllAgents):
    for calOOOAgent in calendarObjects:
        calOOOAgent.needToNotifyManager = True
        for zdOOOAgent in zdOOOAgents:
            # Found a match between the zd list and the gcal list
            if calOOOAgent.creator == zdOOOAgent.email:
                calOOOAgent.needToNotifyManager = False
        
        # Need to attach some more info from the whole export of zd agents
        if calOOOAgent.needToNotifyManager == True:
            for zdAgent in zdAllAgents:
                # found match
                if calOOOAgent.creator == zdAgent.email:
                    # move over the manager notify group. (We've already gotten the zd
                    # agent's primary group in zd and then referenced the groupIds dict
                    # from global vars.)
                    calOOOAgent.managerNotify = zdAgent.managerNotify
                    # Should prob get the name too bc ppl do not like to be called numbers.
                    calOOOAgent.name = zdAgent.name
                    # now lets get the actual emails if they're in one of the US groups.
                    if getattr(zdAgent, 'managerEmails', None) is not None:
                        calOOOAgent.managerEmails = zdAgent.managerEmails

    return [a for a in calendarObjects if a.needToNotifyManager == True]

def createAgentListsForManagerEmail(objects, managerEmails):
    emailMatch = {}
    for k,v in managerEmails.items():
        emailMatch[k] = {}
        emailMatch[k]['managerEmails'] = []
        emailMatch[k]['agents'] = []
    
    for obj in objects:
        if getattr(obj, 'managerNotify', None) is not None:
            if obj.managerNotify in emailMatch.keys():
                emailMatch[obj.managerNotify]['managerEmails'].append([a for a in obj.managerEmails \
                                    if a not in emailMatch[obj.managerNotify]['managerEmails']])
                emailMatch[obj.managerNotify]['agents'].append(obj.name)
                continue
    return emailMatch


logging = initLogger()

def main():

    # At several points we are going to turn these vars to false if there is an error or 
    # unexpected results. Doing so will prevent any emails from going out.
    proceedToEmailMangers, proceedToEmailAgents = True, True
    proceedManagerReasons, proceedAgentReasons = [], []

    # These events have already results in a warning email to the agent. The 
    # event IDs were stored in a txt file from prior runs of the script.
    calendarEventsAlreadyNotified, retrieveCalFuncStatus = retrieveCalendarEventsAlreadyNotified()
    logging.info('Retrieved {} events from list of previously reminded PTO events.'.format(\
                                                           len(calendarEventsAlreadyNotified)))
    
    if retrieveCalFuncStatus == False:
        proceedToEmailAgents = False
        proceedAgentReasons.append('Could not get list of previously notified events.')
    if notifyAgentsThisCycle == False:
        proceedToEmailAgents = False
        proceedAgentReasons.append('Not within the hours to notify agents.')

    # Upcoming events from the User Services calendar. 
    upcomingEvents = googleCalAuth()
    logging.info('Retrieved {} upcoming events from the User Services calendar.'.format(
                                                                   len(upcomingEvents['items'])))
    if len(upcomingEvents['items']) == 0:
        logging.exception('Exiting because there are no events retrieved from calendar.')
        quit()

    for i in upcomingEvents['items']:
        logging.debug('\t{} ({})'.format(i['summary'], i['start']['date']))

    
    # Creating a list of objects for: 
    #   events: all events
    #   oooEvents: All events with an ooo type string in their title
    # When initialized, the events contain a bool attr notifyToday --
    # if the agent is off on the next business day and they haven't yet been
    # notified for the event.
    events, oooEvents, initEventsFuncManagerStatus, initEventsFuncAgentStatus = initEvents(\
                                upcomingEvents, calendarEventsAlreadyNotified, oooStringList)
    logging.info('Proceeding with {} OOO events.'.format(len(oooEvents)))
    for i in oooEvents:
        logging.debug('\t{} ({})'.format(i.summary, i.start))

    if initEventsFuncManagerStatus == False:
        proceedToEmailMangers = False
        proceedManagerReasons.append('Problem initializing events.')
    if initEventsFuncAgentStatus == False:
        proceedToEmailAgents = False
        proceedAgentReasons.append('Problem initializing events.')

    # Now a list of events for which we need to see if the agent is OOO
    # in Zendesk. If not, we'll notify their manager. We're calling it a
    # list of agents even though their event objects bc we're only really
    # interested in this list for the agent info.
    agentsOOOOnCalendar = whichAgentsOffToday(oooEvents, today)
    logging.info('There are {} agents off today.'.format(len(agentsOOOOnCalendar)))
    
    if len(agentsOOOOnCalendar) == 0:
        proceedToEmailMangers = False
        proceedManagerReasons.append('No agents OOO on calendar.')

    # Get a list of emails for the agents we need to email today. We're then
    # done with this work stream.
    agentEmailsToWarn, notifiedEventIds = getAgentWarnedEmails(oooEvents, runMode)
    logging.debug('Agent emails to notify: '.format(agentEmailsToWarn))
    logging.debug('Event Ids to write to already-notified file: '.format(notifiedEventIds))

    if len(agentEmailsToWarn) == 0:
        proceedToEmailAgents = False
        proceedAgentReasons.append('No agent emails to warn.')

    # Recording the ids for the events for which we're reminding the agent
    # in a text file. (When this script repeats it will make sure not to 
    # send another notification for these events.)
    didItWork = recordEventsThatWereNotified(notifiedEventIds)

    if didItWork == False:
        logging.exception('Could not record the notifed event IDs.')
        proceedToEmailAgents = False
        proceedAgentReasons.append('Could not write the new event ids to persistent file.')

    # These agents are registered as OOO in Zendesk. If an agent from 
    # agentsOOOOnCalendar is NOT on this list, we need to let their manager know.
    zdOOOAgents, zdAllAgents, getOOOAgentsStatus = getOOOAgents()

    if getOOOAgentsStatus == False:
        proceedToEmailMangers = False
        proceedManagerReasons.append('There are no OOO agents today.')

    # Compare the list of calendar OOO objects and the list of zd OOO agents and
    # see which agents need to have their managers notified.
    agentsNeedManagerNotification = getAgentsNeedManagerNotification(\
                                agentsOOOOnCalendar, zdOOOAgents, zdAllAgents)

    managerEmailList = createAgentListsForManagerEmail(\
        agentsNeedManagerNotification, managerEmails)

    if proceedToEmailMangers == True:
        emailManagers(managerEmailList, 1)
    else:
        logging.critical('MANAGERS NOT EMAILED.')
        logging.critical('Reasons: {}'.format([a for a in proceedManagerReasons]))
    if proceedToEmailAgents == True:
        emailAgents(agentEmailsToWarn)
    else:
        logging.critical('AGENTS NOT EMAILED.')
        logging.critical('Reasons: {}'.format([a for a in proceedAgentReasons]))


if __name__ == '__main__':

    main()
