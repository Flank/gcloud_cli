# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A base class for tests of captured sessions."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import json
import os
import sys
import time
import traceback
import urlparse

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import session_capturer
from googlecloudsdk.core.resource import yaml_printer
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import httplib2
import six
from six.moves import BaseHTTPServer
from six.moves import map  # pylint: disable=redefined-builtin
from six.moves import StringIO
from six.moves import zip  # pylint: disable=redefined-builtin


def NoExceptions(func):
  def _Wrapper(*args, **kwargs):
    try:
      func(*args, **kwargs)
    except Exception:  # pylint: disable=broad-except
      pass
  return _Wrapper


class SessionHttpMock(object):
  """Class to mock http.request using captured session."""

  def __init__(self, test, regen=False):
    self._test = test
    self._regen = regen

  def Request(self, uri, method='GET', body=None, headers=None,
              unused_redirections=httplib2.DEFAULT_MAX_REDIRECTS,
              unused_connection_type=None):
    """Replaces the http.request method."""
    if self._regen:
      self._test.AssertNextSessionEntryMatches(
          'request', **session_capturer.GetHttpRequestDict(
              uri, method, body, headers))
    else:
      request = self._test.GetNextSessionEntry('request')
      session_uri = request.get('uri', '')
      session_method = request.get('method', '')
      session_body = request.get('body', '')
      session_headers = request.get('headers', '')
      self.AssertUriEqual(self._test, uri, session_uri)
      self._test.assertEquals(method, session_method)
      requests = self._SplitBatchRequest(uri, method, body, headers)
      session_requests = self._SplitBatchRequest(
          session_uri, session_method, session_body, session_headers)
      self._test.assertEquals(len(requests), len(session_requests))
      for req, session_req in zip(requests, session_requests):
        session_req[1].AssertSessionEquals(req[1])
        self._test.assertEquals(req[2], session_req[2])  # body
    return self._GetResponse()

  @staticmethod
  def AssertUriEqual(test, uri_1, uri_2):
    parsed_uri_1 = urlparse.urlparse(uri_1)
    parsed_uri_2 = urlparse.urlparse(uri_2)
    test.assertEquals(parsed_uri_1.path, parsed_uri_2.path)
    parse_qs = lambda p: urlparse.parse_qs(p.query)
    test.assertEquals(parse_qs(parsed_uri_1), parse_qs(parsed_uri_2))

  class _HttpRequest(BaseHTTPServer.BaseHTTPRequestHandler):

    # pylint: disable=super-init-not-called
    def __init__(self, request_text):
      self.rfile = StringIO(request_text)
      self.raw_requestline = self.rfile.readline()
      self.error_code = self.error_message = None
      self.parse_request()

    def send_error(self, code, message):
      self.error_code = code
      self.error_message = message

  class _HttpHeaders(object):
    """A class handling uri, method and headers of a request."""

    def __init__(self, test, uri, method, headers):
      self._test = test
      self.uri = uri
      self.method = method
      self.headers = headers

    def AssertSessionEquals(self, other):
      SessionHttpMock.AssertUriEqual(self._test, self.uri, other.uri)
      self._test.assertEquals(self.method, other.method)
      self._AssertHeadersPresent(other.headers)

    def _AssertHeadersPresent(self, other_headers):
      for session_header in self.headers:
        self._test.assertIn(session_header, other_headers)

  def _GetResponse(self):
    """Reads the response from session file."""
    record = self._test.GetNextSessionEntry('response')
    response = httplib2.Response(record['response'])
    content = ''
    for part in record['content']:
      if isinstance(part, six.string_types):
        content += part
      else:
        self._test.assertEquals(list(six.iterkeys(part)), ['json'])
        content += json.dumps(part['json'])

    return response, content

  def _SplitBatchRequest(self, uri, method, body, headers):
    """Splits the batch request into a list of requests."""
    content_type = headers.get('content-type', '')
    pattern = 'boundary="'
    if content_type.find(pattern) == -1:
      headers = ['{}: {}'.format(k, v) for k, v in six.iteritems(headers)]
      return [('', self._HttpHeaders(self._test, uri, method, headers), body,)]
    boundary = content_type[content_type.find(pattern) + len(pattern):]
    boundary = '--' + boundary[:boundary.find('"')]
    result = body.split(boundary)
    self._test.assertEquals(result[0], '')
    self._test.assertEquals(result[-1].strip(), '--')

    def _SplitSingleRequest(request):
      part_headers, request_headers, request_body = request.split('\n\n', 2)
      http_request = self._HttpRequest(request_headers)
      method = http_request.requestline.split(' ', 1)[0]
      return part_headers, self._HttpHeaders(
          self._test, http_request.path, method, http_request.headers.headers
      ), request_body

    return sorted(
        map(_SplitSingleRequest, result[1:-1]),
        key=lambda result: (result[1].uri, result[2]))


class SessionInputMock(io.IOBase):
  """Class to mock stdin to one captured in session."""

  def __init__(self, value):
    super(SessionInputMock, self).__init__()
    self._stream = StringIO(value)

  def read(self, *args, **kwargs):
    return self._stream.read(*args, **kwargs)

  def readline(self, *args, **kwargs):
    return self._stream.readline(*args, **kwargs)

  def readlines(self, *args, **kwargs):
    return self._stream.readlines(*args, **kwargs)

  def isatty(self, *args, **kwargs):
    return True

  @property
  def Eof(self):
    return not self._stream.read()


class SessionOutputMock(StringIO):

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    pass


class SessionFileIoMock(session_capturer.FileIoCapturerBase):
  """A class providing captured input(if any) and saving the output."""

  def __init__(self, captured_files, test):
    super(SessionFileIoMock, self).__init__()
    self._files = {}
    for f in captured_files:
      self._files[f['name']] = f['content']
    self._test = test
    self._accessed_files = set()

  def Open(self, name, mode='r', buffering=-1, **kwargs):
    if 'w' in mode:
      if not self._ShouldCaptureFile(name, sys._getframe().f_back):  # pylint: disable=protected-access
        return self._real_open(name, mode, buffering)
      capturer = SessionOutputMock()
      self._Save(self._outputs, name, capturer)
      return capturer
    else:
      if name not in self._files:  # File not captured
        return self._real_open(name, mode, buffering)
      self._accessed_files.add(name)
      return SessionInputMock(self._files[name])

  def Finalize(self):
    for k in self._files:
      self._test.assertIn(
          k, self._accessed_files,
          '{} is specified in session but not opened for reading.'.format(k))
    self._accessed_files = set()


class SessionManager(object):
  """A class to manage recorded session."""

  def __init__(self, test, session_file):
    self._test = test
    self._session_file = session_file
    self._regen_tests_root = os.getenv('CLOUD_SDK_TEST_REGEN')

  def __enter__(self):
    with open(self._session_file) as f:
      self._test.LoadSessionFile(f, bool(self._regen_tests_root))
    self._test.CreateMocks()
    self._test.LoadProperties()
    # Properties can affect the logger so we need to reset to pick them up.
    log.Reset()

  def __exit__(self, exc_type, exc_val, exc_tb):
    self._test.Unmock()
    self._test.AssertSessionOutputMatches()
    self._test.AssertSessionIsOver()
    self._test.Finalize(exc_val)
    if self._regen_tests_root:
      session_file = os.path.join(self._regen_tests_root,
                                  self._GetTestRelPath())
      with open(session_file, 'w') as f:
        printer = yaml_printer.YamlPrinter(f)
        for record in self._test.GetNewSession():
          printer.AddRecord(record)

  _TEST_DIR = os.path.join('tests', 'integration', 'surface')

  def _GetTestRelPath(self):
    abs_path = os.path.abspath(self._session_file)
    test_dir_idx = abs_path.rfind(self._TEST_DIR)
    return abs_path[test_dir_idx + len(self._TEST_DIR) + 1:]


class _CapturedAssertionErrorMcs(type):
  """A metaclass which creates exceptions saving all their instances.

  The exception classes are normally derived from AssertionError.
  Each class contains cls.errors - list of all created instances.
  """

  def __new__(mcs, name, bases=(AssertionError,), namespace=None):
    if namespace is None:
      namespace = {}
    namespace['errors'] = []
    def Init(self, *args, **kwargs):
      super(type(self), self).__init__(*args, **kwargs)
      self.UpdateTraceback()
      self.errors.append(self)
    namespace['__init__'] = Init
    def New(cls, *args, **kwargs):
      err = AssertionError.__new__(cls, *args, **kwargs)
      err.UpdateTraceback()
      cls.errors.append(err)
      return err
    namespace['__new__'] = classmethod(New)
    def Str(self):
      return '{}\nTraceback:\n{}'.format(super(type(self), self).__str__(),
                                         self.traceback)
    namespace['__str__'] = Str
    def UpdateTraceback(self):
      self.traceback = ''.join(traceback.format_stack())
    namespace['UpdateTraceback'] = UpdateTraceback

    return super(_CapturedAssertionErrorMcs, mcs).__new__(
        mcs, name, bases, namespace)


class _State(object):

  def __init__(self, state):
    self._state = state

  def Mock(self, test):
    for k, v in six.iteritems(session_capturer.SessionCapturer.STATE_MOCKS):
      value = self._state.get(k, v.default_value)
      v.Mock(test, value)


class SessionTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """A base class for tests using captured sessions."""

  # Make cls.failureException unraisable - self.failureException should be
  # used instead.
  failureException = None  # pylint: disable=invalid-name

  def GetNextSessionEntry(self, key):
    entry = next(self._session)
    self.assertEqual(list(six.iterkeys(entry)), [key])
    if self._regen:
      self._records.append(entry)
    return entry[key]

  def AssertNextSessionEntryMatches(self, key, **kwargs):
    session_entry = next(self._session)
    self.assertEqual(list(six.iterkeys(session_entry)), [key])
    if self._regen:
      self._records.append({key: {k: v for k, v in six.iteritems(kwargs) if v}})
    else:
      for k, v in six.iteritems(kwargs):
        if v:
          if isinstance(v, six.string_types):
            self.assertMultiLineEqual(session_entry[key].get(k), v)
          else:
            self.assertEqual(session_entry[key].get(k), v)

  def GetNewSession(self):
    self.assertTrue(self._regen,
                    'Attempt to get session that has not been regenerated.')
    return self._records

  def LoadSessionFile(self, stream, regen=False):
    self._session = iter(list(yaml.load_all(stream)))
    self._regen = regen
    self._records = []
    args = self.GetNextSessionEntry('args')
    specified_args = []
    for k, v in six.iteritems(args['specified_args']):
      if v is True:
        specified_args.append(k)
      elif v is False:
        self.assertTrue(k.startswith('--no-'),
                        'A False argument should start with --no-')
        specified_args.append(k)
      else:
        specified_args.append('{}=\'{}\''.format(
            k, six.text_type(v).replace("'", r"\'")))
    self.command = '{} {}'.format(args['command'], ' '.join(specified_args))
    self._state = _State(self.GetNextSessionEntry('state'))
    self._properties = self.GetNextSessionEntry('properties')
    input_data = self.GetNextSessionEntry('input')
    self._stdin = SessionInputMock(input_data.get('stdin', ''))
    self._fileio = SessionFileIoMock(input_data.get('files', []), self)

  def CreateMocks(self):
    http_mock = SessionHttpMock(self, self._regen)
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    request_mock.side_effect = http_mock.Request
    sys.stdin = self._stdin
    sys.stdout.isatty = lambda: True
    sys.stderr.isatty = lambda: True
    self._state.Mock(self)
    self.StartObjectPatch(time, 'sleep', return_value=None)
    self._fileio.Mock()
    # Class is different for each session
    self.failureException = _CapturedAssertionErrorMcs(  # pylint: disable=invalid-name
        b'{} Failure Exception'.format(id(self._session)))
    log.Reset(sys.stdout, sys.stderr)

  def Unmock(self):
    sys.stdin = sys.__stdin__
    self._fileio.Unmock()

  def LoadProperties(self):
    for section in properties.VALUES:
      if section.name in self._properties:
        for prop, value in six.iteritems(self._properties[section.name]):
          section.Property(prop).Set(value)

  def Run(self, *args, **kwargs):
    try:
      super(SessionTestBase, self).Run(*args, **kwargs)
    except self.failureException:  # pylint: disable=catching-non-exception
      pass
    except Exception as e:  # pylint: disable=broad-except
      # Check if it's the exception captured in session
      context = exceptions.ExceptionContext(e)
      if not self.failureException.errors:  # No assertion errors happened
        try:
          self.AssertNextSessionEntryMatches(
              'exception',
              message=e.message,
              type=six.text_type(type(e)))
        except (StopIteration, self.failureException):  # pylint: disable=catching-non-exception
          # Not the same: save and reraise original error
          self.failureException.errors = []
          self.failureException(e)
          context.Reraise()

  @NoExceptions
  def AssertSessionOutputMatches(self):
    self.AssertNextSessionEntryMatches(
        'output',
        stdout=self.GetOutput(),
        stderr=self.GetErr(),
        files=self._fileio.GetOutputs(),
        private_files=self._fileio.GetPrivateOutputs())

  @NoExceptions
  def AssertSessionIsOver(self):
    self.assertTrue(self._stdin.Eof, 'Not all the stdin has been read.')
    self._fileio.Finalize()
    self.assertRaises(StopIteration, lambda: next(self._session))

  def Finalize(self, exc):
    errors = self.failureException.errors
    if errors:
      if exc is None or exc.message != errors[0].message:
        errors[0].args = ("""\
WARNING: Assertion Error caught. Different exception raised.

Assertion Error: {}""".format(errors[0].message),)
        raise errors[0]
      else:
        raise
