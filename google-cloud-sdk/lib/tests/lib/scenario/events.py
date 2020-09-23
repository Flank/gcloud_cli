# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Defines the different types of scenario event handlers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import enum
import json
import os
import traceback

from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import http_encoding
from tests.lib.scenario import assertions
from tests.lib.scenario import updates

import six
from six.moves import http_client as httplib
from six.moves import urllib


class Error(Exception):
  """General exception for the module."""
  pass


class UnknownFieldError(Error):
  """Exception for when a referenced field does not exist in the data."""
  pass


class Request(object):
  """Class representing a request.

  Attributes:
    uri: str, URI of the request
    method: str, HTTP method of the request
    headers: dict, HTTP request headers.
    body: str, HTTP request body
  """

  @classmethod
  def FromApitoolsRequest(cls, apitools_request):
    return cls(apitools_request.url,
               apitools_request.http_method,
               apitools_request.headers,
               apitools_request.body)

  def __init__(self, uri, method, headers, body):
    self.uri = uri
    self.method = method
    self.headers = headers
    self.body = body


class Response(object):
  """Class representing a response.

  Attributes:
    status: int, HTTP status code.
    headers: dict, HTTP response headers.
    body: str, HTTP response body
  """

  @classmethod
  def FromApitoolsResponse(cls, apitools_response):
    headers = apitools_response.info.copy()
    status = int(headers.pop('status', httplib.OK))
    return cls(status, headers, apitools_response.content)

  def __init__(self, status, headers, body):
    self.status = status
    self.headers = headers
    self.body = body

  def __eq__(self, other):
    return (self.status == other.status and
            self.headers == other.headers and
            self.body == other.body)

  def ParseBody(self):
    try:
      return json.loads(self.body)
    except (ValueError, TypeError):
      # Not a json object.
      return self.body


class Event(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for all events."""

  def __init__(self, update_context):
    self._update_context = update_context

  @classmethod
  def EventType(cls):
    return None

  def UpdateContext(self):
    return self._update_context

  @abc.abstractmethod
  def Handle(self, *args, **kwargs):
    return []

  def Summary(self):
    return []

  def __str__(self):
    return '{}: [{}]'.format(self.EventType(), self._update_context.Location())


class _SingleValueEvent(six.with_metaclass(abc.ABCMeta, Event)):
  """Base class for all event types that just check a single value."""

  @classmethod
  def _Build(cls,
             backing_data,
             field,
             default=None,
             was_missing=False,
             location=None):
    value = backing_data.get(field, default)
    if value is None:
      value = ''
    update_context = updates.Context(
        backing_data,
        field,
        cls.EventType().UpdateMode(),
        was_missing=was_missing,
        location=location)
    return cls(update_context, assertions.Assertion.ForComplex(value))

  def __init__(self, update_context, assertion):
    super(_SingleValueEvent, self).__init__(update_context)
    self._assertion = assertion

  def Handle(self, value):
    return self._assertion.Check(self._update_context, value)

  def Summary(self):
    return [{str(self.EventType()): self._assertion.ValueRepr()}]


class StdoutEvent(_SingleValueEvent):
  """Checks that the captured stdout matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.STDOUT

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_stdout')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        collections.OrderedDict(),
        'expect_stdout',
        was_missing=True,
        location=location)


class StderrEvent(_SingleValueEvent):
  """Checks that the captured stderr matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.STDERR

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_stderr')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        collections.OrderedDict(),
        'expect_stderr',
        was_missing=True,
        location=location)


class ExitEvent(Event):
  """Checks that the command exit code matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.EXIT

  @classmethod
  def FromData(cls, backing_data):
    exit_data = backing_data['expect_exit']
    code = exit_data.get('code')
    has_message = 'message' in exit_data
    message = exit_data.get('message')
    return cls(
        updates.Context(backing_data, 'expect_exit',
                        cls.EventType().UpdateMode()), code,
        assertions.EqualsAssertion(code),
        assertions.Assertion.ForComplex(message) if has_message else None)

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context({'expect_exit': collections.OrderedDict()},
                                     'expect_exit',
                                     cls.EventType().UpdateMode(),
                                     was_missing=True,
                                     location=location)
    return cls(update_context, 0, assertions.EqualsAssertion(None),
               assertions.EqualsAssertion(None))

  def __init__(self, update_context, code, code_assertion, message_assertion):
    super(ExitEvent, self).__init__(update_context)
    self._code = code
    self._code_assertion = code_assertion
    self._message_assertion = message_assertion

  def Handle(self, exc, exc_tb=None):
    code = getattr(exc, 'exit_code', 1) if exc else 0
    message = six.text_type(exc) if exc else None
    details = '\n'.join(traceback.format_tb(exc_tb)) if exc_tb else None
    return self.HandleReturnCode(code, message, details=details)

  def HandleReturnCode(self, return_code, message=None, details=None):
    failures = []
    failures.extend(
        self._code_assertion.Check(
            self._update_context.ForKey('code'), return_code))
    if self._message_assertion or (failures and message):
      msg_assertion = self._message_assertion or assertions.EqualsAssertion('')
      failure = msg_assertion.Check(
          self._update_context.ForKey('message'), message)
      if details and failure:
        failure[0].details = details
      failures.extend(failure)
    return failures

  def Summary(self):
    if self._code == 0:
      return []
    return [{
        'error':
            '{}: {}'.format(
                self._code,
                self._message_assertion.ValueRepr()
                if self._message_assertion else None)
    }]


class UserInputEvent(Event):
  """Provides user input to a prompt."""

  @classmethod
  def EventType(cls):
    return EventType.USER_INPUT

  @classmethod
  def FromData(cls, backing_data):
    return cls(
        updates.Context(backing_data, 'user_input',
                        cls.EventType().UpdateMode()),
        backing_data.get('user_input') or [])

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context(
        collections.OrderedDict(),
        'user_input',
        cls.EventType().UpdateMode(),
        was_missing=True,
        location=location)
    return cls(update_context, [])

  def __init__(self, update_context, lines):
    super(UserInputEvent, self).__init__(update_context)
    self._lines = lines

  def Lines(self):
    return self._lines

  def Handle(self):
    """Handle the event.

    A user input event is a little different from the others because it is not
    an assertion. Basically, if there are lines registered, there is no failure
    because it provides the input and execution moves on. If there are no lines,
    then the prompt cannot be answered and it is an error.

    Returns:
      [Failure], The failures or []
    """
    if self._lines:
      return []
    return [
        assertions.Failure.ForGeneric(
            self._update_context, title='Missing user input event')
    ]

  def Summary(self):
    return [{'input': self._lines}]


class FileWrittenEvent(Event):
  """Checks that a given file was written with the given contents."""

  @classmethod
  def EventType(cls):
    return EventType.FILE_WRITTEN

  @classmethod
  def FromData(cls, backing_data):
    file_data = backing_data['expect_file_written']
    update_context = updates.Context(backing_data, 'expect_file_written',
                                     cls.EventType().UpdateMode())

    path_assertion = assertions.EqualsAssertion(file_data.get('path'))
    contents_assertion = assertions.Assertion.ForComplex(
        file_data.get('contents'))
    binary_contents = file_data.get('binary_contents')
    if (binary_contents is not None and
        isinstance(binary_contents, six.text_type)):
      binary_contents = binary_contents.encode('utf-8')
    binary_contents_assertion = assertions.Assertion.ForComplex(binary_contents)
    is_private_assertion = assertions.EqualsAssertion(
        file_data.get('is_private') or False)

    return cls(update_context, path_assertion, contents_assertion,
               binary_contents_assertion, is_private_assertion)

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context(
        {'expect_file_written': collections.OrderedDict()},
        'expect_file_written',
        cls.EventType().UpdateMode(),
        was_missing=True,
        location=location)
    return cls(update_context, assertions.EqualsAssertion(None),
               assertions.EqualsAssertion(None),
               assertions.EqualsAssertion(None),
               assertions.EqualsAssertion(False))

  def __init__(self, update_context, path_assertion, contents_assertion,
               binary_contents_assertion, is_private_assertion):
    super(FileWrittenEvent, self).__init__(update_context)
    self._path_assertion = path_assertion
    self._contents_assertion = contents_assertion
    self._binary_contents_assertion = binary_contents_assertion
    self._is_private_assertion = is_private_assertion

  def Handle(self, path, contents, private):
    # Normalize slashes so the schema in the yaml file can stay the same.
    path = path.replace('\\', '/')

    failures = []
    failures.extend(
        self._path_assertion.Check(self._update_context.ForKey('path'), path))
    if isinstance(contents, six.text_type):
      binary_contents = None
    else:
      binary_contents = contents
      contents = None

    failures.extend(
        self._contents_assertion.Check(
            self._update_context.ForKey('contents'), contents))
    failures.extend(
        self._binary_contents_assertion.Check(
            self._update_context.ForKey('binary_contents'), binary_contents))
    failures.extend(
        self._is_private_assertion.Check(
            self._update_context.ForKey('is_private'), private))
    return failures

  def Summary(self):
    return [{'write_file': self._path_assertion.ValueRepr()}]


class ApiCallEvent(Event):
  """Checks that the API request matches an expected request."""

  @classmethod
  def EventType(cls):
    return EventType.API_CALL

  @classmethod
  def FromData(cls, backing_data):
    """Builds a request event handler from yaml data."""
    call_data = backing_data['api_call']
    update_context = updates.Context(backing_data, 'api_call',
                                     cls.EventType().UpdateMode())

    poll_operation = call_data.get('poll_operation', None)
    is_repeatable = call_data.get('repeatable', None)
    is_optional = call_data.get('optional', False)
    request_assertion = RequestAssertion.FromCallData(call_data)
    response_assertion = ResponseAssertion.FromCallData(call_data)

    response_payload = HTTPResponsePayload.FromBackingData(backing_data)
    return cls(update_context, poll_operation, is_repeatable, is_optional,
               request_assertion, response_assertion, response_payload)

  @classmethod
  def ForMissing(cls, location):
    backing_data = {
        'api_call':
            collections.OrderedDict([('expect_request',
                                      collections.OrderedDict([('uri', ''),
                                                               ('method', ''),
                                                               ('headers', {}),
                                                               ('body', {
                                                                   'text': None,
                                                                   'json': {}
                                                               })])),
                                     ('return_response',
                                      collections.OrderedDict([
                                          ('status', int(httplib.OK)),
                                          ('headers', {}),
                                          ('body', None)]))])
    }
    update_context = updates.Context(
        backing_data,
        'api_call',
        cls.EventType().UpdateMode(),
        was_missing=True,
        location=location)
    return cls(
        update_context, None, None, False,
        RequestAssertion.ForMissing(),
        None,
        HTTPResponsePayload.FromBackingData(backing_data))

  def __init__(self, update_context, poll_operation, is_repeatable, is_optional,
               request_assertion, response_assertion, response_payload):
    super(ApiCallEvent, self).__init__(update_context)
    self._poll_operation = poll_operation
    self._is_repeatable = is_repeatable
    self._is_optional = is_optional
    self._was_repeated = False
    self._request_assertion = request_assertion
    self._response_assertion = response_assertion
    self._response_payload = response_payload
    self._call_data = None
    self._generated_op = None

  def IsOptional(self):
    return self._is_optional

  def CanBeRepeated(self):
    # We will try to repeat events if necessary unless this is explicitly set to
    # False.
    return self._is_repeatable or self._is_repeatable is None

  def MarkRepeated(self):
    self._was_repeated = True

  def MarkCalledWith(self, request, response):
    response_body = response.ParseBody() if response else None
    self._call_data = (request.uri, request.method, request.body, response_body)

  def MatchesPreviousCall(self, request, response):
    response_body = response.ParseBody() if response else None
    new_call = (request.uri, request.method, request.body, response_body)
    return self._call_data == new_call

  def GetMatchingOperationForRequest(self, request):
    if (self._generated_op and
        self._generated_op.MatchesPollingRequest(request)):
      return self._generated_op
    return None

  def CheckRepeatable(self):
    return assertions.EqualsAssertion(self._is_repeatable).Check(
        self._update_context.ForKey('repeatable'), self._was_repeated)

  def Handle(self, request, dry_run=False):
    return self._request_assertion.Check(
        self._update_context, request, dry_run=dry_run)

  def HandleResponse(self,
                     response,
                     resource_ref_resolver,
                     dry_run=False,
                     generate_extras=False):
    failures = []
    if generate_extras:
      failures.extend(
          self._GenerateOperationPolling(resource_ref_resolver, response))
    elif self._poll_operation and not dry_run:
      op = Operation.FromResponse(response,
                                  force_operation=self._poll_operation)
      self._ExtractOperationPollingName(resource_ref_resolver, op)

    if self._response_assertion:
      if not dry_run:
        self._response_assertion.ExtractReferences(resource_ref_resolver,
                                                   response.body)
      failures.extend(
          self._response_assertion.Check(
              self._update_context, response, dry_run=dry_run))
    elif (generate_extras and
          not self._poll_operation and self._poll_operation is not None):
      # Legacy operation detection.
      failures.extend(
          self._GenerateOperationsExtras(resource_ref_resolver, response))
    return failures

  def _GenerateOperationPolling(self, resource_ref_resolver, response):
    if not self._poll_operation and self._poll_operation is not None:
      # If explicitly disabled, don't treat this as an operation no matter what.
      return []

    op = Operation.FromResponse(response, force_operation=self._poll_operation)
    if not op or resource_ref_resolver.IsExtractedIdCurrent(
        'operation', op.name):
      # Not an operation response at all.
      if self._poll_operation is None:
        return []
      return assertions.EqualsAssertion(self._poll_operation).Check(
          self._update_context.ForKey('poll_operation'), False)

    # We've identified the response as an operation, make sure polling is turned
    # on.
    self._ExtractOperationPollingName(resource_ref_resolver, op)
    failures = assertions.EqualsAssertion(self._poll_operation).Check(
        self._update_context.ForKey('poll_operation'), True)
    return failures

  def _ExtractOperationPollingName(self, resource_ref_resolver, op):
    self._generated_op = op
    resource_ref_resolver.SetExtractedId('operation', op.name)
    resource_ref_resolver.SetExtractedId('operation-basename',
                                         os.path.basename(op.name))

  def _GenerateOperationsExtras(self, resource_ref_resolver, response):
    """Generates extra data if this response looks like an operation.

    If the body has a kind attribute that indicates an operation, this will
    update the scenario spec to include a default extract_references block
    to pull out the operation id. This should only be called if an
    expect_response block is not already present. If this is a polling operation
    it will be marked as optional.

    Args:
      resource_ref_resolver: ResourceReferenceResolver, The resolver to track
        the extracted references.
      response: Response, the response from the server.

    Returns:
      [Failure], The failures to update the spec and inject the new block or [].
    """
    op = Operation.FromResponse(response, force_operation=self._poll_operation)
    if not op:
      # Not an operation response at all.
      return []
    if resource_ref_resolver.IsExtractedIdCurrent('operation', op.name):
      # This is an op, but the id has already been extracted in a previous
      # event. This means that this is not the call that generated the op, but
      # rather the polling of the op. No need to generate the ref extraction,
      # but we do want to mark polling steps as optional and repeated calls.
      self.MarkRepeated()
      failures = self.CheckRepeatable()
      if op.status:
        # In order for optional to work, we need to also generate an assertion
        # against the status in the response.
        failures = assertions.EqualsAssertion(self._is_optional).Check(
            self._update_context.ForKey('optional'), True)
        failures.append(
            assertions.Failure.ForGeneric(
                self._update_context.ForKey('expect_response'),
                'Adding operation response assertion for optional polling',
                collections.OrderedDict([('body', {
                    'json': {
                        'status': op.status
                    }
                })])))
      return failures

    # This is a call that resulted in an operation being created. Extract its
    # id for future polling calls.
    resource_ref_resolver.SetExtractedId('operation', op.name)
    return [
        assertions.Failure.ForGeneric(
            self._update_context.ForKey('expect_response'),
            'Adding reference extraction for Operations response',
            collections.OrderedDict([('extract_references', [
                collections.OrderedDict([('field', 'name'),
                                         ('reference', 'operation')])
            ]), ('body', {
                'json': {}
            })]))
    ]

  def GetResponse(self):
    return self._response_payload.Respond()

  def UpdateResponsePayload(self, response):
    return self._response_payload.Update(self._update_context, response)

  def __str__(self):
    # pylint: disable=protected-access
    return super(ApiCallEvent, self).__str__() + ' [{}]'.format(
        self._request_assertion._uri_assertion)


class Operation(object):
  """Holds information about an operation that got returned an can be polled."""

  _NEXT_STATE = {
      'PENDING': 'RUNNING',
      'RUNNING': 'DONE',
      'DONE': 'DONE',
      None: 'DONE',
  }

  @classmethod
  def FromResponse(cls, response, force_operation=False):
    """Construct an Operation from an API response."""
    try:
      json_data = json.loads(response.body)
    except (ValueError, TypeError):
      # Not a json object.
      return None

    name = json_data.get('name')
    if not name:
      return None

    if (json_data.get('kind', '').endswith('#operation') or
        'operationType' in json_data):
      return _OldOperation(name, response)

    t = (json_data.get('metadata') or {}).get('@type') or ''
    if force_operation or 'done' in json_data or 'operation' in t.lower():
      return _NewOperation(name, response)

    return None

  def __init__(self, name, response):
    self._name = name
    self._response = response

  @property
  def name(self):
    return self._name

  def MatchesPollingRequest(self, request):
    uri, method = request.uri, request.method
    # Operations can be polled using an async Get method or a sync Wait method.
    is_operation_get = method == 'GET' and '/{}'.format(self.name) in uri
    is_operation_wait = (
        method == 'POST' and '/{}/wait'.format(self.name) in uri)
    return is_operation_get or is_operation_wait

  def Respond(self):
    self.status = Operation._NEXT_STATE[self.status]
    return self._response


class _NewOperation(Operation):
  """Represents a new style LRO.

  New Operations have a name and done=true/false. Other than that they have
  service specific metadata that can take any form. Because of this, we don't
  do the normal advancement of the status because we don't know where it is.
  """

  @property
  def status(self):
    return None

  @status.setter
  def status(self, value):
    if value == 'DONE':
      body = json.loads(self._response.body)
      body['done'] = True
      body['response'] = {}
      self._response.body = json.dumps(body)


class _OldOperation(Operation):
  """Represents an old style LRO."""

  @property
  def status(self):
    body = json.loads(self._response.body)
    return body['status']

  @status.setter
  def status(self, value):
    body = json.loads(self._response.body)
    body['status'] = value
    self._response.body = json.dumps(body)


class HTTPResponsePayload(object):
  """Encapsulates the data of a response payload."""

  HEADER_DENYLIST_PREFIX = frozenset([
      'x-google-',
      'alt-svc',
      '-content-encoding',
      'date',
      'content-location',
      'expires',
      'server',
      'transfer-encoding',
      'vary',
      'x-content-type-options',
      'x-frame-options',
      'x-xss-protection',
  ])

  @classmethod
  def FromBackingData(cls, backing_data):
    """"Create a response from the backing data."""
    response_payload_data = (backing_data['api_call'].get('return_response') or
                             collections.OrderedDict())
    status = response_payload_data.get('status')
    # Get the status from the header, for any httplib2 generated scenario tests.
    if not status:
      status = int(response_payload_data.get('headers', {}).get('status',
                                                                httplib.OK))

    headers = response_payload_data.get('headers', {}).copy()
    headers.pop('status', None)

    response_body = response_payload_data.get('body')
    if yaml.dict_like(response_body):
      response_body = json.dumps(response_body)

    response = Response(
        status,
        headers,
        response_body or '')
    return HTTPResponsePayload(response,
                               response_payload_data.get('omit_fields'))

  def __init__(self, response, omit_fields):
    self._response = response
    self._omit_fields = omit_fields

  def _SaveHeader(self, header):
    for prefix in HTTPResponsePayload.HEADER_DENYLIST_PREFIX:
      if header.lower().startswith(prefix):
        return False
    return True

  def Respond(self):
    return self._response

  def Update(self, context, response):
    """Updates the canned response data with real API response data."""

    def _ResponseUpdateHook(context, actual):
      """Custom update hook since this is not a real assertion failure."""
      data = context.BackingData()

      try:
        json_b = json.loads(actual.body,
                            object_pairs_hook=collections.OrderedDict)
      except (ValueError, TypeError):
        # Not a json object.
        json_b = None

      if json_b and self._omit_fields:
        for omit in self._omit_fields:
          try:
            del json_b[omit]
          except KeyError:
            raise UnknownFieldError(
                'Field [{}] in omit_fields was not found in the API '
                'response data'.format(omit))

      data['return_response']['status'] = actual.status
      data['return_response']['headers'] = collections.OrderedDict(
          (key, value)
          for key, value in sorted(six.iteritems(actual.headers))
          if self._SaveHeader(key))
      data['return_response']['body'] = json_b or actual.body
      return True

    update_context = context.ForKey(
        'return_response',
        update_mode=assertions.updates.Mode.API_RESPONSE_PAYLOADS,
        custom_update_hook=_ResponseUpdateHook)
    return [
        assertions.Failure.ForGeneric(update_context, 'API Response Payload',
                                      response)
    ]


class ReferenceExtraction(object):
  """Encapsulates an extract_reference directive."""

  @classmethod
  def FromData(cls, extraction_data):
    return cls(extraction_data['field'], extraction_data['reference'],
               extraction_data.get('modifiers', {}).get('basename'))

  def __init__(self, field, reference, basename):
    self._field = field
    self._reference = reference
    self._basename = basename

  def Extract(self, json_data, resource_ref_resolver):
    resource_id = resource_transform.GetKeyValue(json_data, self._field)
    if resource_id is None:
      raise Error(
          'Unable to extract resource reference for field: [{}] from data: [{}]'
          .format(self._field, json_data))

    if self._basename:
      resource_id = os.path.basename(resource_id)
    resource_ref_resolver.SetExtractedId(self._reference, resource_id)


def _Decode(value):
  return (http_encoding.Decode(value)
          if isinstance(value, six.binary_type) else value)


def MakeHttpHeadersAssertion(http_data, for_response=False):
  """Returns an assertion to check HTTP headers match the given values.

  Args:
    http_data: dict, api_call.expect_request or api_call.expect_response.
    for_response: bool, whether or not these are request or response headers.

  Returns:
    Assertion
  """
  headers_assertion = assertions.DictAssertion()
  for header, value in six.iteritems(http_data.get('headers', {})):
    # Even though headers might contain status, we've pulled it out and are
    # checking it in ResponseAssertion._status_assertion
    if for_response and header == 'status':
      continue
    headers_assertion.AddAssertion(header,
                                   assertions.Assertion.ForComplex(value))
  return headers_assertion


class HttpBodyAssertion(object):
  """Checks that the body in a HTTP request or response matches."""

  @classmethod
  def FromData(cls, mode, http_data):
    """Creates an HttpBodyAssertion for an HTTP request or response.

    Args:
      mode: string, 'expect_request' or 'expect_response' depending on if it is
          a request or response.
      http_data: dict, api_call.expect_request or api_call.expect_response.

    Returns:
      HttpBodyAssertion
    """
    payload_json_assertion = None
    payload_text_assertion = None
    body_present = True
    body_data = http_data.get('body')
    if 'body' not in http_data or (not body_data and body_data is not None):
      # The body section is missing entirely or it is present and is an empty
      # dictionary. In these cases, the assertions are not present and will be
      # updated always.
      body_present = False
      payload_json_assertion = assertions.JsonAssertion().Matches(
          '', assertions.MISSING_VALUE)
      payload_text_assertion = assertions.EqualsAssertion(
          assertions.MISSING_VALUE)
      http_data['body'] = {'text': None, 'json': {}}
    elif body_data is None:
      # The body section is present and explicitly None. This implies assertions
      # that the body is actual None. If it is not, the assertions will fail.
      body_present = False
      payload_json_assertion = assertions.JsonAssertion().Matches('', None)
      payload_text_assertion = assertions.EqualsAssertion(None)
    else:
      # The body is present, load the assertions that were provided.
      if 'text' in body_data:
        payload_text_assertion = assertions.Assertion.ForComplex(
            body_data['text'])
      if 'json' in body_data:
        payload_json_assertion = assertions.JsonAssertion()
        json_data = body_data['json']
        if not json_data or json_data == assertions.MISSING_VALUE:
          # If explicitly None, this asserts that the request is empty.
          # If explicitly the empty dictionary, the assertion checks nothing.
          payload_json_assertion.Matches('', json_data)
        else:
          for field, struct in six.iteritems(json_data):
            payload_json_assertion.Matches(field, struct)

    return cls(mode, body_present, payload_json_assertion,
               payload_text_assertion)

  def __init__(self, mode, body_present, payload_json_assertion,
               payload_text_assertion):
    self._mode = mode
    self._body_present = body_present
    self._payload_json_assertion = payload_json_assertion
    self._payload_text_assertion = payload_text_assertion

  def _Key(self, key):
    return self._mode + '.' + key

  def Check(self, context, body, dry_run):
    """Checks that the body in a HTTP request or response matches.

    Args:
      context: updates.Context, context for how to perform an update.
      body: str, The body payload of the request or response.
      dry_run: bool, dry run.

    Returns:
      List of assertions.Failure
    """
    # Don't differentiate between a None body and an empty body. It's the same.
    if body:
      body = _Decode(body)
    else:
      body = None

    json_data = None
    try:
      json_data = json.loads(body, object_pairs_hook=collections.OrderedDict)
    except (ValueError, TypeError):
      # Not a json object.
      pass

    if json_data is not None and not self._body_present:
      # When there is no body present, we only want to generate one of the text
      # or json assertions (not both). If both are present, we update them
      # accordingly.
      body = None

    body_context = context.ForKey(self._Key('body'))
    backing_data = body_context.BackingData()
    if not dry_run and backing_data.get('body') is None and (body or json_data):
      # Body was explicitly set to None, but there is a body. The assertion
      # updates are going to trigger so we need to make sure there is a
      # dictionary for the values to get put into.
      backing_data['body'] = {}

    def _CleanupHook(context, actual):
      # This just does the normal update, but then sets the body to None if
      # both assertions were removed.
      result = context.StandardUpdateHook(actual)
      if not backing_data['body']:
        backing_data['body'] = None
      return result

    failures = []
    if self._payload_json_assertion:
      failures.extend(
          self._payload_json_assertion.Check(
              context.ForKey(
                  self._Key('body.json'), custom_update_hook=_CleanupHook),
              json_data or None))
    if self._payload_text_assertion:
      failures.extend(
          self._payload_text_assertion.Check(
              context.ForKey(
                  self._Key('body.text'), custom_update_hook=_CleanupHook),
              body))
    return failures


class HTTPAssertion(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for API request or response assertions."""

  def __init__(self, headers_assertion, body_assertion):
    self._headers_assertion = headers_assertion
    self._body_assertion = body_assertion

  @abc.abstractmethod
  def _Key(self, key):
    pass

  def CheckHeaders(self, context, headers):
    decoded_headers = {_Decode(h): _Decode(v)
                       for h, v in six.iteritems(headers)}
    return self._headers_assertion.Check(
        context.ForKey(self._Key('headers')), decoded_headers)

  def CheckBody(self, context, body, dry_run):
    return self._body_assertion.Check(context, body, dry_run)


def _OrderedUri(uri):
  """Sorts URI params to ensure they are always processed in same order."""
  url_parts = urllib.parse.urlsplit(uri)
  params = urllib.parse.parse_qs(url_parts.query)
  ordered_query_params = collections.OrderedDict(
      sorted(six.iteritems(params)))
  url_parts = list(url_parts)
  # pylint:disable=redundant-keyword-arg, this is valid syntax for this lib
  url_parts[3] = urllib.parse.urlencode(ordered_query_params, doseq=True)
  # pylint:disable=too-many-function-args, This is just bogus.
  return urllib.parse.urlunsplit(url_parts)


class RequestAssertion(HTTPAssertion):
  """Checks that an HTTP request matches."""

  @classmethod
  def FromCallData(cls, call_data):
    """Creates a RequestAssertion from an api_call dict."""
    http_data = call_data['expect_request']
    uri_assertion = assertions.Assertion.ForComplex(http_data.get('uri', ''))
    method_assertion = assertions.EqualsAssertion(
        http_data.get('method', 'GET'))
    headers_assertion = MakeHttpHeadersAssertion(http_data)
    body_assertion = HttpBodyAssertion.FromData('expect_request', http_data)
    return cls(uri_assertion, method_assertion, headers_assertion,
               body_assertion)

  @classmethod
  def ForMissing(cls):
    """Creates a RequestAssertion for a missing api_call."""
    uri_assertion = assertions.EqualsAssertion(assertions.MISSING_VALUE)
    method_assertion = assertions.EqualsAssertion(assertions.MISSING_VALUE)
    headers_assertion = assertions.DictAssertion()

    payload_json_assertion = (assertions.JsonAssertion()
                              .Matches('', assertions.MISSING_VALUE))
    payload_text_assertion = assertions.EqualsAssertion(
        assertions.MISSING_VALUE)
    body_assertion = HttpBodyAssertion('expect_request', False,
                                       payload_json_assertion,
                                       payload_text_assertion)
    return cls(uri_assertion, method_assertion, headers_assertion,
               body_assertion)

  def __init__(self, uri_assertion, method_assertion, headers_assertion,
               body_assertion):
    super(RequestAssertion, self).__init__(headers_assertion, body_assertion)
    self._uri_assertion = uri_assertion
    self._method_assertion = method_assertion

  def _Key(self, key):
    return 'expect_request.' + key

  def CheckURI(self, context, uri):
    return self._uri_assertion.Check(
        context.ForKey(self._Key('uri')), _OrderedUri(uri))

  def CheckMethod(self, context, method):
    return self._method_assertion.Check(
        context.ForKey(self._Key('method')), method)

  def Check(self, context, request, dry_run=False):
    failures = self.CheckURI(context, request.uri)
    failures.extend(self.CheckMethod(context, request.method))
    failures.extend(self.CheckHeaders(context, request.headers))
    failures.extend(self.CheckBody(context, request.body, dry_run))
    return failures


class ResponseAssertion(HTTPAssertion):
  """Checks that an HTTP response matches."""

  @classmethod
  def FromCallData(cls, call_data):
    """Creates a ResponseAssertion from an api_call dict."""
    if 'expect_response' not in call_data:
      return None

    http_data = call_data['expect_response']
    status = http_data.get('status')
    if not status:
      status = int(http_data.get('headers', {}).get('status', httplib.OK))
    status_assertion = assertions.EqualsAssertion(status)
    headers_assertion = MakeHttpHeadersAssertion(http_data, for_response=True)
    body_assertion = HttpBodyAssertion.FromData('expect_response', http_data)
    extract_references = [
        ReferenceExtraction.FromData(d)
        for d in http_data.get('extract_references', [])
    ]
    return cls(status_assertion, headers_assertion, body_assertion,
               extract_references)

  def __init__(self, status_assertion, headers_assertion, body_assertion,
               extract_references):
    super(ResponseAssertion, self).__init__(headers_assertion, body_assertion)
    self._status_assertion = status_assertion
    self._extract_references = extract_references

  def _Key(self, key):
    return 'expect_response.' + key

  def ExtractReferences(self, resource_ref_resolver, body):
    """Extract any references from an API response.

    If this response assertion has registered references to extract, pull them
    out of the payload data and add them to the resolver for future use.

    Args:
      resource_ref_resolver: ResourceReferenceResolver, the resolver that is
        tracking resource references.
      body: str, The body payload of the response.

    Raises:
      Error: If a given reference cannot be extracted.
    """
    if not self._extract_references:
      return
    json_data = json.loads(body)
    for extraction in self._extract_references:
      extraction.Extract(json_data, resource_ref_resolver)

  def CheckStatus(self, context, status):
    return self._status_assertion.Check(
        context.ForKey(self._Key('status')), status)

  def Check(self, context, response, dry_run=False):
    failures = self.CheckStatus(context, response.status)
    failures.extend(self.CheckHeaders(context, response.headers))
    failures.extend(self.CheckBody(context, response.body, dry_run))
    return failures


class _UXEvent(six.with_metaclass(abc.ABCMeta, Event)):
  """A base class for events based on the UX JSON blob."""

  @classmethod
  def _Build(cls, backing_data, field, was_missing=False, location=None):
    ux_event_data = backing_data.setdefault(field, collections.OrderedDict())
    update_context = updates.Context(
        backing_data,
        field,
        cls.EventType().UpdateMode(),
        was_missing=was_missing,
        location=location)

    attr_assertions = collections.OrderedDict()
    for a in cls.EventType().UXElementAttributes():
      if was_missing or a in ux_event_data:
        # Only create assertions for things that were specified, or if the event
        # was missing, assert everything so it all gets filled in.
        attr_assertions[a] = assertions.EqualsAssertion(
            ux_event_data.get(a, None))

    return cls(update_context, attr_assertions, ux_event_data)

  def __init__(self, update_context, attr_assertions, ux_event_data):
    del ux_event_data
    super(_UXEvent, self).__init__(update_context)
    self._attr_assertions = attr_assertions

  def Handle(self, ux_event_data):
    failures = []
    for attribute, attribute_assertion in self._attr_assertions.items():
      failures.extend(
          attribute_assertion.Check(
              self._update_context.ForKey(attribute),
              ux_event_data.get(attribute)))
    return failures

  def Summary(self):
    attrs = [{
        attr: assertion.ValueRepr()
    } for attr, assertion in self._attr_assertions.items()]
    return [{str(self.EventType()): attrs}]


class ProgressBarEvent(_UXEvent):
  """Checks that the Progress Bar Event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROGRESS_BAR

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_progress_bar')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        collections.OrderedDict(),
        'expect_progress_bar',
        was_missing=True,
        location=location)


class ProgressTrackerEvent(_UXEvent):
  """Checks that the tracker event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROGRESS_TRACKER

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_progress_tracker')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        collections.OrderedDict(),
        'expect_progress_tracker',
        was_missing=True,
        location=location)


class StagedProgressTrackerEvent(_UXEvent):
  """Checks that the staged tracker event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.STAGED_PROGRESS_TRACKER

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_staged_progress_tracker')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        collections.OrderedDict(),
        'expect_staged_progress_tracker',
        was_missing=True,
        location=location)


class _PromptEvent(six.with_metaclass(abc.ABCMeta, _UXEvent)):
  """Base class for UX events that involve a prompt with user input."""

  def __init__(self, update_context, attr_assertions, ux_event_data):
    super(_PromptEvent, self).__init__(update_context, attr_assertions,
                                       ux_event_data)
    self._user_input = ux_event_data.get('user_input')

  @classmethod
  def DefaultValue(cls):
    return ''

  def UserInput(self):
    return self._user_input or self.DefaultValue()

  def Handle(self, ux_event_data):
    failures = super(_PromptEvent, self).Handle(ux_event_data)
    if self._user_input is None:
      # Set the answer to 'y' if the entire assertion was missing.
      failures.extend(
          assertions.EqualsAssertion(None).Check(
              self._update_context.ForKey('user_input'), self.DefaultValue()))
    return failures

  def Summary(self):
    attrs = [{
        attr: assertion.ValueRepr()
    } for attr, assertion in self._attr_assertions.items()]
    attrs.append({'input': self.UserInput()})
    return [{'prompt': attrs}]


class PromptContinueEvent(_PromptEvent):
  """Checks that the prompt event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROMPT_CONTINUE

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_prompt_continue')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        collections.OrderedDict(),
        'expect_prompt_continue',
        was_missing=True,
        location=location)

  @classmethod
  def DefaultValue(cls):
    return 'y'


class PromptChoiceEvent(_PromptEvent):
  """Checks that the prompt choice event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROMPT_CHOICE

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_prompt_choice')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        collections.OrderedDict(),
        'expect_prompt_choice',
        was_missing=True,
        location=location)


class PromptResponseEvent(_PromptEvent):
  """Checks that the prompt response event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROMPT_RESPONSE

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_prompt_response')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        collections.OrderedDict(),
        'expect_prompt_response',
        was_missing=True,
        location=location)


class EventType(enum.Enum):
  """Describes the set of events we can handle as part of a scenario."""
  STDOUT = (StdoutEvent, assertions.updates.Mode.RESULT, None, False)
  STDERR = (StderrEvent, assertions.updates.Mode.UX, None, False)
  USER_INPUT = (UserInputEvent, assertions.updates.Mode.UX, None, False)
  API_CALL = (ApiCallEvent, assertions.updates.Mode.API_REQUESTS, None, False)
  FILE_WRITTEN = (FileWrittenEvent, assertions.updates.Mode.RESULT, None, None)
  EXIT = (ExitEvent, assertions.updates.Mode.RESULT, None, False)
  PROGRESS_BAR = (ProgressBarEvent, assertions.updates.Mode.UX,
                  console_io.UXElementType.PROGRESS_BAR, False)
  PROGRESS_TRACKER = (ProgressTrackerEvent, assertions.updates.Mode.UX,
                      console_io.UXElementType.PROGRESS_TRACKER, False)
  STAGED_PROGRESS_TRACKER = (StagedProgressTrackerEvent,
                             assertions.updates.Mode.UX,
                             console_io.UXElementType.STAGED_PROGRESS_TRACKER,
                             False)
  PROMPT_CONTINUE = (PromptContinueEvent, assertions.updates.Mode.UX,
                     console_io.UXElementType.PROMPT_CONTINUE, True)
  PROMPT_CHOICE = (PromptChoiceEvent, assertions.updates.Mode.UX,
                   console_io.UXElementType.PROMPT_CHOICE, True)
  PROMPT_RESPONSE = (PromptResponseEvent, assertions.updates.Mode.UX,
                     console_io.UXElementType.PROMPT_RESPONSE, True)

  def __init__(self, impl, update_mode, ux_element_type, has_user_input):
    self._impl = impl
    self._update_mode = update_mode
    self._ux_element_type = ux_element_type
    self._has_user_input = has_user_input

  def Impl(self):
    return self._impl

  def UpdateMode(self):
    return self._update_mode

  def UXElementAttributes(self):
    return self._ux_element_type.GetDataFields()

  def HasUserInput(self):
    return self._has_user_input

  def __str__(self):
    return self.name.lower()
