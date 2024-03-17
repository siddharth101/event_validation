import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Optional app description')

# Required positional argument
parser.add_argument('--fname', required=False, type=str, help='full filename path of the csv summary file', default='/home/dqr/event-validation/data/events_O4a.csv')
parser.add_argument('--git_dir', required=False, type=str, help='git directory path', default='/home/dqr/event-validation')
parser.add_argument('--prefix', required=False, type=str, help='prefix for output plots', default='O4a')
args = parser.parse_args()

# read the csv summary file
csv = pd.read_csv(args.fname)

## STATS
finalized = []
for final_bool in csv['Finalized']:
    finalized.append(1) if final_bool == 'Yes' else finalized.append(0)

# counters for finalized events
no_dq_issues = 0
glitch_sub_req = 0
dq_issues_no_glitch_sub_req = 0
retracted = 0

# counters for not finalized events
ev = 0
glitch_sub_req_not_finalized = 0
review = 0
pe = 0

for idx, val in enumerate(finalized):

    if val:
        iloc = csv['Review conclusion'].iloc[idx]
        if iloc == "No DQ issues":
            no_dq_issues += 1
        elif iloc == "Noise mitigation required":
            glitch_sub_req += 1
        elif iloc == "DQ issues but no noise mitigation required":
            dq_issues_no_glitch_sub_req += 1
        elif iloc == "Retracted":
            retracted += 1

    else:
        iloc = csv['Next step'].iloc[idx][0:4]
        if iloc == "Even":
            ev += 1
        elif iloc == "Glit":
            glitch_sub_req_not_finalized += 1
        elif iloc == "Revi":
            review += 1
        elif iloc == 'PE (':
            pe +=1

## PLOTS
# total
total = np.array([np.sum(finalized), len(finalized) - np.sum(finalized)])
labels = ["Finalized", "Not finalized"]

plt.figure()
plt.pie(total, labels=labels,
        autopct=lambda x: '{:.0f}'.format(x*total.sum()/100))
plt.axis('equal')
plt.title('All events')
plt.savefig(f'{args.git_dir}/docs/img/{args.prefix}_total.png', dpi=200)

# finalized
finalized = np.array([no_dq_issues, glitch_sub_req, dq_issues_no_glitch_sub_req, retracted])
labels = ['No DQ issues', 'Glitch subtraction required', 'DQ issues but no glitch subtraction required', 'Retracted']

plt.figure()
plt.pie(finalized, labels=labels,
        autopct=lambda x: '{:.0f}'.format(x*finalized.sum()/100))
plt.axis('equal')
plt.title('Finalized events')
plt.savefig(f'{args.git_dir}/docs/img/{args.prefix}_finalized.png', dpi=200)

# not finalized
not_finalized = np.array([ev, glitch_sub_req_not_finalized, review, pe])
labels = ['Event \n validation', 'Glitch \n subtraction', 'Review', 'PE']
plt.figure()
plt.bar(labels, not_finalized)
plt.title('Next step for not finalized events')
plt.grid(False)
plt.savefig(f'{args.git_dir}/docs/img/{args.prefix}_not_finalized.png', dpi=200)

#not_finalized = np.array([ev, glitch_sub_req_not_finalized, review])
#labels = ['Event validation', 'Glitch subtraction', 'Review']

#plt.figure()
#plt.pie(not_finalized, labels=labels,
#        autopct=lambda x: '{:.0f}'.format(x*not_finalized.sum()/100))
#plt.axis('equal')
#plt.title('Next step for not finalized events')
#plt.savefig(f'{args.git_dir}/docs/img/{args.prefix}_not_finalized.png', dpi=200)
