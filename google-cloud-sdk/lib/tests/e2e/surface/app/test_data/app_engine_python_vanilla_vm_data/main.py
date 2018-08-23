# -*- coding: utf-8 -*- #
"""Simple app that verifies headers."""

import json
import os

import flask

app = flask.Flask(__name__)


def _IsFlex():
  """Return true iff app is flex."""
  return os.environ.get('GAE_AFFINITY', 'true') == 'false'


@app.errorhandler(Exception)
def _ErrorHandler(e):
  return 'UNEXPECTED ERROR:\n%s\n' % str(e), 500


@app.route('/')
def HelloWorld():
  """Simple endpoint to check that the app is serving without using health."""
  return 'Hello world'


@app.route('/headers', methods=['GET', 'POST'])
def RequestHeaders():
  """Returns request headers for verification.

  Gives a json object containing a boolean isFlex value and
  a dict of all request headers.

  In addition if called as a POST method, the user can set extra headers
  that will be set on the response, in order to verify response headers.

  Returns:
      A Response object
  """
  resp_data = {'isFlex': _IsFlex(),
               'headers': dict(flask.request.headers)}
  if flask.request.method == 'POST':
    resp_data['form'] = flask.request.form
  resp_body = json.dumps(resp_data)
  resp = flask.Response(resp_body, mimetype='test/json')
  if flask.request.method == 'POST':
    for header in flask.request.form:
      resp.headers[header] = flask.request.form[header]
  return resp


@app.route('/_ah/health')
def Health():
  return flask.Response('ok', mimetype='text/plain')


if __name__ == '__main__':
  # This is used when running locally. Gunicorn is used to run the
  # application on Google App Engine. See entrypoint in app.yaml.
  app.run(host='127.0.0.1', port=8080, debug=True)
