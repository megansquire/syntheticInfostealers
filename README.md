# syntheticInfostealers
This software creates reasonable facsimiles of the typical files included in an "infostealer log" purchase. Currently covers the following infostealer families:
* Atomic
* Lumma
* Redline
* Stealc
* Vidar

### Personas.csv
The personas.csv file contains the information needed to create the synthetic logs. Users should edit this file as needed to add/delete rows. Columns should remain the same since those are used by the software to make a realistic log file.

The first column in the spreadsheet, "Infection," indicates which stealer we want to infect this person.

All of the data in the sample spreadsheet is fake, including fake names, fake domains and emails, etc.

### Config Files
The config files within each infostealer family directory contain various synethic string values that will show up in the fake logs. Users should edit those files as they see fit, however it is not required to edit these.

### Example Files
The example files are samples created with the software, so you can see the types of files it makes. There are 4 Atomic samples, 24 Lumma samples, 24 Redline samples, 16 Stealc samples, and 24 Vidar samples. There are only 16 Stealc examples (and not 24) because Github refused to upload some of the Stealc samples for an unknown security reason (error message did not match reality - will fix later).
