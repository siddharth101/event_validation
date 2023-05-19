#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: nu:ai:ts=4:sw=4

"""
FLASK website for event validation
Based on https://dcc.ligo.org/LIGO-G2300083, https://dcc.ligo.org/LIGO-T2200265
"""

import json, argparse, os
import pandas as pd

from .utils import get_events_dict, first_upper, send_email, get_dets

from wtforms import Form, TextAreaField, validators, SelectField
from flask import Flask, render_template, request, flash

__author__ = 'Ronaldas Macas'
__email__ = 'ronaldas.macas@ligo.org'
__version__ = '0.6'
__process_name__ = 'ev-forms-website'

#------------------------------------------------------------------------------

def create_app(url, wdir, event_list, website_md, notify):
    app = Flask(__name__)

    # app.config['SECRET_KEY'] = 'gw150914'
    # app.config['DEBUG'] = True
    flask_base_url = f'{url}/'

    md_fname = f'{wdir}/data/{website_md}'
    event_list_fname = f'{wdir}/data/{event_list}'
    events = get_events_dict(event_list_fname, wdir)

    ifos = ['H1', 'L1', 'V1']
    status_flags = ['not started', 'in progress', 'completed']
    val_flags = ['Not observing', 'No DQ issues', 'DQ issues']
    val_team_flags = ['Not observing', 'no DQ issues', 'DQ issues but no noise mitigation required', 'Noise mitigation required']
    dq_flags = ['N/A', 'no DQ issues', 'DQ issues but no noise mitigation required', 'noise mitigation required']
    # mitigation_flags = ['N/A', 'in progress', 'completed']
    # review_flags = ['no', 'yes', 'N/A']

    messages = []
    for key, item in sorted(list(events.items()), key=lambda x:x[0].lower(), reverse=True):

        # add a warning if one wants to overwrite event validation form
        if item["status"] == 0:
            validation_url = f'{flask_base_url}validation/{key}'
        else:
            validation_url = f'{flask_base_url}warning_eval_form/{key}'

        #TODO: add more warnings since there are more forms
        # add a warning if one wants to overwrite noise mitigation form
        # add a warning if one wants to fill in the noise mitigation form even though it is not required because there are no data quality issues
        # if item['noise_mitigation']['H1']['required'] == 0 and item['noise_mitigation']['L1']['required'] == 0 and item['noise_mitigation']['V1']['required'] == 0:
            # mitig_url = f'{flask_base_url}warning_mitig_form2/{key}'

        summary_url = f'{flask_base_url}summary/{key}'
        review_url = f'{flask_base_url}review/{key}'
        fixme_url = 'none'

        title = f'{key}: {status_flags[item["status"]]}'
        message = {'title':title, 'content':f'', 'summary':summary_url, 'validation':validation_url, 'review':review_url, 'glitch_request':fixme_url, 'glitch_results':fixme_url, 'gracedb':item['links']['gracedb'], 'dqr_url':item['links']['dqr'], 'issue':item['links']['issue']}
        messages.append(message)

#-------------------------------

    class form_validation(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])
        notes = TextAreaField('notes:')

        validation_status = [(0, val_flags[0]), (1, val_flags[1]), (2, val_flags[2])]
        low_noise = [(0, 'No'), (1, 'Yes')]

        h1_val = SelectField('h1_val:', coerce=int, choices=validation_status, validators=[validators.InputRequired()])
        h1_low_noise = SelectField('h1_low_noise:', coerce=int, choices=low_noise, validators=[validators.InputRequired()])
        h1_noise_tstart = TextAreaField('h1_noise_tstart:')
        h1_noise_tend = TextAreaField('h1_noise_tend:')
        h1_noise_flow = TextAreaField('h1_noise_flow:')
        h1_noise_fhigh = TextAreaField('h1_noise_fhigh:')

        l1_val = SelectField('l1_val:', coerce=int, choices=validation_status, validators=[validators.InputRequired()])
        l1_low_noise = SelectField('l1_low_noise:', coerce=int, choices=low_noise, validators=[validators.InputRequired()])
        l1_noise_tstart = TextAreaField('l1_noise_tstart:')
        l1_noise_tend = TextAreaField('l1_noise_tend:')
        l1_noise_flow = TextAreaField('l1_noise_flow:')
        l1_noise_fhigh = TextAreaField('l1_noise_fhigh:')

        v1_val = SelectField('v1_val:', coerce=int, choices=validation_status, validators=[validators.InputRequired()])
        v1_low_noise = SelectField('v1_low_noise:', coerce=int, choices=low_noise, validators=[validators.InputRequired()])
        v1_noise_tstart = TextAreaField('v1_noise_tstart:')
        v1_noise_tend = TextAreaField('v1_noise_tend:')
        v1_noise_flow = TextAreaField('v1_noise_flow:')
        v1_noise_fhigh = TextAreaField('v1_noise_fhigh:')


    class form_review(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])
        notes = TextAreaField('notes:')

        duration = TextAreaField('duration:', validators=[validators.InputRequired()])

        validation_team_status = [(0, val_team_flags[0]), (1, val_team_flags[1]), (2, val_team_flags[2]), (3, val_team_flags[3])]
        recommend_detector = [(0, 'No'), (1, 'Yes')]
        left_noise = [(0, 'No'), (1, 'Yes')]

        h1_team_val = SelectField('h1_team_val:', coerce=int, choices=validation_team_status, validators=[validators.InputRequired()])
        h1_det = SelectField('h1_det:', coerce=int, choices=recommend_detector, validators=[validators.InputRequired()])
        h1_tstart = TextAreaField('h1_tstart:')
        h1_tend = TextAreaField('h1_tend:')
        h1_flow = TextAreaField('h1_flow:')
        h1_fhigh = TextAreaField('h1_fhigh:')
        h1_frame = TextAreaField('h1_frame:')
        h1_channel = TextAreaField('h1_channel:')
        h1_left_noise = SelectField('h1_left_noise:', coerce=int, choices=left_noise, validators=[validators.InputRequired()])

        l1_team_val = SelectField('l1_team_val:', coerce=int, choices=validation_team_status, validators=[validators.InputRequired()])
        l1_det = SelectField('l1_det:', coerce=int, choices=recommend_detector, validators=[validators.InputRequired()])
        l1_tstart = TextAreaField('l1_tstart:')
        l1_tend = TextAreaField('l1_tend:')
        l1_flow = TextAreaField('l1_flow:')
        l1_fhigh = TextAreaField('l1_fhigh:')
        l1_frame = TextAreaField('l1_frame:')
        l1_channel = TextAreaField('l1_channel:')
        l1_left_noise = SelectField('l1_left_noise:', coerce=int, choices=left_noise, validators=[validators.InputRequired()])

        v1_team_val = SelectField('v1_team_val:', coerce=int, choices=validation_team_status, validators=[validators.InputRequired()])
        v1_det = SelectField('v1_det:', coerce=int, choices=recommend_detector, validators=[validators.InputRequired()])
        v1_tstart = TextAreaField('v1_tstart:')
        v1_tend = TextAreaField('v1_tend:')
        v1_flow = TextAreaField('v1_flow:')
        v1_fhigh = TextAreaField('v1_fhigh:')
        v1_frame = TextAreaField('v1_frame:')
        v1_channel = TextAreaField('v1_channel:')
        v1_left_noise = SelectField('v1_left_noise:', coerce=int, choices=left_noise, validators=[validators.InputRequired()])


    class form_review2(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])
        comment = TextAreaField('comment:')

        review_status = [(0, 'No'), (1, 'Yes')]

        review = SelectField('final_review:', coerce=int, choices=review_status, validators=[validators.InputRequired()])


    class form_comment(Form):

        comment = TextAreaField('comment:')

#-------------------------------

    @app.route('/')
    def index():
        return render_template('index.html', messages=messages)


    @app.route('/validation/<gid>', methods=('GET', 'POST'))
    def gen_valid_form(gid):

        form = form_validation(request.form)

        if request.method == 'POST':
            if form.validate():

                # read event list and find idx
                event_list_df = pd.read_csv(event_list_fname, keep_default_na=False)
                gid_idx = event_list_df.loc[event_list_df['Event'].isin([gid])].index[0]

                # read event json
                with open(f'{wdir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)

                # if (form.h1_val.data == 1 or form.h1_val.data == 0) and (form.l1_val.data == 1 or form.l1_val.data == 0) and (form.v1_val.data == 1 or form.v1_val.data == 0):
                # if needs mitigation
                if form.h1_val.data == 3 or form.l1_val.data == 3 or form.v1_val.data == 3:

                    # update the event json
                    event_data['valid_status'] = 1
                    event_data['valid_conclusion'] = 3
                    event_data['noise_mitigation']['H1']['required'] = 1 if form.h1_val.data == 3 else 0
                    event_data['noise_mitigation']['H1']['status'] = 1 if form.h1_val.data == 3 else 0
                    event_data['noise_mitigation']['L1']['required'] = 1 if form.l1_val.data == 3 else 0
                    event_data['noise_mitigation']['L1']['status'] = 1 if form.l1_val.data == 3 else 0
                    event_data['noise_mitigation']['V1']['required'] = 1 if form.v1_val.data == 3 else 0
                    event_data['noise_mitigation']['V1']['status'] = 1 if form.v1_val.data == 3 else 0

                    event_data['detectors'] = get_dets(form.h1_det.data, form.l1_det.data, form.v1_det.data)

                    event_data['validation']['H1']['fstart'] = form.h1_fstart.data
                    event_data['validation']['H1']['fend'] = form.h1_fend.data
                    event_data['validation']['H1']['tstart'] = form.h1_tstart.data
                    event_data['validation']['H1']['tend'] = form.h1_tend.data
                    event_data['validation']['H1']['duration'] = form.h1_duration.data
                    event_data['validation']['L1']['fstart'] = form.l1_fstart.data
                    event_data['validation']['L1']['fend'] = form.l1_fend.data
                    event_data['validation']['L1']['tstart'] = form.l1_tstart.data
                    event_data['validation']['L1']['tend'] = form.l1_tend.data
                    event_data['validation']['L1']['duration'] = form.l1_duration.data
                    event_data['validation']['V1']['fstart'] = form.v1_fstart.data
                    event_data['validation']['V1']['fend'] = form.v1_fend.data
                    event_data['validation']['V1']['tstart'] = form.v1_tstart.data
                    event_data['validation']['V1']['tend'] = form.v1_tend.data
                    event_data['validation']['V1']['duration'] = form.v1_duration.data

                    event_data['comments']['validator'] = form.comment.data
                    event_data['contacts']['validator_name'] = form.name.data
                    event_data['contacts']['validator_email'] = form.email.data

                    # update the events list
                    event_list_df.at[gid_idx,'Status'] = first_upper(val_flags[1])
                    event_list_df.at[gid_idx,'Conclusion'] = first_upper(dq_flags[3])
                    event_list_df.at[gid_idx,'Noise mitigation'] = first_upper(mitigation_flags[1])
                    event_list_df.at[gid_idx,'Contact person'] = f"{event_data['contacts']['mitigation_name']} ([email](mailto:{event_data['contacts']['mitigation_email']}))"
                    event_list_df.to_csv(event_list_fname, index=False)

                    if notify:
                        subject = f'Event validation report complete for {gid}: {first_upper(dq_flags[3])}'
                        body_valid = f'{subject}. See the summary at {summary_url}.'
                        body_mitig = f'{gid} requires noise mitigation, see the event validation report summary at {summary_url} .\n\nPlease submit your noise mitigation report at {flask_base_url}/mitigation/{gid} .'

                        # send an email to validator
                        send_email(form.email.data, subject, body_valid)
                        # send an email to leads
                        send_email(event_data['contacts']['lead1_email'], subject, body_valid)
                        send_email(event_data['contacts']['lead2_email'], subject, body_valid)
                        # send an email to noise mitigation
                        send_email(event_data['contacts']['mitigation_email'], subject, body_mitig)

                else: # l/h/v no need for noise mitigation

                    # update the event json
                    event_data['valid_status'] = 1
                    if form.h1_val.data == 2 or form.l1_val.data == 2 or form.v1_val.data == 2:
                        event_data['valid_conclusion'] = 2
                    else:
                        event_data['valid_conclusion'] = 1
                    event_data['noise_mitigation']['H1']['required'] = 0
                    event_data['noise_mitigation']['H1']['status'] = 0
                    event_data['noise_mitigation']['L1']['required'] = 0
                    event_data['noise_mitigation']['L1']['status'] = 0
                    event_data['noise_mitigation']['V1']['required'] = 0
                    event_data['noise_mitigation']['V1']['status'] = 0

                    event_data['detectors'] = get_dets(form.h1_det.data, form.l1_det.data, form.v1_det.data)

                    event_data['validation']['H1']['fstart'] = form.h1_fstart.data
                    event_data['validation']['H1']['fend'] = form.h1_fend.data
                    event_data['validation']['H1']['tstart'] = form.h1_tstart.data
                    event_data['validation']['H1']['tend'] = form.h1_tend.data
                    event_data['validation']['H1']['duration'] = form.h1_duration.data
                    event_data['validation']['L1']['fstart'] = form.l1_fstart.data
                    event_data['validation']['L1']['fend'] = form.l1_fend.data
                    event_data['validation']['L1']['tstart'] = form.l1_tstart.data
                    event_data['validation']['L1']['tend'] = form.l1_tend.data
                    event_data['validation']['L1']['duration'] = form.l1_duration.data
                    event_data['validation']['V1']['fstart'] = form.v1_fstart.data
                    event_data['validation']['V1']['fend'] = form.v1_fend.data
                    event_data['validation']['V1']['tstart'] = form.v1_tstart.data
                    event_data['validation']['V1']['tend'] = form.v1_tend.data
                    event_data['validation']['V1']['duration'] = form.v1_duration.data

                    event_data['comments']['validator'] = form.comment.data
                    event_data['contacts']['validator_name'] = form.name.data
                    event_data['contacts']['validator_email'] = form.email.data

                    # update the events list
                    event_list_df.at[gid_idx,'Status'] = first_upper(val_flags[1])
                    if form.h1_val.data == 2 or form.l1_val.data == 2 or form.v1_val.data == 2:
                        event_list_df.at[gid_idx,'Conclusion'] = first_upper(dq_flags[2])
                    else:
                        event_list_df.at[gid_idx,'Conclusion'] = first_upper(dq_flags[1])
                    event_list_df.at[gid_idx,'Noise mitigation'] = first_upper(mitigation_flags[0])
                    event_list_df.at[gid_idx,'Contact person'] = f"{event_data['contacts']['review_name']} ([email](mailto:{event_data['contacts']['review_email']}))"
                    event_list_df.to_csv(event_list_fname, index=False)

                    if notify:
                        subject = f'Event validation report complete for {gid}: {first_upper(dq_flags[1])}'
                        body_valid = f'{subject}. See summary at {summary_url} .'
                        body_review = f'{subject}, see the mitigation report summary at {summary_url}.\n\nPlease submit review form at {flask_base_url}/review/{gid} .'

                        # send an email to validator
                        send_email(form.email.data, subject, body_valid)
                        # send an email to leads
                        send_email(event_data['contacts']['lead1_email'], subject, body_valid)
                        send_email(event_data['contacts']['lead2_email'], subject, body_valid)
                        # send an email to reviewer
                        send_email(event_data['contacts']['review_email'], subject, body_review)


                # update website's .md table
                with open(md_fname, 'w') as md:
                    event_list_df.to_markdown(buf=md, numalign="center", index=False)
                os.system(f'cd {wdir}; mkdocs -q build')

                # update event json
                with open(f'{wdir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)

                return render_template('form_success.html', gid=gid, name=form.name.data, h1=dq_flags[form.h1_val.data], l1=dq_flags[form.l1_val.data], v1=dq_flags[form.v1_val.data])

            else:
                flash('Error:'+str(form.errors),'danger')

        return render_template('form_validation.html', form=form, gid=gid)


    @app.route('/review/<gid>', methods=('GET', 'POST'))
    def gen_review_form(gid):

        form = form_review(request.form)
        form_output = {"fname":form.name.data,
                       "email":form.email.data,
                       "notes": form.notes.data,
                       "duration": form.duration.data,
                       "H1_team_val": form.h1_team_val.data,
                       "H1_det": form.h1_det.data,
                       "H1_tstart": form.h1_tstart.data,
                       "H1_tend": form.h1_tend.data,
                       "H1_flow": form.h1_flow.data,
                       "H1_fhigh": form.h1_fhigh.data,
                       "H1_frame": form.h1_frame.data,
                       "H1_channel": form.h1_channel.data,
                       "H1_left_noise": form.h1_left_noise.data,
                       "L1_team_val": form.l1_team_val.data,
                       "L1_det": form.l1_det.data,
                       "L1_tstart": form.l1_tstart.data,
                       "L1_tend": form.l1_tend.data,
                       "L1_flow": form.l1_flow.data,
                       "L1_fhigh": form.l1_fhigh.data,
                       "L1_frame": form.l1_frame.data,
                       "L1_channel": form.l1_channel.data,
                       "L1_left_noise": form.l1_left_noise.data,
                       "V1_team_val": form.v1_team_val.data,
                       "V1_det": form.v1_det.data,
                       "V1_tstart": form.v1_tstart.data,
                       "V1_tend": form.v1_tend.data,
                       "V1_flow": form.v1_flow.data,
                       "V1_fhigh": form.v1_fhigh.data,
                       "V1_frame": form.v1_frame.data,
                       "V1_channel": form.v1_channel.data,
                       "V1_left_noise": form.v1_left_noise.data
                       }

        if request.method == 'POST':
            if form.validate():

                # read event json
                with open(f'{wdir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)

                # update the event json
                for ifo in ifos:
                    event_data['noise_mitigation'][ifo]['status'] = 2
                    event_data['noise_mitigation'][ifo]['frame_type'] = form_output[f'{ifo}_frame']
                    event_data['noise_mitigation'][ifo]['channel'] = form_output[f'{ifo}_channel']
                    event_data['validation'][ifo]['fstart'] = form_output[f'{ifo}_fstart']
                    event_data['validation'][ifo]['fend'] = form_output[f'{ifo}_fend']
                    event_data['validation'][ifo]['tstart'] = form_output[f'{ifo}_tstart']
                    event_data['validation'][ifo]['tend'] = form_output[f'{ifo}_tend']
                    event_data['validation'][ifo]['duration'] = form_output[f'{ifo}_duration']

                event_data['detectors'] = get_dets(form.h1_det.data, form.l1_det.data, form.v1_det.data)
                event_data['comments']['mitigation'] = form.comment.data
                event_data['contacts']['mitigation_name'] = form.name.data
                event_data['contacts']['mitigation_email'] = form.email.data

                # update event json
                with open(f'{wdir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)

                # read event list and find idx
                event_list_df = pd.read_csv(event_list_fname, keep_default_na=False)
                gid_idx = event_list_df.loc[event_list_df['Event'].isin([gid])].index[0]

                # update the events list
                event_list_df.at[gid_idx,'Noise mitigation'] = first_upper(mitigation_flags[2])
                event_list_df.at[gid_idx,'Contact person'] = f"{event_data['contacts']['review_name']} ([email](mailto:{event_data['contacts']['review_email']}))"
                event_list_df.to_csv(event_list_fname, index=False)

                # update website's .md table
                with open(md_fname, 'w') as md:
                    event_list_df.to_markdown(buf=md, numalign="center", index=False)
                os.system(f'cd {wdir}; mkdocs -q build')

                if notify:
                    subject = f'Noise mitigation report complete for {gid}'
                    body_mitig = f'{subject}. See the summary at {summary_url}.'
                    body_review = f'{subject}, see the mitigation report summary at {summary_url}.\n\nPlease submit review form at {flask_base_url}/review/{gid}.'

                    # send an email to mitigator
                    send_email(form.email.data, subject, body_mitig)
                    # send an email to validator
                    send_email(event_data['contacts']['validator_email'], subject, body_mitig)
                    # send an email to leads
                    send_email(event_data['contacts']['lead1_email'], subject, body_mitig)
                    send_email(event_data['contacts']['lead2_email'], subject, body_mitig)
                    # send an email to the review
                    send_email(event_data['contacts']['review_email'], subject, body_review)

                return render_template('form_mitigation_success.html', gid=gid, name=form.name.data)

            else:
                flash('Error:'+str(form.errors),'danger')


        return render_template('form_review.html', form=form, gid=gid)


    @app.route('/review2/<gid>', methods=('GET', 'POST'))
    def gen_final_review_form(gid):

        form = form_review(request.form)

        if request.method == 'POST':
            if form.validate():

                if form.review.data == 1:

                    # read event json
                    with open(f'{wdir}/data/events/{gid}.json', 'r') as fp:
                        event_data = json.load(fp)

                    event_data['contacts']['review_name'] = form.name.data
                    event_data['contacts']['review_email'] = form.email.data
                    event_data['comments']['review'] = form.comment.data
                    event_data['reviewed'] = 1
                    event_data['valid_status'] = 2

                    # update event json
                    with open(f'{wdir}/data/events/{gid}.json', 'w') as fp:
                        json.dump(event_data, fp, indent=4)

                    # read event list and find idx
                    event_list_df = pd.read_csv(event_list_fname, keep_default_na=False)
                    gid_idx = event_list_df.loc[event_list_df['Event'].isin([gid])].index[0]

                    # update the events list
                    event_list_df.at[gid_idx,'Contact person'] = f"{event_data['contacts']['lead1_name']} ([email](mailto:{event_data['contacts']['lead1_email']}))"
                    event_list_df.at[gid_idx,'Reviewed'] = 'Yes'
                    event_list_df.at[gid_idx,'Status'] = first_upper(val_flags[2])
                    event_list_df.to_csv(event_list_fname, index=False)

                    # update website's .md table
                    with open(md_fname, 'w') as md:
                        event_list_df.to_markdown(buf=md, numalign="center", index=False)
                    os.system(f'cd {wdir}; mkdocs -q build')

                    if notify:
                        subject = f'Final review completed for {gid}'
                        body_review = f'{subject}. See the summary at {summary_url}.'

                        # send an email to the reviewer
                        send_email(form.email.data, subject, body_review)
                        # send an email to leads
                        send_email(event_data['contacts']['lead1_email'], subject, body_review)
                        send_email(event_data['contacts']['lead2_email'], subject, body_review)

                    # TODO CBC SCHEMA STUFF HERE


                return render_template('form_review_success.html', gid=gid, name=form.name.data)

            else:
                flash('Error:'+str(form.errors),'danger')

        return render_template('form_review2.html', form=form, gid=gid)


    @app.route('/summary/<gid>', methods=('GET', 'POST'))
    def get_summary(gid):

        if events[gid]['valid_status'] == 0:

            args = [gid, events[gid]['contacts']['lead1_name'], events[gid]['contacts']['lead1_email']]
            return render_template('val_summary_404.html', args=args)

        else:

            summary = [first_upper(review_flags[events[gid]['reviewed']]), first_upper(val_flags[events[gid]['valid_status']]), dq_flags[events[gid]['valid_conclusion']], str(events[gid]['detectors']).replace("'", "")[1:-1]]
            comments = list(events[gid]['comments'].values())
            contacts = list(events[gid]['contacts'].values())
            urls = [events[gid]['dqr_url'], events[gid]['git_issue_url']]

            noise_mitig = []

            if events[gid]['noise_mitigation']['H1']['status'] == 2 or events[gid]['noise_mitigation']['L1']['status'] == 2 or events[gid]['noise_mitigation']['V1']['status'] == 2:

                nm_summ_h1 = list(events[gid]['noise_mitigation']['H1'].values())
                nm_summ_h1[0] = bool(nm_summ_h1[0])
                nm_summ_h1[1] = first_upper(val_flags[nm_summ_h1[1]])
                nm_summ_l1 = list(events[gid]['noise_mitigation']['L1'].values())
                nm_summ_l1[0] = bool(nm_summ_l1[0])
                nm_summ_l1[1] = first_upper(val_flags[nm_summ_l1[1]])
                nm_summ_v1 = list(events[gid]['noise_mitigation']['V1'].values())
                nm_summ_v1[0] = bool(nm_summ_v1[0])
                nm_summ_v1[1] = first_upper(val_flags[nm_summ_v1[1]])

                valid_summ_h1 = list(events[gid]['validation']['H1'].values())
                valid_summ_l1 = list(events[gid]['validation']['L1'].values())
                valid_summ_v1 = list(events[gid]['validation']['V1'].values())

                return render_template('mitig_summary.html', gid=gid, summary=summary, comments=comments, contacts=contacts, urls=urls, nmh1=nm_summ_h1, nml1=nm_summ_l1, nmv1=nm_summ_v1, vh1=valid_summ_h1, vl1=valid_summ_l1, vv1=valid_summ_v1)


            else:

                valid_summ_h1 = list(events[gid]['validation']['H1'].values())
                valid_summ_l1 = list(events[gid]['validation']['L1'].values())
                valid_summ_v1 = list(events[gid]['validation']['V1'].values())

                return render_template('val_summary.html', gid=gid, summary=summary, comments=comments, contacts=contacts, urls=urls, vh1=valid_summ_h1, vl1=valid_summ_l1, vv1=valid_summ_v1)


    @app.route('/warning_eval_form/<gid>', methods=('GET', 'POST'))
    def warning_eval_form(gid):

        fname = events[gid]['contacts']['validator_name']
        args = [gid, fname, events[gid]['contacts']['validator_email'],
                f'{flask_base_url}summary/{gid}',
                f'{flask_base_url}validation/{gid}']

        return render_template('warning_eval_form.html', args=args)


    @app.route('/warning_mitig_form/<gid>', methods=('GET', 'POST'))
    def warning_mitig_form(gid):
        fname = events[gid]['contacts']['mitigation_name']
        args = [gid, fname, events[gid]['contacts']['mitigation_email'],
                f'{flask_base_url}summary/{gid}',
                f'{flask_base_url}mitigation/{gid}']

        return render_template('warning_mitig_form.html', args=args)


    @app.route('/warning_mitig_form2/<gid>', methods=('GET', 'POST'))
    def warning_mitig_form2(gid):
        args = [gid, f'{flask_base_url}summary/{gid}', f'{flask_base_url}mitigation/{gid}']

        return render_template('warning_mitig_form2.html', args=args)


    @app.route('/comment/<gid>', methods=('GET', 'POST'))
    def add_comment(gid):

        form = form_comment(request.form)
        if request.method == 'POST':
            if form.validate():

                # update event json
                with open(f'{wdir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)

                if len(event_data['comments']['other']) == 0:
                    event_data['comments']['other'] = form.comment.data
                else:
                    event_data['comments']['other'] = event_data['comments']['other'] + ' ' + form.comment.data

                with open(f'{wdir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)

                return render_template('comment_success.html', gid=gid)

            else:
                flash('Error:'+str(form.errors),'danger')


        return render_template('comment.html', form=form, gid=gid)


    @app.route('/json/<gid>', methods=('GET', 'POST'))
    def event_json(gid):

        with open(f'{wdir}/data/events/{gid}.json', 'r') as fp:
            event_json = json.load(fp)

        return event_json


    @app.route('/about/')
    def about():
        return render_template('about.html')

    return app

#------------------------------------------------------------------------------

def main():

    # parse args
    parser = argparse.ArgumentParser(description=__doc__, prog=__process_name__)
    parser.add_argument('--url', type=str, help='flask website url')
    parser.add_argument('--events', type=str, help='event list .csv file in /data directory')
    parser.add_argument('--table', type=str, help='website table .md file in /data directory')
    parser.add_argument('--wdir', type=os.path.abspath, help='directory of this app')
    parser.add_argument('--send_email', type=int, default=0, help='Send notification emails, default = 0 (False).')
    args = parser.parse_args()

    app = create_app(url=args.url,
                     wdir=args.wdir,
                     event_list=args.events,
                     website_md=args.table,
                     notify=args.send_email)
    app.run()

#------------------------------------------------------------------------------

# allow to be run on the command line
if __name__ == "__main__":
    main()
