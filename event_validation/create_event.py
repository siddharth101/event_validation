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
__version__ = '0.6'
__process_name__ = 'ev-create-event'

def init_event_validation(event_name,
                          graceid,
                          jsonid,
                          t0,
                          time,
                          far,
                          far_threshold,
                          ignore_far,
                          git_dir,
                          label,
                          events_file,
                          md_file,
                          vol_file,
                          contact_file,
                          validator,
                          expert,
                          mitigation,
                          review,
                          dqr_url,
                          superevent_url,
                          detector_url,
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

    # apply label to events/md table/vol files if no files given
    if events_file is None:
        events_file = f'events_{label}.csv'

    if md_file is None:
        md_file = f'table_{label}.md'

    if vol_file is None:
        vol_file = f'rota_{label}.csv'

    #--------------------------------------------------------------------------

    # make urls
    t0_date = Time(t0, format='gps').iso[0:10].replace("-","")
    detector_url = f'{detector_url}/day/{t0_date}'
    ev_summary_url = f'{eval_url}/summary/{event_name}'
    ev_form_url = f'{eval_url}/validation/{event_name}'

    #--------------------------------------------------------------------------

    # make event dict
    logger.debug(f'Creating event dictionary for {event_name}')
    init_status = 0  # initial status, nothing started
    valid_dict = {
                  'conclusion': "",
                  'low_noise': "",
                  'noise_tstart': "",
                  'noise_tend': "",
                  'noise_flow': "",
                  'noise_fhigh': ""
                  }
    review_dict = {
                  'conclusion': "",
                  'recommend_ifo': "",
                  'analysis_tstart': "",
                  'analysis_tend': "",
                  'analysis_flow': "",
                  'analysis_fhigh': "",
                  'frame_type': "",
                  'channel': "",
                  'noise_left': ""
                  }
    glitch_request_dict = {
                          'required': "",
                          'noise_tstart': "",
                          'noise_tend': "",
                          'noise_flow': "",
                          'noise_fhigh': ""
                          }
    glitch_result_dict = {
                          'frame_type': "",
                          'channel': ""
                          }
    event_data = {
                  'event_name': event_name,
                  'status': init_status,
                  'reviewed': init_status,
                  'links': {
                            'gracedb': superevent_url,
                            'detector': detector_url,
                            'dqr': dqr_url,
                            'issue': gitlab_url,
                            'summary': ev_summary_url
                            },
                  'forms': {
                            'validation': {
                                           'H1': valid_dict,
                                           'L1': valid_dict,
                                           'V1': valid_dict},
                            'review': {
                                       'duration': "",
                                       'H1': review_dict,
                                       'L1': review_dict,
                                       'V1': review_dict},
                            'glitch_request': {
                                               't0':t0,
                                               'H1': glitch_request_dict,
                                               'L1': glitch_request_dict,
                                               'V1': glitch_request_dict},
                            'glitch_result': {
                                              'H1': glitch_result_dict,
                                              'L1': glitch_result_dict,
                                              'V1': glitch_result_dict}
                             },
                  'comments': {
                               'validation': "",
                               'review': "",
                               'glitch_request': "",
                               'glitch_result': "",
                               'other': ""
                               },
                  'contacts': {
                               'validator_name': "",
                               'validator_email': "",
                               'expert_name': "",
                               'expert_email': "",
                               'mitigation_name': "",
                               'mitigation_email': "",
                               'review_name': "",
                               'review_email': "",
                               'lead1_name': "",
                               'lead1_email': "",
                               'lead2_name': "",
                               'lead2_email': ""
                               },
                  'other': "",
                  'cmd': cmd
                  }

    #--------------------------------------------------------------------------

    # assign people
    logger.debug('Assigning volunteers')
    event_data = assign_people(event_data, time, git_dir, vol_file, contact_file, validator, expert, mitigation, review, logger)

    #--------------------------------------------------------------------------

    # update data files
    logger.debug('Updating data files')
    update_data(event_data, git_dir, events_file, md_file, logger)

    #--------------------------------------------------------------------------

    # create a git issue using gitlab api
    if create_issue:
        logger.debug('Making a git issue')
        token = 'glpat-CE-i6fzUxsUpUhcyRmFC'
        project_id = 13628
        git_issue(event_data, gitlab_url, token, project_id, label, logger)

    #--------------------------------------------------------------------------

    # create a json for the event
    logger.debug('Creating event file')
    event_fname = f'{git_dir}/data/events/{event_name}.json'
    with open(event_fname, 'w', encoding='utf-8') as f:
        json.dump(event_data, f, ensure_ascii=False, indent=4)

    logger.info(f'Created event file: {git_dir}/data/events/{event_name}.json')

    #--------------------------------------------------------------------------

    # send emails
    if send_email:
        logger.debug('Sending emails')
        emails(event_data, ev_form_url, logger)

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
    parser.add_argument('--t0', type=float, required=True, help='merger time for a CBC event, central time for a Burst event.')
    parser.add_argument('--time', type=float, help='GPS time for which a validation team will be selected. Default: current GPS time')
    parser.add_argument('--far', type=float, help='event FAR. If given, it will be compared to threshold FAR. If above threshold FAR, there will be no event validation.')
    parser.add_argument('--far_threshold', type=float, default=0.000000193, help='Threshold FAR. Event validation is performed only if event FAR is smaller than threshold FAR.')
    parser.add_argument('--ignore_far', action=argparse.BooleanOptionalAction, help='Perform event validation independent on event FAR.')
    parser.add_argument('--git_dir', type=os.path.abspath, required=True, help='Event validation infrastructure git directory')
    parser.add_argument('--label', type=str, required=True, help="label to apply to git issues; can also be used for events_LABEL.csv, table_LABEL.md, rota_LABEL.csv files")
    parser.add_argument('--events_file', type=str, help="csv file containing events in 'data' folder; if empty, uses label as suffix")
    parser.add_argument('--md_file', type=str, help="MD table to be edited with new event in 'data' folder; if empty, uses label as suffix")
    parser.add_argument('--vol_file', type=str, help="csv file containing volunteer information in 'data' folder; if empty, uses label as suffix")
    parser.add_argument('--contact_file', type=str, default='contacts.csv', help="csv file containing volunteer contact information in 'data' folder")
    parser.add_argument('--validator', type=str, help="Validator name and surname")
    parser.add_argument('--expert', type=str, help="Expert name and surname")
    parser.add_argument('--mitigation', type=str, help="Noise mitigation contact name and surname")
    parser.add_argument('--review', type=str, help="Event validation review contact name and surname")
    parser.add_argument('--dqr_url', type=str, required=True, help='Data quality report URL')
    parser.add_argument('--superevent_url', type=str, required=True, help='GraceDB super event URL')
    parser.add_argument('--eval_url', type=str, default='https://dqr.ligo.caltech.edu/ev_forms', help='Event validation form URL, default: https://dqr.ligo.caltech.edu/ev_forms')
    parser.add_argument('--detector_url', type=str, default='https://ldas-jobs.ligo.caltech.edu/~detchar/summary', help='DetChar summary URL, default: https://ldas-jobs.ligo.caltech.edu/~detchar/summary')
    parser.add_argument('--gitlab_url', type=str, default='https://git.ligo.org/detchar/event-validation/-/issues', help='GitLab issues URL, default: https://git.ligo.org/detchar/event-validation/-/issues')
    parser.add_argument('--docs_url', type=str, default='https://ldas-jobs.ligo.caltech.edu/~dqr/event_validation', help='Documentation URL, default: https://ldas-jobs.ligo.caltech.edu/~dqr/event_validation')
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
                          t0=args.t0,
                          time=args.time,
                          far=args.far,
                          far_threshold=args.far_threshold,
                          ignore_far=args.ignore_far,
                          git_dir=args.git_dir,
                          label=args.label,
                          events_file=args.events_file,
                          md_file=args.md_file,
                          vol_file=args.vol_file,
                          contact_file=args.contact_file,
                          validator=args.validator,
                          expert=args.expert,
                          mitigation=args.mitigation,
                          review=args.review,
                          dqr_url=args.dqr_url,
                          superevent_url=args.superevent_url,
                          detector_url=args.detector_url,
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
