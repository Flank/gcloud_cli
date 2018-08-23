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
"""Tests for the history_picker module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from surface.firebase.test.android import run
from tests.lib import test_case
from tests.lib.surface.firebase.test.android import unit_base

TOOLRESULTS_MESSAGES = apis.GetMessagesModule('toolresults', 'v1beta3')

HISTORY_LIST_REQ = TOOLRESULTS_MESSAGES.ToolresultsProjectsHistoriesListRequest(
    projectId=unit_base.AndroidUnitTestBase.PROJECT_ID,
    filterByName='superbowl.49')
HISTORY_WITH_ID1 = TOOLRESULTS_MESSAGES.History(
    name='superbowl.49', historyId='bh.1')
HISTORY_WITH_ID2 = TOOLRESULTS_MESSAGES.History(
    name='superbowl.49', historyId='bh.2')


class ToolResultsHistoryPickerTest(unit_base.AndroidMockClientTest):
  """Unit tests for the history picker."""

  def testHistoryCreatedIfDoesNotExist(self):
    self.tr_client.projects_histories.List.Expect(
        request=HISTORY_LIST_REQ,
        response=self.toolresults_msgs.ListHistoriesResponse(histories=[]))
    self.tr_client.projects_histories.Create.Expect(
        request=self.toolresults_msgs.ToolresultsProjectsHistoriesCreateRequest(
            projectId=self.PROJECT_ID,
            history=self.toolresults_msgs.History(
                name='superbowl.49', displayName='superbowl.49'),),
        response=HISTORY_WITH_ID1)

    history_id = self.picker.GetToolResultsHistoryId('superbowl.49')

    self.assertEqual('bh.1', history_id)

  def testHistoryNotCreatedIfAlreadyExists(self):
    self.tr_client.projects_histories.List.Expect(
        request=HISTORY_LIST_REQ,
        response=self.toolresults_msgs.ListHistoriesResponse(
            histories=[HISTORY_WITH_ID1]))

    history_id = self.picker.GetToolResultsHistoryId('superbowl.49')

    self.assertEqual('bh.1', history_id)

  def testUsesNewestHistoryIdIfMoreThanOneExists(self):
    self.tr_client.projects_histories.List.Expect(
        request=HISTORY_LIST_REQ,
        response=self.toolresults_msgs.ListHistoriesResponse(
            histories=[HISTORY_WITH_ID2, HISTORY_WITH_ID1]))

    history_id = self.picker.GetToolResultsHistoryId('superbowl.49')

    self.assertEqual('bh.2', history_id)

  def testFindHistoryId_UsesResultsHistoryNameIfPresent(self):
    args = self.NewTestArgs(
        results_history_name='superbowl.49', app_package='com.sea.hawks')
    history_name = run.PickHistoryName(args)
    self.assertEqual(history_name, 'superbowl.49')

    history2 = self.toolresults_msgs.History(
        name=history_name, historyId='bh.2')
    self.tr_client.projects_histories.List.Expect(
        request=self.toolresults_msgs.ToolresultsProjectsHistoriesListRequest(
            projectId=self.PROJECT_ID, filterByName=history_name),
        response=self.toolresults_msgs.ListHistoriesResponse(
            histories=[history2]))

    history_id = self.picker.GetToolResultsHistoryId(history_name)

    self.assertEqual('bh.2', history_id)

  def testFindHistoryId_UsesAppPackage_WhenNoHistoryNameIsGiven(self):
    args = self.NewTestArgs(
        results_history_name=None, app_package='com.sea.hawks')
    history_name = run.PickHistoryName(args)
    self.assertEqual(history_name, 'com.sea.hawks (gcloud)')

    history3 = self.toolresults_msgs.History(
        name=history_name, historyId='bh.3')
    self.tr_client.projects_histories.List.Expect(
        request=self.toolresults_msgs.ToolresultsProjectsHistoriesListRequest(
            projectId=self.PROJECT_ID, filterByName=history_name),
        response=self.toolresults_msgs.ListHistoriesResponse(
            histories=[history3]))

    history_id = self.picker.GetToolResultsHistoryId(history_name)
    self.assertEqual('bh.3', history_id)

  def testFindHistoryId_IsNoneWhenNoHistoryNameOrAppPackageIsGiven(self):
    args = self.NewTestArgs(results_history_name=None, app_package=None)
    history_name = run.PickHistoryName(args)
    history_id = self.picker.GetToolResultsHistoryId(history_name)

    self.assertEqual(None, history_id)


if __name__ == '__main__':
  test_case.main()
