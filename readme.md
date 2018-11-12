# Zendesk - GCal OOO Notifier

## Purpose

Via the Google Calendar API, Gmail API, and the Zendesk API, this script seeks to minimize situations where a support agent does not remember to mark themselves out-of-office via the ZD OOO app so they are assigned cases without being available to respond. It does so two ways:
1. Sending a reminder email to an agent the business day before their PTO event begins, and
2. Sending an email to the agent's manager if he or she is PTO according to the team calendar and not marked as OOO in Zendesk.

## A Little Deeper

The context for this script makes a few assumptions:
1. Members of the support team post their OOO events on a shared calendar.
2. The team uses the Zendesk OOO app to manage agent availability. 
3. Agents are assigned cases via automation rather than manually selelcting them.

It first accesses the group calendar and pulls all upcoming events. It filters the events down to ones that contain one of a few keywords ('pto', 'ooo', etc.). 

*All configuration changes (e.g. list of keywords, manager emails, etc.) can be made in the globalVars file.*

It then pulls all agents in Zendesk. After the initial pull, it will only process agents whose default group are in a preterminded list (in globalVars). It will see if they are currently labelled OOO and get some more tangential information. 

For the first step--emails the agents a reminder--it checks two things: Is the agent's ooo event's start date the next business day? and, Have we emailed a reminder about this event yet? (a safety check, really, so that we could run this part multiple times a day if we wanted to for some reason).

For the second step--emailing agents' managers if the agent is OOO on the calendar but not OOO in Zendesk, it sees, obviously, if the agent is OOO on the calendar and OOO in Zendesk. It gets the agent's primary group and then checks that against a list in globalVars to put the agent on the right people-team. Then it checks another list of managers' email addresses (also in globalVars) to see who should be alerted. 

It then accesses the gmail API to send out emails to the agents and managers.

### How and When to Run

Designed to be set on a cron to run ~ twice a day. Once in the morning and once in the afternoon. Choose the times via cron manager. **TBD: How exactly to do this so that the agent-notify portion only runs once a day, but the manager run portion runs once early in the morning, and once just short of mid-day.** Theoretically, this should not be needed because the script would not send out an email to the agent twice for the same event, but for efficiency sake.... (On the other hand, notifying managers twice is by design.)

### Testing

In globalVars, there is a var 'runMode'. You can toggle it between 'PROD' and 'DEV'. In prod, it runs as designed. In 'DEV', it replaces the email addresses to notify with a list you determine and randomizes which agents are OOO in Zendesk and the calendar. 

Logging should generally be set to 'WARNING' but can be toggled (in utils) to 'INFO' or 'DEBUG' for more verbosity. Logs write to files in /logs and auto-rotate and delete. 

As of writing no formal testing exists but some pytest modules will be created soon.

### Files

Main is calendarscript.py. To follow to script, start in main. General information is commented in above the functions in main and more information is commented in the functions themselves. 

The credsSCRUBBED.py file and globalVarsSCRUBBED.py files are included but with no data.

### Weaknesses

1. Spot checking that the inital list of ooo phrases--strings to search for in calendar event summaries--captures 99+% of OOO events but it may over capture. The most obvious scenario would be where a small segment of agents put "OOO today" meaning they are physically out of the office but still working. 

2. There is no mechanism, yet, to alert on errors.

3. Some OOO events indicate they are for partial days (e.g. 'Mary PTO afternoon'). There is no serious attempt to accomodate this yet but it's a fairly simple addition. This feature addition would make it more difficult to create a cron schedule without a remedy for 4 below.

4. General lack of timezone support. This script works for a single region as long as the cron can run at the same time for every recipient. Adding timezone support is a high priority but it is unclear how useful this could be for our usecase at the moment because of the lack of a global joint calendar. 

