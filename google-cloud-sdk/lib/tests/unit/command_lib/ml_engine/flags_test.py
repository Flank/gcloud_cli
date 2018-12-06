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

"""Unit tests for ml-engine completers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.ml_engine import flags
from tests.lib import completer_test_base
from tests.lib import parameterized
from tests.lib.surface.iam import unit_test_base
from tests.lib.surface.ml_engine import base


class CompletionTest(unit_test_base.BaseTest,
                     completer_test_base.CompleterBase):

  def SetUp(self):
    self.returned_roles = [
        self.msgs.Role(
            description='Read access to all resources.',
            name='roles/viewer',
            title='Viewer',
        ),
        self.msgs.Role(
            description='Read-only access to GCE networking resources.',
            name='roles/compute.networkViewer',
            title='Compute Network Viewer',
        ),
    ]
    self.roles_response = self.msgs.QueryGrantableRolesResponse(
        roles=self.returned_roles)

  def testMlEngineIamRolesCompleter(self):
    uri = 'https://ml.googleapis.com/v1/projects/my-a-project/models/my-b-model'
    self.client.roles.QueryGrantableRoles.Expect(
        request=self.msgs.QueryGrantableRolesRequest(
            fullResourceName=uri[6:].replace('/v1/', '/'),
            pageSize=100),
        response=self.roles_response,
    )

    self.RunCompleter(
        flags.MlEngineIamRolesCompleter,
        expected_command=[
            'beta',
            'iam',
            'list-grantable-roles',
            '--quiet',
            '--flatten=name',
            '--format=disable',
            uri,
        ],
        expected_completions=['roles/viewer', 'roles/compute.networkViewer'],
        cli=self.cli,
        args={
            '--model': uri,
            '--project': 'my-a-project',
        },
    )


class FlagsTest(base.MlGaPlatformTestBase, parameterized.TestCase):

  def testEmptyAccelerator(self):
    self.assertEqual(None, flags.ParseAcceleratorFlag(None))

  @parameterized.parameters(
      (0, dict([('count', 1), ('type', 'nvidia-tesla-k80')]), 1),
      (1, dict([('count', 1), ('type', 'nvidia-tesla-p100')]), 1),
      (2, dict([('count', 2), ('type', 'nvidia-tesla-v100')]), 2),
      (3, dict([('count', 2), ('type', 'nvidia-tesla-p4')]), 2),
      )
  def testValidateAccelerator(self, index, accelerator, expected_count):
    accelerator_msg = self.msgs.GoogleCloudMlV1AcceleratorConfig
    accelerator_types = accelerator_msg.TypeValueValuesEnum
    accelerator_type_list = [
        accelerator_types.NVIDIA_TESLA_K80,
        accelerator_types.NVIDIA_TESLA_P100,
        accelerator_types.NVIDIA_TESLA_V100,
        accelerator_types.NVIDIA_TESLA_P4]
    expected_type = accelerator_type_list[index]
    self.assertEqual(expected_type,
                     flags.ParseAcceleratorFlag(accelerator).type)
    self.assertEqual(expected_count,
                     flags.ParseAcceleratorFlag(accelerator).count)

  def testInvalidAcceleratorType(self):
    with self.AssertRaisesExceptionMatches(
        flags.ArgumentError, """\
The type of the accelerator can only be one of the following: 'nvidia-tesla-k80', 'nvidia-tesla-p100', 'nvidia-tesla-v100' and 'nvidia-tesla-p4'.
"""):
      flags.ParseAcceleratorFlag(dict([('count', 1), ('type', 'o')]))

  @parameterized.parameters(0, -1)
  def testInvalidAcceleratorCount(self, invalid_count):
    with self.AssertRaisesExceptionMatches(
        flags.ArgumentError, """\
The count of the accelerator must be greater than 0.
"""):
      flags.ParseAcceleratorFlag(
          dict([('count', invalid_count), ('type', 'nvidia-tesla-k80')]))

if __name__ == '__main__':
  completer_test_base.main()
