# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

  test_obj.PREFIX = ('https://compute.googleapis.com/compute/{}/projects/'
                     '{}/global/instanceTemplates/{}')
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


class InstanceGroupManagersUpdateInstancesZonalTest(test_base.BaseTest):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA
    self.should_list_per_instance_configs = False

  def SetUp(self):
    SetUpClass(self, self.api_version)
    self.igms = test_resources.MakeInstanceGroupManagersWithVersions(
        self.api_version, self.ZONE)
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

  def generateListPerInstanceConfigsRequestStub(self, get_request):
    return (self.messages.
            ComputeInstanceGroupManagersListPerInstanceConfigsRequest(
                instanceGroupManager=get_request.instanceGroupManager,
                project=get_request.project,
                zone=get_request.zone))

  def checkUpdateRequest(self, expected_get_request, expected_update_request):
    if self.should_list_per_instance_configs:
      expected_list_pics_request = (
          self.generateListPerInstanceConfigsRequestStub(expected_get_request))
      self.CheckRequests(
          [(self.compute.instanceGroupManagers, 'Get', expected_get_request)],
          [(self.compute.instanceGroupManagers, 'ListPerInstanceConfigs',
            expected_list_pics_request)],
          [(self.compute.instanceGroupManagers, 'Patch',
            expected_update_request)])
    else:
      self.CheckRequests(
          [(self.compute.instanceGroupManagers, 'Get', expected_get_request)],
          [(self.compute.instanceGroupManagers, 'Patch',
            expected_update_request)])

  def testRestartOneVersionDefault(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action restart {} '
             '--zone {}'.format(self.IGM_NAME_A, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.RESTART
    self.checkUpdateRequest(get_request, update_request)

  def testRestartTwoVersionsAsFastAsPossible(self):
    self.make_requests.side_effect = iter([[self.igms[1]], [], []])
    self.Run('compute instance-groups managed rolling-action restart {} '
             '--max-unavailable 100% --zone {}'.format(self.IGM_NAME_B,
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
    ) = self.MinimalActionValueValuesEnum.RESTART
    self.checkUpdateRequest(get_request, update_request)

  def testRestartInstanceTemplateDefault(self):
    self.make_requests.side_effect = iter([[self.igms[2]], [], []])
    self.Run('compute instance-groups managed rolling-action restart {} '
             '--zone {}'.format(self.IGM_NAME_C, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_C)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_C)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.RESTART
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run('compute instance-groups managed rolling-action restart {} '
               '--zone {}'.format(self.IGM_NAME_A, self.ZONE))


class InstanceGroupManagersUpdateInstancesRegionalTest(test_base.BaseTest):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA
    self.should_list_per_instance_configs = False

  def SetUp(self):
    SetUpClass(self, self.api_version)
    self.igms = test_resources.MakeInstanceGroupManagersWithVersions(
        self.api_version, self.REGION, 'region')
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

  def generateListPerInstanceConfigsRequestStub(self, get_request):
    return (self.messages.
            ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest(
                instanceGroupManager=get_request.instanceGroupManager,
                project=get_request.project,
                region=get_request.region))

  def checkUpdateRequest(self, expected_get_request, expected_update_request):
    if self.should_list_per_instance_configs:
      expected_list_pics_request = (
          self.generateListPerInstanceConfigsRequestStub(expected_get_request))
      self.CheckRequests(
          [(self.compute.regionInstanceGroupManagers, 'Get',
            expected_get_request)],
          [(self.compute.regionInstanceGroupManagers, 'ListPerInstanceConfigs',
            expected_list_pics_request)],
          [(self.compute.regionInstanceGroupManagers, 'Patch',
            expected_update_request)])
    else:
      self.CheckRequests(
          [(self.compute.regionInstanceGroupManagers, 'Get',
            expected_get_request)],
          [(self.compute.regionInstanceGroupManagers, 'Patch',
            expected_update_request)])

  def testRestartDefault(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action restart {} '
             '--region {}'.format(self.IGM_NAME_A, self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.RESTART
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)

  def testRestartAllAsFastAsPossible(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action restart {} '
             '--region {} '
             '--max-unavailable 100%'.format(self.IGM_NAME_A, self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(percent=100)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.RESTART
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)

  def testRestartAllTwoAtATime(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action restart {} '
             '--region {} '
             '--max-unavailable 2'.format(self.IGM_NAME_A, self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=2)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.RESTART
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)


class InstanceGroupManagersUpdateInstancesBetaZonalTest(
    InstanceGroupManagersUpdateInstancesZonalTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceGroupManagersUpdateInstancesBetaRegionalTest(
    InstanceGroupManagersUpdateInstancesRegionalTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceGroupManagersUpdateInstancesAlphaZonalTest(
    InstanceGroupManagersUpdateInstancesBetaZonalTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.should_list_per_instance_configs = True

  def testRestartIgmWithStatefulPolicy(self):
    igm = test_resources.MakeStatefulInstanceGroupManager(
        self.api_version, self.ZONE)
    self.make_requests.side_effect = iter([[igm], [], []])
    self.Run('compute instance-groups managed rolling-action restart {0} '
             '--zone {1} --max-unavailable 1'
             .format(igm.name, self.ZONE))

    get_request = self.generateGetRequestStub(igm.name)
    update_request = self.generateUpdateRequestStub(igm.name)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=1)
    (update_request.instanceGroupManagerResource.updatePolicy.maxSurge
    ) = self.FixedOrPercent(fixed=0)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.RESTART
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)

  def testRestartIgmWithPerInstanceConfigs(self):
    pics = self.messages.InstanceGroupManagersListPerInstanceConfigsResp(
        items=[self.messages.PerInstanceConfig(name='instance123')])
    self.make_requests.side_effect = iter([[self.igms[0]], [pics], []])
    self.Run('compute instance-groups managed rolling-action restart {0} '
             '--zone {1} --max-unavailable 1'
             .format(self.IGM_NAME_A, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=1)
    (update_request.instanceGroupManagerResource.updatePolicy.maxSurge
    ) = self.FixedOrPercent(fixed=0)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.RESTART
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    (update_request.instanceGroupManagerResource.versions[0].name
    ) = '0/' + TIME_NOW_STR
    self.checkUpdateRequest(get_request, update_request)


class InstanceGroupManagersUpdateInstancesAlphaRegionalTest(
    InstanceGroupManagersUpdateInstancesBetaRegionalTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.should_list_per_instance_configs = True

if __name__ == '__main__':
  test_case.main()
