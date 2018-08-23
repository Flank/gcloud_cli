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
"""Tests for Datapol API utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.category_manager import utils
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.projects import util as projects_test_util


class UtilTest(sdk_test_base.WithFakeAuth):

  def testGetProjectRef(self):
    """Test acquiring project resource object from utils.GetProjectResource."""
    project_id = projects_test_util.GetTestActiveProjectWithOrganizationParent(
    ).projectId
    self.addCleanup(properties.VALUES.core.project.Set,
                    properties.VALUES.core.project.Get())
    properties.VALUES.core.project.Set(project_id)
    self.assertEqual(
        resources.REGISTRY.Create(
            'cloudresourcemanager.projects', projectId=project_id),
        utils.GetProjectResource())


if __name__ == '__main__':
  test_case.main()
