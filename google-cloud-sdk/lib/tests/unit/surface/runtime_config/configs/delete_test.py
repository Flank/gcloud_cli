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
"""Tests for surface.runtime_config.configs.delete."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class ConfigurationsDeleteTest(base.RuntimeConfigTestBase):

  def testDelete(self):
    config_name = 'projects/{0}/configs/foobar'.format(self.Project())
    expected_request = self.messages.RuntimeconfigProjectsConfigsDeleteRequest(
        name=config_name,
    )
    wanted_result = self.messages.Empty()

    self.config_client.Delete.Expect(expected_request, wanted_result)
    got_result = self.RunRuntimeConfig('delete foobar')

    # Delete.Run() doesn't return anything.
    self.assertIsNone(got_result)

  def testDeleteNotFound(self):
    config_name = 'projects/{0}/configs/foobar'.format(self.Project())
    expected_request = self.messages.RuntimeconfigProjectsConfigsDeleteRequest(
        name=config_name,
    )
    wanted_exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.config_client.Delete.Expect(expected_request,
                                     exception=wanted_exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunRuntimeConfig('delete foobar')


if __name__ == '__main__':
  test_case.main()
