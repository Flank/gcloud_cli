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

"""Assertion class for the scenario testing framework."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import json
import os
import re
import sys
import enum

from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import http_encoding

import httplib2
import six


class Error(Exception):
  pass


UPDATE_MODES_ENV_VAR = 'CLOUDSDK_SCENARIO_TESTING_UPDATE_MODE'


class UpdateMode(enum.Enum):
  """Enum representing which assertion categories we are allowed to updated.

  Assertions that are not updatable will be raised as errors.

  Attributes:
    NONE: This value is not actually ever used in the environment, but indicates
      that an update should never trigger.
    RESULT: Update programmatically usable command outputs.
    UX: Update stderr and other UX for the command.
    API_REQUESTS: Update api request assertions to match actual requests.
    API_RESPONSES: Make real api calls and update canned response data.
  """
  NONE = 0
  RESULT = 1
  UX = 2
  API_REQUESTS = 3
  API_RESPONSES = 4

  @classmethod
  def Current(cls):
    """Gets the current set of update modes."""
    modes = encoding.GetEncodedValue(
        os.environ, UPDATE_MODES_ENV_VAR, '').upper().split(',')
    # TODO(b/79161265): This should not be a pytype error.
    return [cls[m] for m in modes if m]  # pytype: disable=not-indexable

  @classmethod
  def MakesApiCalls(cls):
    """True if the update mode requires actually making real API calls."""
    return UpdateMode.API_RESPONSES in UpdateMode.Current()

  def __str__(self):
    return self.name


class UpdateHook(object):
  """A wrapper for an update function and a mode of when it should be triggered.

  An update function takes a single argument which is the actual value and
  updates a golden file to match. The mode describes when the function should
  trigger vs raise an assertion error.
  """

  @classmethod
  def NoOp(cls):
    return cls(lambda _: None, UpdateMode.NONE)

  def __init__(self, func, mode):
    self._func = func
    self._mode = mode

  def Update(self, actual, modes):
    """Triggers the update hook.

    Args:
      actual: The actual value of the assertion.
      modes: [UpdateMode], The update modes that are currently active.

    Returns:
      True if an update was done or False if this assertion should be raised as
      an error.
    """
    if self._mode not in modes:
      return False
    self._func(actual)
    return True


class Context(object):
  """Encapsulates the context of the assertion like line number and update hook.
  """

  @classmethod
  def Empty(cls, custom_update_hook=None):
    return Context(
        None, None, UpdateMode.NONE, custom_update_hook=custom_update_hook)

  def __init__(self, data_dict, field, update_mode, was_missing=False,
               location=None, custom_update_hook=None):
    self._data_dict = data_dict
    self._field = field
    self._update_mode = update_mode
    self._was_missing = was_missing
    self._location = location
    self._custom_update_hook = custom_update_hook

  def WasMissing(self):
    return self._was_missing

  def ForKey(self, key):
    """Get a new assertion Context for a sub-key in this context's dict."""
    if self._data_dict is None:
      return self
    if not key:
      # Attribute path is empty, just return this node.
      return self

    data = self._data_dict[self._field]
    parts = key.split('.')
    for attr in parts[:-1]:
      if attr:
        data = data[attr]

    return Context(data, parts[-1], self._update_mode)

  def Field(self):
    return self._field if self._field is not None else '?'

  def Location(self):
    """"Get the line and column number for the source data for this assertion.

    Returns:
      (str, str), The line and column number of '?', '?' if unknown.
    """
    if self._location:
      return self._location
    if self._data_dict is None:
      return '?', '?'
    lc = getattr(self._data_dict, 'lc', None)
    if not lc:
      return '?', '?'
    if self._field:
      field_location = lc.data[self._field]
      line, col = field_location[0] + 1, field_location[1]
    else:
      line, col = lc.line, lc.col

    return str(line), str(col)

  def UpdateHook(self):
    """Get the update hook for this assertion."""
    if self._custom_update_hook:
      return self._custom_update_hook
    if self._update_mode == UpdateMode.NONE:
      return UpdateHook.NoOp()

    def _Update(actual):
      if actual is None and isinstance(self._data_dict, dict):
        del self._data_dict[self._field]
      else:
        self._data_dict[self._field] = actual

    return UpdateHook(_Update, self._update_mode)


class Failure(object):
  """Encapsulates the error information about a specific assertion failure."""

  @classmethod
  def ForError(cls, msg):
    return cls(Context.Empty(), None, msg)

  @classmethod
  def ForScalar(cls, assertion_context, expected, actual, msg='', e=None):
    return cls._ForAssertion(
        assertion_context=assertion_context, msg=msg, expected=expected,
        actual=actual, e=e)

  @classmethod
  def ForDict(cls, assertion_context, key, expected, actual, msg='', e=None):
    msg = 'in section [{}]: {msg}'.format(assertion_context.Field(), msg=msg)
    return cls._ForAssertion(
        assertion_context=assertion_context.ForKey(key), msg=msg,
        expected=expected, actual=actual, e=e)

  @classmethod
  def _ForAssertion(cls, assertion_context, expected, actual, msg='', e=None):
    """Creates a failure for an assertion error."""
    line, col = assertion_context.Location()
    # TODO(b/78588819): Need much better error messages.
    message = (
        '{title} [Line: {line}, Col: {col}]: For field [{field}]: '
        '{msg}\n'
        '\tExpected: <<<{expected}>>>\n'
        '\tAcutal:   <<<{actual}>>>\n'
        '\tDetails: {e}'.format(
            title=('Missing Assertion' if assertion_context.WasMissing()
                   else 'Assertion Error'),
            line=line, col=col, field=assertion_context.Field(), msg=msg,
            expected=expected, actual=actual, e=e))
    return cls(assertion_context, actual, message)

  def __init__(self, assertion_context, actual, msg=''):
    self.assertion_context = assertion_context
    self.actual = actual
    self._message = msg

  def __str__(self):
    return self._message


class FailureCollector(object):
  """A context manager that collections failures and then handles them.

  Failures will either be updated or raised as assertion errors when the block
  exits.
  """

  def __init__(self, update_modes=None):
    self._failures = []
    self._update_modes = (UpdateMode.Current() if update_modes is None
                          else update_modes)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if not self._failures:
      return

    # Try to do updates instead of failing.
    unhandled = []
    for f in self._failures:
      handled = f.assertion_context.UpdateHook().Update(f.actual,
                                                        self._update_modes)
      if handled:
        sys.__stderr__.write('Updating assertion error: {}\n\n'.format(f))
      else:
        unhandled.append(f)

    # If there are things that could not be updated, error.
    if unhandled:
      # TODO(b/78588819): better error mesage
      raise Error('\n\n'.join(six.text_type(f) for f in unhandled))

  def Add(self, failure):
    self._failures.append(failure)

  def ShouldMakeRequests(self):
    return UpdateMode.API_RESPONSES in self._update_modes


class Assertion(six.with_metaclass(abc.ABCMeta, object)):
  """Base assertion type."""

  ABSENT = object()

  def __init__(self, assertion_context):
    self._assertion_context = assertion_context

  @abc.abstractmethod
  def Check(self, failures, value):
    pass


class ScalarAssertion(Assertion):
  """Asserts that a scalar equals a specific value."""

  def __init__(self, assertion_context, value):
    super(ScalarAssertion, self).__init__(assertion_context)
    self._value = value

  def Check(self, failures, value):
    if self._value != value:
      failures.Add(
          Failure.ForScalar(self._assertion_context, self._value, value))


class ScalarRegexAssertion(Assertion):
  """Asserts that a scalar matches a regular expression."""

  def __init__(self, assertion_context, value_regex):
    super(ScalarRegexAssertion, self).__init__(assertion_context)
    if not value_regex.endswith('$'):
      value_regex += '$'
    self._regex = value_regex

  def Check(self, failures, value):
    if self._regex is not None and not re.match(
        self._regex, value, flags=re.DOTALL):
      failures.Add(
          Failure.ForScalar(self._assertion_context, self._regex, value))


class DictAssertion(Assertion):
  """Asserts that a dictionary has a specific set of keys/values."""

  def __init__(self, assertion_context, is_bytes=True):
    super(DictAssertion, self).__init__(assertion_context)
    self._is_bytes = is_bytes
    self._regexes = {}

  def KeyEquals(self, key, value):
    self.KeyMatches(key, '^{}$'.format(re.escape(value)))
    return self

  def KeyMatches(self, key, value_regex):
    if not value_regex.endswith('$'):
      value_regex += '$'
    self._regexes[key] = value_regex
    return self

  def KeyIsAbsent(self, key):
    self._regexes[key] = Assertion.ABSENT
    return self

  def _Encode(self, value):
    if self._is_bytes:
      return http_encoding.Encode(value)
    return value

  def Check(self, failures, d):
    for header, regex in six.iteritems(self._regexes):
      value = d.get(http_encoding.Encode(header) if self._is_bytes else header)
      value = http_encoding.Decode(value) if self._is_bytes else value
      if value is None:
        if regex is not Assertion.ABSENT:
          failures.Add(
              Failure.ForDict(self._assertion_context, header, regex, value))
      elif regex is Assertion.ABSENT:
        failures.Add(
            Failure.ForDict(self._assertion_context, header, None, value))
      elif not re.match(regex, value):
        failures.Add(
            Failure.ForDict(self._assertion_context, header, regex, value))


class JsonAssertion(Assertion):
  """Asserts that a json object matches a given structure."""

  def __init__(self, assertion_context):
    super(JsonAssertion, self).__init__(assertion_context)
    self._field_structures = {}

  def Matches(self, field, sub_structure):
    self._field_structures[field] = sub_structure
    return self

  def IsAbsent(self, field):
    self._field_structures[field] = Assertion.ABSENT
    return self

  def Check(self, failures, value):
    json_body = json.loads(value) if value else None
    for field, expected_sub_structure in six.iteritems(self._field_structures):
      if expected_sub_structure is Assertion.ABSENT:
        try:
          # TODO(b/78588819): This is wrong for now. GetSubStrucutre() needs to
          # be able to reliably determine if the attribute is there or not.
          # Right now we don't really know why it failed.
          actual = self._GetSubStructure(json_body, field)
          failures.Add(
              Failure.ForDict(self._assertion_context, field, None, actual))
        except AttributeError:
          # TODO(b/78588819): Actually handle this correctly.
          pass
      else:
        try:
          node = self._GetSubStructure(json_body, field)
          self._CheckNode(failures, field, node, expected_sub_structure)
        except AttributeError as e:
          failures.Add(
              Failure.ForDict(
                  self._assertion_context, field, 'present', None,
                  msg='Attribute not found', e=e))

  def _CheckNode(self, failures, field, node, expected):
    # TODO(b/78588819): There is a lot of duplication in here. Needs to be
    # completely refactored.
    if isinstance(expected, dict):
      if not isinstance(node, dict):
        failures.Add(
            Failure.ForDict(self._assertion_context, field, 'type(dict)', node))
      for key, value in six.iteritems(expected):
        self._CheckNode(failures, field, node.get(key), value)
    elif isinstance(expected, list):
      if not isinstance(node, list):
        failures.Add(
            Failure.ForDict(self._assertion_context, field, 'type(list)', node))
      if len(expected) != len(node):
        failures.Add(
            Failure.ForDict(self._assertion_context, field, len(expected),
                            len(node)))
      for x, item in enumerate(expected):
        self._CheckNode(failures, field, node[x], item)
    elif isinstance(expected, six.string_types):
      if not isinstance(node, six.string_types):
        failures.Add(
            Failure.ForDict(
                self._assertion_context, field, 'type(string)', node))
      if not re.match(expected, node):
        failures.Add(
            Failure.ForDict(self._assertion_context, field, expected, node))
    else:
      if node != expected:
        failures.Add(
            Failure.ForDict(self._assertion_context, field, expected, node))

  def _GetSubStructure(self, d, attr_path):
    """Gets attributes and sub-attributes out of an object.

    Args:
      d: {}, The dictionary.
      attr_path: str, The dotted path of attributes to extract.

    Raises:
      AttributeError: If the attribute doesn't exist on the object.

    Returns:
      The desired attribute or None if any of the parent attributes were
      None.
    """
    # TODO(b/78588819): This should be totally rewritten.
    if not attr_path:
      return d
    for attr in attr_path.split('.'):
      if not attr:
        continue
      if d is not None:
        if not isinstance(d, dict):
          raise AttributeError(
              'Attribute path [{}] cannot be found on list'.format(attr_path))
        try:
          d = d[attr]
        except KeyError:
          raise AttributeError(
              'Attribute path [{}] not found on type [{}]'.format(
                  attr_path, d))
      else:
        raise AttributeError(
            'Attribute path [{}] not found on type [{}]'.format(
                attr_path, d))
    return d


class ResponsePayloadAssertion(Assertion):
  """Asserts that the response payload equals reality."""

  def __init__(self, assertion_context, headers=None, payload=None):
    super(ResponsePayloadAssertion, self).__init__(assertion_context)
    self._headers = {h: http_encoding.Encode(v)
                     for h, v in six.iteritems(headers)} if headers else {}
    if payload is None:
      payload = ''
    if isinstance(payload, dict):
      payload = json.dumps(payload)
    self._payload = http_encoding.Encode(payload)

  def Check(self, failures, value):
    response, payload = value
    # TODO(b/78588819): This is not actually asserting anything, it just always
    # updates.
    failures.Add(
        Failure.ForScalar(
            self._assertion_context, (self._headers, self._payload),
            (response, payload)))

  def Respond(self):
    return (httplib2.Response(self._headers), self._payload)
