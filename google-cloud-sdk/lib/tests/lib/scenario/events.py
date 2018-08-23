# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
from collections import OrderedDict
import json
import enum


from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import http_encoding
from tests.lib.scenario import assertions
from tests.lib.scenario import updates

import httplib2
import six
from six.moves import urllib


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


class _SingleValueEvent(six.with_metaclass(abc.ABCMeta, Event)):
  """Base class for all event types that just check a single value."""

  @classmethod
  def _Build(cls, backing_data, field, default=None, was_missing=False,
             location=None):
    value = backing_data.get(field, default)
    if value is None:
      value = ''
    update_context = updates.Context(
        backing_data, field, cls.EventType().UpdateMode(),
        was_missing=was_missing, location=location)
    return cls(update_context, assertions.EqualsAssertion(value))

  def __init__(self, update_context, assertion):
    super(_SingleValueEvent, self).__init__(update_context)
    self._assertion = assertion

  def Handle(self, value):
    return self._assertion.Check(self._update_context, value)


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
        OrderedDict(), 'expect_stdout', was_missing=True, location=location)


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
        OrderedDict(), 'expect_stderr', was_missing=True, location=location)


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
        updates.Context(
            backing_data, 'expect_exit', cls.EventType().UpdateMode()),
        assertions.EqualsAssertion(code),
        assertions.EqualsAssertion(message) if has_message else None
    )

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context(
        {'expect_exit': OrderedDict()}, 'expect_exit',
        cls.EventType().UpdateMode(), was_missing=True, location=location)
    return cls(update_context,
               assertions.EqualsAssertion(None),
               assertions.EqualsAssertion(None))

  def __init__(self, update_context, code_assertion, message_assertion):
    super(ExitEvent, self).__init__(update_context)
    self._code_assertion = code_assertion
    self._message_assertion = message_assertion

  def Handle(self, exc):
    code = getattr(exc, 'exit_code', 1) if exc else 0
    message = six.text_type(exc) if exc else None
    failures = []
    failures.extend(
        self._code_assertion.Check(self._update_context.ForKey('code'), code))
    if self._message_assertion:
      failures.extend(
          self._message_assertion.Check(
              self._update_context.ForKey('message'), message))
    return failures


class UserInputEvent(Event):
  """Provides user input to a prompt."""

  @classmethod
  def EventType(cls):
    return EventType.USER_INPUT

  @classmethod
  def FromData(cls, backing_data):
    return cls(
        updates.Context(
            backing_data, 'user_input', cls.EventType().UpdateMode()),
        backing_data.get('user_input') or [])

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context(
        OrderedDict(), 'user_input', cls.EventType().UpdateMode(),
        was_missing=True, location=location)
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
    return [assertions.Failure.ForGeneric(
        self._update_context, title='Missing user input event')]


class FileWrittenEvent(Event):
  """Checks that a given file was written with the given contents."""

  @classmethod
  def EventType(cls):
    return EventType.FILE_WRITTEN

  @classmethod
  def FromData(cls, backing_data):
    file_data = backing_data['expect_file_written']
    update_context = updates.Context(
        backing_data, 'expect_file_written', cls.EventType().UpdateMode())

    path_assertion = assertions.EqualsAssertion(file_data.get('path'))
    contents_assertion = _CreateAssertion(file_data.get('contents'))
    binary_contents = file_data.get('binary_contents')
    if (binary_contents is not None and
        isinstance(binary_contents, six.text_type)):
      binary_contents = binary_contents.encode('utf8')
    binary_contents_assertion = _CreateAssertion(binary_contents)
    is_private_assertion = assertions.EqualsAssertion(
        file_data.get('is_private') or False)

    return cls(update_context, path_assertion, contents_assertion,
               binary_contents_assertion, is_private_assertion)

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context(
        {'expect_file_written': OrderedDict()}, 'expect_file_written',
        cls.EventType().UpdateMode(), was_missing=True, location=location)
    return cls(update_context,
               assertions.EqualsAssertion(None),
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


def _CreateAssertion(value):
  """Adds an additional assertion to a DictAssertion for a given key."""
  if not isinstance(value, dict):
    return assertions.EqualsAssertion(value)
  elif 'equals' in value:
    return assertions.EqualsAssertion(value['equals'])
  elif 'matches' in value:
    return assertions.MatchesAssertion(value['matches'])
  elif 'is_none' in value:
    return assertions.IsNoneAssertion(value['is_none'])
  elif 'in' in value:
    return assertions.InAssertion(value['in'])
  # This should never happen for things that pass schema validation.
  raise ValueError('Assertion type is invalid.')


class ApiCallEvent(Event):
  """Checks that the API request matches an expected request."""

  @classmethod
  def EventType(cls):
    return EventType.API_CALL

  @classmethod
  def FromData(cls, backing_data):
    """Builds a request event handler from yaml data."""
    call_data = backing_data['api_call']
    update_context = updates.Context(
        backing_data, 'api_call', cls.EventType().UpdateMode())

    is_repeatable_assertion = assertions.EqualsAssertion(
        call_data.get('repeatable', False))
    request_assertion = HTTPAssertion.ForRequest(call_data['expect_request'])
    response_assertion = HTTPAssertion.ForResponse(
        call_data.get('expect_response'))

    response_payload_data = call_data.get('return_response') or OrderedDict()
    response_payload = HTTPResponsePayload(
        headers=response_payload_data.get('headers', {'status': '200'}),
        payload=response_payload_data.get('body', ''))

    return cls(update_context, is_repeatable_assertion, request_assertion,
               response_assertion, response_payload)

  @classmethod
  def ForMissing(cls, location):
    backing_data = {
        'api_call': OrderedDict([
            ('expect_request',
             OrderedDict([('uri', ''),
                          ('method', ''),
                          ('headers', {}),
                          ('body', {'text': None, 'json': {}})])),
            ('return_response',
             OrderedDict([('headers', {'status': '200'}),
                          ('body', None)]))
        ])
    }
    update_context = updates.Context(
        backing_data, 'api_call', cls.EventType().UpdateMode(),
        was_missing=True, location=location)
    response = backing_data['api_call']['return_response']

    return cls(
        update_context,
        assertions.EqualsAssertion(False),
        HTTPAssertion(
            'expect_request',
            assertions.EqualsAssertion(assertions.MISSING_VALUE),
            assertions.EqualsAssertion(assertions.MISSING_VALUE),
            assertions.DictAssertion(),
            assertions.JsonAssertion().Matches('', assertions.MISSING_VALUE),
            assertions.EqualsAssertion(assertions.MISSING_VALUE),
            False,
            {}),
        None,
        HTTPResponsePayload(headers=response['headers'],
                            payload=response['body']))

  def __init__(self, update_context, is_repeatable_assertion, request_assertion,
               response_assertion, response_payload):
    super(ApiCallEvent, self).__init__(update_context)
    self._is_repeatable_assertion = is_repeatable_assertion
    self._request_assertion = request_assertion
    self._response_assertion = response_assertion
    self._response_payload = response_payload

  def CheckRepeatable(self, was_repeated):
    return self._is_repeatable_assertion.Check(
        self._update_context.ForKey('repeatable'), was_repeated)

  def Handle(self, uri, method, headers, body):
    return self._request_assertion.Check(
        self._update_context, uri, method, headers, body)

  def HandleResponse(self, headers, body, resource_ref_resolver):
    if self._response_assertion:
      self._response_assertion.ExtractReferences(resource_ref_resolver, body)
      return self._response_assertion.Check(
          self._update_context, None, None, headers, body.decode('utf8'))
    else:
      return self._GenerateOperationsRefExtraction(resource_ref_resolver, body)

  def _GenerateOperationsRefExtraction(self, resource_ref_resolver,
                                       response_body):
    """Generates an extract_references block if it looks like an operation.

    If the body has a kind attribute that indicates an operation, this will
    update the scenario spec to include a default extract_references block
    to pull out the operation id. This should only be called if an
    expect_response block is not already present.

    Args:
      resource_ref_resolver: ResourceReferenceResolver, The resolver to track
        the extracted references.
      response_body: str, The body of the response from the server.

    Returns:
      [Failure], The failures to update the spec and inject the new block or [].
    """
    def _UpdateHook(context, actual):
      """Custom update hook since this is not a real assertion failure."""
      del actual
      data = context.BackingData()
      data['expect_response'] = OrderedDict([
          ('extract_references',
           [OrderedDict([('field', 'name'), ('reference', 'operation')])]),
          ('body', {'json': {}})])
      return True

    try:
      json_data = json.loads(response_body)
    except (ValueError, TypeError):
      # Not a json object.
      return []
    if not json_data.get('kind', '').endswith('#operation'):
      # not an operation response.
      return []
    op_id = json_data.get('name', None)
    if (not op_id or
        resource_ref_resolver.IsExtractedIdCurrent('operation', op_id)):
      # Couldn't find the operation id in the normal place or the id has
      # already been extracted in a prevent event.
      return []

    resource_ref_resolver.SetExtractedId('operation', op_id)
    update_context = self._update_context.ForKey(
        'expect_response',
        update_mode=assertions.updates.Mode.API_REQUESTS,
        custom_update_hook=_UpdateHook)
    return [assertions.Failure.ForGeneric(
        update_context, 'Adding reference extraction for Operations response')]

  def GetResponsePayload(self):
    return self._response_payload.Respond()

  def UpdateResponsePayload(self, headers, body):
    return self._response_payload.Update(self._update_context, headers, body)


class HTTPResponsePayload(object):
  """Encapsulates the data of a response payload."""

  HEADER_BLACKLIST_PREFIX = {
      'x-google-', 'alt-svc', '-content-encoding', 'date', 'content-location',
      'expires', 'server', 'transfer-encoding', 'vary',
      'x-content-type-options', 'x-frame-options', 'x-xss-protection',
  }

  def __init__(self, headers, payload):
    self._headers = headers
    if isinstance(payload, dict):
      payload = json.dumps(payload)
    payload = payload or ''
    self._payload = http_encoding.Encode(payload)

  def _SaveHeader(self, header):
    for prefix in HTTPResponsePayload.HEADER_BLACKLIST_PREFIX:
      if header.startswith(prefix):
        return False
    return True

  def Respond(self):
    return (httplib2.Response(self._headers), self._payload)

  def Update(self, context, headers, body):
    """Updates the canned response data with real API response data."""

    def _ResponseUpdateHook(context, actual):
      """Custom update hook since this is not a real assertion failure."""
      data = context.BackingData()
      h, b = actual

      try:
        b = json.loads(b, object_pairs_hook=OrderedDict)
      except (ValueError, TypeError):
        # Not a json object.
        pass

      data['return_response']['headers'] = OrderedDict(
          (key, value) for key, value in sorted(six.iteritems(h))
          if self._SaveHeader(key))
      data['return_response']['body'] = b
      return True

    update_context = context.ForKey(
        'return_response',
        update_mode=assertions.updates.Mode.API_RESPONSE_PAYLOADS,
        custom_update_hook=_ResponseUpdateHook)
    return [assertions.Failure.ForGeneric(
        update_context, 'API Response Payload', (headers, body.decode('utf8')))]


class HTTPAssertion(object):
  """Holds all the component assertions of an API request or response assertion.
  """

  @classmethod
  def ForRequest(cls, http_data):
    uri_assertion = assertions.EqualsAssertion(http_data.get('uri', ''))
    method_assertion = assertions.EqualsAssertion(
        http_data.get('method', 'GET'))
    return cls._ForCommon('expect_request', http_data, uri_assertion,
                          method_assertion, {})

  @classmethod
  def ForResponse(cls, http_data):
    if not http_data:
      return None
    extract_references = {x['field']: x['reference']
                          for x in http_data.get('extract_references', [])}
    return cls._ForCommon(
        'expect_response', http_data, None, None, extract_references)

  @classmethod
  def _ForCommon(cls, mode, http_data, uri_assertion, method_assertion,
                 extract_references):
    """Builder for the attributes applicable to both requests and responses."""
    header_assertion = assertions.DictAssertion()
    for header, value in six.iteritems(http_data.get('headers', {})):
      header_assertion.AddAssertion(header, _CreateAssertion(value))

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
        payload_text_assertion = _CreateAssertion(body_data['text'])
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

    return cls(mode, uri_assertion, method_assertion, header_assertion,
               payload_json_assertion, payload_text_assertion, body_present,
               extract_references)

  def __init__(self, mode, uri_assertion, method_assertion,
               headers_assertion, payload_json_assertion,
               payload_text_assertion, body_present, extract_references):
    self._mode = mode
    self._uri_assertion = uri_assertion
    self._method_assertion = method_assertion
    self._headers_assertion = headers_assertion
    self._payload_json_assertion = payload_json_assertion
    self._payload_text_assertion = payload_text_assertion
    self._body_present = body_present
    self._extract_references = extract_references

  def _OrderedUri(self, uri):
    """Sorts URI params to ensure they are always processed in same order."""
    url_parts = urllib.parse.urlsplit(uri)
    params = urllib.parse.parse_qs(url_parts.query)
    ordered_query_params = OrderedDict(sorted(six.iteritems(params)))
    url_parts = list(url_parts)
    # pylint:disable=redundant-keyword-arg, this is valid syntax for this lib
    url_parts[3] = urllib.parse.urlencode(ordered_query_params, doseq=True)
    # pylint:disable=too-many-function-args, This is just bogus.
    return urllib.parse.urlunsplit(url_parts)

  def _Key(self, key):
    return self._mode + '.' + key

  def ExtractReferences(self, resource_ref_resolver, body):
    """Extract any references from an API response.

    If this response assertion has registered references to extract, pull them
    out of the payload data and add them to the resolver for future use.

    Args:
      resource_ref_resolver: ResourceReferenceResolver, the resolver that is
        tracking resource references.
      body: str, The body payload of the response.
    """
    if not self._extract_references:
      return
    json_data = json.loads(body)
    for field, reference in six.iteritems(self._extract_references):
      resource_id = resource_transform.GetKeyValue(json_data, field)
      resource_ref_resolver.SetExtractedId(reference, resource_id)

  def Check(self, context, uri, method, headers, body):
    """Validates that the assertion matches the real data."""
    failures = []

    if self._uri_assertion:
      failures.extend(
          self._uri_assertion.Check(
              context.ForKey(self._Key('uri')), self._OrderedUri(uri)))
    if self._method_assertion:
      failures.extend(
          self._method_assertion.Check(
              context.ForKey(self._Key('method')), method))

    def _Decode(value):
      return (http_encoding.Decode(value) if isinstance(value, six.binary_type)
              else value)
    failures.extend(
        self._headers_assertion.Check(
            context.ForKey(self._Key('headers')),
            {_Decode(h): _Decode(v) for h, v in six.iteritems(headers)}))

    # Don't differentiate between a None body and an empty body. It's the same.
    if not body:
      body = None

    json_data = None
    try:
      json_data = json.loads(body, object_pairs_hook=OrderedDict)
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
    if backing_data.get('body') is None and (body or json_data):
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

    if self._payload_json_assertion:
      failures.extend(
          self._payload_json_assertion.Check(
              context.ForKey(self._Key('body.json'),
                             custom_update_hook=_CleanupHook),
              json_data or None))
    if self._payload_text_assertion:
      failures.extend(
          self._payload_text_assertion.Check(
              context.ForKey(self._Key('body.text'),
                             custom_update_hook=_CleanupHook),
              body))

    return failures


class RepeatableAPICall(object):
  """A class to encapsulate an api_call event and how it was previously used.

  For events that are declared as repeatable, we allow them to be reused
  (instead) of you manually having to repeat the event for each call. This holds
  how the call was used last time, and can only be reused if the new call is
  exactly the same as the previous one.
  """

  def __init__(self, uri, method, body, event, response):
    self._uri = uri
    self._method = method
    self._body = body
    self._event = event
    self._response_body = response[1]
    self._was_repeated = False

  def Matches(self, uri, method, body, response):
    _, response_body = response
    return (self._uri == uri and
            self._method == method and
            self._body == body and
            self._response_body == response_body)

  def Event(self):
    return self._event

  def MarkRepeated(self):
    self._was_repeated = True

  def Check(self):
    return self._event.CheckRepeatable(self._was_repeated)


class _UXEvent(six.with_metaclass(abc.ABCMeta, Event)):
  """A base class for events based on the UX JSON blob."""

  @classmethod
  def _Build(cls, backing_data, field, was_missing=False, location=None):
    ux_event_data = backing_data.setdefault(field, OrderedDict())
    update_context = updates.Context(
        backing_data, field, cls.EventType().UpdateMode(),
        was_missing=was_missing, location=location)

    attr_assertions = OrderedDict()
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
          attribute_assertion.Check(self._update_context.ForKey(attribute),
                                    ux_event_data.get(attribute)))
    return failures


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
    return cls._Build(OrderedDict(), 'expect_progress_bar', was_missing=True,
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
    return cls._Build(OrderedDict(), 'expect_progress_tracker',
                      was_missing=True, location=location)


class _PromptEvent(six.with_metaclass(abc.ABCMeta, _UXEvent)):
  """Base class for UX events that involve a prompt with user input."""

  def __init__(self, update_context, attr_assertions, ux_event_data):
    super(_PromptEvent, self).__init__(
        update_context, attr_assertions, ux_event_data)
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
    return cls._Build(OrderedDict(), 'expect_prompt_continue', was_missing=True,
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
    return cls._Build(OrderedDict(), 'expect_prompt_choice', was_missing=True,
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
  PROMPT_CONTINUE = (PromptContinueEvent, assertions.updates.Mode.UX,
                     console_io.UXElementType.PROMPT_CONTINUE, True)
  PROMPT_CHOICE = (PromptChoiceEvent, assertions.updates.Mode.UX,
                   console_io.UXElementType.PROMPT_CHOICE, True)

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

