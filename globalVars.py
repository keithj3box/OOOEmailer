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
# used instead of the actual email addresses.
runMode = 'DEV'

devAgentEmails = ['kjohnson+agent1@box.com', 'kjohnson+agent2@box.com']
devManagerEmails = ['kjohnson+manager1@box.com', 'kjohnson+manager2@box.com']

# List of common OOO phrases in the User Services calendar. These are the terms
# that we'll search for in events to determin if it's an OOO event. (The calendar
# event descriptions will be automatically converted to lowercase.)

oooStringList = ['ooo', 'pto', 'out of office', 'vacation']

partialDayKeyWords = {'morning': ['am', 'morning'],
					  'afternoon': ['pm', 'afternoon']
					 }

# Lists of ZD group IDs. This will tell us which managers need to get the notification.
groupIds = {
    'premier': [20249732, 360000179428, 360000164988, 41953987, 360000175927],
    'tier1':   [21423573, 360000179448, 360000164968, 360000161068, 360000175947],
    'tier2':   [20051287, 360000175967, 360000162167, 360000161867, 360000175987]
                }

if runMode == 'PROD':
	managerEmails = {
	    'premier': ['kjohnson+ps1@box.com', 'kjohnson+ps2@box.com'],
	    'tier1':   ['kjohnson+t11@box.com', 'kjohnson+t12@box.com'],
	    'tier2':   ['kjohnson+t21@box.com', 'kjohnson+t22@box.com'],
	                }
if runMode == 'DEV':
	managerEmails = {
	    'premier': ['kjohnson+ps1@box.com', 'kjohnson+ps2@box.com'],
	    'tier1':   ['kjohnson+t11@box.com', 'kjohnson+t12@box.com'],
	    'tier2':   ['kjohnson+t21@box.com', 'kjohnson+t22@box.com'],
	                }
