#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: nu:ai:ts=4:sw=4

"""
A script to be executed by the DQR workflow to distribute candidate events and
notify people related to the event validation. Based on LIGO-T2200265
"""

import argparse, os, sys, logging
from .utils import *

__author__ = 'Ronaldas Macas'
__email__ = 'ronaldas.macas@ligo.org'
__version__ = '0.3'
__process_name__ = 'Event Validation'

def init_event_validation(event_name,
                          graceid,
                          jsonid,
                          time,
                          far,
                          far_threshold,
                          ignore_far,
                          git_dir,
                          events_file,
                          md_file,
                          vol_file,
                          contact_file,
                          validator,
                          expert,
                          mitigation,
                          review,
                          dqr_url,
                          eval_url,
                          gitlab_url,
                          docs_url,
                          send_email,
                          create_issue,
                          cmd,
                          logger):

    logger.info(f'EVAL: start')

    #--------------------------------------------------------------------------

    # find what to use: GraceDB ID, json or event name
    if jsonid:
        logger.info(f'Reading event {jsonid}')
        try:
            with open(jsonid, 'r') as f:
                event = json.load(f)
                event_name = event['graceid']
                far = event['far']
        except:
            raise ValueError(f'Error loading json file {jsonid}')

    elif graceid:
        logger.info(f'Parsing GraceDB {jsonid}')
        try:
            os.system(f'gdb2json {graceid}')
            with open(f'{graceid}.json', 'r') as f:
                event = json.load(f)
                event_name = event['graceid']
                far = event['far']
            os.system(f'rm {graceid}.json')
        except:
            raise ValueError(f'Error parsing GraceDB for {graceid}')
    elif event_name:
        logger.info(f'Using provided candidate event name {event_name}')
    else:
        raise ValueError('Need to provide either event name, json file or GraceDB ID.')

    #--------------------------------------------------------------------------

    # decide if prepare event validation depending on FAR
    if far:
        if far > far_threshold:
            if ignore_far:
                logger.warning(f'Setting up event validation even though event FAR ({far}) is bigger than FAR threshold ({far_threshold})')
            else:
                logger.warning(f'Event FAR ({far}) is bigger than FAR threshold ({far_threshold}). No need for event validation, exiting.')
                exit()

    #--------------------------------------------------------------------------

    # make event dict
    logger.debug(f'Creating event dictionary for {event_name}')
    valid_status = 0  # i.e. validation not started
    review_status = 0  # i.e. not reviewed
    eval_summary_url = f'{eval_url}/summary/{event_name}'
    noise_mitig_dict = {'required': [],
                        'status': [],
                        'method': [],
                        'fstart': [],
                        'fend': [],
                        'tstart': [],
                        'tend': [],
                        'frame': []
                        }
    event_data = {'event_name': event_name,
                  'valid_status': valid_status,
                  'valid_conclusion': [],
                  'reviewed': review_status,
                  'dqr_url': dqr_url,
                  'eval_summary_url': eval_summary_url,
                  'git_issue_url': gitlab_url,
                  'detectors': [],
                  'noise_mitigation': {'H1': noise_mitig_dict,
                                       'L1': noise_mitig_dict,
                                       'V1': noise_mitig_dict},
                  'comments': {'validator': [],
                               'mitigation': [],
                               'review': [],
                               'other': []
                               },
                  'contacts': {'validator_name': [],
                               'validator_email': [],
                               'expert_name': [],
                               'expert_email': [],
                               'mitigation_name': [],
                               'mitigation_email': [],
                               'review_name': [],
                               'review_email': [],
                               'lead1_name': [],
                               'lead1_email': [],
                               'lead2_name': [],
                               'lead2_email': []
                               },
                  'other': [],
                  'cmd': cmd
                  }

    #--------------------------------------------------------------------------

    # assign people
    logger.debug('Assigning volunteers')
    event_data = assign_people(event_data, time, git_dir, vol_file, contact_file, validator, expert, mitigation, review, logger)

    #--------------------------------------------------------------------------

    # create a json for the event
    logger.debug('Creating event file')
    event_fname = f'{git_dir}/data/events/{event_name}.json'
    with open(event_fname, 'w', encoding='utf-8') as f:
        json.dump(event_data, f, ensure_ascii=False, indent=4)

    logger.info(f'Created event file: {git_dir}/data/events/{event_name}.json')

    #--------------------------------------------------------------------------

    # update data files
    logger.debug('Updating data files')
    update_data(event_data, git_dir, events_file, md_file, eval_url, logger)

    #--------------------------------------------------------------------------

    # create a git issue by sending an email
    if create_issue:
        logger.debug('Making a git issue')
        issue_email = 'contact+detchar-event-validation-13628-iczve9w98b94opzztj2puptg-issue@support.ligo.org'
        git_issue(event_data, issue_email, logger)

    #--------------------------------------------------------------------------

    # send emails
    if send_email:
        logger.debug('Sending emails')
        emails(event_data, docs_url, logger)

     #--------------------------------------------------------------------------

    # update mkdocs
    logger.debug('Updating mkdocs')
    os.system(f'cd {git_dir}; mkdocs -q build')
    logger.info('Updated mkdocs')

    #--------------------------------------------------------------------------

    logger.info('EVAL: end')


def main():

    # parse args
    parser = argparse.ArgumentParser(description=__doc__,
                                     prog=__process_name__)
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbose output')
    parser.add_argument('-V', '--version', action='version',
                        version=__version__)
    parser.add_argument('-q', '--quiet', default=False, action='store_true',
                        help='show only fatal errors')
    parser.add_argument('--event_name', type=str, help='event name')
    parser.add_argument('--graceid', type=str, help='event GraceDB ID')
    parser.add_argument('--jsonid', type=str, help='event GraceDB json file')
    parser.add_argument('--time', type=float, help='GPS time for which a validation team will be selected. Default: current GPS time')
    parser.add_argument('--far', type=float, help='event FAR. If given, it will be compared to threshold FAR. If above threshold FAR, there will be no event validation.')
    parser.add_argument('--far_threshold', type=float, default=0.000000193, help='Threshold FAR. Event validation is performed only if event FAR is smaller than threshold FAR.')
    parser.add_argument('--ignore_far', action=argparse.BooleanOptionalAction, help='Perform event validation independent on event FAR.')
    parser.add_argument('--git_dir', type=os.path.abspath, required=True, help='Event validation infrastructure git directory')
    parser.add_argument('--events_file', type=str, required=True, help="csv file containing events in 'data' folder")
    parser.add_argument('--md_file', type=str, required=True, help="MD table to be edited with new event in 'data' folder")
    parser.add_argument('--vol_file', type=str, required=True, help="csv file containing volunteer information in 'data' folder")
    parser.add_argument('--contact_file', type=str, required=True, help="csv file containing volunteer contact information in 'data' folder")
    parser.add_argument('--validator', type=str, help="Validator name and surname")
    parser.add_argument('--expert', type=str, help="Expert name and surname")
    parser.add_argument('--mitigation', type=str, help="Noise mitigation contact name and surname")
    parser.add_argument('--review', type=str, help="Event validation review contact name and surname")
    parser.add_argument('--dqr_url', type=str, required=True, help='Data quality report URL')
    parser.add_argument('--eval_url', type=str, default='https://ldas-jobs.ligo.caltech.edu/~detchar/eval', help='Event validation form URL, default: https://ldas-jobs.ligo.caltech.edu/~detchar/eval/')
    parser.add_argument('--gitlab_url', type=str, default='https://git.ligo.org/detchar/event-validation/-/issues', help='GitLab issues URL, default: https://git.ligo.org/detchar/event-validation/-/issues')
    parser.add_argument('--docs_url', type=str, default='https://ldas-jobs.ligo.caltech.edu/~ronaldas.macas/eval_website/', help='Documentation URL, default: https://ldas-jobs.ligo.caltech.edu/~ronaldas.macas/eval_website/')
    parser.add_argument('--send_email', action=argparse.BooleanOptionalAction, help='Send notification emails.')
    parser.add_argument('--create_issue', action=argparse.BooleanOptionalAction, help='Create a git issue for the candidate event')
    args = parser.parse_args()

#------------------------------------------------------------------------------


    # command line used to run this script
    cmd_line = ' '.join(sys.argv)

    # set up logging
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s')
    logger = logging.getLogger(__process_name__)
    logger.setLevel(logging.DEBUG)

    verbosity = 0 if args.quiet else args.verbose
    if verbosity < 1:
        logger.setLevel(logging.CRITICAL)
    elif verbosity < 2:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

    init_event_validation(event_name=args.event_name,
                          graceid=args.graceid,
                          jsonid=args.jsonid,
                          time=args.time,
                          far=args.far,
                          far_threshold=args.far_threshold,
                          ignore_far=args.ignore_far,
                          git_dir=args.git_dir,
                          events_file=args.events_file,
                          md_file=args.md_file,
                          vol_file=args.vol_file,
                          contact_file=args.contact_file,
                          validator=args.validator,
                          expert=args.expert,
                          mitigation=args.mitigation,
                          review=args.review,
                          dqr_url=args.dqr_url,
                          eval_url=args.eval_url,
                          gitlab_url=args.gitlab_url,
                          docs_url=args.docs_url,
                          send_email=args.send_email,
                          create_issue=args.create_issue,
                          cmd=cmd_line,
                          logger=logger)

#------------------------------------------------------------------------------

# allow to be run on the command line
if __name__ == "__main__":
    main()
