---
title: EVforms
author: Ronaldas Macas <ronaldas.macas@ligo.org>
---

# EVforms

EVforms is a website that automates the process of communicating DetChar event validation results between different groups. To do that, the website contains forms that event validation volunteers and the noise mitigation review team should fill out. 

The website can be found [here](https://dqr.ligo.caltech.edu/ev_forms).

## Event validation form

Volunteers will be asked to fill an online event validation form with the following fields:

- Name:
- Email:
- Notes:

*Hanford*

- Validation conclusion:
	- not observing
	- no DQ issues
	- DQ issues
- Detector is in low noise:
	- No
	- Yes
<!---->
<!---->
<!---->
- Noise box start GPS time:
- Noise box end GPS time:
- Noise box f_low in Hz:
- Noise box f_high in Hz:

*Repeated for Livingston and Virgo*

## Guidelines on how to fill an event validation form

**Validation conclusion**:

- Not observing — if the detector is not observing
- No DQ issues — if there are no data quality (DQ) issues
- DQ issues — if there are DQ issues present in any of the interferometer

**Detector is in low noise**: this can be checked from the summary pages (e.g. [link](https://ldas-jobs.ligo-la.caltech.edu/~detchar/summary/day/20230501/)) in the Lock Segments plot.


**Noise box start GPS time**: If there are glitches present in the longest OmegaScan plot from DQR, note the gpstime of the first occurrence of a glitch

**Noise box end GPS time** : If there are glitches present in the longest OmegaScan plot from DQR, note the gpstime of the last occurrence of a glitch

**Noise box f_low**: If there are glitches present in the longest OmegaScan plot from DQR, note the starting frequency of a glitch

**Noise box f_high**: If there are glitches present in the longest OmegaScan plot from DQR, note the highest frequency of a glitch

### Example

Here is an OmegaScan for an event at 1368658140.57 with a glitch just after it. The glitch is from +1.6 to +1.9s after the event time 1368658140.57.

Noise box properties:

- Noise box start GPS time: 1368658142.17
- Noise box end GPS time: 1368658142.47
- Noise box f_low in Hz: 15
- Noise box f_high in Hz: 350


