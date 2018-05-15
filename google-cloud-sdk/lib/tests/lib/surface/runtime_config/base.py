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

"""Base for Runtime Config surface unit tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
import contextlib
import time

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error


MESSAGE_MODULE = apis.GetMessagesModule('runtimeconfig', 'v1beta1')
CLIENT_CLASS = apis.GetClientClass('runtimeconfig', 'v1beta1')


class RuntimeConfigTestBase(sdk_test_base.WithFakeAuth,
                            cli_test_base.CliTestBase):
  """Base class for Runtime Config unit tests."""

  def SetUp(self):
    self.mocked_client = mock.Client(
        client_class=CLIENT_CLASS,
        real_client=CLIENT_CLASS(credentials=store.Load()))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    # Mock out time.sleep calls in operation polling
    # time of 0 is a problematic for dateutil since it adjust for timezone and
    # ends up getting negative time.
    self.time_mock = self.StartObjectPatch(time, 'time', return_value=1e6)
    self.sleep_mock = self.StartObjectPatch(time, 'sleep')

  def RunRuntimeConfig(self, command, output_enabled=False):
    properties.VALUES.core.user_output_enabled.Set(output_enabled)
    return self.Run('beta runtime-config configs {0}'.format(command))

  @property
  def config_client(self):
    return self.mocked_client.projects_configs

  @property
  def variable_client(self):
    return self.mocked_client.projects_configs_variables

  @property
  def waiter_client(self):
    return self.mocked_client.projects_configs_waiters

  @property
  def messages(self):
    return MESSAGE_MODULE


def MakeHttpError(code, status, message='Error'):
  """Create an exceptions.HttpError with a specified code, status and message.

  The HttpError is of the form that would be thrown by an apitools RPC.

  Args:
    code: int, the http error code
    status: str, the string error status (e.g., NOT_FOUND or DEADLINE_EXCEEDED)
    message: str, the error message

  Returns:
    the generated HttpError
  """
  del status  # TODO(b/67435348): Remove this wrapper entirely
  return http_error.MakeHttpError(code=code, message=message)


class RuntimeConfigIntegrationTest(
    e2e_base.WithServiceAuth, sdk_test_base.WithTempCWD):
  """A base class for runtime-config tests that need to use a real client."""

  def RunRuntimeConfig(self, command):
    return self.Run('beta runtime-config configs {0}'.format(command))

  @contextlib.contextmanager
  def _RuntimeConfig(self, prefix, description=''):
    name = next(e2e_utils.GetResourceNameGenerator(prefix))
    try:
      self.RunRuntimeConfig(
          'create {0} --description={1}'.format(name, description))
      yield name
    finally:
      self.RunRuntimeConfig('delete {0}'.format(name))
