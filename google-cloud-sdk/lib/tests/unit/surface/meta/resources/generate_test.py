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

"""Tests for the `gcloud meta resources generate` command."""

from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.core import resources
from tests.lib import calliope_test_base


class GenerateCommandTest(calliope_test_base.CalliopeTestBase):

  def testGenerateDefaultReturn(self):
    actual = self.Run('meta resources generate --format=disable '
                      '--collection=compute.instances')
    expected = [
        'https://www.googleapis.com/compute/v1/projects/my-project-1/'
        'zones/my-zone-1/instances/my-instance-1'
    ]
    self.assertEqual(expected, actual)

  def testGenerateOneReturn(self):
    actual = self.Run('meta resources generate --format=disable '
                      '--collection=compute.instances --count=1')
    expected = [
        'https://www.googleapis.com/compute/v1/projects/my-project-1/'
        'zones/my-zone-1/instances/my-instance-1',
    ]
    self.assertEqual(expected, actual)

  def testGenerateTwoReturn(self):
    actual = self.Run('meta resources generate --format=disable '
                      '--collection=compute.instances --count=2')
    expected = [
        'https://www.googleapis.com/compute/v1/projects/my-project-1/'
        'zones/my-zone-1/instances/my-instance-1',
        'https://www.googleapis.com/compute/v1/projects/my-project-2/'
        'zones/my-zone-2/instances/my-instance-2',
    ]
    self.assertEqual(expected, actual)

  def testGenerateThreeJson(self):
    self.Run('meta resources generate --format=json '
             '--collection=compute.instances --count=3')
    self.AssertOutputEquals("""\
[
  "https://www.googleapis.com/compute/v1/projects/my-project-1/zones/my-zone-1/instances/my-instance-1",
  "https://www.googleapis.com/compute/v1/projects/my-project-2/zones/my-zone-2/instances/my-instance-2",
  "https://www.googleapis.com/compute/v1/projects/my-project-3/zones/my-zone-3/instances/my-instance-3"
]
""")

  def testGenerateNoCollection(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --collection: Must be specified.'):
      self.Run('meta resources generate --format=json')

  def testGenerateUnknownApi(self):
    with self.AssertRaisesExceptionMatches(
        apis_util.UnknownAPIError,
        'API named [foo] does not exist in the APIs map'):
      self.Run('meta resources generate --format=json --collection=foo.bar')

  def testGenerateUnknownCollection(self):
    with self.AssertRaisesExceptionMatches(
        resources.InvalidCollectionException,
        'unknown collection [compute.foo]'):
      self.Run('meta resources generate --format=json --collection=compute.foo')


if __name__ == '__main__':
  calliope_test_base.main()
