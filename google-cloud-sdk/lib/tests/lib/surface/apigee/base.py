# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Base classes for all gcloud apigee tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import json
import os

from googlecloudsdk.core import config
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


def _JsonDataBogoType(json_data):
  """Returns whether a JSON data value is an object, list, or primitive."""
  if isinstance(json_data, collections.Mapping):
    return "object"

  # Strings look like sequences even though they aren't.
  # Get types from literals so that the code can be the same on py2 and py3.
  if isinstance(json_data, type("")) or isinstance(json_data, type(b"")):
    return "primitive"

  if isinstance(json_data, collections.Sequence):
    return "list"

  return "primitive"


MismatchInfo = collections.namedtuple("MismatchInfo",
                                      "path description expected actual")


def _JsonDataMismatches(expected, actual, parent_path=None):
  """Yields MismatchInfo for each mismatch between `expected` and `actual`."""
  if expected == actual:
    return
  json_type = _JsonDataBogoType(actual)
  expected_type = _JsonDataBogoType(expected)
  if json_type != expected_type:
    yield MismatchInfo(parent_path, "Unexpected type", expected_type, json_type)
    return

  if json_type == "primitive":
    yield MismatchInfo(parent_path, "Mismatched values", expected, actual)
    return

  if json_type == "object":
    for key in expected:
      path = parent_path + "." + key if parent_path else key
      if key in actual:
        for mismatch in _JsonDataMismatches(expected[key], actual[key], path):
          yield mismatch
      else:
        yield MismatchInfo(path, "Missing object member", expected[key], None)

    for key in actual:
      if key not in expected:
        yield MismatchInfo(path, "Unexpected object member", None, actual[key])
    return

  # Values are lists. Attempt to determine how the actual list differs from the
  # expected one.
  expected_items = expected[:]
  actual_items = actual[:]
  while len(expected_items) and len(actual_items):
    next_expected = expected_items[0]
    next_actual = actual_items[0]
    if next_expected == next_actual:
      expected_items = expected_items[1:]
      actual_items = actual_items[1:]
      continue

    # The rest of this code is optimized for readability, not performance.
    actual_is_unexpected = (next_actual not in expected_items)
    expected_is_missing = (next_expected not in actual_items)
    if actual_is_unexpected and expected_is_missing:
      # If neither value is recognized, assume one replaced the other.
      index_in_expected = len(expected) - len(expected_items)
      index_in_actual = len(actual) - len(actual_items)
      if index_in_expected == index_in_actual:
        index_string = "[%d]" % index_in_expected
      else:
        index_string = "[%d -> %d]" % (index_in_expected, index_in_actual)
      for mismatch in _JsonDataMismatches(
          next_expected, next_actual,
          parent_path + index_string if parent_path else index_string):
        yield mismatch
      expected_items = expected_items[1:]
      actual_items = actual_items[1:]
      continue

    # If one value is recognized but the other is not, assume the unrecognized
    # value is the abnormal one.
    if actual_is_unexpected:
      yield MismatchInfo(parent_path, "Unexpected list item", None, next_actual)
      actual_items = actual_items[1:]
      continue
    if expected_is_missing:
      yield MismatchInfo(parent_path, "Missing list item", next_expected, None)
      expected_items = expected_items[1:]
      continue

    # Both values are recognized; they just shouldn't be "here". Choose the
    # least disruptive reordering.
    actual_position_of_expected = actual_items.index(next_expected)
    expected_position_of_actual = expected_items.index(next_actual)
    if actual_position_of_expected < expected_position_of_actual:
      expected_items = expected_items[1:]
      del actual_items[actual_position_of_expected]
    else:
      del expected_items[expected_position_of_actual]
      actual_items = actual_items[1:]
  # At most one of the two lists remain. Process each item as a mismatch.
  for next_actual in actual_items:
    yield MismatchInfo(parent_path, "Unexpected list item", None, next_actual)
  for next_expected in expected_items:
    yield MismatchInfo(parent_path, "Missing list item", next_expected, None)


class ApigeeBaseTest(cli_test_base.CliTestBase, sdk_test_base.WithTempCWD):
  """Base class for tests of gcloud Apigee support."""

  def SetUp(self):
    self._already_seen_output_prefix = ""

  def GetJsonOutput(self):
    output_text = self.GetOutput()
    # Trim off the part at the front that has already been checked by previous
    # calls to GetJsonOutput().
    if output_text.startswith(self._already_seen_output_prefix):
      relevant_output_text = output_text[len(self._already_seen_output_prefix):]
    else:
      relevant_output_text = output_text
    self._already_seen_output_prefix = output_text

    try:
      return json.loads(relevant_output_text)
    except ValueError as e:
      self.fail("Output is not valid JSON.\n%s" % (e))

  def AssertJsonOutputMatches(self, expected_output, message=None):
    if message is None:
      message = ""
    else:
      message += ": "

    output_data = self.GetJsonOutput()

    for mismatch in _JsonDataMismatches(expected_output, output_data):
      self.fail("%s%s for %s\nExpected: %s\nActual: %s" %
                (message, mismatch.description, mismatch.path or "[root]",
                 yaml.dump(mismatch.expected), yaml.dump(mismatch.actual)))


class WithRunApigee(cli_test_base.CliTestBase):
  """Tests that invoke `gcloud apigee` commands."""

  def SetUp(self):
    super(WithRunApigee, self).SetUp()

    # Wipe out any config or cache state that might be left over from previous
    # tests.
    config_dir = config.Paths().global_config_dir
    for filename in os.listdir(config_dir):
      if not filename.startswith(".apigee"):
        continue
      full_path = os.path.join(config_dir, filename)
      if os.path.isdir(full_path):
        files.RmTree(full_path)
      else:
        os.unlink(full_path)
    self.Run("config unset project")

  def RunApigee(self, command):
    """Runs `command` in the most current available apigee surface."""
    # TODO(b/150206546): At GA launch, remove "alpha" here.
    return self.Run("alpha apigee " + command)


class WithJSONBodyValidation(e2e_base.WithMockHttp):
  """Tests that can check the JSON contents of HTTP request bodies."""

  def SetUp(self):
    self._expected_json_bodies = {}

  def AddHTTPResponse(self, url, *args, **kwargs):
    if url not in self._expected_json_bodies:
      self._expected_json_bodies[url] = []

    if "expected_json_body" in kwargs:
      self._expected_json_bodies[url].append(kwargs["expected_json_body"])
      del kwargs["expected_json_body"]
    else:
      self._expected_json_bodies[url].append(None)

    return super(WithJSONBodyValidation,
                 self).AddHTTPResponse(url, *args, **kwargs)

  def _request(self, uri, *args, **kwargs):
    if "?" in uri:
      cut_uri = uri.split("?", 1)[0]
    else:
      cut_uri = uri

    response = super(WithJSONBodyValidation,
                     self)._request(uri, *args, **kwargs)

    self.assertIn(
        cut_uri, self._expected_json_bodies,
        "Unexpected request to %s. Only expected: %s" %
        (uri, self._expected_json_bodies.keys()))
    self.assertNotEqual(self._expected_json_bodies[cut_uri], [],
                        "Unexpected additional request to %s" % uri)

    expected_json_body = self._expected_json_bodies[cut_uri].pop(0)
    if expected_json_body is not None:
      body = None
      if "body" in kwargs:
        body = kwargs["body"]
      elif len(args) > 1:
        body = args[1]
      self.assertIsNotNone(body, "Expected a body for %s but saw none." % uri)
      try:
        actual_body = json.loads(body)
      except (ValueError, TypeError) as e:
        self.fail("Body is not valid JSON.\n%s" % e)
      for mismatch in _JsonDataMismatches(expected_json_body, actual_body):
        self.fail("Request body mismatch: %s for %s\nExpected: %s\nActual: %s" %
                  (mismatch.description, mismatch.path or "[root]",
                   yaml.dump(mismatch.expected), yaml.dump(mismatch.actual)))

    return response


class ApigeeServiceAccountTest(ApigeeBaseTest, e2e_base.WithServiceAuth,
                               WithRunApigee):
  """End-to-end tests of `gcloud apigee` surface commands.

  These tests run against the cloud-sdk-integration-testing Cloud Platform
  project via a service account.
  """


class ApigeeIsolatedTest(e2e_base.WithMockHttp, ApigeeBaseTest,
                         sdk_test_base.WithFakeAuth):
  """Isolated tests of gcloud Apigee support."""


class ApigeeSurfaceTest(ApigeeIsolatedTest, WithRunApigee):
  """Isolated tests of `gcloud apigee` surface commands."""
