# DetChar Event Validation - Ronaldas Macas

import os, json, datetime
import pandas as pd
import numpy as np

from astropy.time import Time
from mdutils.mdutils import MdUtils


def assign_people(event_data, time, git_dir, vol_file, contact_file, validator, expert, mitigation, review, logger):

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
    t_starts = np.array(t_starts)
    vol_idx = np.where(t_starts - valid_time > 0)[0][0] - 1

    # read in contact list
    contact_file = f'{git_dir}/data/{contact_file}'
    contact_data = pd.read_csv(contact_file)

    if validator:
        contact_idx = contact_data.index[contact_data['name'] == validator][0]
    else:
        contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['validator']][0]
    event_data['contacts']['validator_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['validator_email'] = contact_data.iloc[contact_idx,:]['email']

    if expert:
        contact_idx = contact_data.index[contact_data['name'] == expert][0]
    else:
        contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['expert']][0]
    event_data['contacts']['expert_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['expert_email'] = contact_data.iloc[contact_idx,:]['email']

    if mitigation:
        contact_idx = contact_data.index[contact_data['name'] == mitigation][0]
    else:
        contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['mitigation']][0]
    event_data['contacts']['mitigation_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['mitigation_email'] = contact_data.iloc[contact_idx,:]['email']

    if review:
        contact_idx = contact_data.index[contact_data['name'] == review][0]
    else:
        contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['review']][0]
    event_data['contacts']['review_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['review_email'] = contact_data.iloc[contact_idx,:]['email']

    contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['lead1']][0]
    event_data['contacts']['lead1_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['lead1_email'] = contact_data.iloc[contact_idx,:]['email']
    contact_idx = contact_data.index[contact_data['name'] == vol_data.iloc[vol_idx,:]['lead2']][0]
    event_data['contacts']['lead2_name'] = contact_data.iloc[contact_idx,:]['name']
    event_data['contacts']['lead2_email'] = contact_data.iloc[contact_idx,:]['email']

    logger.info(f"Assigned event validation team: validator {event_data['contacts']['validator_name']}, "
                f"expert {event_data['contacts']['expert_name']}, "
                f"noise mitigation {event_data['contacts']['mitigation_name']}, "
                f"review {event_data['contacts']['review_name']}, "
                f"lead {event_data['contacts']['lead1_name']}, "
                f"lead {event_data['contacts']['lead2_name']}")

    return event_data


def update_data(event_data, git_dir, events_file, md_file, eval_url, logger):

    eval_url_md = f"[link]({event_data['eval_summary_url']})"
    dqr_url_md = f"[link]({event_data['dqr_url']})"
    contact_md = f"{event_data['contacts']['validator_name']} ([email](mailto:{event_data['contacts']['validator_email']}))"

    # create new event dict
    new_event = {'Event': [event_data['event_name']],
                 'Status': 'Not started',
                 'Conclusion': 'N/A',
                 'Noise mitigation': 'N/A',
                 'Reviewed': 'No',
                 'DQR': [dqr_url_md],
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


def git_issue(event_data, issue_email, issue_label, logger):

    lead1_name = event_data['contacts']['lead1_name'].split(' ')
    lead1_handle = f'{lead1_name[0].lower()}.{lead1_name[1].lower()}'
    lead2_name = event_data['contacts']['lead2_name'].split(' ')
    lead2_handle = f'{lead2_name[0].lower()}.{lead2_name[1].lower()}'

    text = (f"A place to discuss event validation for {event_data['event_name']}.\n\n"
            f"Assigned volunteer {event_data['contacts']['validator_name']} ({event_data['contacts']['validator_email']}), DetChar expert {event_data['contacts']['expert_name']} ({event_data['contacts']['expert_email']}), noise mitigation {event_data['contacts']['mitigation_name']} ({event_data['contacts']['mitigation_email']}), and reviewer {event_data['contacts']['review_name']} ({event_data['contacts']['review_email']}).\n\n"
            f"Checklist for the volunteer:\n"
            f"1. [ ] View the Data Quality Report\n"
            f"  - [ ] Make extensive notes for each detector\n"
            f"  - [ ] Decide if there are DQ issues in data; if there are DQ issues, decide if noise mitigation is needed\n"
            f"2. [ ] Fill in the event validation form\n"
            f"3. [ ] [If needed] Wait until the noise mitigation is completed\n"
            f"4. [ ] Report event validation findings at a DetChar call\n\n"
            f"For any questions, contact @{lead1_handle} ({event_data['contacts']['lead1_email']}) and @{lead2_handle} ({event_data['contacts']['lead2_email']}).\n\n"+issue_label
            )

    send_email(issue_email, event_data['event_name'], text)

    logger.info('Created a git issue')

    return

def emails(event_data, docs_url, logger):

    valid_email = event_data['contacts']['validator_email']
    expert_email = event_data['contacts']['expert_email']
    mitigation_email = event_data['contacts']['mitigation_email']
    review_email = event_data['contacts']['review_email']
    lead1_email = event_data['contacts']['lead1_email']
    lead2_email = event_data['contacts']['lead2_email']

    valid_name = event_data['contacts']['validator_name']
    expert_name = event_data['contacts']['expert_name']
    mitigation_name = event_data['contacts']['mitigation_name']
    review_name = event_data['contacts']['review_name']
    lead1_name = event_data['contacts']['lead1_name']
    lead2_name = event_data['contacts']['lead2_name']

    subject = f"A request to validate {event_data['event_name']}"

    pre_body_lead = f"Validator: {valid_email}, expert: {expert_email}, noise mitigation: {mitigation_email}, review: {review_email}.\n\n"
    pre_body_valid = f"You are assigned to validate candidate event {event_data['event_name']}. For more technical event validation questions, please refer to the DetChar expert {expert_name} ({expert_email}). More information about the event is given below.\n\n"
    pre_body_expert = f"{valid_name} ({valid_email}) has been assigned to validate candidate event {event_data['event_name']}, while you are assigned to act a DetChar expert. More information about the event is given below.\n\n"
    body = (f"Candidate event: {event_data['event_name']}\n"
            f"DQR: {event_data['dqr_url']}\n"
            f"Event validation form: {event_data['dqr_url']}\n"
            f"GitLab issue: {event_data['git_issue_url']}\n"
            f"Event validation documentation: {docs_url}\n"
            f"Validator: {valid_name} ({valid_email})\n"
            f"DetChar expert: {expert_name} ({expert_email})\n"
            f"Noise mitigation: {mitigation_name} ({mitigation_email})\n"
            f"Review: {review_name} ({review_email})\n\n")
    post_body = f"For any questions, contact {lead1_name} ({lead1_email}) and {lead2_name} ({lead2_email})."

    send_email(valid_email, subject, pre_body_valid+body+post_body)
    send_email(expert_email, subject, pre_body_expert+body+post_body)
    send_email(lead1_email, subject, pre_body_lead+body)
    send_email(lead2_email, subject, pre_body_lead+body)

    logger.info('Sent emails')

    return


def get_events_dict(list_fname, wdir):

    list_content = pd.read_csv(list_fname)
    list_events = list_content['Event']

    events = {}
    for event in list_events:

        fname = f'{wdir}/data/events/{event}.json'
        with open(fname, 'r') as event_json:
            event_data = json.load(event_json)


        event_dict = {}
        for key in event_data:
            if key != 'event_name':
                event_dict.update({f'{key}':event_data[key]})

        events.update({event_data['event_name']:event_dict})

    return events


def first_upper(string):
    final_string = f'{string[0].upper()}{string[1:]}'
    return final_string


def send_email(email, subject, body):

    sender = os.environ.get('USER')
    sender = f'{sender}@ligo.org'

    os.system(f'Mail -v -s "{subject}" -r {sender} {email} <<< "{body}"')

    return

def get_dets(h1, l1, v1):

    dets = []
    if h1:
        dets.append('H1')
    if l1:
        dets.append('L1')
    if v1:
        dets.append('V1')

    return dets
