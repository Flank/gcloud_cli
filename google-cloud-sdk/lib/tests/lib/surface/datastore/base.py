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
"""Base class for all Datastore Command Unit tests."""

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class DatastoreCommandUnitTest(cli_test_base.CliTestBase,
                               sdk_test_base.WithFakeAuth):
  """A base class for Datastore command unit tests."""

  def SetUp(self):
    self.mock_datastore_v1 = mock.Client(client_class=apis.GetClientClass(
        'datastore', 'v1'))
    self.mock_datastore_v1.Mock()
    self.addCleanup(self.mock_datastore_v1.Unmock)
    properties.VALUES.core.disable_prompts.Set(True)

  def Serialize(self, x):
    """Serialize a list or dict into a filter-compatible format."""
    if isinstance(x, dict):
      return ','.join(['%s=%s' % (k, v) for k, v in x.iteritems()])
    elif isinstance(x, list):
      return ','.join(x)
    else:
      raise ValueError('%s is not a dict or list: %s', x, type(x))

  def Project(self):
    """Override to set the application project."""
    return 'my-test-project'

  def RunDatastoreTest(self, command):
    """Helper to run command with appropriate flags set."""
    return self.Run('datastore %s --format=disable' % command)
