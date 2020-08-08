# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Unit tests for the compute tpus execution group utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.exceptions import HttpNotFoundError
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.tpus.execution_groups import util as tpu_utils
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core.util import retry
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.compute import test_base as compute_test_base
from tests.lib.surface.compute.tpus.execution_groups import base as exec_group_base

import mock as base_mock


class TPUNodeTest(exec_group_base.TpuUnitTestBase):

  def PreSetUp(self):
    self._SetTrack(calliope_base.ReleaseTrack.GA)
    self._SetApiVersion('v1')

  def testNodeIsRunning(self):
    node_helper = tpu_utils.TPUNode(self.track)
    node = self.tpu_messages.Node()
    node.state = self.tpu_messages.Node.StateValueValuesEnum.READY
    self.assertTrue(node_helper.IsRunning(node), True)
    node.state = self.tpu_messages.Node.StateValueValuesEnum.CREATING
    node.ipAddress = 'fake-address'
    self.assertTrue(node_helper.IsRunning(node))

  def testNodeIsNotRunning(self):
    node_helper = tpu_utils.TPUNode(self.track)
    node = self.tpu_messages.Node()
    state_enum = self.tpu_messages.Node.StateValueValuesEnum
    for state in state_enum:
      if state not in [state_enum.READY, state_enum.CREATING]:
        node.state = state
        self.assertFalse(node_helper.IsRunning(node))

    node.state = state_enum.CREATING
    node.ipAddress = ''
    self.assertFalse(node_helper.IsRunning(node))

  def testNodeNameMatch(self):
    node_helper = tpu_utils.TPUNode(self.track)
    node = self.tpu_messages.Node()
    node.name = 'projects/fake-project/locations/fake-location/nodes/fake-node'
    got = node_helper.NodeName(node)
    self.assertEqual(got, 'fake-node')

  def testNodeNameNoMatch(self):
    node_helper = tpu_utils.TPUNode(self.track)
    node = self.tpu_messages.Node()
    name_list = [
        '',
        'projects/fake-project/locations/fake-node',
        'fake-project/locations/fake-location/nodes/fake-node',
    ]
    for name in name_list:
      node.name = name
      got = node_helper.NodeName(node)
      self.assertEqual(got, '')

  def testStableTensorflowVersionListerSingleElement(self):
    node_helper = tpu_utils.TPUNode(self.track)
    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', [['fake-tf-name', '1.5']])
    stable_tf_version = node_helper.LatestStableTensorflowVersion('central2-a')
    self.assertEqual(stable_tf_version, '1.5')

  def testStableTensorflowVersionListerMultipleElements(self):
    node_helper = tpu_utils.TPUNode(self.track)
    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', [
            ['fake-tf-1.5', '1.5'],
            ['fake-tf-1.6', '1.6']
        ])
    stable_tf_version = node_helper.LatestStableTensorflowVersion('central2-a')
    self.assertEqual(stable_tf_version, '1.6')

    # Invert order.
    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', [
            ['fake-tf-1.6', '1.6'],
            ['fake-tf-1.5', '1.5']
        ])
    stable_tf_version = node_helper.LatestStableTensorflowVersion('central2-a')
    self.assertEqual(stable_tf_version, '1.6')

    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', [
            ['fake-tf-1.6', '1.6'],
            ['fake-tf-1.5', '1.5'],
            ['fake-tf-1.7', '1.7']
        ])
    stable_tf_version = node_helper.LatestStableTensorflowVersion('central2-a')
    self.assertEqual(stable_tf_version, '1.7')

    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', [
            ['fake-tf-1.6', '1.6'],
            ['fake-tf-nightly', 'nightly'],
        ])
    stable_tf_version = node_helper.LatestStableTensorflowVersion('central2-a')
    self.assertEqual(stable_tf_version, '1.6')

    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', [
            ['fake-tf-1.7-RC0', '1.7-RC0'],
            ['fake-tf-1.7', '1.7'],
            ['fake-tf-nightly', 'nightly'],
        ])
    stable_tf_version = node_helper.LatestStableTensorflowVersion('central2-a')
    self.assertEqual(stable_tf_version, '1.7')

    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', [
            ['fake-tf-nightly-20180201', 'nightly-20180201'],
            ['fake-tf-nightly', 'nightly'],
            ['fake-tf-1.7-RC0', '1.7-RC0'],
            ['fake-tf-1.6', '1.6'],
            ['fake-tf-1.5', '1.5'],
        ])
    stable_tf_version = node_helper.LatestStableTensorflowVersion('central2-a')
    self.assertEqual(stable_tf_version, '1.6')

  def testStableTensorflowVersionNotFound(self):
    node_helper = tpu_utils.TPUNode(self.track)
    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', [
            ['fake-tf-nightly-20180201', 'nightly-20180201'],
        ])
    with self.assertRaisesRegex(
        HttpNotFoundError,
        'No stable release found'
        ):
      node_helper.LatestStableTensorflowVersion('central2-a')

    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', [
            ['fake-tf-nightly', 'nightly']
        ])
    with self.assertRaisesRegex(
        HttpNotFoundError,
        'No stable release found'
        ):
      node_helper.LatestStableTensorflowVersion('central2-a')


class TPUNodeTestAlpha(TPUNodeTest):

  def PreSetUp(self):
    self._SetTrack(calliope_base.ReleaseTrack.ALPHA)
    self._SetApiVersion('v1alpha1')


# TODO(b/157058781) For some reason, v1beta1 is not recognized, need to
# explore further
# class TPUNodeTestBeta(TPUNodeTest):

#   def PreSetUp(self):
#     self._SetTrack(calliope_base.ReleaseTrack.BETA)
#     self._SetApiVersion('v1beta1')


class InstanceTest(exec_group_base.TpuUnitTestBase):

  def PreSetUp(self):
    self.compute_api_version = 'v1'
    self._SetTrack(calliope_base.ReleaseTrack.GA)

  def SetUp(self):
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

  def testInstanceIsRunning(self):
    instance_helper = tpu_utils.Instance(self.track)
    instance = instance_helper.BuildInstanceSpec('fake-instance', 'fake-zone',
                                                 'fake-machine-type', -1, False,
                                                 'default')
    instance.status = self.instances_messages.Instance.StatusValueValuesEnum.RUNNING
    self.assertEqual(instance_helper.IsRunning(instance), True)

  def testInstanceIsNotRunning(self):
    instance_helper = tpu_utils.Instance(self.track)
    instance = instance_helper.BuildInstanceSpec('fake-instance', 'fake-zone',
                                                 'fake-machine-type', -1, False,
                                                 'default')
    state_enum = self.instances_messages.Instance.StatusValueValuesEnum
    for state in state_enum:
      if state != state_enum.RUNNING:
        instance.status = state
        self.assertFalse(instance_helper.IsRunning(instance))

  def createMultipleLabels(self):
    return [
        self.instances_messages.Instance.LabelsValue.AdditionalProperty(
            key='fake-label-2', value='fake-instance-2'),
        self.instances_messages.Instance.LabelsValue.AdditionalProperty(
            key='fake-label-3', value='fake-instance-3'),
        self.instances_messages.Instance.LabelsValue.AdditionalProperty(
            key='ctpu', value='fake-instance')
    ]

  def testVMCreatedByExecGroup(self):
    instance_helper = tpu_utils.Instance(self.track)
    instance = instance_helper.BuildInstanceSpec('fake-instance', 'fake-zone',
                                                 'fake-machine-type', -1, False,
                                                 'default')
    instance.labels = self.instances_messages.Instance.LabelsValue(
        additionalProperties=self.createMultipleLabels())
    self.assertTrue(instance_helper._VMCreatedByExecGroup(instance))

  def testVMNotCreatedByExecGroup(self):
    instance_helper = tpu_utils.Instance(self.track)
    instance = instance_helper.BuildInstanceSpec('fake-instance', 'fake-zone',
                                                 'fake-machine-type', -1, False,
                                                 'default')
    instance.labels = self.instances_messages.Instance.LabelsValue()
    self.assertFalse(instance_helper._VMCreatedByExecGroup(instance))

  def testImageFamilyFromTensorflowVersion(self):
    tests = [
        [
            '1.6',
            True,
            'tf-1-6-gpu'
        ],
        [
            '1.6.35',
            False,
            'tf-1-6-35'
        ],
        [
            '1.6',
            False,
            'tf-1-6'
        ],
    ]
    instance_helper = tpu_utils.Instance(self.track)
    for test in tests:
      got = instance_helper._ImageFamilyFromTensorflowVersion(
          test[0], test[1])
      self.assertEqual(got, test[2])

  def testImageFamilyFromTensorflowVersionWithParseError(self):
    instance_helper = tpu_utils.Instance(self.track)
    with self.assertRaisesRegex(
        tpu_utils.TensorflowVersionParser.ParseError,
        r'Invalid tensorflow version:1.7-RC3 \(non-empty modifier\); please '
        'set the --gce-image flag'
        ):
      instance_helper._ImageFamilyFromTensorflowVersion('1.7-RC3', False)
    with self.assertRaisesRegex(
        tpu_utils.TensorflowVersionParser.ParseError,
        r'Invalid tensorflow version:1.6-RC1 \(non-empty modifier\); please set '
        'the --gce-image flag'
        ):
      instance_helper._ImageFamilyFromTensorflowVersion('1.6-RC1', True)

  def testImageFamilyResolutionFromTensorflowVersion(self):
    instance_helper = tpu_utils.Instance(self.track)

    self.ExpectComputeImagesGetFamily(
        'tf-1-6-gpu', 'fake-project', 'fake-image-self-link')
    instance_helper.ResolveImageFromTensorflowVersion(
        '1.6', 'fake-project', True)

    self.ExpectComputeImagesGetFamily(
        'tf-1-7-35', 'fake-project-2', 'fake-image-self-link')
    instance_helper.ResolveImageFromTensorflowVersion(
        '1.7.35', 'fake-project-2', False)


class InstanceTestAlpha(InstanceTest):

  def PreSetUp(self):
    self.compute_api_version = 'alpha'
    self._SetTrack(calliope_base.ReleaseTrack.ALPHA)


class InstanceTestBeta(InstanceTest):

  def PreSetUp(self):
    self.compute_api_version = 'beta'
    self._SetTrack(calliope_base.ReleaseTrack.BETA)


class SSHTest(compute_test_base.BaseSSHTest, test_case.WithInput):

  class Args(object):

    def __init__(self, name, zone, forward_ports):
      self.name = name
      self.zone = zone
      self.forward_ports = forward_ports
      self.ssh_key_file = None
      self.plain = None
      self.strict_host_key_checking = None
      self.force_key_file_overwrite = None

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    datetime_patcher = base_mock.patch(
        'datetime.datetime', compute_test_base.FakeDateTimeWithTimeZone)
    self.addCleanup(datetime_patcher.stop)
    datetime_patcher.start()
    self._originals['environment']['TPU_NAME'] = 'fake-name'

  def _makeFakeInstance(self, instance_name):
    return self.messages.Instance(
        id=1111,
        name=instance_name,
        networkInterfaces=[
            self.messages.NetworkInterface(
                accessConfigs=[
                    self.messages.AccessConfig(
                        name='external-nat', natIP='23.251.133.75'),
                ],),
        ],
        status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/instances/instance-1'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1'))

  def _makeFakeProjectResource(self):
    ssh_keys = textwrap.dedent("""\
       me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
       """)
    return self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=ssh_keys),
            ]),
        name='my-project',
    )

  def testSSHToInstance(self):
    ssh_util = tpu_utils.SSH(self.track)
    args = SSHTest.Args('fake-name', 'central2-a', True)
    instance = self._makeFakeInstance('fake-instance')

    self.make_requests.side_effect = iter([
        [self._makeFakeProjectResource()],
        [self._makeFakeProjectResource()],
        [self._makeFakeProjectResource()],
    ])

    ssh_util.SSHToInstance(args, instance)

    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True
        )

    self.poller_poll.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        self.env, force_connect=True
        )

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=ssh.Remote('23.251.133.75', ssh.GetDefaultSshUsername()),
        identity_file=self.private_key_file,
        extra_flags=[
            '-A', '-L', '6006:localhost:6006', '-L', '8888:localhost:8888'],
        options=dict(
            self.options,
            HostKeyAlias='compute.1111',
            SendEnv='TPU_NAME',
            )
        )

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.env, force_connect=True)

  def testSSHToInstanceWithoutPortForwarding(self):
    ssh_util = tpu_utils.SSH(self.track)
    forward_ports = False
    args = SSHTest.Args('fake-name', 'central2-a', forward_ports)
    instance = self._makeFakeInstance('fake-instance')

    self.make_requests.side_effect = iter([
        [self._makeFakeProjectResource()],
        [self._makeFakeProjectResource()],
        [self._makeFakeProjectResource()],
    ])

    ssh_util.SSHToInstance(args, instance)

    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True
        )

    self.poller_poll.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        self.env, force_connect=True
        )

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=ssh.Remote('23.251.133.75', ssh.GetDefaultSshUsername()),
        identity_file=self.private_key_file,
        extra_flags=[],
        options=dict(
            self.options,
            HostKeyAlias='compute.1111',
            SendEnv='TPU_NAME',
            )
        )

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.env, force_connect=True)

  def testSSHTimeout(self):
    args = SSHTest.Args('fake-name', 'central2-a', True)
    instance = self._makeFakeInstance('fake-instance')
    # Polling the instance leads to an unreachable instance.
    self.poller_poll.side_effect = retry.WaitException('msg', 'last', 'state')

    self.make_requests.side_effect = iter([
        [self._makeFakeProjectResource()],
        [self._makeFakeProjectResource()],
        [self._makeFakeProjectResource()],
    ])
    ssh_util = tpu_utils.SSH(self.track)
    with self.AssertRaisesExceptionRegexp(
        ssh_utils.NetworkError,
        'Could not SSH into the instance.  It is possible that '
        'your SSH key has not propagated to the instance yet. '
        'Try running this command again.  If you still cannot connect, '
        'verify that the firewall and instance are set to accept '
        'ssh traffic.'):
      ssh_util.SSHToInstance(args, instance)
    self.AssertErrContains('Updating project ssh metadata')

  def testSSHErrorException(self):
    args = SSHTest.Args('fake-name', 'central2-a', True)
    instance = self._makeFakeInstance('fake-instance')
    self.make_requests.side_effect = iter([
        [self._makeFakeProjectResource()],
        [self._makeFakeProjectResource()],
        [self._makeFakeProjectResource()],
    ])
    ssh_util = tpu_utils.SSH(self.track)
    self.ssh_run.side_effect = ssh.CommandError('ssh', return_code=255)
    with self.assertRaisesRegex(
        ssh.CommandError,
        r'\[ssh\] exited with return code \[255\].'):
      ssh_util.SSHToInstance(args, instance)


class SSHTestAlpha(SSHTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


class SSHTestBeta(SSHTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class TensorflowVersionParserTest(test_case.WithInput):

  def testParseBadVersion(self):
    with self.assertRaisesRegex(
        tpu_utils.TensorflowVersionParser.ParseError,
        'Bad argument: tf_version is empty'
        ):
      tpu_utils.TensorflowVersionParser.ParseVersion('')

  def testParseVersion(self):
    tests = [
        [
            'nightly',
            tpu_utils.TensorflowVersionParser.Result(is_nightly=True)
        ],
        [
            'nightly-20190218',
            tpu_utils.TensorflowVersionParser.Result(
                is_nightly=True, modifier='-20190218')
        ],
        [
            '1.6',
            tpu_utils.TensorflowVersionParser.Result(major=1, minor=6)
        ],
        [
            '1.7',
            tpu_utils.TensorflowVersionParser.Result(major=1, minor=7)
        ],
        [
            '1.7-RC3',
            tpu_utils.TensorflowVersionParser.Result(
                major=1, minor=7, modifier='-RC3')
        ],
        [
            '1.7.2-RC0',
            tpu_utils.TensorflowVersionParser.Result(
                major=1, minor=7, modifier='.2-RC0')
        ],
        [
            'test_version',
            tpu_utils.TensorflowVersionParser.Result(modifier='test_version')
        ],
        [
            'unknown',
            tpu_utils.TensorflowVersionParser.Result(modifier='unknown')
        ],
    ]

    for test in tests:
      got = tpu_utils.TensorflowVersionParser.ParseVersion(test[0])
      self.assertEqual(got, test[1], 'Got:{}, want:{}'.format(
          vars(got), vars(test[1])))

  def testSortVersions(self):
    tests = [
        [
            ['1.7', '1.6'],
            ['1.7', '1.6']
        ],
        [
            ['1.6', '1.7', 'nightly'],
            ['1.7', '1.6', 'nightly']
        ],
        [
            ['1.6', '1.7', 'nightly-20180901'],
            ['1.7', '1.6', 'nightly-20180901']
        ],
        [
            ['1.6', '1.7', 'nightly', 'nightly-20180901'],
            ['1.7', '1.6', 'nightly', 'nightly-20180901']
        ],
        [
            ['1.6', '1.7', 'nightly-20180901', 'nightly'],
            ['1.7', '1.6', 'nightly', 'nightly-20180901']
        ],
        [
            ['1.6', '1.7', '1.7RC1', 'nightly'],
            ['1.7', '1.7RC1', '1.6', 'nightly']
        ],
        [
            ['1.7RC0', '1.7', 'nightly'],
            ['1.7', '1.7RC0', 'nightly']
        ],
        [
            ['1.7RC0', '1.7RC1', 'nightly'],
            ['1.7RC1', '1.7RC0', 'nightly']
        ],
        [
            ['2.1', '1.7', 'nightly'],
            ['2.1', '1.7', 'nightly']
        ],
        [
            ['nightly', '2.1', '1.8'],
            ['2.1', '1.8', 'nightly']
        ],
        [
            ['nightly', 'test_version', '2.1', '1.8'],
            ['2.1', '1.8', 'nightly', 'test_version']
        ],
        [
            ['other_version', 'nightly-20180901', 'nightly',
             'nightly-20170101', 'test_version'],
            ['nightly', 'nightly-20180901', 'nightly-20170101',
             'other_version', 'test_version']
        ],
        [
            ['test_version', '0.1', 'other_version',
             'nightly', 'nightly-20180901'],
            ['0.1', 'nightly', 'nightly-20180901',
             'other_version', 'test_version']
        ],
    ]

    for test in tests:
      input_result_list = []
      expected_result_list = []

      for tf_version in test[0]:
        input_result_list.append(
            tpu_utils.TensorflowVersionParser.ParseVersion(tf_version))

      for tf_version in test[1]:
        expected_result_list.append(
            tpu_utils.TensorflowVersionParser.ParseVersion(tf_version))

      sorted_result_list = sorted(input_result_list)
      self.assertSequenceEqual(sorted_result_list, expected_result_list)

if __name__ == '__main__':
  test_case.main()
