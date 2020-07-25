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

"""Unit tests for ml-engine completers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.ml_engine import jobs
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from tests.lib import cli_test_base
from tests.lib import completer_test_base
from tests.lib import parameterized
from tests.lib.calliope import util
from tests.lib.surface.iam import unit_test_base
from tests.lib.surface.ml_engine import base


_ACCELERATOR_TYPE_MAPPER = arg_utils.ChoiceEnumMapper(
    'generic-accelerator',
    jobs.GetMessagesModule().GoogleCloudMlV1AcceleratorConfig
    .TypeValueValuesEnum,
    help_str='The available types of accelerators.',
    include_filter=lambda x: x != 'ACCELERATOR_TYPE_UNSPECIFIED',
    required=False)

_INVALID_ACCELERATOR_MESSAGE = ('Invalid accelerator: bad-type. Valid '
                                'choices are: [{}]'.format(', '.join(
                                    _ACCELERATOR_TYPE_MAPPER.choices)))


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

  def _getAcceleratorTypes(self):
    accelerator_msg = self.msgs.GoogleCloudMlV1AcceleratorConfig
    accelerator_types = accelerator_msg.TypeValueValuesEnum
    return [
        accelerator_types.NVIDIA_TESLA_K80, accelerator_types.NVIDIA_TESLA_P100,
        accelerator_types.NVIDIA_TESLA_V100, accelerator_types.NVIDIA_TESLA_P4,
        accelerator_types.NVIDIA_TESLA_T4, accelerator_types.TPU_V2
    ]

  def testEmptyAccelerator(self):
    self.assertEqual(None, flags.ParseAcceleratorFlag(None))

  @parameterized.parameters(
      (0, dict([('count', 1), ('type', 'nvidia-tesla-k80')]), 1),
      (1, dict([('count', 1), ('type', 'nvidia-tesla-p100')]), 1),
      (2, dict([('count', 2), ('type', 'nvidia-tesla-v100')]), 2),
      (3, dict([('count', 2), ('type', 'nvidia-tesla-p4')]), 2),
      (4, dict([('count', 3), ('type', 'nvidia-tesla-t4')]), 3),
      (5, dict([('count', 4), ('type', 'tpu-v2')]), 4),
  )
  def testValidateAccelerator(self, index, accelerator, expected_count):
    expected_type = self._getAcceleratorTypes()[index]
    self.assertEqual(expected_type,
                     flags.ParseAcceleratorFlag(accelerator).type)
    self.assertEqual(expected_count,
                     flags.ParseAcceleratorFlag(accelerator).count)

  def testInvalidAcceleratorType(self):
    with self.AssertRaisesExceptionMatches(
        flags.ArgumentError, """\
The type of the accelerator can only be one of the following: {}.
""".format(', '.join(
    ["'{}'".format(c) for c in _ACCELERATOR_TYPE_MAPPER.choices]))):
      flags.ParseAcceleratorFlag(dict([('count', 1), ('type', 'o')]))

  @parameterized.parameters(0, -1)
  def testInvalidAcceleratorCount(self, invalid_count):
    with self.AssertRaisesExceptionMatches(
        flags.ArgumentError, """\
The count of the accelerator must be greater than 0.
"""):
      flags.ParseAcceleratorFlag(
          dict([('count', invalid_count), ('type', 'nvidia-tesla-k80')]))

  @parameterized.parameters(
      (0, dict([('count', 1), ('type', 'nvidia-tesla-k80')]), 1),
      (1, dict([('count', 1), ('type', 'nvidia-tesla-p100')]), 1),
      (2, dict([('count', 2), ('type', 'nvidia-tesla-v100')]), 2),
      (3, dict([('count', 2), ('type', 'nvidia-tesla-p4')]), 2),
      (4, dict([('count', 3), ('type', 'nvidia-tesla-t4')]), 3),
      (5, dict([('count', 4), ('type', 'tpu-v2')]), 4),
  )
  def testMainAcceleratorType(self, index, accelerator, expected_count):
    parser = util.ArgumentParser()
    expected_type = self._getAcceleratorTypes()[index]
    flags.GetMainAccelerator().AddToParser(parser)
    args = parser.parse_args(['--main-accelerator',
                              'type={0},count={1}'.format(
                                  accelerator['type'], accelerator['count'])])

    self.assertEqual(expected_type,
                     args.main_accelerator['type'])
    self.assertEqual(expected_count,
                     args.main_accelerator['count'])

  def testMainAcceleratorTypeErrors(self):
    parser = util.ArgumentParser()
    flags.GetMainAccelerator().AddToParser(parser)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           _INVALID_ACCELERATOR_MESSAGE):
      parser.parse_args(['--main-accelerator', 'type=bad_type,count=2'])

    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, 'The count of the accelerator '
                                         'must be greater than 0.'):
      parser.parse_args(['--main-accelerator',
                         'type=nvidia-tesla-p4,count=0'])

  @parameterized.parameters(
      (0, dict([('count', 1), ('type', 'nvidia-tesla-k80')]), 1),
      (1, dict([('count', 1), ('type', 'nvidia-tesla-p100')]), 1),
      (2, dict([('count', 2), ('type', 'nvidia-tesla-v100')]), 2),
      (3, dict([('count', 2), ('type', 'nvidia-tesla-p4')]), 2),
      (4, dict([('count', 3), ('type', 'nvidia-tesla-t4')]), 3),
      (5, dict([('count', 4), ('type', 'tpu-v2')]), 4),
  )
  def testParameterServerAcceleratorType(
      self, index, accelerator, expected_count):
    parser = util.ArgumentParser()
    expected_type = self._getAcceleratorTypes()[index]
    flags.GetParameterServerAccelerator().AddToParser(parser)
    args = parser.parse_args(['--parameter-server-accelerator',
                              'type={0},count={1}'.format(
                                  accelerator['type'], accelerator['count'])])

    self.assertEqual(expected_type,
                     args.parameter_server_accelerator['type'])
    self.assertEqual(expected_count,
                     args.parameter_server_accelerator['count'])

  def testParameterServerTypeErrors(self):
    parser = util.ArgumentParser()
    flags.GetParameterServerAccelerator().AddToParser(parser)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           _INVALID_ACCELERATOR_MESSAGE):
      parser.parse_args(['--parameter-server-accelerator',
                         'type=bad_type,count=2'])

    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, 'The count of the accelerator '
                                         'must be greater than 0.'):
      parser.parse_args(['--parameter-server-accelerator',
                         'type=nvidia-tesla-p4,count=0'])

  @parameterized.parameters(
      (0, dict([('count', 1), ('type', 'nvidia-tesla-k80')]), 1),
      (1, dict([('count', 1), ('type', 'nvidia-tesla-p100')]), 1),
      (2, dict([('count', 2), ('type', 'nvidia-tesla-v100')]), 2),
      (3, dict([('count', 2), ('type', 'nvidia-tesla-p4')]), 2),
      (4, dict([('count', 3), ('type', 'nvidia-tesla-t4')]), 3),
      (5, dict([('count', 4), ('type', 'tpu-v2')]), 4),
  )
  def testWorkerAcceleratorType(self, index, accelerator, expected_count):
    parser = util.ArgumentParser()
    expected_type = self._getAcceleratorTypes()[index]
    flags.GetWorkerAccelerator().AddToParser(parser)
    args = parser.parse_args(['--worker-accelerator',
                              'type={0},count={1}'.format(
                                  accelerator['type'], accelerator['count'])])

    self.assertEqual(expected_type,
                     args.worker_accelerator['type'])
    self.assertEqual(expected_count,
                     args.worker_accelerator['count'])

  def testWorkerAcceleratorTypeErrors(self):
    parser = util.ArgumentParser()
    flags.GetWorkerAccelerator().AddToParser(parser)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           _INVALID_ACCELERATOR_MESSAGE):
      parser.parse_args(['--worker-accelerator',
                         'type=bad_type,count=2'])

    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, 'The count of the accelerator '
                                         'must be greater than 0.'):
      parser.parse_args(['--worker-accelerator',
                         'type=nvidia-tesla-p4,count=0'])


if __name__ == '__main__':
  completer_test_base.main()
