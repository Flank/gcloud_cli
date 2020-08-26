# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Completion Tests for instance in miscellaneous subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instances import test_resources
from tests.lib.surface.compute.machine_types import test_resources as machine_type_resources


class InstancesMiscTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def _CollectCompletions(self, *args):
    return self.collect_completions(*args)

  def runTest(self, command):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion('compute instances ' +  command  + ' --zone=zone-1 i',
                       ['instance-3',
                        'instance-2',
                        'instance-1'])
    self.RunCompletion('compute instances ' +  command  + ' --zone=zone-1 ',
                       ['instance-3',
                        'instance-2',
                        'instance-1'])

  def testStartCompletion(self):
    self.runTest('start')

  def testStopCompletion(self):
    self.runTest('stop')

  def testListCompletion(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion('compute instances list i',
                       ['instance-1\\ --zones=zone-1',
                        'instance-2\\ --zones=zone-1',
                        'instance-3\\ --zones=zone-1'])

  def testMoveCompletion(self):
    self.runTest('move')

  def testResetCompletion(self):
    self.runTest('reset')

  def testAddDiskCompletion(self):
    self.runTest('attach-disk')

  def testDeleteDiskCompletion(self):
    self.runTest('detach-disk')

  def testAddTagsCompletion(self):
    self.runTest('add-tags')

  def testRemoveTagsCompletion(self):
    self.runTest('remove-tags')

  def testAddMetadataCompletion(self):
    self.runTest('add-metadata')

  def testRemoveMetaDataCompletion(self):
    self.runTest('remove-metadata')

  def testAddAccessConfigCompletion(self):
    self.runTest('add-access-config')

  def testDeleteAccessConfigCompletion(self):
    self.runTest('delete-access-config')

  def testSetSchedulingCompletion(self):
    self.runTest('set-scheduling')

  def testGetSerialPortOutputCompletion(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion('compute instances get-serial-port-output i',
                       ['instance-1\\ --zone=zone-1',
                        'instance-2\\ --zone=zone-1',
                        'instance-3\\ --zone=zone-1'])
    self.RunCompletion('compute instances get-serial-port-output '
                       '--zone=zone-1 i',
                       ['instance-1',
                        'instance-2',
                        'instance-3'])

  def testSetDiskAutoDeleteCompletion(self):
    self.runTest('set-disk-auto-delete')

  def testSetMachineTypeCompletion(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    mtype = '--machine-type ' + machine_type_resources.MACHINE_TYPES[0].name
    self.RunCompletion('beta compute instances set-machine-type ' + mtype +
                       ' --zone=zone-1 i',
                       ['instance-3',
                        'instance-2',
                        'instance-1'])

  def testUseMatchingZoneProperty(self):
    prev_default = properties.VALUES.compute.zone.Get(required=False)
    properties.VALUES.compute.zone.Set('zone-1')
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion('compute instances delete i',
                       ['instance-3',
                        'instance-2',
                        'instance-1'])
    properties.VALUES.compute.zone.Set(prev_default)

  def testIgnoreNonMatchingZoneProperty(self):
    prev_default = properties.VALUES.compute.zone.Get(required=False)
    properties.VALUES.compute.zone.Set('not-zone-1')
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion('compute instances delete i',
                       ['instance-2\\ --zone=zone-1',
                        'instance-3\\ --zone=zone-1',
                        'instance-1\\ --zone=zone-1'])
    properties.VALUES.compute.zone.Set(prev_default)

  def testUseMatchingZoneFlag(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion('compute instances delete --zone=zone-1 i',
                       ['instance-3',
                        'instance-2',
                        'instance-1'])

  def testUseNonMatchingZoneFlag(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion('compute instances delete --zone=fake-zone i',
                       [''])

  def testStaticCompletions(self):
    self.RunCompletion('compu', ['compute'])
    self.RunCompletion('compute inst', ['instance-groups', 'instances',
                                        'instance-templates'])
    self.RunCompletion('compute instances li', ['list'])
    self.RunCompletion('compute instances list --li', ['--limit'])


if __name__ == '__main__':
  test_case.main()
