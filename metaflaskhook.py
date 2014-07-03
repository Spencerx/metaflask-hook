import re
from functools import update_wrapper

import click
import requests

from flask import Flask, request, abort, jsonify
from werkzeug.urls import url_join, url_quote


app = Flask(__name__)
app.config.update(
    ACCESS_TOKEN='add me',
    MEMBER_TEAM_ID='899232',
    METAFLASK_REPO='pocoo/metaflask',
    METAFLASK_MEMBERS_FOLDER='members',
    HOOK_SECRET='5aedb4c4-b1ae-4b66-8426-d641054f9102',
    API_BASE_URL='https://api.github.com/',
)
app.config.from_pyfile('localconfig.py', silent=True)

_member_fn_re = re.compile(r'^(\d{4})_(.*?)\.txt$')


def require_hook_secret(f):
    def new_func(*args, **kwargs):
        secret = request.args.get('secret')
        if secret != app.config['HOOK_SECRET']:
            abort(401)
        return f(*args, **kwargs)
    return update_wrapper(new_func, f)


def api_request(method, url, *args, **kwargs):
    kwargs['auth'] = (app.config['ACCESS_TOKEN'], 'x-oauth-basic')
    url = url_join(app.config['API_BASE_URL'], url)
    return requests.request(url=url, method=method, *args, **kwargs)


def add_member(username):
    api_request('PUT', 'teams/%s/members/%s' % (
        app.config['MEMBER_TEAM_ID'],
        url_quote(username),
    )).raise_for_status()


def remove_member(username):
    api_request('DELETE', 'teams/%s/members/%s' % (
        app.config['MEMBER_TEAM_ID'],
        url_quote(username),
    )).raise_for_status()


def get_current_members():
    rv = api_request('GET', 'teams/%s/members' % (
        app.config['MEMBER_TEAM_ID'],
    ))
    rv.raise_for_status()
    return [x['login'] for x in rv.json()]


def get_intended_members():
    rv = api_request('GET', 'repos/%s/contents/%s' % (
        app.config['METAFLASK_REPO'],
        app.config['METAFLASK_MEMBERS_FOLDER'],
    ))
    rv.raise_for_status()

    members = []
    for item in rv.json():
        m = _member_fn_re.match(item['name'])
        if m is None:
            continue
        num, name = m.groups()
        if name.endswith('.inactive'):
            continue
        members.append((int(num), name))

    members.sort()
    return [x[1] for x in members]


def sync_members():
    log = []
    _log = lambda x, u: log.append((x, u))

    current_members = set(get_current_members())
    intended_members = get_intended_members()

    new_members = set()
    for member in intended_members:
        if member not in current_members:
            add_member(member)
            _log('added', member)
        else:
            _log('retained', member)
        new_members.add(member)

    for member in current_members - new_members:
        remove_member(member)
        _log('deleted', member)

    return log


@app.route('/sync')
@require_hook_secret
def index():
    return jsonify(operations=sync_members())


@app.cli.command('sync-members')
def sync_members_cmd():
    """Synchronizes all members manually."""
    click.echo('Synchronizing members')
    for op, member in sync_members():
        click.echo('  %s %s' % (
            click.style(op, fg={
                'added': 'green',
                'retained': 'cyan',
                'deleted': 'red',
            }[op]),
            member,
        ))
    click.echo('Done.')
