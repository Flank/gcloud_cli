
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
"""E2E tests for `gcloud iot` commands."""
import contextlib

from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


class IotE2eTests(e2e_base.WithServiceAuth, cli_test_base.CliTestBase):

  _REGION = 'us-central1'

  @contextlib.contextmanager
  def _CreateDeviceRegistry(self, region):
    registry_id = next(e2e_utils.GetResourceNameGenerator('iot-registry'))
    try:
      self.Run('iot registries create '
               '    --region {} '
               '    {}'.format(region, registry_id))
      yield registry_id
    finally:
      self.WriteInput('y\n')
      self.Run('iot registries delete '
               '    --region {} '
               '    {}'.format(region, registry_id))

  @contextlib.contextmanager
  def _CreateDevice(self, region, registry_id):
    device_id = next(e2e_utils.GetResourceNameGenerator('iot-device'))
    try:
      self.Run(
          'iot devices create '
          '    --region {} '
          '    --registry {} '
          '   {}'.format(region, registry_id, device_id))
      yield device_id
    finally:
      self.WriteInput('y\n')
      self.Run(
          'iot devices delete '
          '    --region {} '
          '    --registry {} '
          '   {}'.format(region, registry_id, device_id))

  def _DescribeDevice(self, region, registry_id, device_id):
    return self.Run(
        'iot devices describe '
        '    --format disable '  # Disable format to get a return value
        '    --region {} '
        '    --registry {} '
        '    {}'.format(region, registry_id, device_id))

  def testIoTCommands(self):
    with self._CreateDeviceRegistry(self._REGION) as registry_id:
      with self._CreateDevice(self._REGION, registry_id) as device_id:
        device = self._DescribeDevice(self._REGION, registry_id, device_id)
    self.assertIn(registry_id, device.name)
    self.assertEqual(device.id, device_id)


if __name__ == '__main__':
  test_case.main()
