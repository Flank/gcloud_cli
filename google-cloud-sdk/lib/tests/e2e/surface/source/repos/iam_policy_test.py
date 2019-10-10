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
"""Test of the 'get-iam-policy' and 'set-iam-policy' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.source import base


@sdk_test_base.Filters.RunOnlyInBundle
class GetIamPolicyTest(base.SourceIntegrationTest):

  @contextlib.contextmanager
  def _Repository(self, name):
    self.RunSourceRepos(['create', name])
    yield
    self.RunSourceRepos(['delete', name])

  def testGetIamPolicy(self):
    properties.VALUES.core.user_output_enabled.Set(True)

    repo_name = next(e2e_utils.GetResourceNameGenerator(prefix='iamtest'))

    with self._Repository(repo_name):
      self.ClearOutput()
      self.RunSourceRepos(['get-iam-policy', repo_name, '--format=json'])
      policy = self.GetOutput()

      policy_file = self.Touch(directory=self.temp_path, contents=policy)
      self.ClearOutput()
      self.RunSourceRepos(
          ['set-iam-policy', repo_name, policy_file, '--format=json'])
      # set changes the etag, so the new policy isn't the same as the old.
      self.AssertOutputNotEquals(policy, normalize_space=True)
      # but let's make sure it looks right
      self.AssertOutputContains('{\n"etag": "', normalize_space=True)


if __name__ == '__main__':
  test_case.main()
