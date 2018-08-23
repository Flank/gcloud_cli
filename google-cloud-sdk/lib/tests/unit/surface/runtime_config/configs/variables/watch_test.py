# -*- coding: utf-8 -*- #
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
"""Tests for surface.runtime_config.configs.variables.watch."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ssl

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base
import mock


# An error class that extends both SSLError (what we want), and
# apitools_exceptions.Error so that the mock client methods accept it.
class MockSSLError(ssl.SSLError, apitools_exceptions.Error):
  pass


class VariablesWatchTest(base.RuntimeConfigTestBase):

  def testWatchSucceeds(self):
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesWatchRequest(
        name=var_name,
        watchVariableRequest=self.messages.WatchVariableRequest(
            newerThan=None,
        )
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        state=self.messages.Variable.StateValueValuesEnum.UPDATED,
        value=b'value1',
    )

    self.variable_client.Watch.Expect(request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'variables watch var1 --config-name foo')

    self.assertEqual(util.FormatVariable(wanted_result), got_result)

  def testWatchMultiSegmentName(self):
    var_name = 'projects/{0}/configs/foo/variables/var1/var2'.format(
        self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesWatchRequest(
        name=var_name,
        watchVariableRequest=self.messages.WatchVariableRequest(
            newerThan=None,
        )
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        state=self.messages.Variable.StateValueValuesEnum.UPDATED,
        value=b'value1',
    )

    self.variable_client.Watch.Expect(request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'variables watch var1/var2 --config-name foo')

    self.assertEqual(util.FormatVariable(wanted_result), got_result)

  def testWatchNewerThan(self):
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesWatchRequest(
        name=var_name,
        watchVariableRequest=self.messages.WatchVariableRequest(
            newerThan='2016-05-16T00:00:00.000Z',
        )
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2017-04-16T00:00:00Z',
        state=self.messages.Variable.StateValueValuesEnum.UPDATED,
        value=b'value1',
    )

    self.variable_client.Watch.Expect(request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'variables watch var1 --config-name foo '
        '--newer-than 2016-05-16T00:00:00Z')

    self.assertEqual(util.FormatVariable(wanted_result), got_result)

  def testWatchNotFound(self):
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesWatchRequest(
        name=var_name,
        watchVariableRequest=self.messages.WatchVariableRequest(
            newerThan=None,
        )
    )
    exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.variable_client.Watch.Expect(request, exception=exception)
    try:
      self.RunRuntimeConfig(
          'variables watch var1 --config-name foo')
    except api_exceptions.HttpException as e:
      self.assertEqual(e.exit_code, 1)  # 1 means something other than timeout
    else:
      self.fail('No HttpException raised')

  def testWatchServerTimeout(self):
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesWatchRequest(
        name=var_name,
        watchVariableRequest=self.messages.WatchVariableRequest(
            newerThan=None,
        )
    )
    exception = base.MakeHttpError(code=504, status='DEADLINE_EXCEEDED')

    self.variable_client.Watch.Expect(request, exception=exception)
    try:
      self.RunRuntimeConfig(
          'variables watch var1 --config-name foo')
    except exceptions.OperationTimeoutError as e:
      self.assertEqual(e.exit_code, 2)  # 2 means we timed out
    else:
      self.fail('No exceptions.OperationTimeoutError raised')

  def testWatchClientTimeout(self):
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesWatchRequest(
        name=var_name,
        watchVariableRequest=self.messages.WatchVariableRequest(
            newerThan=None,
        )
    )
    # An error that is raised when an SSL socket timeout expires.
    exception = MockSSLError('The read operation timed out')

    self.variable_client.Watch.Expect(request, exception=exception)
    try:
      self.RunRuntimeConfig(
          'variables watch var1 --config-name foo --max-wait 5')
    except exceptions.OperationTimeoutError as e:
      self.assertEqual(e.exit_code, 2)  # 2 means we timed out
    else:
      self.fail('No exceptions.OperationTimeoutError raised')

  def testWatchNonTimeoutSocketError(self):
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesWatchRequest(
        name=var_name,
        watchVariableRequest=self.messages.WatchVariableRequest(
            newerThan=None,
        )
    )
    # A non-timeout error should be raised without additional handling
    exception = MockSSLError('Some other error')

    self.variable_client.Watch.Expect(request, exception=exception)
    with self.assertRaises(core_exceptions.NetworkIssueError):
      self.RunRuntimeConfig('variables watch var1 --config-name foo')

  def testWatchSetsSocketTimeoutAndRetries(self):
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesWatchRequest(
        name=var_name,
        watchVariableRequest=self.messages.WatchVariableRequest(
            newerThan=None,
        )
    )
    result = self.messages.Variable(
        name=var_name,
        updateTime='2017-04-16T00:00:00Z',
        state=self.messages.Variable.StateValueValuesEnum.UPDATED,
        value=b'value1',
    )
    self.variable_client.Watch.Expect(request, result)

    with mock.patch(
        'googlecloudsdk.api_lib.runtime_config.util.Client',
        wraps=util.Client) as m:
      self.RunRuntimeConfig(
          'variables watch var1 --config-name foo --max-wait 5')
      m.assert_called_with(timeout=5, num_retries=0)


if __name__ == '__main__':
  test_case.main()
