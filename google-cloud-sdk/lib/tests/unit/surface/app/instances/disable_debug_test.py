# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for gcloud app instances disable-debug."""

from __future__ import absolute_import
from googlecloudsdk.api_lib.app import instances_util
from tests.lib.surface.app import api_test_util
from tests.lib.surface.app import instances_base


class InstancesDisableDebugTest(instances_base.InstancesTestBase):

  def SetUp(self):
    self.select_instance_mock = self.StartObjectPatch(
        instances_util, 'SelectInstanceInteractive')

  def AssertDebugCalled(self, service, version, instance):
    self.AssertErrContains(
        'Any local changes will be LOST')
    self.AssertErrContains(
        'About to disable debug mode for instance [{0}/{1}/{2}]'
        .format(service, version, instance))
    self.AssertErrContains(
        'Disabling debug mode for instance [{0}/{1}/{2}]'
        .format(service, version, instance))

  def testDisableDebug_NoMatches(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    with self.assertRaisesRegex(
        instances_util.InvalidInstanceSpecificationError,
        r'No instances match the given specification\.'):
      self.Run('app instances disable-debug bad')

  def testDisableDebug_TooManyMatches(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    with self.assertRaisesRegex(
        instances_util.InvalidInstanceSpecificationError,
        r'More than one instance matches the given specification\.'):
      self.Run('app instances disable-debug i1')

  def testDisableDebug(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    self._ExpectDeleteInstanceCall('default', 'v1_flex', 'i2')
    self.Run('app instances disable-debug i2')
    self.AssertDebugCalled('default', 'v1_flex', 'i2')

  def testDisableDebug_MixedEnvironments(self):
    """Ensures that mvm, flex are working and standard ignored."""
    self._ExpectCalls([
        ('default', [
            ('v1_mvm', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_standard', None)])
    ])
    self._ExpectDeleteInstanceCall('default', 'v1_mvm', 'i2')
    self.Run('app instances disable-debug i2')
    self.AssertDebugCalled('default', 'v1_mvm', 'i2')

  def testDisableDebug_FilterService(self):
    self._ExpectCalls([
        ('default', []),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    self._ExpectDeleteInstanceCall('service1', 'v1_flex', 'i1')
    self.Run('app instances disable-debug --service service1 i1')
    self.AssertDebugCalled('service1', 'v1_flex', 'i1')

  def testDisableDebug_FilterVersion(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', []),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', [])])
    ])
    self._ExpectDeleteInstanceCall('default', 'v2_flex', 'i1')
    self.Run('app instances disable-debug --version v2_flex i1')
    self.AssertDebugCalled('default', 'v2_flex', 'i1')

  def testDisableDebug_FilterBoth(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', [])
        ]),
        ('service1', [])
    ])
    self._ExpectDeleteInstanceCall('default', 'v1_flex', 'i1')
    self.Run(
        'app instances disable-debug --service default --version v1_flex i1')
    self.AssertDebugCalled('default', 'v1_flex', 'i1')

  def testDisableDebug_ResourcePath(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    with self.assertRaisesRegex(
        instances_util.InvalidInstanceSpecificationError,
        r'No instances match the given specification\.'):
      self.Run('app instances disable-debug default/v1/i1')

  def testDisableDebug_Interactive(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    instances = [
        self._MakeUtilInstance('default', 'v1_flex', 'i1'),
        self._MakeUtilInstance('default', 'v1_flex', 'i2'),
        self._MakeUtilInstance('default', 'v2_flex', 'i1'),
        self._MakeUtilInstance('service1', 'v1_flex', 'i1')
    ]
    instance = instances[0]  # chosen arbitrarily
    self.select_instance_mock.return_value = instance

    self._ExpectDeleteInstanceCall(instance.service, instance.version,
                                   instance.id)

    self.Run('app instances disable-debug')

    self.AssertDebugCalled(instance.service, instance.version, instance.id)
    self.select_instance_mock.assert_called_once_with(instances,
                                                      service=None,
                                                      version=None)

  def testDisableDebug_InteractiveFilter(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', [])
        ]),
        ('service1', [])
    ])
    instances = [
        self._MakeUtilInstance('default', 'v1_flex', 'i1'),
        self._MakeUtilInstance('default', 'v1_flex', 'i2')
    ]
    instance = instances[0]  # chosen arbitrarily
    self.select_instance_mock.return_value = instance

    self._ExpectDeleteInstanceCall(instance.service, instance.version,
                                   instance.id)

    self.Run(
        'app instances disable-debug --service {0} --version {1}'.format(
            instance.service, instance.version))

    self.AssertDebugCalled(instance.service, instance.version, instance.id)
    self.select_instance_mock.assert_called_once_with(instances,
                                                      service=instance.service,
                                                      version=instance.version)

  def testDisableDebug_URI(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    self._ExpectDeleteInstanceCall('default', 'v1_flex', 'i2')
    self.Run('app instances disable-debug https://appengine.googleapis.com'
             '/{api_version}/apps/{appsId}/services/{servicesId}/versions/'
             '{versionsId}/instances/{instancesId}'.format(
                 api_version=api_test_util.APPENGINE_API_VERSION,
                 appsId=self.PROJECT,
                 servicesId='default',
                 versionsId='v1_flex',
                 instancesId='i2'))
    self.AssertErrContains('About to disable debug mode for instance '
                           '[default/v1_flex/i2].')
    self.AssertDebugCalled('default', 'v1_flex', 'i2')
