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

"""Code that manages updates to the schema based on assertion failures."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import enum

from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import encoding


# This can be set by external tools running scenario tests to trigger updates.
# It is a comma separated list of the below enums.
UPDATE_MODES_ENV_VAR = 'CLOUDSDK_SCENARIO_TESTING_UPDATE_MODE'


class Error(Exception):
  """Base error for the module."""
  pass


class Mode(enum.Enum):
  """Enum representing which assertion categories we are allowed to updated.

  Assertions that are not updatable will be raised as errors.

  Attributes:
    NONE: This value is not actually ever used in the environment, but indicates
      that an update should never trigger.
    RESULT: Update programmatically usable command outputs.
    UX: Update stderr and other UX for the command.
    API_REQUESTS: Update api request and response assertions to match actual
      requests.
    API_RESPONSE_PAYLOADS: Make real api calls and update canned response data.
  """
  NONE = 0
  RESULT = 1
  UX = 2
  API_REQUESTS = 3
  API_RESPONSE_PAYLOADS = 4

  @classmethod
  def FromEnv(cls):
    """Gets the current set of update modes."""
    modes = {m for m in encoding.GetEncodedValue(
        os.environ, UPDATE_MODES_ENV_VAR, '').upper().split(' ') if m}
    if 'ALL' in modes:
      return Mode._All()
    # TODO(b/79161265): This should not be a pytype error.
    members = set(cls.__members__)
    unknown = modes - members
    if unknown:
      raise Error(
          'Unknown update mode values: [{}]. '
          'Valid values are: [{}]'
          .format(', '.join(unknown), ', '.join(m.name for m in cls._All())))
    # pytype: disable=not-indexable
    return [cls[m] for m in modes]

  @classmethod
  def _All(cls):
    return [cls.RESULT, cls.UX, cls.API_REQUESTS, cls.API_RESPONSE_PAYLOADS]

  def __str__(self):
    return self.name


class Context(object):
  """Encapsulates the context of how to perform an update."""

  @classmethod
  def Empty(cls, custom_update_hook=None):
    return cls(None, None, Mode.NONE, custom_update_hook=custom_update_hook)

  def __init__(self, data_dict, field, update_mode, section=None,
               was_missing=False, location=None, custom_update_hook=None):
    """Creates an update context.

    A context stores the backing data for an assertion that can be updated
    if the assertion is invalid. The context stores the dictionary that the
    field to be updated lives in (so that if the field shouldn't exist at all,
    it can be deleted).

    Args:
      data_dict: The dictionary containing the backing data that can be
        updated.
      field: str, The name of the field that this context is for.
      update_mode: Mode, The mode that must be enabled for an update to trigger
        on this field.
      section: str, The field name of the parent if it is known. This can be
        used for additional error reporting.
      was_missing: bool, True if this assertion was missing originally and was
        added automatically. These blank assertions will fail like normal
        assertions, but we want to show a different message.
      location: (str, str), A tuple of the line and column number of where
        the field lives in the original file. If None, we attempt to extract
        it from the data_dict (if the data contains line numbers from the
        YAML rount trip parser).
      custom_update_hook: f(Context, object), A custom function to use to do
        the update. It takes a reference to this context and the actual value
        found by the assertion failure.
    """
    self._data_dict = data_dict
    self._field = field
    self._update_mode = update_mode
    self._section = section
    self._was_missing = was_missing
    self._location = location
    self._custom_update_hook = custom_update_hook

  def BackingData(self):
    return self._data_dict

  def WasMissing(self):
    return self._was_missing

  # TODO: (b/80470220) Fix Key_as_path use case.
  def ForKey(self, key, update_mode=None, custom_update_hook=None,
             key_as_path=True):
    """Get a new assertion Context for a sub-key in this context's dict.

    Args:
      key: str, A dotted attribute path for a sub key (ex a.b.c).
      update_mode: Mode, A new update mode (if different than the parent field).
      custom_update_hook: A new custom hook (if different than the parent
        field).
      key_as_path: bool, If true (default) key will be interpreted as '.'
        separated path. If false, it will be parsed as a string.

    Returns:
      Context, The new context.
    """
    if self._data_dict is None:
      return self
    # pylint: disable=g-explicit-bool-comparison, No, key can be 0 which should
    # not trigger this.
    if key is None or key == '':
      # Attribute path is empty, just return this node.
      return self

    last_section = self._field
    data = self._data_dict[self._field]
    last_known_location = self.Location()
    if key_as_path:
      parts = key.split('.')
      for attr in parts[:-1]:
        if attr:
          last_section = attr
          next_location = Location(data, attr)
          if next_location != ('?', '?'):
            last_known_location = next_location
          data = data.get(attr)
      new_field = parts[-1]
    else:
      new_field = key

    location = self._location
    if not location and Location(data, new_field) == ('?', '?'):
      location = last_known_location

    return Context(
        data, new_field, update_mode or self._update_mode, last_section,
        self._was_missing, location,
        custom_update_hook or self._custom_update_hook)

  def Field(self):
    return self._field if self._field is not None else '?'

  def Section(self):
    return self._section

  def Location(self):
    """"Get the line and column number for the source data for this assertion.

    Returns:
      (str, str), The line and column number of '?', '?' if unknown.
    """
    if self._location:
      return self._location
    return Location(self._data_dict, self._field)

  def Update(self, actual, modes):
    """Triggers the update hook.

    Args:
      actual: The actual value of the assertion.
      modes: [UpdateMode], The update modes that are currently active.

    Returns:
      True if an update was done or False if this assertion should be raised as
      an error.
    """
    if self._update_mode not in modes:
      # We are not allowed to update given the current modes.
      return False
    if self._custom_update_hook:
      result = self._custom_update_hook(self, actual)
    else:
      result = self.StandardUpdateHook(actual)
    # This conversion operates on either a dict or a list. We want to change
    # as little of the formatting as possible, so we convert the immediately
    # enclosing dict of the field that is being changed.
    yaml.convert_to_block_text(self._data_dict)
    return result

  def StandardUpdateHook(self, actual):
    """Updates the backing data based on the correct actual value."""
    if actual is None and yaml.dict_like(self._data_dict):
      if self._field in self._data_dict:
        del self._data_dict[self._field]
    else:
      self._data_dict[self._field] = actual
    return True


def Location(data_dict, field):
  """Extract line and column numbers from a ruamel parsed dictionary."""
  if data_dict is None:
    return '?', '?'
  lc = getattr(data_dict, 'lc', None)
  if not lc:
    return '?', '?'
  if field and lc.data and field in lc.data:
    field_location = lc.data[field]
    line, col = field_location[0] + 1, field_location[1]
  else:
    line, col = lc.line, lc.col

  return str(line), str(col)
