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

"""Tests for gcloud meta list-cli-trees."""

from googlecloudsdk.command_lib.meta import list_cli_trees
from tests.lib import calliope_test_base


class ListCliTreesTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.list_all = self.StartObjectPatch(list_cli_trees, 'ListAll')

  def testListCliTrees(self):
    self.Run(['meta', 'cli-trees', 'list'])
    self.list_all.assert_called_once_with(directory=None)

  def testListCliTreesWithDirectory(self):
    directory = 'foo/bar'
    self.Run(['meta', 'cli-trees', 'list', '--directory', directory])
    self.list_all.assert_called_once_with(directory=directory)


if __name__ == '__main__':
  calliope_test_base.main()
