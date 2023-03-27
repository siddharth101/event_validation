#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: nu:ai:ts=4:sw=4

"""
FLASK website for event validation
Based on https://dcc.ligo.org/LIGO-G2300083, https://dcc.ligo.org/LIGO-T2200265
"""

import json, argparse, os, subprocess
import pandas as pd

from wtforms import Form, TextAreaField, validators, SubmitField, SelectField, IntegerField
from flask import Flask, render_template, request, url_for, flash


__author__ = 'Ronaldas Macas'
__email__ = 'ronaldas.macas@ligo.org'
__version__ = '0.3'
__process_name__ = 'eval-website'

#------------------------------------------------------------------------------

# read events file and update the messages list
def get_events_dict(list_fname, git_dir):

    list_content = pd.read_csv(list_fname)
    list_events = list_content['Event']

    events = {}
    for event in list_events:

        fname = f'{git_dir}/data/events/{event}.json'
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

def send_email(git_dir, email, subject, body):

    subprocess.check_call([f'{git_dir}/code/send_email.sh', email, subject, body])

    return
#------------------------------------------------------------------------------


def create_app(port, git_dir, event_list, website_md, notify):
    app = Flask(__name__)

    # app.config['SECRET_KEY'] = 'gw150914'
    # app.config['DEBUG'] = True

    flask_base_url = f'http://127.0.0.1:{port}/'

    md_fname = f'{git_dir}/data/{website_md}'
    event_list_fname = f'{git_dir}/data/{event_list}'
    events = get_events_dict(event_list_fname, git_dir)

    ifos = ['H1', 'L1', 'V1']
    val_flags = ['not started', 'in progress', 'completed']
    dq_flags = ['N/A', 'no DQ issues', 'noise mitigation required']
    mitigation_flags = ['N/A', 'in progress', 'completed']
    review_flags = ['no', 'yes', 'N/A']

    messages = []
    for key, item in sorted(list(events.items()), key=lambda x:x[0].lower(), reverse=True):

        # add a warning if one wants to overwrite event validation form
        if item["valid_status"] == 0:
            form_url = f'{flask_base_url}forms/{key}'
        else:
            form_url = f'{flask_base_url}warning_eval_form/{key}'

        # add a warning if one wants to overwrite noise mitigation form
        for ifo in ifos:
            if item['noise_mitigation'][ifo]['status'] == 2:
                mitig_url = f'{flask_base_url}warning_mitig_form/{key}'
            else:
                mitig_url = f'{flask_base_url}mitigation/{key}'

        # add a warning if one wants to fill in the noise mitigation form even though it is not required because there are no data quality issues
        if item['noise_mitigation']['H1']['required'] == 0 and item['noise_mitigation']['L1']['required'] == 0 and item['noise_mitigation']['V1']['required'] == 0:
            mitig_url = f'{flask_base_url}warning_mitig_form2/{key}'

        summary_url = f'{flask_base_url}summaries/{key}'
        dqr_url = events[key]['dqr_url']
        docs_url = dqr_url

        title = f'{key}: {val_flags[item["valid_status"]]}'
        message = {'title':title, 'content':f'', 'form_url':form_url, 'mitig_url':mitig_url, 'docs_url':docs_url, 'gitlab_issue_url':item['git_issue_url'], 'dqr_url':dqr_url, 'summary_url':summary_url}
        messages.append(message)


    class Questionnaire(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])

        validation_status = [(0, dq_flags[0]), (1, dq_flags[1]), (2, dq_flags[2])]

        conclusion_h1 = SelectField('conclusion_h1:', coerce=int, choices=validation_status, validators=[validators.InputRequired()])
        conclusion_l1 = SelectField('conclusion_l1:', coerce=int, choices=validation_status, validators=[validators.InputRequired()])
        conclusion_v1 = SelectField('conclusion_v1:', coerce=int, choices=validation_status, validators=[validators.InputRequired()])

        comment = TextAreaField('comment:')


    class Questionnaire_mitigation(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])
        comment = TextAreaField('comment:')

        H1_method = TextAreaField('H1_method:')
        H1_tstart = TextAreaField('H1_tstart:')
        H1_tend = TextAreaField('H1_tend:')
        H1_fstart = TextAreaField('H1_fstart:')
        H1_fend = TextAreaField('H1_fend:')
        H1_frame = TextAreaField('H1_frame:')

        L1_method = TextAreaField('L1_method:')
        L1_tstart = TextAreaField('L1_tstart:')
        L1_tend = TextAreaField('L1_tend:')
        L1_fstart = TextAreaField('L1_fstart:')
        L1_fend = TextAreaField('L1_fend:')
        L1_frame = TextAreaField('L1_frame:')


        V1_method = TextAreaField('V1_method:')
        V1_tstart = TextAreaField('V1_tstart:')
        V1_tend = TextAreaField('V1_tend:')
        V1_fstart = TextAreaField('V1_fstart:')
        V1_fend = TextAreaField('V1_fend:')
        V1_frame = TextAreaField('V1_frame:')


    class Questionnaire_review(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])
        comment = TextAreaField('comment:')

        review_status = [(0, 'No'), (1, 'Yes')]

        review = SelectField('final_review:', coerce=int, choices=review_status, validators=[validators.InputRequired()])


    class Questionnaire_comment(Form):

        comment = TextAreaField('comment:')

    @app.route('/')
    def index():
        return render_template('index.html', messages=messages)


    @app.route('/summaries/<gid>', methods=('GET', 'POST'))
    def get_summary(gid):

        if events[gid]['valid_status'] == 0:

            args = [gid, events[gid]['contacts']['lead1_name'], events[gid]['contacts']['lead1_email']]
            return render_template('val_summary_404.html', args=args)

        else:

            summary = [first_upper(review_flags[events[gid]['reviewed']]), first_upper(val_flags[events[gid]['valid_status']]), dq_flags[events[gid]['valid_conclusion']]]
            comments = list(events[gid]['comments'].values())
            contacts = list(events[gid]['contacts'].values())
            urls = [events[gid]['dqr_url'], events[gid]['git_issue_url']]

            noise_mitig = []
            review_flags_summary = ['In progress', 'Completed', 'N/A']

            if events[gid]['noise_mitigation']['H1']['status'] == 2 or events[gid]['noise_mitigation']['L1']['status'] == 2 or events[gid]['noise_mitigation']['V1']['status'] == 2:

                nm_summ_h1 = list(events[gid]['noise_mitigation']['H1'].values())
                nm_summ_h1[0] = bool(nm_summ_h1[0])
                nm_summ_h1[1] = first_upper(val_flags[nm_summ_h1[1]])
                nm_summ_h1[2] = review_flags_summary[nm_summ_h1[2]]
                nm_summ_l1 = list(events[gid]['noise_mitigation']['L1'].values())
                nm_summ_l1[0] = bool(nm_summ_l1[0])
                nm_summ_l1[1] = first_upper(val_flags[nm_summ_l1[1]])
                nm_summ_l1[2] = review_flags_summary[nm_summ_l1[2]]
                nm_summ_v1 = list(events[gid]['noise_mitigation']['V1'].values())
                nm_summ_v1[0] = bool(nm_summ_v1[0])
                nm_summ_v1[1] = first_upper(val_flags[nm_summ_v1[1]])
                nm_summ_v1[2] = review_flags_summary[nm_summ_v1[2]]

                print(bool(events[gid]['noise_mitigation']['H1']['required']))

                return render_template('mitig_summary.html', gid=gid, summary=summary, comments=comments, contacts=contacts, urls=urls, nmh1=nm_summ_h1, nml1=nm_summ_l1, nmv1=nm_summ_v1)


            else:
                noise_mitig_summary = []
                for ifo in ifos:
                    if events[gid]['noise_mitigation'][ifo]['required'] == 1:
                        noise_mitig_summary.append('required')
                    else:
                        noise_mitig_summary.append('not required')
                    noise_mitig_summary.append(f"{mitigation_flags[events[gid]['noise_mitigation'][ifo]['status']]}")

                return render_template('val_summary.html', gid=gid, summary=summary, comments=comments, contacts=contacts, urls=urls, nmsummary=noise_mitig_summary)


    @app.route('/warning_eval_form/<gid>', methods=('GET', 'POST'))
    def warning_eval_form(gid):

        fname = events[gid]['contacts']['validator_name']
        args = [gid, fname, events[gid]['contacts']['validator_email'],
                f'{flask_base_url}summaries/{gid}',
                f'{flask_base_url}forms/{gid}']

        return render_template('warning_eval_form.html', args=args)


    @app.route('/warning_mitig_form/<gid>', methods=('GET', 'POST'))
    def warning_mitig_form(gid):
        fname = events[gid]['contacts']['mitigation_name']
        args = [gid, fname, events[gid]['contacts']['mitigation_email'],
                f'{flask_base_url}summaries/{gid}',
                f'{flask_base_url}mitigation/{gid}']

        return render_template('warning_mitig_form.html', args=args)


    @app.route('/warning_mitig_form2/<gid>', methods=('GET', 'POST'))
    def warning_mitig_form2(gid):
        args = [gid, f'{flask_base_url}summaries/{gid}', f'{flask_base_url}mitigation/{gid}']

        return render_template('warning_mitig_form2.html', args=args)


    @app.route('/json/<gid>', methods=('GET', 'POST'))
    def event_json(gid):

        # read event json
        with open(f'{git_dir}/data/events/{gid}.json', 'r') as fp:
            event_json = json.load(fp)

        return event_json


    @app.route('/mitigation/<gid>', methods=('GET', 'POST'))
    def gen_mitigation_form(gid):

        form = Questionnaire_mitigation(request.form)
        form_output = {"fname":form.name.data,
                       "email":form.email.data,
                       "comment": form.comment.data,
                       "H1_method": form.H1_method.data,
                       "H1_tstart": form.H1_tstart.data,
                       "H1_tend": form.H1_tend.data,
                       "H1_fstart": form.H1_fstart.data,
                       "H1_fend": form.H1_fend.data,
                       "H1_frame": form.H1_frame.data,
                       "L1_method": form.L1_method.data,
                       "L1_tstart": form.L1_tstart.data,
                       "L1_tend": form.L1_tend.data,
                       "L1_fstart": form.L1_fstart.data,
                       "L1_fend": form.L1_fend.data,
                       "L1_frame": form.L1_frame.data,
                       "V1_method": form.V1_method.data,
                       "V1_tstart": form.V1_tstart.data,
                       "V1_tend": form.V1_tend.data,
                       "V1_fstart": form.V1_fstart.data,
                       "V1_fend": form.V1_fend.data,
                       "V1_frame": form.V1_frame.data
                       }

        if request.method == 'POST':
            if form.validate():

                # read event json
                with open(f'{git_dir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)

                # update the event json
                for ifo in ifos:
                    event_data['noise_mitigation'][ifo]['status'] = 2
                    event_data['noise_mitigation'][ifo]['method'] = form_output[f'{ifo}_method']
                    event_data['noise_mitigation'][ifo]['tstart'] = form_output[f'{ifo}_tstart']
                    event_data['noise_mitigation'][ifo]['tend'] = form_output[f'{ifo}_tend']
                    event_data['noise_mitigation'][ifo]['fstart'] = form_output[f'{ifo}_fstart']
                    event_data['noise_mitigation'][ifo]['fend'] = form_output[f'{ifo}_fend']
                    event_data['noise_mitigation'][ifo]['frame'] = form_output[f'{ifo}_frame']

                event_data['comments']['mitigation'] = form.comment.data
                event_data['contacts']['mitigation_name'] = form.name.data
                event_data['contacts']['mitigation_email'] = form.email.data

                # update event json
                with open(f'{git_dir}/data/events/{gid}.json', 'w') as fp:
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
                os.system(f'cd {git_dir}; mkdocs -q build')

                subject = f'Noise mitigation report complete for {gid}'
                body_mitig = f'{subject}. See summary at {summary_url} .'
                body_review = f'{subject}, see the mitigation report summary at {summary_url}.\n\nPlease submit review form at {flask_base_url}/review/{gid} .'

                if notify:
                    # send an email to mitigator
                    send_email(git_dir, form.email.data, subject, body_mitig)
                    # send an email to the lead
                    send_email(git_dir, event_data['contacts']['lead1_email'], subject, body_mitig)
                    # send an email to the mitigation review
                    send_email(git_dir, event_data['contacts']['review_email'], subject, body_review)

                return render_template('form_mitigation_success.html', gid=gid, name=form.name.data, h1=form.H1_method.data, l1=form.L1_method.data, v1=form.V1_method.data)

            else:
                flash('Error:'+str(form.errors),'danger')


        return render_template('form_mitigation.html', form=form, gid=gid)


    @app.route('/comment/<gid>', methods=('GET', 'POST'))
    def add_comment(gid):

        form = Questionnaire_comment(request.form)
        if request.method == 'POST':
            if form.validate():

                # update event json
                with open(f'{git_dir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)

                #TODO: append form data, not overwrite
                event_data['comments']['other'] = form.comment.data

                with open(f'{git_dir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)

                return render_template('comment_success.html', gid=gid)

            else:
                flash('Error:'+str(form.errors),'danger')


        return render_template('comment.html', form=form, gid=gid)


    @app.route('/review/<gid>', methods=('GET', 'POST'))
    def gen_final_review_form(gid):

        form = Questionnaire_review(request.form)

        if request.method == 'POST':
            if form.validate():

                if form.review.data == 1:

                    # read event json
                    with open(f'{git_dir}/data/events/{gid}.json', 'r') as fp:
                        event_data = json.load(fp)

                    event_data['contacts']['review_name'] = form.name.data
                    event_data['contacts']['review_email'] = form.email.data
                    event_data['comments']['review'] = form.comment.data
                    event_data['reviewed'] = 1
                    event_data['valid_status'] = 2

                    # update event json
                    with open(f'{git_dir}/data/events/{gid}.json', 'w') as fp:
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
                    os.system(f'cd {git_dir}; mkdocs -q build')

                    subject = f'Final review completed for {gid}'
                    body_review = f'{subject}. See the summary at {summary_url}.'
                    if notify:
                        # send an email to the reviewer
                        send_email(git_dir, form.email.data, subject, body_review)
                        # send an email to the lead
                        send_email(git_dir, event_data['contacts']['lead1_email'], subject, body_review)

                    # TODO CBC SCHEMA STUFF HERE


                return render_template('form_review_success.html', gid=gid, name=form.name.data)

            else:
                flash('Error:'+str(form.errors),'danger')


        return render_template('form_review.html', form=form, gid=gid)


    @app.route('/forms/<gid>', methods=('GET', 'POST'))
    def gen_event_form(gid):

        form = Questionnaire(request.form)

        if request.method == 'POST':
            if form.validate():

                # read event list and find idx
                event_list_df = pd.read_csv(event_list_fname, keep_default_na=False)
                gid_idx = event_list_df.loc[event_list_df['Event'].isin([gid])].index[0]

                # read event json
                with open(f'{git_dir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)

                # if h/l/v have no DQ issues
                if (form.conclusion_h1.data == 1 or form.conclusion_h1.data == 0) and (form.conclusion_l1.data == 1 or form.conclusion_l1.data == 0) and (form.conclusion_v1.data == 1 or form.conclusion_v1.data == 0):

                    # update the event json
                    event_data['valid_status'] = 1
                    event_data['valid_conclusion'] = 1
                    event_data['noise_mitigation']['H1']['required'] = 0
                    event_data['noise_mitigation']['H1']['status'] = 0
                    event_data['noise_mitigation']['L1']['required'] = 0
                    event_data['noise_mitigation']['L1']['status'] = 0
                    event_data['noise_mitigation']['V1']['required'] = 0
                    event_data['noise_mitigation']['V1']['status'] = 0
                    event_data['comments']['validator'] = form.comment.data
                    event_data['contacts']['validator_name'] = form.name.data
                    event_data['contacts']['validator_email'] = form.email.data

                    # update the events list
                    event_list_df.at[gid_idx,'Status'] = first_upper(val_flags[1])
                    event_list_df.at[gid_idx,'Conclusion'] = first_upper(dq_flags[1])
                    event_list_df.at[gid_idx,'Noise mitigation'] = first_upper(mitigation_flags[0])
                    event_list_df.at[gid_idx,'Contact person'] = f"{event_data['contacts']['review_name']} ([email](mailto:{event_data['contacts']['review_email']}))"
                    event_list_df.to_csv(event_list_fname, index=False)

                    subject = f'Event validation report complete for {gid}: {first_upper(dq_flags[1])}'
                    body_valid = f'{subject}. See summary at {summary_url} .'
                    body_review = f'{subject}, see the mitigation report summary at {summary_url}.\n\nPlease submit review form at {flask_base_url}/review/{gid} .'
                    if notify:
                        # send an email to validator
                        send_email(git_dir, form.email.data, subject, body_valid)
                        # send an email to the lead
                        send_email(git_dir, event_data['contacts']['lead1_email'], subject, body_valid)
                        # send an email to reviewer
                        send_email(git_dir, event_data['contacts']['review_email'], subject, body_review)


                else: # if h/l/v have issues

                    # update the event json
                    event_data['valid_status'] = 1
                    event_data['valid_conclusion'] = 2
                    event_data['noise_mitigation']['H1']['required'] = 1 if form.conclusion_h1.data == 2 else 0
                    event_data['noise_mitigation']['H1']['status'] = 1 if form.conclusion_h1.data == 2 else 0
                    event_data['noise_mitigation']['L1']['required'] = 1 if form.conclusion_l1.data == 2 else 0
                    event_data['noise_mitigation']['L1']['status'] = 1 if form.conclusion_l1.data == 2 else 0
                    event_data['noise_mitigation']['V1']['required'] = 1 if form.conclusion_v1.data == 2 else 0
                    event_data['noise_mitigation']['V1']['status'] = 1 if form.conclusion_v1.data == 2 else 0
                    event_data['comments']['validator'] = form.comment.data
                    event_data['contacts']['validator_name'] = form.name.data
                    event_data['contacts']['validator_email'] = form.email.data

                    # update the events list
                    event_list_df.at[gid_idx,'Status'] = first_upper(val_flags[1])
                    event_list_df.at[gid_idx,'Conclusion'] = first_upper(dq_flags[2])
                    event_list_df.at[gid_idx,'Noise mitigation'] = first_upper(mitigation_flags[1])
                    event_list_df.at[gid_idx,'Contact person'] = f"{event_data['contacts']['mitigation_name']} ([email](mailto:{event_data['contacts']['mitigation_email']}))"
                    event_list_df.to_csv(event_list_fname, index=False)

                    subject = f'Event validation report complete for {gid}: {first_upper(dq_flags[2])}'
                    body_valid = f'{subject}. See summary at {summary_url} .'
                    body_mitig = f'{gid} requires noise mitigation, see the event validation report summary at {summary_url} .\n\nPlease submit your noise mitigation report at {flask_base_url}/mitigation/{gid} .'
                    if notify:
                        # send an email to validator
                        send_email(git_dir, form.email.data, subject, body_valid)
                        # send an email to the lead
                        send_email(git_dir, event_data['contacts']['lead1_email'], subject, body_valid)
                        # send an email to noise mitigation
                        send_email(git_dir, event_data['contacts']['mitigation_email'], subject, body_mitig)

                # update website's .md table
                with open(md_fname, 'w') as md:
                    event_list_df.to_markdown(buf=md, numalign="center", index=False)
                os.system(f'cd {git_dir}; mkdocs -q build')

                # update event json
                with open(f'{git_dir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)

                return render_template('form_success.html', gid=gid, name=form.name.data, h1=dq_flags[form.conclusion_h1.data], l1=dq_flags[form.conclusion_l1.data], v1=dq_flags[form.conclusion_v1.data])

            else:
                flash('Error:'+str(form.errors),'danger')

        return render_template('form.html', form=form, gid=gid)


    @app.route('/about/')
    def about():
        return render_template('about.html')

    return app

#------------------------------------------------------------------------------

def main():

    # parse args
    parser = argparse.ArgumentParser(description=__doc__, prog=__process_name__)
    parser.add_argument('--port', type=int, help='port to host the website')
    parser.add_argument('--events', type=str, help='event list .csv file in /data directory')
    parser.add_argument('--table', type=str, help='website table .md file in /data directory')
    parser.add_argument('--git', type=str, help='git directory of this app')
    parser.add_argument('--notify', action=argparse.BooleanOptionalAction, help='Send notification emails.')
    args = parser.parse_args()

    app = create_app(port=args.port,
                     git_dir=args.git,
                     event_list=args.events,
                     website_md=args.table,
                     notify=args.notify)
    app.run()

#------------------------------------------------------------------------------

# allow to be run on the command line
if __name__ == "__main__":
    main()
