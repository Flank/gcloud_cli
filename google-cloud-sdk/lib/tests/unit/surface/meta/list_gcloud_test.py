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
"""Tests for gcloud meta list-gcloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import cli_tree
from tests.lib import calliope_test_base


class ListGCloudTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.StartObjectPatch(cli_tree, '_IsRunningUnderTest', return_value=True)
    self.WalkTestCli('sdk4')

  def testListCommandsAll(self):
    """Test the list of all commands via Run()."""
    self.Run('meta list-gcloud')
    self.AssertOutputIsGolden(self.test_data_dir, 'gcloud.json')

  def testListCommandsBranch(self):
    """Test the list of a command branch via Run()."""
    self.Run('meta list-gcloud --branch=sdk.subgroup')
    self.AssertOutputIsGolden(self.test_data_dir, 'gcloud-branch.json')

  def testListCompletionsBranch(self):
    """Test the list of the static completion CLI tree for a command branch."""
    self.Run('meta list-gcloud --completions --branch=sdk.subgroup')
    self.AssertOutputIsGolden(
        self.test_data_dir,
        'gcloud_completions_branch.golden')


if __name__ == '__main__':
  calliope_test_base.main()
