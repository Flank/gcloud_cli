# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Base classes for repos tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


class SourceTest(cli_test_base.CliTestBase):

  def RunSource(self, command):
    return self.Run(['alpha', 'source'] + command)

  def RunSourceRepos(self, command):
    """Run gcloud source repos [command].

    It uses the inherited CliTestBase.Run method, which uses self.track to
    determine which track to run on.

    Args:
      command: list giving the command to run, without the source repos or track

    Returns:
      The result of executing the command.
    """
    return self.Run(['source', 'repos'] + command)


class SourceSdkTest(sdk_test_base.WithFakeAuth, SourceTest):
  pass


class SourceIntegrationTest(e2e_base.WithServiceAuth, SourceTest):
  """Base class for all source integration tests."""
