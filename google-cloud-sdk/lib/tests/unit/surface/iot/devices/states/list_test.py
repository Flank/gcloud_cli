# -*- coding: utf-8 -*- #
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

"""Tests for `gcloud iot states list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base

from six.moves import range  # pylint: disable=redefined-builtin


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class StatesListTest(base.CloudIotBase):

  def _MakeStates(self, num=10):
    states = []
    for idx in range(num):
      states.append(
          self.messages.DeviceState(
              updateTime='2017-01-{:02d}T00:00Z'.format(idx+1),
              binaryData=bytes(idx)
          )
      )
    return states

  def SetUp(self):
    self.device_name = (
        'projects/{}/locations/us-central1/registries/'
        'my-registry/devices/my-device'.format(self.Project()))

  def _ExpectListStates(self, states, num_states=None, device_name=None):
    """Helper function to add expected request & response for listing states.

    Args:
      states: [cloudiot_v1_messages.DeviceState], the states to return.
      num_states: int, the number of states.
      device_name: str, the URI of the parent device if not the default
        (self.device_name).
    """
    device_name = device_name or self.device_name
    service = self.client.projects_locations_registries_devices_states
    request_type = getattr(self.messages,
                           'CloudiotProjectsLocationsRegistries'
                           'DevicesStatesListRequest')
    service.List.Expect(
        request_type(name=device_name,
                     numStates=num_states),
        self.messages.ListDeviceStatesResponse(deviceStates=states)
    )

  def testList(self, track):
    self.track = track
    states = self._MakeStates()
    self._ExpectListStates(states)

    results = self.Run(
        'iot devices states list'
        '    --format disable '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.assertEqual(list(results), states)

  def testList_Limit(self, track):
    self.track = track
    states = self._MakeStates()
    self._ExpectListStates(states[-3:], num_states=3)

    self.Run(
        'iot devices states list'
        '    --limit 3 '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')
    self.AssertOutputEquals("""\
        UPDATE_TIME
        2017-01-08T00:00Z
        2017-01-09T00:00Z
        2017-01-10T00:00Z
        """, normalize_space=True)

  def testList_RelativeName(self, track):
    self.track = track
    states = self._MakeStates()
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-other-registry/'
                   'devices/my-other-device').format(self.Project())
    self._ExpectListStates(states, device_name=device_name)

    results = self.Run(
        'iot devices states list'
        '    --format disable '
        '    --device {}'.format(device_name))

    self.assertEqual(list(results), states)


if __name__ == '__main__':
  test_case.main()
