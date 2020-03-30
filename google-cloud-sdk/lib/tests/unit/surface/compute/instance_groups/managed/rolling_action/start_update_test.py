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
"""Tests for instance-groups managed rolling-action start-update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
from mock import patch

TIME_NOW_STR = str(test_base.FakeDateTime.now())


def SetUpClass(test_obj, api_version):
  test_obj.SelectApi(api_version)

  test_obj.PREFIX = ('https://compute.googleapis.com/compute/{0}/projects/'
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

  def testOneToOneVersion(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} --zone {2}'.format(
                 self.IGM_NAME_A, self.TEMPLATE_B_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    self.checkUpdateRequest(get_request, update_request)

  def testOneToOneVersionOnlyName(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} --zone {2}'.format(
                 self.IGM_NAME_A, 'template-2', self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    self.checkUpdateRequest(get_request, update_request)

  def testOneToOneNamedVersion(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1},name=my-name --zone {2}'.format(
                 self.IGM_NAME_A, self.TEMPLATE_B_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    update_request.instanceGroupManagerResource.versions[0].name = 'my-name'
    self.checkUpdateRequest(get_request, update_request)

  def testOneToTwoVersions(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} '
             '--canary-version template={2},target-size=100% --zone {3}'.format(
                 self.IGM_NAME_A, self.TEMPLATE_A_NAME, self.TEMPLATE_B_NAME,
                 self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_two_version
    self.checkUpdateRequest(get_request, update_request)

  def testOneToTwoOtherVersionsFail(self):
    with self.AssertRaisesToolExceptionMatches(
        'Update inconsistent with current state. '
        'The only allowed transitions between versions are: '
        'X -> Y, X -> (X, Y), (X, Y) -> X, (X, Y) -> Y, (X, Y) -> (X, Y). '
        'Please check versions templates or use --force.'):
      self.make_requests.side_effect = iter([[self.igms[0]], [], []])
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--version template={1} '
          '--canary-version template={2},target-size=100% --zone {3}'.format(
              self.IGM_NAME_A, self.TEMPLATE_C_NAME, self.TEMPLATE_D_NAME,
              self.ZONE))

  def testOneToTwoOtherVersionsForce(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--force --version template={1} --canary-version '
             'template={2},target-size=100% --zone {3}'.format(
                 self.IGM_NAME_A, self.TEMPLATE_C_NAME, self.TEMPLATE_D_NAME,
                 self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_two_version
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_C_NAME
    (update_request.instanceGroupManagerResource.versions[1].instanceTemplate
    ) = self.TEMPLATE_D_NAME
    self.checkUpdateRequest(get_request, update_request)

  def testTwoToFirstVersion(self):
    self.make_requests.side_effect = iter([[self.igms[1]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} --zone {2}'.format(
                 self.IGM_NAME_B, self.TEMPLATE_A_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_B)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_B)
    update_request.instanceGroupManager = self.IGM_NAME_B
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    self.checkUpdateRequest(get_request, update_request)

  def testTwoToFirstVersion_TwoDifferentTagsInIgm(self):
    self.make_requests.side_effect = iter([[self.igms[3]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} --zone {2}'.format(
                 self.IGM_NAME_D, self.TEMPLATE_A_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_D)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_D)
    update_request.instanceGroupManager = self.IGM_NAME_D
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    update_request.instanceGroupManagerResource.versions[0].name = 'other-tag'
    self.checkUpdateRequest(get_request, update_request)

  def testTwoToSecondVersion(self):
    self.make_requests.side_effect = iter([[self.igms[1]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} --zone {2}'.format(
                 self.IGM_NAME_B, self.TEMPLATE_B_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_B)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_B)
    self.checkUpdateRequest(get_request, update_request)

  def testTwoToTwoVersions(self):
    self.make_requests.side_effect = iter([[self.igms[1]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--canary-version template={1},target-size=3 '
             '--version template={2} --zone {3}'.format(
                 self.IGM_NAME_B, self.TEMPLATE_A_NAME, self.TEMPLATE_B_NAME,
                 self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_B)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_B)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_two_version
    (update_request.instanceGroupManagerResource.versions[0].targetSize
    ) = self.FixedOrPercent(fixed=3)
    (update_request.instanceGroupManagerResource.versions[1].targetSize) = None
    version = update_request.instanceGroupManagerResource.versions[0]
    update_request.instanceGroupManagerResource.versions[
        0] = update_request.instanceGroupManagerResource.versions[1]
    update_request.instanceGroupManagerResource.versions[1] = version
    self.checkUpdateRequest(get_request, update_request)

  def testTwoToOneOtherVersionFail(self):
    with self.AssertRaisesToolExceptionMatches(
        'Update inconsistent with current state. '
        'The only allowed transitions between versions are: '
        'X -> Y, X -> (X, Y), (X, Y) -> X, (X, Y) -> Y, (X, Y) -> (X, Y). '
        'Please check versions templates or use --force.'):
      self.make_requests.side_effect = iter([[self.igms[1]], [], []])
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--version template={1} --zone {2}'.format(
              self.IGM_NAME_B, self.TEMPLATE_C_NAME, self.ZONE))

  def testTwoToTwoMixedVersionsFail(self):
    with self.AssertRaisesToolExceptionMatches(
        'Update inconsistent with current state. '
        'The only allowed transitions between versions are: '
        'X -> Y, X -> (X, Y), (X, Y) -> X, (X, Y) -> Y, (X, Y) -> (X, Y). '
        'Please check versions templates or use --force.'):
      self.make_requests.side_effect = iter([[self.igms[1]], [], []])
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--canary-version template={1},target-size=3 '
          '--version template={2} --zone {3}'.format(
              self.IGM_NAME_B, self.TEMPLATE_A_NAME, self.TEMPLATE_C_NAME,
              self.ZONE))

  def testTwoToTwoOtherVersionsFail(self):
    with self.AssertRaisesToolExceptionMatches(
        'Update inconsistent with current state. '
        'The only allowed transitions between versions are: '
        'X -> Y, X -> (X, Y), (X, Y) -> X, (X, Y) -> Y, (X, Y) -> (X, Y). '
        'Please check versions templates or use --force.'):
      self.make_requests.side_effect = iter([[self.igms[1]], [], []])
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--canary-version template={1},target-size=3 '
          '--version template={2} --zone {3}'.format(
              self.IGM_NAME_B, self.TEMPLATE_C_NAME, self.TEMPLATE_D_NAME,
              self.ZONE))

  def testTwoToOneOtherVersionForce(self):
    self.make_requests.side_effect = iter([[self.igms[1]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--force --version template={1} --zone {2}'.format(
                 self.IGM_NAME_B, self.TEMPLATE_C_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_B)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_B)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_one_version
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_C_NAME
    self.checkUpdateRequest(get_request, update_request)

  def testTwoToTwoMixedVersionsForce(self):
    self.make_requests.side_effect = iter([[self.igms[1]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--force --version template={1} --canary-version '
             'template={2},target-size=100% --zone {3}'.format(
                 self.IGM_NAME_B, self.TEMPLATE_A_NAME, self.TEMPLATE_C_NAME,
                 self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_B)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_B)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_two_version
    (update_request.instanceGroupManagerResource.versions[1].instanceTemplate
    ) = self.TEMPLATE_C_NAME
    self.checkUpdateRequest(get_request, update_request)

  def testTwoToTwoOtherVersionsForce(self):
    self.make_requests.side_effect = iter([[self.igms[1]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--force --version template={1} --canary-version '
             'template={2},target-size=100% --zone {3}'.format(
                 self.IGM_NAME_B, self.TEMPLATE_C_NAME, self.TEMPLATE_D_NAME,
                 self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_B)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_B)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_two_version
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_C_NAME
    (update_request.instanceGroupManagerResource.versions[1].instanceTemplate
    ) = self.TEMPLATE_D_NAME
    self.checkUpdateRequest(get_request, update_request)

  def testTwoToTwoIdenticalVersionsForceFail(self):
    with self.AssertRaisesToolExceptionMatches(
        'Provided instance templates must be different.'):
      self.make_requests.side_effect = iter([[self.igms[2]], [], []])
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--version template={1} '
          '--canary-version template={1},target-size=100% --zone {2}'.format(
              self.IGM_NAME_C, self.TEMPLATE_C_NAME, self.ZONE))

  def testInstanceTemplateToOneVersion(self):
    self.make_requests.side_effect = iter([[self.igms[2]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} --zone {2}'.format(
                 self.IGM_NAME_C, self.TEMPLATE_A_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_C)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_C)
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_A_NAME
    self.checkUpdateRequest(get_request, update_request)

  def testInstanceTemplateToTwoVersions(self):
    self.make_requests.side_effect = iter([[self.igms[2]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} '
             '--canary-version template={2},target-size=100% --zone {3}'.format(
                 self.IGM_NAME_C, self.TEMPLATE_A_NAME, self.TEMPLATE_B_NAME,
                 self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_C)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_C)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_two_version
    self.checkUpdateRequest(get_request, update_request)

  def testInstanceTemplateToTwoOtherVersionsFail(self):
    with self.AssertRaisesToolExceptionMatches(
        'Update inconsistent with current state. '
        'The only allowed transitions between versions are: '
        'X -> Y, X -> (X, Y), (X, Y) -> X, (X, Y) -> Y, (X, Y) -> (X, Y). '
        'Please check versions templates or use --force.'):
      self.make_requests.side_effect = iter([[self.igms[2]], [], []])
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--version template={1} '
          '--canary-version template={2},target-size=100% --zone {3}'.format(
              self.IGM_NAME_C, self.TEMPLATE_C_NAME, self.TEMPLATE_D_NAME,
              self.ZONE))

  def testInstanceTemplateToTwoOtherVersionsForce(self):
    self.make_requests.side_effect = iter([[self.igms[2]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--force --version template={1} --canary-version '
             'template={2},target-size=100% --zone {3}'.format(
                 self.IGM_NAME_C, self.TEMPLATE_C_NAME, self.TEMPLATE_D_NAME,
                 self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_C)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_C)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_two_version
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_C_NAME
    (update_request.instanceGroupManagerResource.versions[1].instanceTemplate
    ) = self.TEMPLATE_D_NAME
    self.checkUpdateRequest(get_request, update_request)

  def testOneVersionDefault(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--force --version template={1} --zone {2}'.format(
                 self.IGM_NAME_A, self.TEMPLATE_B_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    self.checkUpdateRequest(get_request, update_request)

  def doTestOneVersionAllSet(self, with_min_ready):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    command_template = (
        'compute instance-groups managed rolling-action start-update {0} '
        '--force --type proactive --max-surge 10 '
        '--max-unavailable 9 --version template={1} --zone {2}' +
        (' --min-ready 1m' if with_min_ready else ''))
    self.Run(
        command_template.format(self.IGM_NAME_A, self.TEMPLATE_B_NAME,
                                self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.maxSurge
    ) = self.FixedOrPercent(fixed=10)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=9)
    if with_min_ready:
      (update_request.instanceGroupManagerResource.updatePolicy.minReadySec
      ) = 60
    self.checkUpdateRequest(get_request, update_request)

  def testOneVersionAllSet(self):
    self.doTestOneVersionAllSet(with_min_ready=False)

  def testOneVersionTooMuchSurgeFail(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--max-surge]: percentage cannot be higher '
        'than 100%.'):
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--force --max-surge 101% --version template={1} '
          '--zone {2}'.format(self.IGM_NAME_A, self.TEMPLATE_D_NAME, self.ZONE))

  def testReplacementMethod(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} --zone {2} --replacement-method recreate'
             .format(self.IGM_NAME_A, self.TEMPLATE_B_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.replacementMethod
    ) = (
        self.messages.InstanceGroupManagerUpdatePolicy
        .ReplacementMethodValueValuesEnum.RECREATE)
    self.checkUpdateRequest(get_request, update_request)

  def testOneVersionTooMuchUnavailableFail(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--max-unavailable]: percentage cannot be higher '
        'than 100%.'):
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--force --max-unavailable 101% --version template={1} --zone {2}'.
          format(self.IGM_NAME_A, self.TEMPLATE_B_NAME, self.ZONE))

  def testOneVersionOpportunistic(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run(
        'compute instance-groups managed rolling-action start-update {0} '
        '--force --type opportunistic --version template={1} --zone {2}'.format(
            self.IGM_NAME_A, self.TEMPLATE_B_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.type
    ) = self.TypeValueValuesEnum.OPPORTUNISTIC
    self.checkUpdateRequest(get_request, update_request)

  def doTestTwoVersions(self, with_min_ready):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    command_template = (
        'compute instance-groups managed rolling-action start-update {0} '
        '--force --max-unavailable 3 --version template={1} '
        '--canary-version template={2},target-size=90% --zone {3}' +
        (' --min-ready 3m' if with_min_ready else ''))
    self.Run(
        command_template.format(self.IGM_NAME_A, self.TEMPLATE_A_NAME,
                                self.TEMPLATE_B_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    if with_min_ready:
      (update_request.instanceGroupManagerResource.updatePolicy.minReadySec
      ) = 180
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=3)
    (update_request.instanceGroupManagerResource.versions
    ) = self.default_two_version
    (update_request.instanceGroupManagerResource.versions[1].targetSize
    ) = self.FixedOrPercent(percent=90)
    self.checkUpdateRequest(get_request, update_request)

  def testTwoVersions(self):
    self.doTestTwoVersions(with_min_ready=False)

  def testTwoVersionsNoTargetSize(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--canary-version target-size=TARGET-SIZE]: '
        'target size must be specified for canary version'
    ):
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--force --type proactive --version template={1} --canary-version '
          'template={2} --zone {3}'.format(self.IGM_NAME_A,
                                           self.TEMPLATE_A_NAME,
                                           self.TEMPLATE_B_NAME, self.ZONE))

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--version template={1} --zone {2}'.format(
              self.IGM_NAME_B, self.TEMPLATE_B_NAME, self.ZONE))


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

  def testOneVersionDefault(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--force --version template={1} --region {2}'.format(
                 self.IGM_NAME_A, self.TEMPLATE_B_NAME, self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    self.checkUpdateRequest(get_request, update_request)

  def doTestOneVersionAllSet(self, with_min_ready):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    command_template = (
        'compute instance-groups managed rolling-action start-update {0} '
        '--force --type proactive --max-surge 10 '
        '--max-unavailable 9 --version template={1} --region {2}' +
        (' --min-ready 1m ' if with_min_ready else ''))
    self.Run(
        command_template.format(self.IGM_NAME_A, self.TEMPLATE_B_NAME,
                                self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.maxSurge
    ) = self.FixedOrPercent(fixed=10)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=9)
    if with_min_ready:
      (update_request.instanceGroupManagerResource.updatePolicy.minReadySec
      ) = 60
    self.checkUpdateRequest(get_request, update_request)

  def testOneVersionAllSet(self):
    self.doTestOneVersionAllSet(with_min_ready=False)

  def testOneVersionCommitment(self):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--force --version template={1} --region {2}'.format(
                 self.IGM_NAME_A, self.TEMPLATE_D_NAME, self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    update_request.instanceGroupManagerResource.versions = [
        self.messages.InstanceGroupManagerVersion(
            instanceTemplate=self.TEMPLATE_D_NAME)
    ]
    self.checkUpdateRequest(get_request, update_request)

  def testOneVersionNoTemplateFail(self):
    with self.AssertRaisesToolExceptionMatches(
        '[--version]: template has to be specified.'):
      self.make_requests.side_effect = iter([[self.igms[0]], [], []])
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--force --version name=template --region {1}'.format(self.IGM_NAME_A,
                                                                self.REGION))

  def doTestTwoVersions(self, with_min_ready):
    self.make_requests.side_effect = iter([[self.igms[0]], [], []])
    command_template = ('compute instance-groups managed rolling-action '
                        'start-update {0} --max-unavailable 3 --force '
                        '--version template={2} --region {3} --canary-version '
                        'template={1},target-size=10' +
                        (' --min-ready 3m' if with_min_ready else ''))
    self.Run(
        command_template.format(self.IGM_NAME_A, self.TEMPLATE_D_NAME,
                                self.TEMPLATE_C_NAME, self.REGION))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    if with_min_ready:
      (update_request.instanceGroupManagerResource.updatePolicy.minReadySec
      ) = 180
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=3)
    update_request.instanceGroupManagerResource.versions = [
        self.messages.InstanceGroupManagerVersion(
            instanceTemplate=self.TEMPLATE_C_NAME),
        self.messages.InstanceGroupManagerVersion(
            instanceTemplate=self.TEMPLATE_D_NAME,
            targetSize=self.FixedOrPercent(fixed=10))
    ]
    self.checkUpdateRequest(get_request, update_request)

  def testTwoVersions(self):
    self.doTestTwoVersions(with_min_ready=False)

  def testTwoVersionsNoTargetSize(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--canary-version target-size=TARGET-SIZE]: '
        'target size must be specified for canary version'
    ):
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--force --type proactive --version template={1} --canary-version '
          'template={2} --region {3}'.format(self.IGM_NAME_A,
                                             self.TEMPLATE_D_NAME,
                                             self.TEMPLATE_C_NAME, self.REGION))

  def testTwoVersionsNoTemplateFail(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--canary-version]: '
        'template has to be specified.'):
      self.make_requests.side_effect = iter([[self.igms[0]], []])
      self.Run(
          'compute instance-groups managed rolling-action start-update {0} '
          '--canary-version target-size=10 --force '
          '--version template={1} '
          '--region {2}'.format(self.IGM_NAME_A, self.TEMPLATE_D_NAME,
                                self.REGION))


class InstanceGroupManagersUpdateInstancesBetaZonalTest(
    InstanceGroupManagersUpdateInstancesZonalTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA
    self.should_list_per_instance_configs = True

  def testOneVersionAllSet(self):
    self.doTestOneVersionAllSet(with_min_ready=True)

  def testTwoVersions(self):
    self.doTestTwoVersions(with_min_ready=True)

  def testReplaceIgmWithStatefulPolicy(self):
    igm = test_resources.MakeStatefulInstanceGroupManager(
        self.api_version, self.ZONE)
    self.make_requests.side_effect = iter([[igm], [], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} --zone {2} --max-unavailable 1'
             .format(igm.name, self.TEMPLATE_B_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(igm.name)
    update_request = self.generateUpdateRequestStub(igm.name)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=1)
    (update_request.instanceGroupManagerResource.updatePolicy.maxSurge
    ) = self.FixedOrPercent(fixed=0)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.REPLACE
    (update_request.instanceGroupManagerResource.updatePolicy.replacementMethod
    ) = (
        self.messages.InstanceGroupManagerUpdatePolicy
        .ReplacementMethodValueValuesEnum.RECREATE)
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_B_NAME
    self.checkUpdateRequest(get_request, update_request)

  def testReplaceIgmWithPerInstanceConfigs(self):
    pics = self.messages.InstanceGroupManagersListPerInstanceConfigsResp(
        items=[self.messages.PerInstanceConfig(name='instance123')])
    self.make_requests.side_effect = iter([[self.igms[0]], [pics], []])
    self.Run('compute instance-groups managed rolling-action start-update {0} '
             '--version template={1} --zone {2} --max-unavailable 1'
             .format(self.IGM_NAME_A, self.TEMPLATE_B_NAME, self.ZONE))

    get_request = self.generateGetRequestStub(self.IGM_NAME_A)
    update_request = self.generateUpdateRequestStub(self.IGM_NAME_A)
    (update_request.instanceGroupManagerResource.updatePolicy.maxUnavailable
    ) = self.FixedOrPercent(fixed=1)
    (update_request.instanceGroupManagerResource.updatePolicy.maxSurge
    ) = self.FixedOrPercent(fixed=0)
    (update_request.instanceGroupManagerResource.updatePolicy.minimalAction
    ) = self.MinimalActionValueValuesEnum.REPLACE
    (update_request.instanceGroupManagerResource.updatePolicy.replacementMethod
    ) = (
        self.messages.InstanceGroupManagerUpdatePolicy
        .ReplacementMethodValueValuesEnum.RECREATE)
    (update_request.instanceGroupManagerResource.versions[0].instanceTemplate
    ) = self.TEMPLATE_B_NAME
    self.checkUpdateRequest(get_request, update_request)


class InstanceGroupManagersUpdateInstancesBetaRegionalTest(
    InstanceGroupManagersUpdateInstancesRegionalTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA
    self.should_list_per_instance_configs = True

  def testOneVersionAllSet(self):
    self.doTestOneVersionAllSet(with_min_ready=True)

  def testTwoVersions(self):
    self.doTestTwoVersions(with_min_ready=True)


class InstanceGroupManagersUpdateInstancesAlphaZonalTest(
    InstanceGroupManagersUpdateInstancesBetaZonalTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.should_list_per_instance_configs = True


class InstanceGroupManagersUpdateInstancesAlphaRegionalTest(
    InstanceGroupManagersUpdateInstancesBetaRegionalTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.should_list_per_instance_configs = True

if __name__ == '__main__':
  test_case.main()
