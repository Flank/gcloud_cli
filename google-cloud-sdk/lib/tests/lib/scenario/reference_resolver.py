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

"""Parses the scenario yaml test file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
import re

from googlecloudsdk.core import yaml
from tests.lib.scenario import assertions
from tests.lib.scenario import updates

import six


class Error(Exception):
  """Base exception for the module."""
  pass


class UnknownReferenceError(Error):
  """Error for when a reference doesn't exist."""
  pass


class ResourceReferenceResolver(object):
  """Tracks and resolves generated, extracted, and defined resource references.

  For REMOTE tests, we cannot use hardcoded names for resources because they
  will collide. The generate_resource_id action allows you to generate a unique
  resource id for a given test run and name it with an alias that you use to
  refer to it in your scenario file. This class keeps track of the mappings
  of reference to generated id.

  The extract_references directive in the expect_response section of an api_call
  allows you to capture a generated resource id (like an operation) that you
  need to use later. This class also tracks those references so they can be
  resolved.

  You can also use the define_reference action to manually define a reference
  for use throughout the test. This is helpful when dealing with different
  release tracks that use different API versions.
  """

  def __init__(self):
    self._references = {}
    self._resource_ids = {}
    self._extracted_ids = {}

  def SetExtractedId(self, reference, resource_id):
    self._extracted_ids[reference] = resource_id

  def IsExtractedIdCurrent(self, reference, resource_id):
    return self._extracted_ids.get(reference) == resource_id

  def AddGeneratedResourceId(self, reference, resource_id,
                             requires_cleanup=True):
    if requires_cleanup:
      self._resource_ids[reference] = resource_id
    else:
      self._references[reference] = resource_id

  def RemoveGeneratedResourceId(self, reference):
    del self._resource_ids[reference]

  def UncleanedReferences(self):
    return self._resource_ids

  def SetReference(self, reference, value):
    self._references[reference] = value

  def Resolve(self, data, extracted_only=False, parent=None, field=None):
    """Recursively resolves references in the given data.

    Args:
      data: The data structure you want to recursively resolve references in.
      extracted_only: bool, If true, only extracted references will be resolved
        (not generated or defined references).
      parent: dict, The data structure of the parent of the current field being
        resolved (used for location information).
      field: str, The name of the current field being resolved (used for
        location information).

    Raises:
      UnknownReferenceError: If a reference cannot be resolved.

    Returns:
      The original data structure with references resolved.
    """
    if data is None:
      pass
    elif isinstance(data, six.string_types):
      refs = re.findall(r'\$\$([-\w_]+)\$\$', data)
      for r in refs:
        value = self._resource_ids.get(r)
        if value is None:
          value = self._extracted_ids.get(r)
        if value is None:
          value = self._references.get(r)
        if value is None:
          raise UnknownReferenceError('Unknown reference {}: [{}]'.format(
              assertions.FormatLocation(updates.Location(parent, field)), r))
        if extracted_only and r not in self._extracted_ids:
          continue
        data = data.replace('$$' + r + '$$', value)
    # We intentionally replace the data in-place here so that the same data
    # structure can be written back out to the scenario file.
    elif yaml.list_like(data):
      for x in range(len(data)):
        data[x] = self.Resolve(data[x], extracted_only=extracted_only,
                               parent=data, field=None)
    elif yaml.dict_like(data):
      for k in data:
        data[k] = self.Resolve(data[k], extracted_only=extracted_only,
                               parent=data, field=k)
    # Things like ints, bools, etc. that don't need processing fall through.
    return data

  def ReverseResolve(self, data):
    """Recursively reverse resolves references in the given data."""
    all_ids = {k: v for k, v in itertools.chain(
        six.iteritems(self._resource_ids),
        six.iteritems(self._extracted_ids),
        six.iteritems(self._references))}
    # Sort by value length, longest first to make sure that values that are
    # substrings of other values are replaced with the correct reference.
    # Empty references (the empty string) are excluded from reverse resolution
    # because they don't have a value that can be replaced.
    sorted_ids = [
        x for x in reversed(sorted(all_ids.items(), key=lambda x: len(x[1])))
        if len(x[1])]
    return self._ReverseResolve(data, sorted_ids)

  def _ReverseResolve(self, data, sorted_ids):
    """Recursively reverse resolves references in the given data."""
    if data is None:
      pass
    elif isinstance(data, six.string_types):
      for reference, value in sorted_ids:
        data = data.replace(value, '$$' + reference + '$$')
    elif yaml.list_like(data):
      for x in range(len(data)):
        data[x] = self.ReverseResolve(data[x])
    elif yaml.dict_like(data):
      for k in data:
        data[k] = self.ReverseResolve(data[k])
    # Things like ints, bools, etc. that don't need processing fall through.
    return data
