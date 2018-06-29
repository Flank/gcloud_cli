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
import re
import sys

from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import http_encoding
from tests.lib.scenario import updates

import httplib2
import six


class Error(Exception):

  def __init__(self, failures):
    # TODO(b/78588819): better error message
    super(Error, self).__init__('\n\n'.join(six.text_type(f) for f in failures))
    self.failures = failures


class Failure(object):
  """Encapsulates the error information about a specific assertion failure."""

  @classmethod
  def ForGeneric(cls, update_context, title):
    msg = cls._TitleLine(update_context, title=title)
    return cls(update_context, None, msg)

  @classmethod
  def ForExtraAssertion(cls, update_context):
    """A failure for when you gave an assertion that didn't match anything."""
    msg = cls._TitleLine(update_context, 'Extra Assertion')
    return cls(update_context, None, msg)

  @classmethod
  def ForScalar(cls, update_context, expected, actual, msg=None, e=None):
    """A failure for when a scalar value didn't match."""
    return cls._ForAssertion(
        update_context=update_context, msg=msg, expected=expected,
        actual=actual, e=e)

  @classmethod
  def ForDict(cls, update_context, key, expected, actual, msg=None, e=None,
              key_as_path=True):
    """A failure for when a key/value in a dictionary didn't match."""
    return cls._ForAssertion(
        update_context=update_context.ForKey(key, key_as_path=key_as_path),
        expected=expected, actual=actual, msg=msg, e=e)

  @classmethod
  def _ForAssertion(cls, update_context, expected, actual, msg=None, e=None):
    """Creates a failure for an assertion error."""
    # TODO(b/78588819): Need much better error messages.
    title = ('Missing Assertion' if update_context.WasMissing()
             else 'Assertion Error')
    message = (
        '{title}\n'
        '\tExpected: {expected}\n'
        '\tActual:   {actual}\n'
        '\tDetails: {e}'.format(
            title=cls._TitleLine(update_context, title, msg=msg),
            expected=cls._FormatValue(expected),
            actual=cls._FormatValue(actual), e=e))
    return cls(update_context, actual, message)

  @classmethod
  def _TitleLine(cls, update_context, title, msg=None):
    line, col = update_context.Location()
    section = update_context.Section()
    return (
        '{title} - [Line: {line}, Col: {col}] - [Field: {section}{field}]{msg}'
        .format(
            title=title,
            line=line, col=col,
            section=(section + '.') if section else '',
            field=update_context.Field(),
            msg=(' - ' + msg) if msg else ''))

  @classmethod
  def _FormatValue(cls, value):
    if value is None:
      return 'None'
    return '<<<{}>>>'.format(value)

  def __init__(self, update_context, actual, msg=''):
    self._update_context = update_context
    self._actual = actual
    self._message = msg

  def Update(self, update_modes):
    return self._update_context.Update(self._actual, update_modes)

  def __str__(self):
    return self._message


class FailureCollector(object):
  """A context manager that collects failures and then handles them at the end.

  When the block exists, each failure that was generated gets processed.
  Depending on the active update modes, failures may be updated and suppressed.
  If there are any failures that could not be updated, a single exception is
  raised with all the failure messages.
  """

  def __init__(self, update_modes=None):
    self._failures = []
    self._update_modes = (
        updates.Mode.Current() if update_modes is None else update_modes)

  def ShouldMakeRequests(self):
    return updates.Mode.API_RESPONSES in self._update_modes

  def Add(self, failure):
    self._failures.append(failure)

  def AddAll(self, failures):
    self._failures.extend(failures)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if not self._failures:
      return

    # Try to do updates instead of failing.
    unhandled = []
    for f in self._failures:
      if f.Update(self._update_modes):
        sys.__stderr__.write('Updating assertion error: {}\n\n'.format(f))
      else:
        unhandled.append(f)

    # If there are things that could not be updated, error.
    if unhandled:
      # TODO(b/78588819): better error message
      raise Error(unhandled)


class Assertion(six.with_metaclass(abc.ABCMeta, object)):
  """Base assertion type."""

  ABSENT = object()

  @abc.abstractmethod
  def Check(self, context, value):
    """Check the assertion against an actual value.

    Args:
      context: updates.Context, The context associated with this assertion
        for update purposes.
      value: The actual value of the data.

    Returns:
       [Failure], A list of failures for this assertion or [] if everything
       succeeded.
    """
    return []


class EqualsAssertion(Assertion):
  """Asserts that a scalar equals a specific value."""

  def __init__(self, value):
    self._value = value

  def Check(self, context, value):
    if self._value != value:
      return [Failure.ForScalar(context, self._value, value)]
    return []


class MatchesAssertion(Assertion):
  """Asserts that a scalar matches a regular expression."""

  def __init__(self, value_regex):
    if not value_regex.endswith('$'):
      value_regex += '$'
    self._regex = value_regex

  def Check(self, context, value):
    if not value or not re.match(self._regex, value, flags=re.DOTALL):
      return [Failure.ForScalar(context, self._regex, value)]
    return []


class IsNoneAssertion(Assertion):
  """Asserts that a scalar value is or is not None."""

  def __init__(self, is_none=True):
    self._is_none = is_none

  def Check(self, context, value):
    if (value is None) != self._is_none:
      return [Failure.ForScalar(
          context, 'Is None: {}'.format(self._is_none), value)]
    return []


class InAssertion(Assertion):
  """Asserts that a scalar value is one of a set of items"""

  def __init__(self, items):
    self._items = items

  def Check(self, context, value):
    for i in self._items:
      if i == value:
        break
    else:
      return [Failure.ForScalar(context, 'In: {}'.format(self._items), value)]
    return []


class DictAssertion(Assertion):
  """Asserts that a dictionary has a specific set of keys/values."""

  def __init__(self):
    self._assertions = {}

  def Equals(self, key, value):
    self._assertions[key] = EqualsAssertion(value)
    return self

  def Matches(self, key, value_regex):
    self._assertions[key] = MatchesAssertion(value_regex)
    return self

  def IsNone(self, key, is_none=True):
    self._assertions[key] = IsNoneAssertion(is_none)
    return self

  def In(self, key, items):
    self._assertions[key] = InAssertion(items)
    return self

  def Check(self, context, d):
    failures = []
    for header, assertion in six.iteritems(self._assertions):
      value = d.get(header)
      failures.extend(assertion.Check(context.ForKey(header), value))
    return failures


class JsonAssertion(Assertion):
  """Asserts that a json object matches a given structure."""

  def __init__(self):
    self._field_structures = {}

  def Matches(self, field, sub_structure):
    self._field_structures[field] = sub_structure
    return self

  def IsAbsent(self, field):
    self._field_structures[field] = Assertion.ABSENT
    return self

  def Check(self, context, value):
    failures = []
    json_body = json.loads(value) if value else None
    for field, expected_sub_structure in six.iteritems(self._field_structures):
      if expected_sub_structure is Assertion.ABSENT:
        try:
          actual = self._GetJsonValueForKey(json_body, field)
          failures.append(Failure.ForDict(context, field, None, actual))
        except AttributeError:
          # TODO(b/78588819): Actually handle this correctly.
          pass
      else:
        try:
          node = self._GetJsonValueForKey(json_body, field)
          failures.extend(
              self._CheckNode(context, field, node, expected_sub_structure))
        except AttributeError as e:
          failures.append(Failure.ForDict(
              context, field, 'present', None, msg='Attribute not found', e=e,
              key_as_path=False))
    return failures

  def _CheckNode(self, context, field, node, expected):
    # TODO(b/78588819): There is a lot of duplication in here. Needs to be
    # completely refactored.
    if isinstance(expected, dict):
      return self._CheckDictValue(context, field, node, expected)
    elif isinstance(expected, list):
      return self._CheckListValue(context, field, node, expected)
    elif isinstance(expected, six.string_types):
      return self._CheckScalarValue(context, field, node, expected)
    else:  # If not list or Scalar or Dict, do absolute comparison
      if node != expected:
        return [Failure.ForDict(context, field, expected, node,
                                key_as_path=False)]
      return []

  def _CheckScalarValue(self, context, field, actual, expected):
    """Validate actual scalar value against expected."""
    if not isinstance(actual, six.string_types):
      return [Failure.ForDict(context, field, 'type(string)', actual,
                              msg='Expected type(string).',
                              key_as_path=False)]
    if not re.match(expected, actual):
      return [Failure.ForDict(context, field, expected, actual,
                              key_as_path=False)]
    return []

  def _CheckListValue(self, context, field, actual, expected):
    """Validate actual list value against expected."""
    if not isinstance(actual, list):
      return [Failure.ForDict(context, field, 'type(list)', actual,
                              msg='Expected type(list).',
                              key_as_path=False)]
    if len(expected) != len(actual):
      return [Failure.ForDict(context, field, len(expected), len(actual),
                              msg='List are different sizes.',
                              key_as_path=False)]
    failures = []
    for x, item in enumerate(expected):
      failures.extend(self._CheckNode(context, field, actual[x], item))
    return failures

  def _CheckDictValue(self, context, field, actual, expected):
    """Validate actual dict value against expected."""
    if not isinstance(actual, dict):
      return [Failure.ForDict(context, field, 'type(dict)', actual,
                              msg='Expected type(dict).',
                              key_as_path=False)]
    failures = []
    for key, value in six.iteritems(expected):
      failures.extend(self._CheckNode(context, field, actual.get(key), value))
    return failures

  def _GetJsonValueForKey(self, json_object, key_path):
    """Extracts the value from a Json like object for a given key.

    Uses core.resource filter expressions to identify object sub-structure to be
    returned. If path is empty returns the entire json_object.

    Args:
      json_object: {}, The json object.
      key_path: str, The dotted path of attributes to extract.

    Raises:
      AttributeError: If the attribute doesn't exist on the object.

    Returns:
      The desired attribute or None if any of the parent attributes were
      None.
    """
    if not key_path:
      return json_object

    value = resource_transform.GetKeyValue(json_object, key_path,
                                           undefined=Assertion.ABSENT)
    if value is Assertion.ABSENT:
      raise AttributeError(
          'Attribute path [{}] not found on type [{}]'.format(key_path,
                                                              json_object))

    return value


class ResponsePayloadAssertion(Assertion):
  """Asserts that the response payload equals reality."""

  def __init__(self, headers=None, payload=None):
    self._headers = {h: http_encoding.Encode(v)
                     for h, v in six.iteritems(headers)} if headers else {}
    if payload is None:
      payload = ''
    if isinstance(payload, dict):
      payload = json.dumps(payload)
    self._payload = http_encoding.Encode(payload)

  def Check(self, context, value):
    response, payload = value
    # TODO(b/78588819): This is not actually asserting anything, it just always
    # updates.
    return [Failure.ForScalar(
        context, (self._headers, self._payload), (response, payload))]

  def Respond(self):
    return (httplib2.Response(self._headers), self._payload)
