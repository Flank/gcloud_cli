# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests of the 'sinks' subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class SinksCreateTest(base.LoggingTestBase):

  def testCreateSuccess(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', filter='foo', includeChildren=False)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project', logSink=new_sink,
            uniqueWriterIdentity=True),
        new_sink)
    self.RunLogging('sinks create my-sink dest --log-filter=foo')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Created [https://logging.googleapis.com/v2/projects/my-project/sinks/my-sink].
More information about sinks can be found at https://cloud.google.com/logging/docs/export/configure_export
""")

  def testCreateProjectSinkWithChildrenSuccess(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', filter='foo', includeChildren=True)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project', logSink=new_sink,
            uniqueWriterIdentity=True),
        new_sink)
    self.RunLogging(
        'sinks create my-sink dest --log-filter=foo --include-children')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
WARNING: include-children only has an effect for sinks at the folder or organization level
Created [https://logging.googleapis.com/v2/projects/my-project/sinks/my-sink].
More information about sinks can be found at https://cloud.google.com/logging/docs/export/configure_export
""")

  def testCreateWithChildrenSuccess(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', filter='foo', includeChildren=True)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='organizations/my-org', logSink=new_sink,
            uniqueWriterIdentity=True),
        new_sink)
    self.RunLogging(
        'sinks create my-sink dest --organization=my-org --log-filter=foo '
        '--include-children')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Created [https://logging.googleapis.com/v2/organizations/my-org/sinks/my-sink].
More information about sinks can be found at https://cloud.google.com/logging/docs/export/configure_export
""")

  def testCreateSuccessEmptyFilter(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', includeChildren=False)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project', logSink=new_sink,
            uniqueWriterIdentity=True),
        new_sink)
    self.WriteInput('Y')
    self.RunLogging('sinks create my-sink dest')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Sink with empty filter matches all entries.

Do you want to continue (Y/n)?  \

Created [https://logging.googleapis.com/v2/projects/my-project/sinks/my-sink].
More information about sinks can be found at https://cloud.google.com/logging/docs/export/configure_export
""")

  def testListNoPerms(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', includeChildren=False)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project', logSink=new_sink,
            uniqueWriterIdentity=True),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('sinks create my-sink dest')

  def testListNoProject(self):
    self.RunWithoutProject('sinks create my-sink dest')

  def testListNoAuth(self):
    self.RunWithoutAuth('sinks create my-sink dest')


if __name__ == '__main__':
  test_case.main()
