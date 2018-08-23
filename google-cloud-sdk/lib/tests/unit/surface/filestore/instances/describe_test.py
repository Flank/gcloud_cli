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
"""Tests for Cloud Filestore instance describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.filestore import base


class CloudFilestoreInstancesDescribeTest(base.CloudFilestoreUnitTestBase,
                                          parameterized.TestCase):

  _TRACK = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SetUpTrack(self._TRACK)
    self.name = (
        'projects/{}/locations/us-central1-c/instances/instance_name'
        .format(self.Project()))

  def RunDescribe(self, *args):
    return self.Run(['filestore', 'instances', 'describe'] + list(args))

  def ExpectDescribeInstance(self, instance):
    self.mock_client.projects_locations_instances.Get.Expect(
        self.messages.FileProjectsLocationsInstancesGetRequest(name=self.name),
        instance)

  def testDescribeValidFilestoreInstance(self):
    test_instance = self.GetTestCloudFilestoreInstance()
    self.ExpectDescribeInstance(test_instance)
    result = self.RunDescribe('instance_name', '--location=us-central1-c')
    self.assertEquals(result, test_instance)

  def testDescribeWithDefaultLocation(self):
    properties.VALUES.filestore.location.Set('us-central1-c')
    test_instance = self.GetTestCloudFilestoreInstance()
    self.ExpectDescribeInstance(test_instance)
    result = self.RunDescribe('instance_name')
    self.assertEquals(result, test_instance)

  @parameterized.named_parameters(
      ('MissingLocation', handlers.ParseError, ['instance_name']),
      ('MissingInstanceName', cli_test_base.MockArgumentError,
       ['--location=us-central1-c']))
  def testMissingLocationWithoutDefault(self, expected_error, args):
    with self.assertRaises(expected_error):
      self.RunDescribe(*args)


class CloudFilestoreInstancesDescribeAlphaTest(
    CloudFilestoreInstancesDescribeTest):

  _TRACK = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
