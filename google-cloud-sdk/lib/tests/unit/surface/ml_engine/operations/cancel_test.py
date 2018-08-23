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
"""ml-engine operations cancel tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class CancelTestBase(object):

  def SetUp(self):
    self.client.projects_operations.Cancel.Expect(
        self.msgs.MlProjectsOperationsCancelRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        self.msgs.GoogleProtobufEmpty()
    )
    properties.VALUES.core.user_output_enabled.Set(False)

  def testCancel(self):
    self.assertEqual(
        self.Run('ml-engine operations cancel opId'),
        self.msgs.GoogleProtobufEmpty())


class CancelGaTest(CancelTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(CancelGaTest, self).SetUp()


class CancelBetaTest(CancelTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(CancelBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
