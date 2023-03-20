# DetChar Event Validation - Ronaldas Macas

import pdb, json, subprocess, datetime
import pandas as pd
import numpy as np

from astropy.time import Time
from mdutils.mdutils import MdUtils


def assign_people(event_data, time, git_dir, vol_file, contact_file, validator, rrt, mitigation, logger):

    # determine which time to use
    if time:
        valid_time = time
    else:
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
        valid_time = Time(now_str, format='isot', scale='utc').gps

    # determine when volunteers are available
    vol_file = f'{git_dir}/data/{vol_file}'
    vol_data = pd.read_csv(vol_file)

    t_starts = []
    for t in vol_data['date_start']:
        t_starts.append(Time(t, format='iso', scale='utc').gps)
    vol_idx = np.where(t_starts - valid_time > 0)[0][0] - 1

    # read in contact list
    contact_file = f'{git_dir}/data/{contact_file}'
    contact_data = pd.read_csv(contact_file)

    if validator:
        try:
            contact_idx = contact_data.index[contact_data['name'] == validator][0]
            event_data['contacts']['validator_name'] = contact_data.iloc[contact_idx,:]['name']
            event_data['contacts']['validator_email'] = contact_data.iloc[contact_idx,:]['email']
        except:
            raise ValueError(f'Unable to find {validator} in {contact_file}')
    else:
        event_data['contacts']['validator_name'] = vol_data.iloc[vol_idx,:]['validator_name']
        event_data['contacts']['validator_email'] = vol_data.iloc[vol_idx,:]['validator_email']

    if rrt:
        try:
            contact_idx = contact_data.index[contact_data['name'] == rrt][0]
            event_data['contacts']['rrt_name'] = contact_data.iloc[contact_idx,:]['name']
            event_data['contacts']['rrt_email'] = contact_data.iloc[contact_idx,:]['email']
        except:
            raise ValueError(f'Unable to find {rrt} in {contact_file}')
    else:
        event_data['contacts']['rrt_name'] = vol_data.iloc[vol_idx,:]['rrt_name']
        event_data['contacts']['rrt_email'] = vol_data.iloc[vol_idx,:]['rrt_email']

    if mitigation:
        try:
            contact_idx = contact_data.index[contact_data['name'] == mitigation][0]
            event_data['contacts']['mitigation_name'] = contact_data.iloc[contact_idx,:]['name']
            event_data['contacts']['mitigation_email'] = contact_data.iloc[contact_idx,:]['email']
        except:
            raise ValueError(f'Unable to find {mitigation} in {contact_file}')
    else:
        event_data['contacts']['mitigation_name'] = vol_data.iloc[vol_idx,:]['mitigation_name']
        event_data['contacts']['mitigation_email'] = vol_data.iloc[vol_idx,:]['mitigation_email']

    event_data['contacts']['lead1_name'] = vol_data.iloc[vol_idx,:]['lead1_name']
    event_data['contacts']['lead1_email'] = vol_data.iloc[vol_idx,:]['lead1_email']
    event_data['contacts']['lead2_name'] = vol_data.iloc[vol_idx,:]['lead2_name']
    event_data['contacts']['lead2_email'] = vol_data.iloc[vol_idx,:]['lead2_email']

    logger.info(f"Assigned event validation team: validator {event_data['contacts']['validator_name']}, "
                f"RRT {event_data['contacts']['rrt_name']}, "
                f"noise mitigation {event_data['contacts']['mitigation_name']}, "
                f"lead {event_data['contacts']['lead1_name']}, "
                f"lead {event_data['contacts']['lead2_name']}")

    return event_data


def update_data(event_data, git_dir, events_file, md_file, eval_url, logger):

    eval_summary_url = f"{eval_url}/summaries/{event_data['event_name']}"
    eval_url_md = f'[link]({eval_summary_url})'
    contact_md = f"{event_data['contacts']['validator_name']} ([email](mailto:{event_data['contacts']['validator_email']}))"

    # create new event dict
    new_event = {'Event': [event_data['event_name']],
                 'Status': 'Not started',
                 'Conclusion': 'N/A',
                 'Noise mitigation': 'N/A',
                 'Reviewed': 'No',
                 'Summary': [eval_url_md],
                 'Contact person': [contact_md]}

    # list_fname = f'{git_dir}/data/event_list.csv'
    # new_event_df = pd.DataFrame.from_dict(new_event)
    # new_event_df.to_csv(list_fname, index=False)
    # read outdated data frame
    old_event_list = pd.read_csv(f'{git_dir}/data/{events_file}', keep_default_na=False)

    # make new event as a pd DFrame
    new_event_df = pd.DataFrame.from_dict(new_event)

    # merge data frames
    new_event_list = pd.concat([old_event_list, new_event_df], ignore_index=True)

    # write to csv
    new_event_list.to_csv(f'{git_dir}/data/{events_file}', index=False)

    # update website's md table
    md_fname = f'{git_dir}/data/{md_file}'
    with open(md_fname, 'w') as md:
        new_event_list.to_markdown(buf=md, numalign="center", index=False)

    logger.info(f"Updated data files")

    return


def git_issue(event_data, git_dir, issue_email, logger):

    lead1_name = event_data['contacts']['lead1_name'].split(' ')
    lead1_handle = f'{lead1_name[0].lower()}.{lead1_name[1].lower()}'
    lead2_name = event_data['contacts']['lead2_name'].split(' ')
    lead2_handle = f'{lead2_name[0].lower()}.{lead2_name[1].lower()}'

    text = (f"A place to discuss event validation for {event_data['event_name']}.\n\n"
            f"Assigned volunteer {event_data['contacts']['validator_name']} ({event_data['contacts']['validator_email']}) and RRT {event_data['contacts']['rrt_name']} ({event_data['contacts']['rrt_email']}).\n\n"
            f"For any questions, contact @{lead1_handle} ({event_data['contacts']['lead1_email']}) and @{lead2_handle} ({event_data['contacts']['lead2_email']}).")

    subprocess.check_call([f'{git_dir}/code/send_email.sh', issue_email, event_data['event_name'], text])
    logger.info('Created a git issue')

    return

def emails(event_data, git_dir, docs_url, logger):

    valid_email = event_data['contacts']['validator_email']
    rrt_email = event_data['contacts']['rrt_email']
    mitigation_email = event_data['contacts']['mitigation_email']
    lead1_email = event_data['contacts']['lead1_email']
    lead2_email = event_data['contacts']['lead2_email']

    valid_name = event_data['contacts']['validator_name']
    rrt_name = event_data['contacts']['rrt_name']
    mitigation_name = event_data['contacts']['mitigation_name']
    lead1_name = event_data['contacts']['lead1_name']
    lead2_name = event_data['contacts']['lead2_name']

    subject = f"A request to validate {event_data['event_name']}"

    pre_body_lead = f"Validator: {valid_email}, RRT: {rrt_email}.\n\n"
    pre_body_valid = f"You are assigned to validate candidate event {event_data['event_name']}. For more technical event validation questions, please refer to your RRT team member {rrt_name} ({rrt_email}). More information about the event is given below.\n\n"
    pre_body_rrt = f"{valid_name} ({valid_email}) has been assigned to validate candidate event {event_data['event_name']}, while you are assigned to act as an RRT member and a technical advisor. More information about the event is given below.\n\n"
    body = (f"Candidate event: {event_data['event_name']}\n"
            f"DQR: {event_data['dqr_url']}\n"
            f"Event validation form: {event_data['dqr_url']}\n"
            f"GitLab issue: {event_data['git_issue_url']}\n"
            f"Event validation documentation: {docs_url}\n"
            f"Validator: {valid_name} ({valid_email})\n"
            f"RRT: {rrt_name} ({rrt_email})\n"
            f"Noise mitigation: {mitigation_name} ({mitigation_name})\n\n")
    post_body = f"For any questions, contact {lead1_name} ({lead1_email}) and {lead2_name} ({lead2_name})."


    subprocess.check_call([f'{git_dir}/code/send_email.sh', valid_email, subject, pre_body_valid+body+post_body])
    subprocess.check_call([f'{git_dir}/code/send_email.sh', rrt_email, subject, pre_body_rrt+body+post_body])
    subprocess.check_call([f'{git_dir}/code/send_email.sh', lead1_email, subject, body])
    subprocess.check_call([f'{git_dir}/code/send_email.sh', lead2_email, subject, body])

    logger.info('Sent emails')

    return
