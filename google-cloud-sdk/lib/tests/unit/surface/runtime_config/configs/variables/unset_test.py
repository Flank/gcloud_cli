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
"""Tests for surface.runtime_config.configs.variables.unset."""

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class VariablesUnsetTest(base.RuntimeConfigTestBase):

  def testUnset(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesDeleteRequest(
        name='projects/{0}/configs/foo/variables/var1'.format(self.Project()),
        recursive=False,
    )

    self.variable_client.Delete.Expect(request, self.messages.Empty())
    got_result = self.RunRuntimeConfig(
        'variables unset var1 --config-name foo')

    self.assertIsNone(got_result)  # nothing should be returned.

  def testUnsetMultiSegmentName(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesDeleteRequest(
        name='projects/{0}/configs/foo/variables/var1/var2'.format(
            self.Project()),
        recursive=False,
    )

    self.variable_client.Delete.Expect(request, self.messages.Empty())
    got_result = self.RunRuntimeConfig(
        'variables unset var1/var2 --config-name foo')

    self.assertIsNone(got_result)  # nothing should be returned.

  def testUnsetRecursive(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesDeleteRequest(
        name='projects/{0}/configs/foo/variables/var1'.format(self.Project()),
        recursive=True,
    )

    self.variable_client.Delete.Expect(request, self.messages.Empty())
    got_result = self.RunRuntimeConfig(
        'variables unset var1 --config-name foo --recursive')

    self.assertIsNone(got_result)  # nothing should be returned.

  def testUnsetFailIfAbsentFails(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesDeleteRequest(
        name='projects/{0}/configs/foo/variables/var1'.format(self.Project()),
        recursive=False,
    )
    exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.variable_client.Delete.Expect(request,
                                       exception=exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunRuntimeConfig('variables unset var1 --config-name foo '
                            '--fail-if-absent')

  def testUnsetFailIfAbsentSucceeds(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesDeleteRequest(
        name='projects/{0}/configs/foo/variables/var1'.format(self.Project()),
        recursive=False,
    )

    self.variable_client.Delete.Expect(request, self.messages.Empty())
    # Shouldn't raise since the delete succeeds.
    got_result = self.RunRuntimeConfig(
        'variables unset var1 --config-name foo --fail-if-absent')

    self.assertIsNone(got_result)  # nothing should be returned.

  def testUnsetIgnoresNotFound(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesDeleteRequest(
        name='projects/{0}/configs/foo/variables/var1'.format(self.Project()),
        recursive=False,
    )
    exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.variable_client.Delete.Expect(request,
                                       exception=exception)

    # Should run without raising.
    self.RunRuntimeConfig('variables unset var1 --config-name foo')

  def testUnsetNonRecursiveFailure(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesDeleteRequest(
        name='projects/{0}/configs/foo/variables/var1'.format(self.Project()),
        recursive=False,
    )
    exception = base.MakeHttpError(code=400, status='FAILED_PRECONDITION',
                                   message='Contains children')

    self.variable_client.Delete.Expect(request,
                                       exception=exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunRuntimeConfig('variables unset var1 --config-name foo')


if __name__ == '__main__':
  test_case.main()
