# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.console.style import log as style_log
from tests.lib import sdk_test_base
from tests.lib import test_case


# TODO(b/117488015): Port over tests from regular log.
class LogResourceChangeTest(sdk_test_base.WithOutputCapture):

  def SetUp(self):
    properties.VALUES.core.color_theme.Set('testing')

  def testCreated(self):
    style_log.CreatedResource('my-cluster')
    self.AssertErrEquals('Created [my-cluster](RESOURCE_NAME).\n')

  def testCreatedNoResourceKind(self):
    style_log.CreatedResource(None)
    self.AssertErrEquals('Created.\n')

  def testCreatedKind(self):
    style_log.CreatedResource(None, kind='cluster')
    self.AssertErrEquals('Created cluster.\n')

  def testCreatedKindDetails(self):
    style_log.CreatedResource('my-cluster', kind='cluster',
                              details='in region [us-east1]')
    self.AssertErrEquals(
        'Created cluster [my-cluster](RESOURCE_NAME) in region [us-east1].\n')

  def testCreatedKindDetailsFailed(self):
    style_log.CreatedResource('my-cluster', kind='cluster',
                              details='in region [us-east1]',
                              failed='Permission denied')
    self.AssertErrEquals(
        'ERROR: Failed to create cluster [my-cluster](RESOURCE_NAME) in '
        'region [us-east1]: Permission denied.\n')

  def testCreatedAsync(self):
    style_log.CreatedResource('my-cluster', is_async=True)
    self.AssertErrEquals(
        'Create in progress for [my-cluster](RESOURCE_NAME).\n')

  def testCreatedKindAsync(self):
    style_log.CreatedResource('my-cluster', kind='cluster', is_async=True)
    self.AssertErrEquals(
        'Create in progress for cluster [my-cluster](RESOURCE_NAME).\n')

  def testCreatedKindDetailsAsync(self):
    style_log.CreatedResource('my-cluster', kind='cluster',
                              details='in region [us-east1]', is_async=True)
    self.AssertErrEquals(
        'Create in progress for cluster [my-cluster](RESOURCE_NAME) in region '
        '[us-east1].\n')

  def testDeleted(self):
    style_log.DeletedResource('my-cluster')
    self.AssertErrEquals('Deleted [my-cluster](RESOURCE_NAME).\n')

  def testDeletedAsync(self):
    style_log.DeletedResource('my-cluster', is_async=True)
    self.AssertErrEquals(
        'Delete in progress for [my-cluster](RESOURCE_NAME).\n')

  def testRestored(self):
    style_log.RestoredResource('my-cluster')
    self.AssertErrEquals('Restored [my-cluster](RESOURCE_NAME).\n')

  def testRestoredAsync(self):
    style_log.RestoredResource('my-cluster', is_async=True)
    self.AssertErrEquals(
        'Restore in progress for [my-cluster](RESOURCE_NAME).\n')

  def testUpdated(self):
    style_log.UpdatedResource('my-cluster')
    self.AssertErrEquals('Updated [my-cluster](RESOURCE_NAME).\n')

  def testUpdatedAsync(self):
    style_log.UpdatedResource('my-cluster', is_async=True)
    self.AssertErrEquals(
        'Update in progress for [my-cluster](RESOURCE_NAME).\n')

  def testReset(self):
    style_log.ResetResource('mytpu')
    self.AssertErrEquals('Reset [mytpu](RESOURCE_NAME).\n')

  def testResetAsync(self):
    style_log.ResetResource('mytpu', is_async=True)
    self.AssertErrEquals('Reset in progress for [mytpu](RESOURCE_NAME).\n')


if __name__ == '__main__':
  test_case.main()
