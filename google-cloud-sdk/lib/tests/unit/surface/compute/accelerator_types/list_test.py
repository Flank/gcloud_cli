# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the accelerator types list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.accelerator_types import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
import mock


class AcceleratorTypesListTest(test_base.BaseTest,
                               completer_test_base.CompleterBase):

  def _MakeAcceleratorTypes(self, msgs, api):
    """Creates a set of accelerator types messages for the given API version.

    Args:
      msgs: The compute messages API handle.
      api: The API version for which to create the instances.

    Returns:
      An aggregated list of message objects representing accelerator types.
    """
    prefix = 'https://compute.googleapis.com/compute/' + api
    return [
        msgs.AcceleratorType(
            name='nvidia-tesla-k80',
            description='Nvidia Tesla K80',
            selfLink=(prefix + '/projects/my-project/'
                      'zones/zone-1/acceleratorTypes/nvidia-tesla-k80'),
            zone=(prefix + '/projects/my-project/zones/zone-1')),
        msgs.AcceleratorType(
            name='nvidia-grid-k2',
            description='Nvidia Grid K2',
            selfLink=(prefix + '/projects/my-project/'
                      'zones/zone-1/acceleratorTypes/nvidia-grid-k2'),
            zone=(prefix + '/projects/my-project/zones/zone-1')),
        msgs.AcceleratorType(
            name='nvidia-grid-k2',
            description='Nvidia Grid K2',
            selfLink=(prefix + '/projects/my-project/'
                      'zones/zone-2/acceleratorTypes/nvidia-grid-k2'),
            zone=(prefix + '/projects/my-project/zones/zone-2')),
    ]

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            self._MakeAcceleratorTypes(self.messages, 'v1'))
    ]

  def testAggregatedOutput(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            self._MakeAcceleratorTypes(self.messages, 'v1'))
    ]

    self.Run('compute accelerator-types list')
    self.AssertOutputEquals(
        """\
            NAME ZONE DESCRIPTION
            nvidia-tesla-k80 zone-1 Nvidia Tesla K80
            nvidia-grid-k2 zone-1 Nvidia Grid K2
            nvidia-grid-k2 zone-2 Nvidia Grid K2
            """,
        normalize_space=True)

  def testSslCertificatesCompleter(self):
    self.make_requests.side_effect = iter(
        [self._MakeAcceleratorTypes(self.messages, 'v1')])
    self.RunCompleter(
        flags.AcceleratorTypesCompleter,
        expected_command=[
            'compute',
            'accelerator-types',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'nvidia-grid-k2',
            'nvidia-tesla-k80',
            'nvidia-grid-k2',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
