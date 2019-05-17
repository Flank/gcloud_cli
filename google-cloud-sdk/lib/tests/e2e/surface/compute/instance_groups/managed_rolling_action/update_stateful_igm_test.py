# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Integration tests for stateful and updater integration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib.surface.compute import e2e_managers_stateful_test_base
from tests.lib.surface.compute import e2e_test_base


class UpdateStatefulIgmZonalAlphaTest(
    e2e_managers_stateful_test_base.ManagedStatefulTestBase):

  def SetUp(self):
    self.prefix = 'mig-update-stateful-igm-zonal'
    self.scope = e2e_test_base.ZONAL
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _CreateStatefulIgm(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1', 'disk2', 'disk3'])
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name,
        stateful_names=True,
        stateful_disks=['disk1', 'disk3'])
    return igm_name, instance_template_name

  def testReplaceIgmWithStatefulDisks(self):
    igm_name, _ = self._CreateStatefulIgm()
    try:
      self.Run("""
                 compute instance-groups managed rolling-action replace
                 {group_name} {scope_flag}
               """.format(
                   group_name=igm_name,
                   scope_flag=self.GetScopeFlag()))
      self.DescribeManagedInstanceGroup(igm_name)
      self.AssertNewOutputContainsAll([
          igm_name,
          'replacementMethod: RECREATE',
          """
            maxSurge:
              calculated: 0
              fixed: 0
          """,
      ], normalize_space=True)
    except exceptions.Error:
      # If Updater+Stateful is disabled, error will be returned
      self.AssertNewErrContains('UpdatePolicy with type set to PROACTIVE is '
                                'not allowed when Stateful is used')

  def testReplaceIgmWithStatefulDisksEnforcingSubstituteReplacementMethod(self):
    igm_name, _ = self._CreateStatefulIgm()
    try:
      self.Run(
          """
            compute instance-groups managed rolling-action replace
            {group_name} {scope_flag} --replacement-method=substitute
          """.format(
              group_name=igm_name,
              scope_flag=self.GetScopeFlag()))
    except exceptions.Error:
      pass
    self.AssertNewErrContains('--replacement-method has to be RECREATE')

  def testStartUpdateIgmWithStatefulDisks(self):
    igm_name, template_name = self._CreateStatefulIgm()
    try:
      self.Run("""
                 compute instance-groups managed rolling-action start-update
                 {group_name} {scope_flag} --version=template={template},name=new
               """.format(
                   group_name=igm_name,
                   scope_flag=self.GetScopeFlag(),
                   template=template_name))
      self.DescribeManagedInstanceGroup(igm_name)
      self.AssertNewOutputContainsAll([
          igm_name,
          'replacementMethod: RECREATE',
          """
            maxSurge:
              calculated: 0
              fixed: 0
          """,
      ], normalize_space=True)
    except exceptions.Error:
      # If Updater+Stateful is disabled, error will be returned
      self.AssertNewErrContains('UpdatePolicy with type set to PROACTIVE is '
                                'not allowed when Stateful is used')

  def testStartUpdateIgmWithStatefulDisksEnforcingMaxSurgeNonZero(self):
    igm_name, template_name = self._CreateStatefulIgm()
    try:
      self.Run(
          """
            compute instance-groups managed rolling-action start-update
            {group_name} {scope_flag} --version=template={template},name=new
            --max-surge=1
          """.format(
              group_name=igm_name,
              scope_flag=self.GetScopeFlag(),
              template=template_name))
    except exceptions.Error:
      pass
    self.AssertNewErrContains('--max-surge has to be 0')


class UpdateStatefulIgmRegionalAlphaTest(
    UpdateStatefulIgmZonalAlphaTest):

  def SetUp(self):
    self.prefix = 'mig-update-stateful-igm-regional'
    self.scope = e2e_test_base.REGIONAL


if __name__ == '__main__':
  e2e_test_base.main()
