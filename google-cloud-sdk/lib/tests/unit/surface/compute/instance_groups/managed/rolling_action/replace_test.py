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
"""Tests for the instance-groups managed update-instances subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
from mock import patch

TIME_NOW_STR = str(test_base.FakeDateTime.now())


def SetUpClass(test_obj, api_version):
  test_obj.SelectApi(api_version)

  test_obj.PREFIX = ('https://www.googleapis.com/compute/{0}/projects/'
                     '{1}/global/instanceTemplates/{2}')
  test_obj.PROJECT_NAME = 'my-project'
  test_obj.TEMPLATE_A_NAME = test_obj.PREFIX.format(
      api_version, test_obj.PROJECT_NAME, 'template-1')
  test_obj.TEMPLATE_B_NAME = test_obj.PREFIX.format(
      api_version, test_obj.PROJECT_NAME, 'template-2')
  test_obj.TEMPLATE_C_NAME = test_obj.PREFIX.format(
      api_version, test_obj.PROJECT_NAME, 'template-3')
  test_obj.TEMPLATE_D_NAME = test_obj.PREFIX.format(
      api_version, test_obj.PROJECT_NAME, 'template-4')
  test_obj.REGION = 'central2'
  test_obj.ZONE = 'central2-a'
  test_obj.IGM_NAME_A = 'group-1'
  test_obj.IGM_NAME_B = 'group-2'
  test_obj.IGM_NAME_C = 'group-3'
  test_obj.IGM_NAME_D = 'group-4'

  test_obj.FixedOrPercent = test_obj.messages.FixedOrPercent
  test_obj.MinimalActionValueValuesEnum = (
      test_obj.messages.InstanceGroupManagerUpdatePolicy.
      MinimalActionValueValuesEnum)
  test_obj.TypeValueValuesEnum = (
      test_obj.messages.InstanceGroupManagerUpdatePolicy.TypeValueValuesEnum)

  test_obj.default_update_policy = (
      test_obj.messages.InstanceGroupManagerUpdatePolicy(
          type=test_obj.TypeValueValuesEnum.PROACTIVE,
          minimalAction=test_obj.MinimalActionValueValuesEnum.REPLACE))
  test_obj.default_one_version = [
      test_obj.messages.InstanceGroupManagerVersion(
          instanceTemplate=test_obj.TEMPLATE_B_NAME)
  ]
  test_obj.default_two_version = [
      test_obj.messages.InstanceGroupManagerVersion(
          instanceTemplate=test_obj.TEMPLATE_A_NAME),
      test_obj.messages.InstanceGroupManagerVersion(
          instanceTemplate=test_obj.TEMPLATE_B_NAME,
          targetSize=test_obj.FixedOrPercent(percent=100))
  ]


class InstanceGroupManagersUpdateInstancesBetaZonalTest(test_base.BaseTest):

  def SetUp(self):
    SetUpClass(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.igms = test_resources.MakeInstanceGroupManagersWithVersions('beta',
                                                                     self.ZONE)
    self.StartPatch('datetime.datetime', test_base.FakeDateTime)

  def generateGetRequestStub(self, igm_name):
    return self.messages.ComputeInstanceGroupManagersGetRequest(
        instanceGroupManager=igm_name,
        project=self.PROJECT_NAME,
        zone=self.ZONE)

  def generateUpdateRequestStub(self, igm_name):
    return self.messages.ComputeInstanceGroupManagersPatchRequest(
        instanceGroupManager=igm_name,
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            updatePolicy=self.default_update_policy,
            versions=self.default_one_version,)),
        project=self.PROJECT_NAME,
        zone=self.ZONE)

  def checkUpdateRequest(self, expected_get_request, expected_update_request):
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'Get', expected_get_request)],
        [(self.compute.instanceGroupManagers, 'Patch',
          expected_update_request)])

  def testReplaceOneVersionDefault(self):
    self.make_requests.side_effect = iter([[self.igms[0]], []])
    self.Run('compute instance-groups managed rolling-action replace {0} '
             '--zone {1}'.format(self.IGM_NAME_A, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.REPLACE
    self.checkUpdateRequest(get_request, update_request)

  def testReplaceTwoVersionsAsFastAsPossible(self):
    self.make_requests.side_effect = iter([[self.igms[1]], []])
    self.Run('compute instance-groups managed rolling-action replace {0} '
             '--max-unavailable 100% --zone {1}'.format(self.IGM_NAME_B,
                                                        self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_B)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_B)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(percent=100)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_two_version
    (update_request.instanceGroupManagerResource.versions[0].targetSize
    ) = self.FixedOrPercent(percent=60)
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    update_request.instanceGroupManagerResource.versions[1].targetSize = None
    (update_request.instanceGroupManagerResource.versions[1].name
    ) = '1/' + TIME_NOW_STR
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.REPLACE
    self.checkUpdateRequest(get_request, update_request)

  def testReplaceInstanceTemplateDefault(self):
    self.make_requests.side_effect = iter([[self.igms[2]], []])
    self.Run('compute instance-groups managed rolling-action replace {0} '
             '--zone {1}'.format(self.IGM_NAME_C, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_C)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_C)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.REPLACE
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run('compute instance-groups managed rolling-action replace {0} '
               '--zone {1}'.format(self.IGM_NAME_A, self.ZONE))


class InstanceGroupManagersUpdateInstancesBetaRegionalTest(test_base.BaseTest):

  def SetUp(self):
    SetUpClass(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.igms = test_resources.MakeInstanceGroupManagersWithVersions(
        'beta', self.REGION, 'region')
    self.StartPatch('datetime.datetime', test_base.FakeDateTime)

  def generateGetRequestStub(self, igm_name):
    return self.messages.ComputeRegionInstanceGroupManagersGetRequest(
        instanceGroupManager=igm_name,
        project=self.PROJECT_NAME,
        region=self.REGION)

  def generateUpdateRequestStub(self, igm_name):
    return self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
        instanceGroupManager=igm_name,
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            updatePolicy=self.default_update_policy,
            versions=self.default_one_version,)),
        project=self.PROJECT_NAME,
        region=self.REGION)

  def checkUpdateRequest(self, expected_get_request, expected_update_request):
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Get',
                         expected_get_request)],
                       [(self.compute.regionInstanceGroupManagers, 'Patch',
                         expected_update_request)])

  def testReplaceDefault(self):
    self.make_requests.side_effect = iter([[self.igms[0]], []])
    self.Run('compute instance-groups managed rolling-action replace {0} '
             '--region {1}'.format(self.IGM_NAME_A, self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.REPLACE
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)

  def testReplaceAllAsFastAsPossible(self):
    self.make_requests.side_effect = iter([[self.igms[0]], []])
    self.Run('compute instance-groups managed rolling-action replace {0} '
             '--region {1} '
             '--max-unavailable 100%'.format(self.IGM_NAME_A, self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(percent=100)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.REPLACE
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)

  def testReplaceAllTwoAtATime(self):
    self.make_requests.side_effect = iter([[self.igms[0]], []])
    self.Run('compute instance-groups managed rolling-action replace {0} '
             '--region {1} '
             '--max-unavailable 2'.format(self.IGM_NAME_A, self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=2)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.REPLACE
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)


class InstanceGroupManagersUpdateInstancesAlphaZonalTest(
    InstanceGroupManagersUpdateInstancesBetaZonalTest):

  def SetUp(self):
    SetUpClass(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.igms = test_resources.MakeInstanceGroupManagersWithVersions('alpha',
                                                                     self.ZONE)


class InstanceGroupManagersUpdateInstancesAlphaRegionalTest(
    InstanceGroupManagersUpdateInstancesBetaRegionalTest):

  def SetUp(self):
    SetUpClass(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.igms = test_resources.MakeInstanceGroupManagersWithVersions(
        'alpha', self.REGION, 'region')

if __name__ == '__main__':
  test_case.main()
