# parse_lmgrd_log
use python to parse a lmgrd.log file

create different stats according license usage in lmgrd.log



1)
if desired, the log file itself can be anonymized:

Anonymized log file – rename user and machine names in log file
   python3 anonym_lmgrd.py lmgrd.log
Resulting in lmgrd_anonym.log file.



2)
main functionality to create statistics:

Scan log file for license information and csv file creation
   python3 parse_lmgrd.py –input=lmgrd.log
Resulting in several .csv files with statistics (default semikolon-separated)



3)
optional output of english/us-american instead of german/european format of csv:

Semikolon-Separated csv File:
   python3 parse_lmgrd.py –input=lmgrd.log
Comma-Separated with --csv-dot option:
   python3 parse_lmgrd.py –input=lmgrd.log --csv-dot


