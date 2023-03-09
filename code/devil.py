#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: nu:ai:ts=4:sw=4

"""                     ***IN PROGRESS***
A script to be executed by the DQR workflow to distribute candidate events and
notify people related to the event validation. Based on https://dcc.ligo.org/..
"""

import argparse, os, sys, logging
from utils import *

__author__ = 'Ronaldas Macas'
__email__ = 'ronaldas.macas@ligo.org'
__version__ = '0.1'
__process_name__ = 'DEVIL'

def initialize_devil(event_name, graceid, jsonid, time, far, far_threshold, ignore_far, git_dir, events_file, md_file, vol_file, contact_file, validator, rrt, dqr_status, val_status, dqr_url, gitlab_url, cmd, logger):

    logger.info(f'DEVIL: start')

    # find what to use, graceid, json or event name
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

    # decide if prepare event validation depending on FAR
    if far:
        if far > far_threshold:
            if ignore_far:
                logger.warning(f'Setting up event validation even though event FAR ({far}) is bigger than FAR threshold ({far_threshold})')
            else:
                logger.warning(f'Event FAR ({far}) is bigger than FAR threshold ({far_threshold}). No need for event validation, exiting.')
                exit()

    # make event dict
    event_data = create_event_data(event_name, dqr_status, val_status, dqr_url, gitlab_url, logger)

    # assign people
    logger.debug('Assigning volunteers')
    event_data = assign_people(event_data, time, git_dir, vol_file, contact_file, validator, rrt, logger)

    # create a file for the event
    logger.debug('Creating event file')
    event_fname = create_event_file(event_data, git_dir, logger)

    # update data files
    # TODO: fix the update_data fn by adding proper dict values, eg rrt member, etc
    logger.debug('Updating data files')
    update_data(event_data, git_dir, events_file, md_file, logger)

    # create a git issue by writing an email to
    # contact+ronaldas-macas-devil-12506-iczve9w98b94opzztj2puptg-issue@support.ligo.org
    # can tag people, e.g. @ronaldas.macas
    print('TODO: create a git issue by sending an email')
    # git_issue(event_data, gitlab_base_issue_url, logger)

    # same as creating a git issue but easier
    print('TODO: send emails to validators')

    logger.info('DEVIL: end')


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
    parser.add_argument('--ignore_far', type=int, default=0, help='Perform event validation independent on event FAR. Default: 0 (False).')
    parser.add_argument('--git_dir', type=os.path.abspath, default='TBD', help='Event validation infrastructure git directory, default: TBD')
    parser.add_argument('--events_file', type=str, required=True, help="csv file containing events in 'data' folder")
    parser.add_argument('--md_file', type=str, required=True, help="MD table to be edited with new event in 'data' folder")
    parser.add_argument('--vol_file', type=str, required=True, help="csv file containing volunteer information in 'data' folder")
    parser.add_argument('--contact_file', type=str, required=True, help="csv file containing volunteer contact information in 'data' folder")
    parser.add_argument('--validator', type=str, help="Validator name and surname")
    parser.add_argument('--rrt', type=str, help="RRT name and surname")
    parser.add_argument('--dqr_url', type=str,  required=True,help='Data quality report URL')
    parser.add_argument('--dqr_status', type=int, help='DQR status: 0 - not started, 1 - ongoing, 2 - finished, 3 - error')
    parser.add_argument('--val_status', type=int, default=0, help='Validation status: 0 - not completed, 1 - completed, 2 - issues, default: 0')
    parser.add_argument('--gitlab_url', type=str, default='TBD', help='GitLab issue URL, default: TDB')
    args = parser.parse_args()

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

    initialize_devil(event_name=args.event_name,
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
                     rrt=args.rrt,
                     dqr_url=args.dqr_url,
                     dqr_status=args.dqr_status,
                     val_status=args.val_status,
                     gitlab_url=args.gitlab_url,
                     cmd=cmd_line,
                     logger=logger)


# allow to be run on the command line
if __name__ == "__main__":
    main()
