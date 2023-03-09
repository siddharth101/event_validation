#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: nu:ai:ts=4:sw=4

"""
FLASK website for event validation
Based on https://dcc.ligo.org/LIGO-G2300083, https://dcc.ligo.org/LIGO-T2200265
"""

import json, argparse
import pandas as pd

from wtforms import Form, TextAreaField, validators, SubmitField, SelectField, IntegerField
from flask import Flask, render_template, request, url_for, flash


__author__ = 'Ronaldas Macas'
__email__ = 'ronaldas.macas@ligo.org'
__version__ = '0.2'
__process_name__ = 'eval-website'

#------------------------------------------------------------------------------

# read events file and update the messages list
def get_events_dict(list_fname, git_dir):

    list_content = pd.read_csv(list_fname)
    list_events = list_content['Candidate event']

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


#------------------------------------------------------------------------------


def create_app(port, git_dir, event_list, website_md):
    app = Flask(__name__)

    flask_base_url = f'http://127.0.0.1:{port}/'

    event_list_fname = f'{git_dir}/data/{event_list}'
    events = get_events_dict(event_list_fname, git_dir)

    val_flags = ['not started', 'ongoing', 'completed', 'issues']
    dq_flags = ['no DQ issues', 'limited analysis window', 'needs further DQ mitigation']

    messages = []
    for key, item in sorted(list(events.items()), key=lambda x:x[0].lower(), reverse=True):
        if item["valid_status"] == 2:
            title = f'{key}: {dq_flags[item["valid_conclusion"]]}'
            form_url = f'{flask_base_url}warning/{key}'
        else:
            title = f'{key}: {val_flags[item["valid_status"]]}'
            form_url = f'{flask_base_url}forms/{key}'

        summary_url = f'{flask_base_url}summaries/{key}'
        dqr_url = events[key]['dqr_url']

        message = {'title': title, 'content': f'', 'form_url': form_url, 'gitlab_issue_url': item['git_issue_url'], 'dqr_url':dqr_url, 'summary_url':summary_url}
        messages.append(message)


    class Questionnaire(Form):

        name = TextAreaField('name', [validators.InputRequired()])
        surname = TextAreaField('surname:', [validators.InputRequired()])
        email = TextAreaField('email:', [validators.InputRequired()])
        flow = IntegerField('flow', [validators.InputRequired(), validators.NumberRange(min=10, max=4096, message='Lowest frequency must be within 10-4096 Hz range.')])
        fhigh = IntegerField('fhigh:', [validators.InputRequired(), validators.NumberRange(min=10, max=4096, message='Highest frequency must be within 10-4096 Hz range.')])

        validation_status = [(0, dq_flags[0]), (1, dq_flags[1]), (2, dq_flags[2])]

        conclusion = SelectField('conclusion:', coerce=int, choices=validation_status, validators=[validators.InputRequired()])


    @app.route('/')
    def index():
        return render_template('index.html', messages=messages)


    @app.route('/summaries/<gid>', methods=('GET', 'POST'))
    def get_summary(gid):

        if events[gid]['valid_status'] == 2:
            summary = [gid] + list(events[gid].values())
            # express validation status and conclusion in str
            summary[1] = val_flags[2]
            summary[3] = dq_flags[summary[3]]
            return render_template('val_summary.html', summary=summary)
        else:
            return render_template('val_summary_404.html', gid=gid)


    @app.route('/warning/<gid>', methods=('GET', 'POST'))
    def form_warning(gid):

        fname = events[gid]['validator_name']
        args = [gid, fname, events[gid]['validator_email'],
                f'{flask_base_url}summaries/{gid}',
                f'{flask_base_url}forms/{gid}']

        return render_template('form_warning.html', args=args)


    @app.route('/forms/<gid>', methods=('GET', 'POST'))
    def gen_event_form(gid):

        form = Questionnaire(request.form)
        form_output = {"fname":form.name.data, "lname":form.surname.data,
                "email":form.email.data, "flow":form.flow.data, "fhigh":form.fhigh.data,
                "val_conclusion": form.conclusion.data}

        if request.method == 'POST':
            if form.validate():

                validator_name = f'{form.name.data} {form.surname.data}'

                # update the events list
                event_list_df = pd.read_csv(event_list_fname, keep_default_na=False)
                gid_idx = event_list_df.loc[event_list_df['Candidate event'].isin([gid])].index[0]
                event_list_df.at[gid_idx,'Validation status'] = 2
                event_list_df.at[gid_idx,'Validation conclusion'] = form.conclusion.data
                event_list_df.at[gid_idx,'Volunteer'] = validator_name
                event_list_df.at[gid_idx,'Email'] = form.email.data
                event_list_df.to_csv(event_list_fname, index=False)

                # update website's .md table
                md_fname = f'{git_dir}/data/{website_md}'
                with open(md_fname, 'w') as md:
                    event_list_df.to_markdown(buf=md, numalign="center", index=False)

                # update the event json
                with open(f'{git_dir}/data/events/{gid}.json', 'r') as fp:
                    event_data = json.load(fp)
                event_data['validator_name'] = validator_name
                event_data['validator_email'] = form.email.data
                event_data['flow'] = form.flow.data
                event_data['fhigh'] = form.fhigh.data
                event_data['valid_conclusion'] = form.conclusion.data
                event_data['valid_status'] = 2
                event_data['devil_form_url'] = f'{flask_base_url}forms/{gid}'
                with open(f'{git_dir}/data/events/{gid}.json', 'w') as fp:
                    json.dump(event_data, fp, indent=4)


                return render_template('form_success.html', gid=gid, name=form.name.data, val_conclusion=dq_flags[form.conclusion.data])

            else:
                flash('Error:'+str(form.errors),'danger')

        return render_template('form.html', form=form, gid=gid)


    @app.route('/faq/')
    def faq():
        return render_template('faq.html')


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
    args = parser.parse_args()

    app = create_app(port=args.port,
                     git_dir=args.git,
                     event_list=args.events,
                     website_md=args.table)
    app.run()

#------------------------------------------------------------------------------

# allow to be run on the command line
if __name__ == "__main__":
    main()
