# syntheticInfostealers
This software creates reasonable facsimiles of the typical files included in an "infostealer log" purchase. 

Given a spreadsheet of data about an infected "persona", and an indicator of which infostealer infected which persona, this software creates a set of infostealer logs that resemble that type of infection.

Currently covers the following infostealer families:
* Atomic
* Lumma
* Redline
* Stealc
* Vidar

### Personas.csv
The personas.csv file contains the information needed to create the synthetic logs. Users should edit this file as needed to add/delete rows. Columns should remain the same since those are used by the software to make a realistic log file.
