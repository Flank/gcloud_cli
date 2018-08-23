# -*- coding: utf-8 -*- #
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
"""Tests for the machine-types describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class MachineTypesDescribeTest(test_base.BaseTest,
                               completer_test_base.CompleterBase,
                               test_case.WithOutputCapture):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.MACHINE_TYPES[0]],
    ])

    self.Run("""
        compute machine-types describe my-machine-type --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.machineTypes,
          'Get',
          messages.ComputeMachineTypesGetRequest(
              machineType='my-machine-type',
              project='my-project',
              zone='zone-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            guestCpus: 1
            memoryMb: 3840
            name: n1-standard-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))

  def testUriCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.MACHINE_TYPES[0]],
    ])

    self.Run("""
        compute machine-types describe https://www.googleapis.com/compute/v1/projects/project-1/zones/zone-1/machineTypes/n1-standard-1
        """)

    self.CheckRequests(
        [(self.compute_v1.machineTypes,
          'Get',
          messages.ComputeMachineTypesGetRequest(
              machineType='n1-standard-1',
              project='project-1',
              zone='zone-1'))],
    )

  def testDesribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.MACHINE_TYPES)
    self.RunCompletion(
        'compute machine-types describe --zone zone-1 ',
        [
            'n1-standard-1',
            'n1-standard-2',
        ])

if __name__ == '__main__':
  test_case.main()
