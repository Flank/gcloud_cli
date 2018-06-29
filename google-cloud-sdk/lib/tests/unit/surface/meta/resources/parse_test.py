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

"""Tests for the `gcloud meta complete` command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.core import resources
from tests.lib import calliope_test_base


class ParseCommandTest(calliope_test_base.CalliopeTestBase):

  def testParseTwoGood(self):
    actual = self.Run('meta resources parse'
                      ' '
                      'https://www.googleapis.com/compute/v1/'
                      'projects/my-project-1/zones/my-zone-1/'
                      'instances/my-instance-1'
                      ' '
                      'https://www.googleapis.com/compute/v1/'
                      'projects/my-project-2/zones/my-zone-2/'
                      'instances/my-instance-2')
    expected = [
        {
            'api_name': 'compute',
            'api_version': 'v1',
            'collection': 'compute.instances',
            'params': {
                'instance': 'my-instance-1',
                'project': 'my-project-1',
                'zone': 'my-zone-1'
            },
            'uri': ('https://www.googleapis.com/compute/v1/'
                    'projects/my-project-1/zones/my-zone-1/'
                    'instances/my-instance-1'),
        },
        {
            'api_name': 'compute',
            'api_version': 'v1',
            'collection': 'compute.instances',
            'params': {
                'instance': 'my-instance-2',
                'project': 'my-project-2',
                'zone': 'my-zone-2'
            },
            'uri': ('https://www.googleapis.com/compute/v1/'
                    'projects/my-project-2/zones/my-zone-2/'
                    'instances/my-instance-2'),
        },
    ]
    self.assertEqual(expected, actual)

  def testParseOneBadOneGood(self):
    with self.AssertRaisesExceptionMatches(
        resources.InvalidResourceException,
        'could not parse resource [https://www.googleapis.com/foo/v1/'
        'projects/my-project-1/bars/my-zone-1/instances/my-instance-1]: '
        'unknown api foo'):
      self.Run('meta resources parse'
               ' '
               'https://www.googleapis.com/foo/v1/'
               'projects/my-project-1/bars/my-zone-1/'
               'instances/my-instance-1'
               ' '
               'https://www.googleapis.com/compute/v1/'
               'projects/my-project-2/zones/my-zone-2/'
               'instances/my-instance-2')

  def testParseOneBadOneGoodWithNoStackTrace(self):
    actual = self.Run('meta resources parse --no-stack-trace'
                      ' '
                      'https://www.googleapis.com/foo/v1/'
                      'projects/my-project-1/bars/my-zone-1/'
                      'instances/my-instance-1'
                      ' '
                      'https://www.googleapis.com/compute/v1/'
                      'projects/my-project-2/zones/my-zone-2/'
                      'instances/my-instance-2')
    expected = [
        {
            'error': ('could not parse resource [https://www.googleapis.com/'
                      'foo/v1/projects/my-project-1/bars/my-zone-1/'
                      'instances/my-instance-1]: unknown api foo'),
            'uri': ('https://www.googleapis.com/foo/v1/'
                    'projects/my-project-1/bars/my-zone-1/'
                    'instances/my-instance-1'),
        },
        {
            'api_name': 'compute',
            'api_version': 'v1',
            'collection': 'compute.instances',
            'params': {
                'instance': 'my-instance-2',
                'project': 'my-project-2',
                'zone': 'my-zone-2'
            },
            'uri': ('https://www.googleapis.com/compute/v1/'
                    'projects/my-project-2/zones/my-zone-2/'
                    'instances/my-instance-2'),
        },
    ]
    self.assertEqual(expected, actual)


class ParseCommandInteractiveTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self._clear_io = False

  def Execute(self, command, track=None):
    if self._clear_io:
      self.ClearOutput()
      self.ClearErr()
    else:
      self._clear_io = True
    return self.Run(command, track=track)

  def testInteractiveParseEOF(self):
    self.Execute('meta resources parse')
    self.AssertErrEquals('PARSE> \n')
    self.AssertOutputEquals('')

  def testInteractiveParseEmptyLine(self):
    self.WriteInput('\n')
    self.Execute('meta resources parse')
    self.AssertErrEquals('PARSE> PARSE> PARSE> \n')
    self.AssertOutputEquals('')

  def testInteractiveParseTwoGood(self):
    self.WriteInput(
        'https://www.googleapis.com/compute/v1/projects/my-project-1/'
        'zones/my-zone-1/instances/my-instance-1\n'
        'https://www.googleapis.com/compute/v1/projects/my-project-2/'
        'zones/my-zone-2/instances/my-instance-2\n')
    self.Run('meta resources parse')
    self.AssertOutputEquals("""\
{
  "instance": "my-instance-1",
  "project": "my-project-1",
  "zone": "my-zone-1"
}
{
  "instance": "my-instance-2",
  "project": "my-project-2",
  "zone": "my-zone-2"
}
""")
    self.AssertErrEquals('PARSE> PARSE> PARSE> PARSE> \n')

  def testInteractiveParseOneBadOneGood(self):
    with self.AssertRaisesExceptionMatches(
        resources.InvalidResourceException,
        'could not parse resource [https://www.googleapis.com/foo/v1/'
        'projects/my-project-1/bars/my-zone-1/instances/my-instance-1]: '
        'unknown api foo'):
      self.WriteInput(
          'https://www.googleapis.com/foo/v1/projects/my-project-1/'
          'bars/my-zone-1/instances/my-instance-1\n'
          'https://www.googleapis.com/compute/v1/projects/my-project-2/'
          'zones/my-zone-2/instances/my-instance-2\n')
      self.Run('meta resources parse')
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'PARSE> '
        'ERROR: (gcloud.meta.resources.parse) '
        'could not parse resource [https://www.googleapis.com/foo/v1/'
        'projects/my-project-1/bars/my-zone-1/instances/my-instance-1]: '
        'unknown api foo\n')

  def testInteractiveParseOneBadOneGoodWithNoStackTrace(self):
    self.WriteInput(
        'https://www.googleapis.com/foo/v1/projects/my-project-1/'
        'bars/my-zone-1/instances/my-instance-1\n'
        'https://www.googleapis.com/compute/v1/projects/my-project-2/'
        'zones/my-zone-2/instances/my-instance-2\n')
    self.Run('meta resources parse --no-stack-trace')
    self.AssertOutputEquals("""\
{
  "instance": "my-instance-2",
  "project": "my-project-2",
  "zone": "my-zone-2"
}
""")
    self.AssertErrEquals(
        'PARSE> '
        'ERROR: could not parse resource [https://www.googleapis.com/foo/v1/'
        'projects/my-project-1/bars/my-zone-1/instances/my-instance-1]: '
        'unknown api foo\n'
        'PARSE> PARSE> PARSE> \n')


if __name__ == '__main__':
  calliope_test_base.main()
