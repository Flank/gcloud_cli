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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.firebase.test import unit_base
import six


class UtilTests(unit_base.TestMockClientTest):
  """Unit tests for test/lib/util.py."""

  def testGetProject_NoProjectSet(self):
    # Mock out properties so that core.project appears to not be set by user.
    self.prop_mock = self.StartObjectPatch(
        properties.VALUES.core.project, 'Get')
    self.prop_mock.return_value = None

    with self.assertRaises(exceptions.MissingProjectError) as ex_ctx:
      util.GetProject()
    self.assertIn('No project specified', six.text_type(ex_ctx.exception))
    self.assertIn('gcloud config set project', six.text_type(ex_ctx.exception))

  def testGetProject_ProjectSet(self):
    properties.VALUES.core.project.Set(self.PROJECT_ID)
    self.assertEqual(util.GetProject(), self.PROJECT_ID)


if __name__ == '__main__':
  test_case.main()
