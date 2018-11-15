import datetime

# Time related vars
# now is only used by the Google api.
now = datetime.datetime.utcnow().isoformat() + 'Z' 
today = datetime.datetime.now().date()
todayWeekday = datetime.datetime.now().weekday()
# mon 0, tues 1, wed 2, thurs 3, fri 4, sat 5, sun 6 

##### NOTE ON TIME VARS
# I'm not bothering with standardizing the vars to UTC because this whole script will
# be run on a cron only a couple of times a day. It's fine to just use system time (PT).
#####

# Options are DEV and PROD. If you use DEV, the list of email addresses below will be
# used instead of the actual email addresses. With gmail, you can format your own email
# address as EMAIL+agent1@, EMAIL+manager2, etc.
runMode = 'DEV'

devAgentEmails = []
devManagerEmails = []

def notifyAgentsThisCycle():
	nowHour = datetime.datetime.now().hour
	if 5 < nowHour < 12:
		return False
	else:
		return True

notifyAgentsThisCycle = notifyAgentsThisCycle()

# List of common OOO phrases in the User Services calendar. These are the terms
# that we'll search for in events to determin if it's an OOO event. (The calendar
# event descriptions will be automatically converted to lowercase.)

oooStringList = ['ooo', 'pto', 'out of office', 'vacation']

# Not using yet.
partialDayKeyWords = {'morning': ['am', 'morning'],
					  'afternoon': ['pm', 'afternoon']
					 }

# Lists of ZD group IDs. This will tell us which managers need to get the notification.
groupIds = {
    'team1':	  [], #ZD group IDs as ints.
    'team2':   [],
    'team3':   []
                }

if runMode == 'PROD':
	managerEmails = {
	    'team1': [], #email address as strings.
	    'team2':   [],
	    'team3':   [],
	                }
if runMode == 'DEV':
	managerEmails = {
	    'premier': [], #email addresses as strings.
	    'tier1':   [],
	    'tier2':   [],
	                }
