# DEVIL: DetChar Event Validation Infrastructure for the LVK - Ronaldas Macas

import pdb
import json
import pandas as pd
from mdutils.mdutils import MdUtils

import datetime
from astropy.time import Time
import numpy as np


def create_event_data(event_name, dqr_status, val_status,  dqr_url, gitlab_url, logger):
    event_data = {'event_name': event_name,
                  'dqr_status': dqr_status,
                  'valid_status': val_status,
                  'valid_conclusion': [],
                  'flow': [],
                  'fhigh': [],
                  'comments': [],
                  'dqr_url': dqr_url,
                  'git_issue_url': gitlab_url,
                  'devil_form_url': [],
                  'validator_name': [],
                  'validator_email': [],
                  'rrt_name': [],
                  'rrt_email': [],
                  'lead1_name': [],
                  'lead1_email': [],
                  'lead2_name': [],
                  'lead2_email': []
                  }

    logger.debug(f'Created event dictionary for {event_name}')

    return event_data


def assign_people(event_data, time, git_dir, vol_file, contact_file, validator, rrt, logger):

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
            event_data['validator_name'] = contact_data.iloc[contact_idx,:]['name']
            event_data['validator_email'] = contact_data.iloc[contact_idx,:]['email']
        except:
            raise ValueError(f'Unable to find {validator} in {contact_file}')
    else:
        event_data['validator_name'] = vol_data.iloc[vol_idx,:]['validator_name']
        event_data['validator_email'] = vol_data.iloc[vol_idx,:]['validator_email']

    if rrt:
        try:
            contact_idx = contact_data.index[contact_data['name'] == rrt][0]
            event_data['rrt_name'] = contact_data.iloc[contact_idx,:]['name']
            event_data['rrt_email'] = contact_data.iloc[contact_idx,:]['email']
        except:
            raise ValueError(f'Unable to find {rrt} in {contact_file}')
    else:
        event_data['rrt_name'] = vol_data.iloc[vol_idx,:]['rrt_name']
        event_data['rrt_email'] = vol_data.iloc[vol_idx,:]['rrt_email']

    event_data['lead1_name'] = vol_data.iloc[vol_idx,:]['lead1_name']
    event_data['lead1_email'] = vol_data.iloc[vol_idx,:]['lead1_email']
    event_data['lead2_name'] = vol_data.iloc[vol_idx,:]['lead2_name']
    event_data['lead2_email'] = vol_data.iloc[vol_idx,:]['lead2_email']

    logger.info(f"Assigned validator {event_data['validator_name']}, "
                f"RRT {event_data['rrt_name']}, "
                f"lead {event_data['lead1_name']}, "
                f"lead {event_data['lead2_name']}")
    return event_data


def create_event_file(event_data, git_dir, logger):

    event_name = event_data['event_name']

    # write to a file
    event_fname = f'{git_dir}/data/events/{event_name}.json'
    with open(event_fname, 'w', encoding='utf-8') as f:
        json.dump(event_data, f, ensure_ascii=False, indent=4)

    logger.info(f'Created event file: {git_dir}/data/events/{event_name}.json')

    return event_fname


def update_data(event_data, git_dir, events_file, md_file, logger):

    # create new event dict
    new_event = {'Candidate event': event_data['event_name'], 'DQR status': [event_data['dqr_status']], 'Validation status': [event_data['valid_status']], 'Validation conclusion':event_data['valid_conclusion'], 'Volunteer':event_data['validator_name'], 'Email':event_data['validator_email']}
    # edit empty validation conclusion
    new_event['Validation conclusion'] = ''

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


def git_issue(event_data, gitlab_base_issue_url, logger):
   # TODO@ send the issue and put the link here
   event_data['git_issue_url'] = gitlab_base_issue_url

   logger.info('IMPLEMENTME: Created git issue')

   return event_data
