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

from wtforms import Form, validators, SelectField, TextAreaField, FloatField, IntegerField
from flask import Flask, render_template, request, flash

__author__ = 'Ronaldas Macas'
__email__ = 'ronaldas.macas@ligo.org'
__version__ = '0.6'
__process_name__ = 'ev-forms-website'

#------------------------------------------------------------------------------

# TODO: add option to add comments
# TODO: check which htmls are used and remove others

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
    glitch_flags = ['not required', 'required']
    # dq_flags = ['N/A', 'no DQ issues', 'DQ issues but no noise mitigation required', 'noise mitigation required']
    # mitigation_flags = ['N/A', 'in progress', 'completed']
    # review_flags = ['no', 'yes', 'N/A']

    messages = []
    for key, item in sorted(list(events.items()), key=lambda x:x[0].lower(), reverse=True):

        # add a warning if one wants to overwrite event validation form
        if item["status"] == 0:
            validation_url = f'{flask_base_url}validation/{key}'
        else:
            validation_url = f'{flask_base_url}validation_warning/{key}'

        #TODO: add more warnings since there are more forms
        # add a warning if one wants to overwrite noise mitigation form
        # add a warning if one wants to fill in the noise mitigation form even though it is not required because there are no data quality issues
        # if item['noise_mitigation']['H1']['required'] == 0 and item['noise_mitigation']['L1']['required'] == 0 and item['noise_mitigation']['V1']['required'] == 0:
            # mitig_url = f'{flask_base_url}warning_mitig_form2/{key}'

        summary_url = f'{flask_base_url}summary/{key}'
        review_url = f'{flask_base_url}review/{key}'
        glitch_request_url = f'{flask_base_url}glitch_request/{key}'
        glitch_results_url = f'{flask_base_url}glitch_results/{key}'

        title = f'{key}: {status_flags[item["status"]]}'
        message = {'title':title, 'content':f'', 'summary':summary_url, 'validation':validation_url, 'review':review_url, 'glitch_request':glitch_request_url, 'glitch_results':glitch_results_url, 'gracedb':item['links']['gracedb'], 'detectors':item['links']['detector'], 'dqr':item['links']['dqr'], 'issue':item['links']['issue']}
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
        h1_noise_tstart = FloatField('h1_noise_tstart:', validators=[validators.Optional()])
        h1_noise_tend = FloatField('h1_noise_tend:', validators=[validators.Optional()])
        h1_noise_flow = IntegerField('h1_noise_flow:', validators=[validators.Optional()])
        h1_noise_fhigh = IntegerField('h1_noise_fhigh', validators=[validators.Optional()])

        l1_val = SelectField('l1_val:', coerce=int, choices=validation_status, validators=[validators.InputRequired()])
        l1_low_noise = SelectField('l1_low_noise:', coerce=int, choices=low_noise, validators=[validators.InputRequired()])
        l1_noise_tstart = FloatField('l1_noise_tstart:', validators=[validators.Optional()])
        l1_noise_tend = FloatField('l1_noise_tend:', validators=[validators.Optional()])
        l1_noise_flow = IntegerField('l1_noise_flow:', validators=[validators.Optional()])
        l1_noise_fhigh = IntegerField('l1_noise_fhigh:', validators=[validators.Optional()])

        v1_val = SelectField('v1_val:', coerce=int, choices=validation_status, validators=[validators.InputRequired()])
        v1_low_noise = SelectField('v1_low_noise:', coerce=int, choices=low_noise, validators=[validators.InputRequired()])
        v1_noise_tstart = FloatField('v1_noise_tstart:', validators=[validators.Optional()])
        v1_noise_tend = FloatField('v1_noise_tend:', validators=[validators.Optional()])
        v1_noise_flow = IntegerField('v1_noise_flow:', validators=[validators.Optional()])
        v1_noise_fhigh = IntegerField('v1_noise_fhigh:', validators=[validators.Optional()])


    class form_review(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])
        notes = TextAreaField('notes:')

        duration = FloatField('duration:', validators=[validators.InputRequired()])

        validation_team_status = [(0, val_team_flags[0]), (1, val_team_flags[1]), (2, val_team_flags[2]), (3, val_team_flags[3])]
        recommend_detector = [(0, 'No'), (1, 'Yes')]
        noise_left = [(0, 'No'), (1, 'Yes')]

        h1_team_val = SelectField('h1_team_val:', coerce=int, choices=validation_team_status, validators=[validators.InputRequired()])
        h1_det = SelectField('h1_det:', coerce=int, choices=recommend_detector, validators=[validators.InputRequired()])
        h1_tstart = FloatField('h1_tstart:', validators=[validators.Optional()])
        h1_tend = FloatField('h1_tend:', validators=[validators.Optional()])
        h1_flow = IntegerField('h1_flow:', validators=[validators.Optional()])
        h1_fhigh = IntegerField('h1_fhigh:', validators=[validators.Optional()])
        h1_frame = TextAreaField('h1_frame:')
        h1_channel = TextAreaField('h1_channel:')
        h1_noise_left = SelectField('h1_noise_left:', coerce=int, choices=noise_left, validators=[validators.InputRequired()])

        l1_team_val = SelectField('l1_team_val:', coerce=int, choices=validation_team_status, validators=[validators.InputRequired()])
        l1_det = SelectField('l1_det:', coerce=int, choices=recommend_detector, validators=[validators.InputRequired()])
        l1_tstart = FloatField('l1_tstart:', validators=[validators.Optional()])
        l1_tend = FloatField('l1_tend:', validators=[validators.Optional()])
        l1_flow = IntegerField('l1_flow:', validators=[validators.Optional()])
        l1_fhigh = IntegerField('l1_fhigh:', validators=[validators.Optional()])
        l1_frame = TextAreaField('l1_frame:')
        l1_channel = TextAreaField('l1_channel:')
        l1_noise_left = SelectField('l1_noise_left:', coerce=int, choices=noise_left, validators=[validators.InputRequired()])

        v1_team_val = SelectField('v1_team_val:', coerce=int, choices=validation_team_status, validators=[validators.InputRequired()])
        v1_det = SelectField('v1_det:', coerce=int, choices=recommend_detector, validators=[validators.InputRequired()])
        v1_tstart = FloatField('v1_tstart:', validators=[validators.Optional()])
        v1_tend = FloatField('v1_tend:', validators=[validators.Optional()])
        v1_flow = IntegerField('v1_flow:', validators=[validators.Optional()])
        v1_fhigh = IntegerField('v1_fhigh:', validators=[validators.Optional()])
        v1_frame = TextAreaField('v1_frame:')
        v1_channel = TextAreaField('v1_channel:')
        v1_noise_left = SelectField('v1_noise_left:', coerce=int, choices=noise_left, validators=[validators.InputRequired()])


    class form_glitch_request(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])
        notes = TextAreaField('notes:')

        glitch_request_status = [(0, 'No'), (1, 'Yes')]

        h1_glitch_request = SelectField('h1_glitch_request:', coerce=int, choices=glitch_request_status, validators=[validators.InputRequired()])
        h1_noise_tstart = FloatField('h1_noise_tstart:', validators=[validators.Optional()])
        h1_noise_tend = FloatField('h1_noise_tend:', validators=[validators.Optional()])
        h1_noise_flow = IntegerField('h1_noise_flow:', validators=[validators.Optional()])
        h1_noise_fhigh = IntegerField('h1_noise_fhigh:', validators=[validators.Optional()])

        l1_glitch_request = SelectField('l1_glitch_request:', coerce=int, choices=glitch_request_status, validators=[validators.InputRequired()])
        l1_noise_tstart = FloatField('l1_noise_tstart:', validators=[validators.Optional()])
        l1_noise_tend = FloatField('l1_noise_tend:', validators=[validators.Optional()])
        l1_noise_flow = IntegerField('l1_noise_flow:', validators=[validators.Optional()])
        l1_noise_fhigh = IntegerField('l1_noise_fhigh:', validators=[validators.Optional()])

        v1_glitch_request = SelectField('v1_glitch_request:', coerce=int, choices=glitch_request_status, validators=[validators.InputRequired()])
        v1_noise_tstart = FloatField('v1_noise_tstart:', validators=[validators.Optional()])
        v1_noise_tend = FloatField('v1_noise_tend:', validators=[validators.Optional()])
        v1_noise_flow = IntegerField('v1_noise_flow:', validators=[validators.Optional()])
        v1_noise_fhigh = IntegerField('v1_noise_fhigh:', validators=[validators.Optional()])


    class form_glitch_results(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])
        notes = TextAreaField('notes:')

        h1_frame = TextAreaField('h1_frame:')
        h1_channel = TextAreaField('h1_channel:')

        l1_frame = TextAreaField('l1_frame:')
        l1_channel = TextAreaField('l1_channel:')

        v1_frame = TextAreaField('v1_frame:')
        v1_channel = TextAreaField('v1_channel:')


    class form_finalize(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])

        finalize_status = [(0, 'No'), (1, 'Yes')]

        finalize = SelectField('finalize:', coerce=int, choices=finalize_status, validators=[validators.InputRequired()])


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

                # update the event json
                event_data['status'] = 1
                event_data['comments']['validation'] = form.notes.data
                event_data['contacts']['validator_name'] = form.name.data
                event_data['contacts']['validator_email'] = form.email.data

                event_data['forms']['validation']['H1']['conclusion'] = form.h1_val.data
                event_data['forms']['validation']['H1']['low_noise'] = form.h1_low_noise.data
                event_data['forms']['validation']['H1']['noise_tstart'] = form.h1_noise_tstart.data
                event_data['forms']['validation']['H1']['noise_tend'] = form.h1_noise_tend.data
                event_data['forms']['validation']['H1']['noise_flow'] = form.h1_noise_flow.data
                event_data['forms']['validation']['H1']['noise_fhigh'] = form.h1_noise_fhigh.data

                event_data['forms']['validation']['L1']['conclusion'] = form.l1_val.data
                event_data['forms']['validation']['L1']['low_noise'] = form.l1_low_noise.data
                event_data['forms']['validation']['L1']['noise_tstart'] = form.l1_noise_tstart.data
                event_data['forms']['validation']['L1']['noise_tend'] = form.l1_noise_tend.data
                event_data['forms']['validation']['L1']['noise_flow'] = form.l1_noise_flow.data
                event_data['forms']['validation']['L1']['noise_fhigh'] = form.l1_noise_fhigh.data

                event_data['forms']['validation']['V1']['conclusion'] = form.v1_val.data
                event_data['forms']['validation']['V1']['low_noise'] = form.v1_low_noise.data
                event_data['forms']['validation']['V1']['noise_tstart'] = form.v1_noise_tstart.data
                event_data['forms']['validation']['V1']['noise_tend'] = form.v1_noise_tend.data
                event_data['forms']['validation']['V1']['noise_flow'] = form.v1_noise_flow.data
                event_data['forms']['validation']['V1']['noise_fhigh'] = form.v1_noise_fhigh.data

                #TODO: fix mkdocs stuff here
                # update the events list
                # event_list_df.at[gid_idx,'Status'] = first_upper(val_flags[1])
                # event_list_df.at[gid_idx,'Conclusion'] = first_upper(dq_flags[3])
                # event_list_df.at[gid_idx,'Noise mitigation'] = first_upper(mitigation_flags[1])
                # event_list_df.at[gid_idx,'Contact person'] = f"{event_data['contacts']['mitigation_name']} ([email](mailto:{event_data['contacts']['mitigation_email']}))"
                # event_list_df.to_csv(event_list_fname, index=False)

                # # update website's .md table
                # with open(md_fname, 'w') as md:
                #     event_list_df.to_markdown(buf=md, numalign="center", index=False)
                # os.system(f'cd {wdir}; mkdocs -q build')

                # update event json
                with open(f'{wdir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)

                if notify:
                    subject = f'Event validation report complete for {gid}.'
                    body_valid = f'{subject}. See the summary at {summary_url}.'
                    body_review = f'{body_valid}\n\nPlease submit your event validation review report at {flask_base_url}/review/{gid}.'

                    # send an email to the validator
                    send_email(form.email.data, subject, body_valid)
                    # send an email to leads
                    send_email(event_data['contacts']['lead1_email'], subject, body_valid)
                    send_email(event_data['contacts']['lead2_email'], subject, body_valid)
                    # send an email to the reviewer
                    send_email(event_data['contacts']['review_email'], subject, body_review)

                return render_template('form_validation_success.html', gid=gid, name=form.name.data, h1=val_flags[form.h1_val.data], l1=val_flags[form.l1_val.data], v1=val_flags[form.v1_val.data])

            else:
                flash('Error:'+str(form.errors),'danger')

        return render_template('form_validation.html', form=form, gid=gid)


    @app.route('/review/<gid>', methods=('GET', 'POST'))
    def gen_review_form(gid):

        form = form_review(request.form)

        if request.method == 'POST':
            if form.validate():

                # read event json
                with open(f'{wdir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)

                # update the event json
                event_data['contacts']['review_name'] = form.name.data
                event_data['contacts']['review_email'] = form.email.data
                event_data['comments']['review'] = form.notes.data

                event_data['forms']['review']['duration'] = form.duration.data

                event_data['forms']['review']['H1']['conclusion'] = form.h1_team_val.data
                event_data['forms']['review']['H1']['recommend_ifo'] = form.h1_det.data
                event_data['forms']['review']['H1']['analysis_tstart'] = form.h1_tstart.data
                event_data['forms']['review']['H1']['analysis_tend'] = form.h1_tend.data
                event_data['forms']['review']['H1']['analysis_flow'] = form.h1_flow.data
                event_data['forms']['review']['H1']['analysis_fhigh'] = form.h1_fhigh.data
                event_data['forms']['review']['H1']['frame_type'] = form.h1_frame.data
                event_data['forms']['review']['H1']['channel'] = form.h1_channel.data
                event_data['forms']['review']['H1']['noise_left'] = form.h1_noise_left.data

                event_data['forms']['review']['L1']['conclusion'] = form.l1_team_val.data
                event_data['forms']['review']['L1']['recommend_ifo'] = form.l1_det.data
                event_data['forms']['review']['L1']['analysis_tstart'] = form.l1_tstart.data
                event_data['forms']['review']['L1']['analysis_tend'] = form.l1_tend.data
                event_data['forms']['review']['L1']['analysis_flow'] = form.l1_flow.data
                event_data['forms']['review']['L1']['analysis_fhigh'] = form.l1_fhigh.data
                event_data['forms']['review']['L1']['frame_type'] = form.l1_frame.data
                event_data['forms']['review']['L1']['channel'] = form.l1_channel.data
                event_data['forms']['review']['L1']['noise_left'] = form.l1_noise_left.data

                event_data['forms']['review']['V1']['conclusion'] = form.v1_team_val.data
                event_data['forms']['review']['V1']['recommend_ifo'] = form.v1_det.data
                event_data['forms']['review']['V1']['analysis_tstart'] = form.v1_tstart.data
                event_data['forms']['review']['V1']['analysis_tend'] = form.v1_tend.data
                event_data['forms']['review']['V1']['analysis_flow'] = form.v1_flow.data
                event_data['forms']['review']['V1']['analysis_fhigh'] = form.v1_fhigh.data
                event_data['forms']['review']['V1']['frame_type'] = form.v1_frame.data
                event_data['forms']['review']['V1']['channel'] = form.v1_channel.data
                event_data['forms']['review']['V1']['noise_left'] = form.v1_noise_left.data

                # update event json
                with open(f'{wdir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)

                # read event list and find idx
                # event_list_df = pd.read_csv(event_list_fname, keep_default_na=False)
                # gid_idx = event_list_df.loc[event_list_df['Event'].isin([gid])].index[0]

                # # update the events list
                # event_list_df.at[gid_idx,'Noise mitigation'] = first_upper(mitigation_flags[2])
                # event_list_df.at[gid_idx,'Contact person'] = f"{event_data['contacts']['review_name']} ([email](mailto:{event_data['contacts']['review_email']}))"
                # event_list_df.to_csv(event_list_fname, index=False)

                # # update website's .md table
                # with open(md_fname, 'w') as md:
                #     event_list_df.to_markdown(buf=md, numalign="center", index=False)
                # os.system(f'cd {wdir}; mkdocs -q build')

                if notify:
                    subject = f'Event validation review report complete for {gid}'
                    body = f'{subject}. See the summary at {summary_url}.'

                    # send an email to the reviewer
                    send_email(form.email.data, subject, body)
                    # send an email to the validator
                    send_email(event_data['contacts']['validator_email'], subject, body)
                    # send an email to leads
                    send_email(event_data['contacts']['lead1_email'], subject, body)
                    send_email(event_data['contacts']['lead2_email'], subject, body)

                return render_template('form_review_success.html', gid=gid, name=form.name.data, h1=val_team_flags[form.h1_team_val.data], l1=val_team_flags[form.l1_team_val.data], v1=val_team_flags[form.v1_team_val.data])

            else:
                flash('Error:'+str(form.errors),'danger')

        return render_template('form_review.html', form=form, gid=gid)

    @app.route('/glitch_request/<gid>', methods=('GET', 'POST'))
    def gen_glitch_request_form(gid):

        form = form_glitch_request(request.form)

        if request.method == 'POST':
            if form.validate():

                # read event json
                with open(f'{wdir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)

                # update the event json
                event_data['contacts']['review_name'] = form.name.data
                event_data['contacts']['review_email'] = form.email.data
                event_data['comments']['glitch_request'] = form.notes.data

                event_data['forms']['glitch_request']['H1']['required'] = form.h1_glitch_request.data
                event_data['forms']['glitch_request']['H1']['noise_tstart'] = form.h1_noise_tstart.data
                event_data['forms']['glitch_request']['H1']['noise_tend'] = form.h1_noise_tend.data
                event_data['forms']['glitch_request']['H1']['noise_flow'] = form.h1_noise_flow.data
                event_data['forms']['glitch_request']['H1']['noise_fhigh'] = form.h1_noise_fhigh.data

                event_data['forms']['glitch_request']['L1']['required'] = form.l1_glitch_request.data
                event_data['forms']['glitch_request']['L1']['noise_tstart'] = form.l1_noise_tstart.data
                event_data['forms']['glitch_request']['L1']['noise_tend'] = form.l1_noise_tend.data
                event_data['forms']['glitch_request']['L1']['noise_flow'] = form.l1_noise_flow.data
                event_data['forms']['glitch_request']['L1']['noise_fhigh'] = form.l1_noise_fhigh.data

                event_data['forms']['glitch_request']['V1']['required'] = form.v1_glitch_request.data
                event_data['forms']['glitch_request']['V1']['noise_tstart'] = form.v1_noise_tstart.data
                event_data['forms']['glitch_request']['V1']['noise_tend'] = form.v1_noise_tend.data
                event_data['forms']['glitch_request']['V1']['noise_flow'] = form.v1_noise_flow.data
                event_data['forms']['glitch_request']['V1']['noise_fhigh'] = form.v1_noise_fhigh.data

                # update event json
                with open(f'{wdir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)

                # TODO: update md tables

                if notify:
                    subject = f'Glitch subtraction requested for {gid}'
                    body = f'{subject}. See the summary at {summary_url}.'

                    # send an email to the reviewer
                    send_email(form.email.data, subject, body)
                    # send an email to the glitch mitigation
                    send_email(event_data['contacts']['mitigation_email'], subject, body)
                    # send an email to leads
                    send_email(event_data['contacts']['lead1_email'], subject, body)
                    send_email(event_data['contacts']['lead2_email'], subject, body)

                return render_template('form_glitch_request_success.html', gid=gid, name=form.name.data, h1=glitch_flags[form.h1_glitch_request.data], l1=glitch_flags[form.l1_glitch_request.data], v1=glitch_flags[form.v1_glitch_request.data])

            else:
                flash('Error:'+str(form.errors),'danger')

        return render_template('form_glitch_request.html', form=form, gid=gid)


    @app.route('/glitch_results/<gid>', methods=('GET', 'POST'))
    def gen_glitch_results_form(gid):

        form = form_glitch_results(request.form)

        if request.method == 'POST':
            if form.validate():

                # read event json
                with open(f'{wdir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)

                # update the event json
                event_data['contacts']['mitigation_name'] = form.name.data
                event_data['contacts']['mitigation_email'] = form.email.data
                event_data['comments']['glitch_result'] = form.notes.data

                event_data['forms']['glitch_result']['H1']['frame_type'] = form.h1_frame.data
                event_data['forms']['glitch_result']['H1']['channel'] = form.h1_channel.data

                event_data['forms']['glitch_result']['L1']['frame_type'] = form.l1_frame.data
                event_data['forms']['glitch_result']['L1']['channel'] = form.l1_channel.data

                event_data['forms']['glitch_result']['V1']['frame_type'] = form.v1_frame.data
                event_data['forms']['glitch_result']['V1']['channel'] = form.v1_channel.data

                # update event json
                with open(f'{wdir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)

                # TODO: update md tables

                if notify:
                    subject = f'Glitch subtraction completed for {gid}'
                    body = f'{subject}. See the summary at {summary_url}.'

                    # send an email to the glitch mitigation
                    send_email(form.email.data, subject, body)
                    # send an email to the reviewer
                    send_email(event_data['contacts']['mitigation_email'], subject, body)
                    # send an email to leads
                    send_email(event_data['contacts']['lead1_email'], subject, body)
                    send_email(event_data['contacts']['lead2_email'], subject, body)

                return render_template('form_glitch_results_success.html', gid=gid, name=form.name.data)

            else:
                flash('Error:'+str(form.errors),'danger')

        return render_template('form_glitch_results.html', form=form, gid=gid)


    @app.route('/finalize/<gid>', methods=('GET', 'POST'))
    def gen_finalize_form(gid):

        form = form_finalize(request.form)

        if request.method == 'POST':
            if form.validate():

                if form.finalize.data == 1:

                    # read event json
                    with open(f'{wdir}/data/events/{gid}.json', 'r') as fp:
                        event_data = json.load(fp)

                    event_data['contacts']['review_name'] = form.name.data
                    event_data['contacts']['review_email'] = form.email.data

                    event_data['reviewed'] = 1

                    # update event json
                    with open(f'{wdir}/data/events/{gid}.json', 'w') as fp:
                        json.dump(event_data, fp, indent=4)

                    # TODO: update md tables

                    if notify:
                        subject = f'Final review completed for {gid}'
                        body= f'{subject}. See the summary at {summary_url}.'

                        # send an email to the reviewer
                        send_email(form.email.data, subject, body)
                        # send an email to leads
                        send_email(event_data['contacts']['lead1_email'], subject, body)
                        send_email(event_data['contacts']['lead2_email'], subject, body)

                    # TODO CBC SCHEMA STUFF HERE

                return render_template('form_review_success.html', gid=gid, name=form.name.data)

            else:
                flash('Error:'+str(form.errors),'danger')

        return render_template('form_finalize.html', form=form, gid=gid)


    @app.route('/summary/<gid>', methods=('GET', 'POST'))
    def get_summary(gid):

        # find if validation or review forms were filled
        flags = ['validation', 'review']
        conclusions = []
        for ifo in ifos:
            for flag in flags:
                print((events[gid]['forms'][flag][ifo]['conclusion']))
                conclusions.append(events[gid]['forms'][flag][ifo]['conclusion'])

        # if not filled, show 404 page
        # TODO: reverse logic bc if true, then show summary
        if any(str(var).isnumeric() for var in conclusions):
            args = [gid, events[gid]['contacts']['lead1_name'], events[gid]['contacts']['lead1_email']]
            return render_template('summary_404.html', args=args)

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


    @app.route('/validation_warning/<gid>', methods=('GET', 'POST'))
    def gen_validation_warning(gid):

        fname = events[gid]['contacts']['validator_name']
        args = [gid, fname, events[gid]['contacts']['validator_email'],
                f'{flask_base_url}summary/{gid}',
                f'{flask_base_url}validation/{gid}']

        return render_template('warning_validation.html', args=args)


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
