# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Test of the 'list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.command_lib.util.concepts import resource_completer_test_base
from tests.lib.surface.bigtable import base


class ListCommandTestGA(base.BigtableV2TestBase, cli_test_base.CliTestBase,
                        resource_completer_test_base.ResourceCompleterBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.cmd = 'bigtable instances list'
    self.svc = self.client.projects_instances.List
    self.msg = self.msgs.BigtableadminProjectsInstancesListRequest(
        parent='projects/' + self.Project())

  def testList(self):
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.ListInstancesResponse(instances=[
            self.msgs.Instance(
                name='projects/' + self.Project() + '/instances/theinstance',
                displayName='thedisplayname',
                state=self.msgs.Instance.StateValueValuesEnum.READY)
        ]))
    self.Run(self.cmd)
    self.AssertOutputEquals('NAME         DISPLAY_NAME    STATE\n'
                            'theinstance  thedisplayname  READY\n')

  def testErrorResponse(self):
    with self.AssertHttpResponseError(self.svc, self.msg):
      self.Run(self.cmd)

  def testCompletion(self):
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.ListInstancesResponse(instances=[
            self.msgs.Instance(
                name='projects/' + self.Project() + '/instances/theinstance',
                displayName='thedisplayname',
                state=self.msgs.Instance.StateValueValuesEnum.READY)
        ]))
    self.RunCompletion('bigtable instances update t', ['theinstance'])

  def testCompletionNoProject(self):
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.ListInstancesResponse(instances=[
            self.msgs.Instance(
                name='projects/' + self.Project() + '/instances/theinstance',
                displayName='thedisplayname',
                state=self.msgs.Instance.StateValueValuesEnum.READY)
        ]))
    self.RunResourceCompleter(
        arguments.GetInstanceResourceSpec(),
        'instance',
        args={'--instance': 'theinstance'},
        projects=[self.Project()],
        expected_completions=['theinstance --project=' + self.Project()])


class ListCommandTestBeta(ListCommandTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ListCommandTestAlpha(ListCommandTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
