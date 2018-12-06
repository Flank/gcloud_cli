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
"""Tests for asset utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.asset import utils
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case


class AssetUtilsTest(cli_test_base.CliTestBase, parameterized.TestCase):

  def testVerifyParent_Conflicting(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.ConflictingArgumentsException,
        '.*arguments not allowed simultaneously.*'):
      utils.VerifyParent('org_id', 'project_id')

  def testVerifyParent_Missing(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.RequiredArgumentException,
        '.*Should specify the project or organization name.*'):
      utils.VerifyParent(None, None)

  @parameterized.parameters(('org_id', None), (None, 'project_id'))
  def testVerifyParent_Normal(self, org_id, project_id):
    utils.VerifyParent(org_id, project_id)

  def testGetParentName_Organization(self):
    self.assertEqual(
        utils.GetParentName('org_id', None), 'organizations/org_id')

  def testGetParentName_Project(self):
    self.assertEqual(
        utils.GetParentName(None, 'project_id'), 'projects/project_id')


if __name__ == '__main__':
  test_case.main()
