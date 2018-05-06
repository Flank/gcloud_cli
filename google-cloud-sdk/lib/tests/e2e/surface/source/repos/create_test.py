# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Test of the source repos create, delete, and describe commands."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.source import base


@sdk_test_base.Filters.RunOnlyInBundle
class CreateTest(base.SourceIntegrationTest):

  def testCreate(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    repo_name = next(e2e_utils.GetResourceNameGenerator(prefix='createtest'))
    self.RunSourceRepos(['create', repo_name, '--format=default'])
    try:
      self.AssertErrContains('Created [createtest', normalize_space=True)
      self.AssertOutputContains('repos/createtest', normalize_space=True)
      self.ClearOutput()
      self.RunSourceRepos(['describe', repo_name])
      self.AssertOutputMatches(
          'name: projects/.*/repos/{repo}\nurl: .*/p/.*/r/{repo}'.format(
              repo=repo_name))
    finally:
      self.RunSourceRepos(['delete', repo_name])


if __name__ == '__main__':
  test_case.main()
