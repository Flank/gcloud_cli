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
"""Tests for Cloud Filestore instances list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.filestore import base


class CloudFilestoreInstancesListTest(base.CloudFilestoreUnitTestBase):

  _TRACK = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SetUpTrack(self._TRACK)
    self.parent = 'projects/{}/locations/us-central1-c'.format(self.Project())
    self.universal_parent = 'projects/{}/locations/-'.format(self.Project())

  def GetTestCloudFilestoreInstancesList(self):
    instances = [
        self.messages.Instance(
            name=('projects/{}/locations/us-central1-c/instances/Instance1'
                  .format(self.Project())),
            networks=[
                self.messages.NetworkConfig(network='my_network')]),
        self.messages.Instance(
            name=('projects/{}/locations/us-central1-c/instances/Instance2'
                  .format(self.Project())),
            networks=[
                self.messages.NetworkConfig(network='my_network')]),
    ]
    for instance in instances:
      self.AddInstanceFileShare(
          instance,
          [self.FileShareMsg()(name='my_vol', capacityGb=3072)])
    return instances

  def FileShareMsg(self):
    return self.messages.FileShareConfig

  def AddInstanceFileShare(self, instance, file_shares):
    instance.fileShares = file_shares

  def RunList(self, *args):
    return self.Run(['filestore', 'instances', 'list'] + list(args))

  def ExpectListInstancesCalls(self, parent, unreachable=None, instances=None):
    self.mock_client.projects_locations_instances.List.Expect(
        self.messages.FileProjectsLocationsInstancesListRequest(
            parent=parent),
        self.messages.ListInstancesResponse(unreachable=unreachable))
    self.mock_client.projects_locations_instances.List.Expect(
        self.messages.FileProjectsLocationsInstancesListRequest(
            parent=parent, pageSize=100),
        self.messages.ListInstancesResponse(instances=instances))

  def testListNoCloudFilestore(self):
    self.ExpectListInstancesCalls(
        self.universal_parent, unreachable=[], instances=[])
    results = list(self.RunList())
    self.assertEqual(len(results), 0)

  def testListOneCloudFilestoreInstance(self):
    test_instance = self.GetTestCloudFilestoreInstance()
    self.ExpectListInstancesCalls(
        self.universal_parent, unreachable=[], instances=[test_instance])
    results = list(self.RunList())
    self.assertEqual([test_instance], results)

  def testListMultipleCloudFilestoreInstances(self):
    test_instances = self.GetTestCloudFilestoreInstancesList()
    self.ExpectListInstancesCalls(
        self.universal_parent, unreachable=[], instances=test_instances)
    results = list(self.RunList())
    self.assertEqual(test_instances, results)

  def testListOutput(self):
    test_instances = self.GetTestCloudFilestoreInstancesList()
    self.ExpectListInstancesCalls(
        self.universal_parent, unreachable=[], instances=test_instances)
    self.RunList()
    # pylint: disable=line-too-long
    self.AssertOutputContains(
        """\
        INSTANCE_NAME LOCATION TIER CAPACITY_GB FILE_SHARE_NAME IP_ADDRESS STATE CREATE_TIME
        Instance1 us-central1-c 3072 my_vol
        Instance2 us-central1-c 3072 my_vol
        """,
        normalize_space=True
    )
    # pylint: enable=line-too-long

  def testListOutputUri(self):
    test_instances = self.GetTestCloudFilestoreInstancesList()
    self.ExpectListInstancesCalls(
        self.universal_parent, unreachable=[], instances=test_instances)
    self.RunList('--uri')
    # pylint: disable=line-too-long
    self.AssertOutputContains(
        """\
        https://file.googleapis.com/{0}/projects/{1}/locations/us-central1-c/instances/Instance1
        https://file.googleapis.com/{0}/projects/{1}/locations/us-central1-c/instances/Instance2
        """.format(self.api_version, self.Project()),
        normalize_space=True
    )
    # pylint: enable=line-too-long

  def testListWithLocation(self):
    test_instance = self.GetTestCloudFilestoreInstance()
    self.ExpectListInstancesCalls(
        self.parent, unreachable=[], instances=[test_instance])
    results = list(self.RunList('--location=us-central1-c'))
    self.assertEqual([test_instance], results)

  def testWithUnreachableLocation(self):
    self.ExpectListInstancesCalls(
        self.universal_parent, unreachable=['us-central1-c'], instances=[])
    results = list(self.RunList())
    self.assertEqual([], results)
    self.AssertErrContains(
        'WARNING: Location us-central1-c may be unreachable.')


class CloudFilestoreInstancesListAlphaTest(CloudFilestoreInstancesListTest):

  _TRACK = calliope_base.ReleaseTrack.ALPHA

  def FileShareMsg(self):
    return self.messages.VolumeConfig

  def AddInstanceFileShare(self, instance, file_shares):
    instance.volumes = file_shares


if __name__ == '__main__':
  test_case.main()
