## Red Team Intelligence Assessment Worksheet
*Remember to refer to rules of engagement before, during, and after assessment*

### Section 0: Information about the infection
*Here we summarize the high level info about this infostealer infection*
- [ ] Infostealer infection date (see header file - be careful of month/year confusion):
- [ ] Infostealer family (see header, YARA rules):
- [ ] Likely infection vector (see screenshot, history):
- [ ] Other notes about infection:


### Section 1: Basic information about the target
*Here we summarize the high level info about this target; Most of this info will come from the autofills*
- [ ] Full name(s) and name variant(s):
- [ ] All primary and alternate email addresses:
- [ ] Phone number(s):
- [ ] Username(s):
- [ ] IP Address (from header file):


### Section 2: Inventory of target's browser profiles
*Studying the profiles will help us understand complexity of account behavior*
#### How does the target use browser profiles?
- [ ] Single profile
- [ ] Multiple profiles
	- [ ] Profiles represent multiple IRL identities (e.g. parent/child)
	- [ ] Profiles represent multiple online identities (e.g. work/home, personal/gaming, secure/insecure)
	- [ ] Multiple profiles for other/unknown reason	
- [ ] Notes:

#### Multiple browser profile summary
| Line | Profile Name | Folder | Notes |
|------|--------------|--------|-------|
| _Example_ | _Chrome Default_ | _/Chrome/Default_| _main computer owner's profile_ |
| 1 | | | |
| 2 | | | |
| 3 | | | |


### Section 3: Inventory of target's interests
*Here we log the target's personal interests and counts*

#### Example:
- [x] Gaming: Twitch (3 logins), Roblox (5 logins), Steam (multiple)

#### Inventory:
- [ ] Dating sites: 
- [ ] Gaming:
- [ ] Gambling: 
- [ ] Health/medical: 
- [ ] Financial services: 
- [ ] Parenting/family: 
- [ ] Social media accounts:
- [ ] Messaging apps:
- [ ] Cloud Storage:
- [ ] IT/Programming/SysAdmin:
- [ ] Other:


### Section 4: Assessment of target's password behaviors
*What does the target's password behavior tell us about their security habits?*

#### Password Behaviors
- [ ] Reuses same password for multiple logins
	- [ ] Password reuse follows username or email 
	- [ ] Password reuse follows site type (business logins get one type of password, gaming logins get another password)
- [ ] Uses variations of base password
- [ ] Keyboard patterns (qwerty, 123456)
- [ ] Personal info in passwords (names, dates)
- [ ] Appears to use password manager 
- [ ] Notes:

#### Password Inventory
| Line | Password | Username | Location | Notes |
|------|------------|----------|----------|-------|
| _Example_ | _password123_| _johnSmith_ | _Passwords.txt_| _reused 14 times but all before 2021_ |
| 1 | | | |
| 2 | | | |
| 3 | | | |


### Section 5: Target's Corporate Access
*Which types of relevant corporate accounts does this target have, according to the infostealer logs?*

#### Table summarizing target's corporate access as shown in logs, if any
| Line | System/URL | Username | Password | Notes |
|------|------------|----------|----------|-------|
| _Example_ | _portal.company.com_ | _johnSmith_ | _password123_| _reused on personal sites_ |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

#### Summary of corporate account types
- [ ] Developer (GitHub, GitLab, IDE logins): 
- [ ] IT/Admin (AWS, Azure, admin panels)
- [ ] Finance (QuickBooks, banking portals)
- [ ] HR (Workday, BambooHR, payroll)
- [ ] Sales (Salesforce, HubSpot, CRM)
- [ ] Executive (board portals, investor sites)
- [ ] Notes:



