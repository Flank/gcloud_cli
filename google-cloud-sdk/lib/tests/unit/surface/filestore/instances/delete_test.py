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
"""Tests for Cloud Filestore instance delete."""

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


class CloudFilestoreInstancesDeleteTest(base.CloudFilestoreUnitTestBase,
                                        parameterized.TestCase):

  _TRACK = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SetUpTrack(self._TRACK)
    self.name = (
        'projects/{}/locations/us-central1-c/instances/instance_name'
        .format(self.Project()))
    self.op_name = (
        'projects/{}/locations/us-central1-c/operations/op'
        .format(self.Project()))

  def RunDelete(self, *args):
    return self.Run(['filestore', 'instances', 'delete'] + list(args))

  def ExpectDeleteInstance(self):
    self.mock_client.projects_locations_instances.Delete.Expect(
        self.messages.FileProjectsLocationsInstancesDeleteRequest(
            name=self.name),
        self.messages.Operation(name=self.op_name))

  def testCancelDeleteValidInstance(self):
    self.WriteInput('n')
    self.RunDelete(
        'instance_name', '--location=us-central1-c',
        '--async')
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'projects/{}/locations/us-central1-c/instances/instance_name'
        .format(self.Project()))

  def testDeleteValidInstance(self):
    self.WriteInput('y')
    self.ExpectDeleteInstance()
    self.RunDelete(
        'instance_name', '--location=us-central1-c',
        '--async')
    self.AssertOutputEquals('')
    self.AssertErrContains('$ gcloud {} filestore instances list'
                           .format(self._TRACK.prefix))
    self.AssertErrContains(
        'projects/{}/locations/us-central1-c/instances/instance_name'
        .format(self.Project()))

  def testWaitForDelete(self):
    self.WriteInput('y')
    self.ExpectDeleteInstance()
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.FileProjectsLocationsOperationsGetRequest(
            name=self.op_name),
        self.messages.Operation(
            name=self.op_name,
            done=True))
    self.RunDelete(
        'instance_name', '--location=us-central1-c')
    self.AssertErrContains(
        'projects/{}/locations/us-central1-c/instances/instance_name'
        .format(self.Project()))
    self.AssertOutputEquals('')

  def testUsingDefaultLocation(self):
    properties.VALUES.filestore.location.Set('us-central1-c')
    self.ExpectDeleteInstance()
    self.WriteInput('y')
    self.RunDelete('instance_name', '--async')
    self.AssertErrContains(
        'projects/{}/locations/us-central1-c/instances/instance_name'
        .format(self.Project()))
    self.AssertOutputEquals('')

  @parameterized.named_parameters(
      ('MissingLocation', handlers.ParseError, ['instance_name', '--async']),
      ('MissingInstanceName', cli_test_base.MockArgumentError,
       ['--location=us-central1-c', '--async']))
  def testMissingLocationWithoutDefault(self, expected_error, args):
    with self.assertRaises(expected_error):
      self.RunDelete(*args)


class CloudFilestoreInstancesDeleteAlphaTest(CloudFilestoreInstancesDeleteTest):

  _TRACK = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
