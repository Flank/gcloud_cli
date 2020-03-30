# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Integration tests for Cloud Logging commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.trace import base


class TraceIntegrationTest(base.TraceIntegrationTestBase):
  """Test commands that operate on sinks."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='trace', sequence_start=1)

    self._parents_and_flags = [('projects/{0}'.format(self.Project()), '')]

  @contextlib.contextmanager
  def CreateTraceSinkResource(self, sink_name):
    destination = ('bigquery.googleapis.com/projects/{0}/datasets/my_dataset'
                   .format('462803083913'))
    try:
      sink = self.RunTrace('sinks create {0} {1}'.format(
          sink_name, destination))
      yield sink
    finally:
      self.WriteInput('Y')
      self.RunTrace('sinks delete {0}'.format(sink_name))

  def testResourceCreation(self):

    def FindSink(sink_name):
      """Get the list of sinks, and check if sink_name is on the list."""
      sinks = self.RunTrace('sinks list')
      return any(sink_name in sink['name'] for sink in sinks)

    sink_name = next(self._name_generator)

    with self.CreateTraceSinkResource(sink_name) as res:
      self.assertEqual(sink_name, res['name'])

      sink = self.RunTrace('sinks describe {0}'.format(sink_name))
      self.assertEqual(sink_name, sink['name'])

      self.assertTrue(FindSink(sink_name))

    self.assertFalse(FindSink(sink_name))


if __name__ == '__main__':
  test_case.main()
