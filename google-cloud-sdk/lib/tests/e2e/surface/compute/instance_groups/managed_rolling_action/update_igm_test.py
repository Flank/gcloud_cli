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
"""Integration tests for IGM updater."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_managers_stateful_test_base
from tests.lib.surface.compute import e2e_test_base


class UpdateIgmZonalTest(e2e_managers_stateful_test_base.ManagedStatefulTestBase
                        ):

  def SetUp(self):
    self.prefix = 'mig-update-igm-zonal'
    self.scope = e2e_test_base.ZONAL
    self.track = calliope_base.ReleaseTrack.GA

  def testUpdateIgmWithSubstituteReplacementMethod(self):
    self.doTestUpdateIgmWithReplacementMethod(replacement_method='substitute')

  def testUpdateIgmWithRecreateReplacementMethod(self):
    self.doTestUpdateIgmWithReplacementMethod(replacement_method='recreate')

  def doTestUpdateIgmWithReplacementMethod(self, replacement_method):
    instance_template_name = self.CreateInstanceTemplate(
        machine_type='n1-standard-1')
    instance_template2_name = self.CreateInstanceTemplate(
        machine_type='n1-standard-2')

    igm_name = self.CreateInstanceGroupManager(instance_template_name, size=1)

    self.WaitUntilStable(igm_name)
    old_instance_name = self.ExtractInstanceNameFromUri(
        self.GetInstanceUris(igm_name)[0])

    # Start update with SUBSTITUTE replacement method
    self.Run("""
          compute instance-groups managed rolling-action start-update
          {group_name} {scope_flag} --version=template={template_name}
          --max-surge=0 --max-unavailable=3
          --replacement-method={replacement_method}
        """.format(
            group_name=igm_name,
            scope_flag=self.GetScopeFlag(),
            template_name=instance_template2_name,
            replacement_method=replacement_method))
    self.WaitUntilStable(igm_name)

    new_instance_uris = self.GetInstanceUris(igm_name)
    new_instance_name = self.ExtractInstanceNameFromUri(new_instance_uris[0])
    self.assertEqual(len(new_instance_uris), 1)
    if replacement_method == 'substitute':
      self.assertNotEqual(new_instance_name, old_instance_name)
    else:
      self.assertEqual(new_instance_name, old_instance_name)
