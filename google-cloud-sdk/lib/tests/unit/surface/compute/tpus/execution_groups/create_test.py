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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import properties
from tests.lib import mock_matchers
from tests.lib.surface.compute.tpus.execution_groups import base


class CreateBase(base.TpuUnitTestBase):

  def PreSetUp(self):
    self._SetTrack(calliope_base.ReleaseTrack.ALPHA)
    self._SetApiVersion('v1alpha1')
    self.compute_api_version = 'alpha'

  def SetUp(self):
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

  def _assertSSHCalled(self):
    self.ensure_keys.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.Keys), None, allow_passphrase=True
        )

    self.poller_poll.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        mock_matchers.TypeMatcher(ssh.Environment),
        force_connect=True)

    # SSH Command
    self.ssh_init.assert_called_once()

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        mock_matchers.TypeMatcher(ssh.Environment),
        force_connect=True)


class Create(CreateBase):

  def PreSetUp(self):
    self._originals['environment']['TPU_NAME'] = 'testinggcloud'

  def testCreateSuccess(self):
    name = 'testinggcloud'
    instance_op_name = 'operation-1588704422227-5a4eb12bd6fe5-8cacd251-ec86b3c2'
    self.ExpectTPUCreateCall(u'testinggcloud', u'v2-8', u'1.6', False)
    self.zone = 'central2-a'
    op_name = 'projects/fake-project/locations/central2-a/operations/fake-operation'
    self.ExpectOperation(self.mock_tpu_client.projects_locations_operations,
                         op_name, self.mock_tpu_client.projects_locations_nodes,
                         op_name)
    self.ExpectComputeImagesGetFamily(
        'tf-1-6', 'ml-images', 'fake-image-self-link')
    self.ExpectInstanceCreateCall(
        name, instance_op_name, False, 'fake-image-self-link')
    self.ExpectInstanceOperationCall(name, instance_op_name)
    self.ExpectInstanceGetCall(name, instance_op_name)
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --zone central2-a --tf-version='1.6' --machine-type=n1-standard-1
    """)
    self._assertSSHCalled()

  def testCreateSuccessWithGCEImageSpecified(self):
    name = 'testinggcloud'
    instance_op_name = 'operation-1588704422227-5a4eb12bd6fe5-8cacd251-ec86b3c2'
    self.ExpectTPUCreateCall(u'testinggcloud', u'v2-8', u'1.6', False)
    self.zone = 'central2-a'
    op_name = 'projects/fake-project/locations/central2-a/operations/fake-operation'
    self.ExpectOperation(self.mock_tpu_client.projects_locations_operations,
                         op_name, self.mock_tpu_client.projects_locations_nodes,
                         op_name)
    self.ExpectInstanceCreateCall(
        name, instance_op_name, False, 'user-entered-gce-image')
    self.ExpectInstanceOperationCall(name, instance_op_name)
    self.ExpectInstanceGetCall(name, instance_op_name)
    self.Run("""
      compute tpus execution-groups create --name testinggcloud \
      --zone central2-a --tf-version='1.6' --machine-type=n1-standard-1 \
      --gce-image user-entered-gce-image
    """)
    self._assertSSHCalled()

  def testCreateSuccessAlternateTPUFlags(self):
    name = 'testinggcloud'
    instance_op_name = 'operation-1588704422227-5a4eb12bd6fe5-8cacd251-ec86b3c2'
    self.ExpectTPUCreateCall(u'testinggcloud', u'v3-32', u'2.0', True)
    self.zone = 'central2-a'
    op_name = 'projects/fake-project/locations/central2-a/operations/fake-operation'
    self.ExpectOperation(self.mock_tpu_client.projects_locations_operations,
                         op_name, self.mock_tpu_client.projects_locations_nodes,
                         op_name)
    self.ExpectComputeImagesGetFamily('tf-2-0', 'ml-images',
                                      'fake-image-self-link')
    self.ExpectInstanceCreateCall(name, instance_op_name, True,
                                  'fake-image-self-link')
    self.ExpectInstanceOperationCall(name, instance_op_name)
    self.ExpectInstanceGetCall(name, instance_op_name)
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --preemptible --preemptible-vm --zone central2-a --tf-version='2.0' --machine-type=n1-standard-1 --accelerator-type=v3-32
    """)
    self._assertSSHCalled()

  def testCreateSuccessWithTFVersionNotSpecified(self):
    name = 'testinggcloud'
    instance_op_name = 'operation-1588704422227-5a4eb12bd6fe5-8cacd251-ec86b3c2'
    expected_versions = [['tf-version-1.5', '1.5'], ['tf-version-2.0', '2.0']]
    self.ExpectTensorflowVersionList(
        'fake-project', 'central2-a', expected_versions)
    self.ExpectTPUCreateCall(u'testinggcloud', u'v3-32', u'2.0', True)
    self.zone = 'central2-a'
    op_name = 'projects/fake-project/locations/central2-a/operations/fake-operation'
    self.ExpectOperation(self.mock_tpu_client.projects_locations_operations,
                         op_name, self.mock_tpu_client.projects_locations_nodes,
                         op_name)
    self.ExpectComputeImagesGetFamily('tf-2-0', 'ml-images',
                                      'fake-image-self-link')
    self.ExpectInstanceCreateCall(name, instance_op_name, True,
                                  'fake-image-self-link')
    self.ExpectInstanceOperationCall(name, instance_op_name)
    self.ExpectInstanceGetCall(name, instance_op_name)
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --preemptible --preemptible-vm --zone central2-a --machine-type=n1-standard-1 --accelerator-type=v3-32
    """)
    self._assertSSHCalled()

  def testCreateSuccessVmOnly(self):
    name = 'testinggcloud'
    instance_op_name = 'operation-1588704422227-5a4eb12bd6fe5-8cacd251-ec86b3c2'
    self.zone = 'central2-a'
    self.ExpectComputeImagesGetFamily('tf-1-6', 'ml-images',
                                      'fake-image-self-link')
    self.ExpectInstanceCreateCall(
        name, instance_op_name, False, 'fake-image-self-link')
    self.ExpectInstanceOperationCall(name, instance_op_name)
    self.ExpectInstanceGetCall(name, instance_op_name)
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --vm-only --zone central2-a --tf-version='1.6' --machine-type=n1-standard-1
    """)
    self._assertSSHCalled()


class CreateFailure(CreateBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)

  def testCreateFailureOnTPUCreate(self):
    self.ExpectTPUCreateCallWithConflictError(u'testinggcloud', u'v2-8', u'1.6',
                                              False)
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --zone central2-a \
      --tf-version='1.6' --machine-type=n1-standard-1
    """)
    expected_responses = ('TPU Node with name:testinggcloud already exists, '
                          'try a different name\n')

    self.AssertErrEquals(expected_responses, normalize_space=True)

  def testCreateFailureOnInstanceCreate(self):
    name = 'testinggcloud'
    self.ExpectTPUCreateCall(u'testinggcloud', u'v2-8', u'1.6', False)
    self.ExpectComputeImagesGetFamily('tf-1-6', 'ml-images',
                                      'fake-image-self-link')
    self.ExpectInstanceCreateCallFailure(name, False, 'fake-image-self-link')
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --zone central2-a \
      --tf-version='1.6' --machine-type=n1-standard-1
    """)
    expected_responses = ('GCE VM with name:{} already exists, try a different '
                          'name. TPU Node:testinggcloud creation is underway '
                          ' and will need to be deleted.\n').format(name)
    self.AssertErrEquals(expected_responses, normalize_space=True)

  def testCreateFailureOnInstanceOnlyCreate(self):
    name = 'testinggcloud'
    self.ExpectComputeImagesGetFamily('tf-1-6', 'ml-images',
                                      'fake-image-self-link')
    self.ExpectInstanceCreateCallFailure(name, False, 'fake-image-self-link')
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --vm-only --zone central2-a \
      --tf-version='1.6' --machine-type=n1-standard-1
    """)
    expected_responses = (
        'GCE VM with name:{} already exists, try a different name.\n'.format(
            name)
        )
    self.AssertErrEquals(expected_responses, normalize_space=True)

  def testCreateFailsWithStableTFVersionNotFound(self):
    expected_versions = [['tf-version-nightly', 'nightly']]
    self.ExpectTensorflowVersionList('fake-project', 'central2-a',
                                     expected_versions)
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --preemptible \
      --preemptible-vm --zone central2-a --machine-type=n1-standard-1 \
      --accelerator-type=v3-32
    """)
    expected_responses = (
        'Could not find stable Tensorflow version, please set tensorflow '
        'version flag using --tf-version\n'
        )
    self.AssertErrEquals(expected_responses, normalize_space=True)


class CreateDryRun(base.TpuUnitTestBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)

  def testCreateDryRun(self):
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --dry-run --zone central2-a --accelerator-type v3-8 --tf-version='1.6' --machine-type=n1-standard-1 --disk-size='100GB'
    """)
    expected_responses = (
        'Creating TPU with Name:testinggcloud, Accelerator '
        'type:v3-8, TF version:1.6, Zone:central2-a, Network:default\n'
        'Creating GCE VM with Name:testinggcloud, Zone:central2-a, Machine '
        'Type:n1-standard-1, Disk Size(GB):100, Preemptible:False, '
        'Network:default\n'
        'SSH to GCE VM:testinggcloud\n')

    self.AssertErrEquals(expected_responses, normalize_space=True)

  def testCreateDryRunVMOnly(self):
    self.Run("""
      compute tpus execution-groups create --name testinggcloud --dry-run --vm-only --zone central2-a --accelerator-type v3-8 --tf-version='1.6' --machine-type=n1-standard-1 --disk-size='100GB'
    """)
    expected_responses = (
        'Creating GCE VM with Name:testinggcloud, Zone:central2-a, Machine '
        'Type:n1-standard-1, Disk Size(GB):100, Preemptible:False, '
        'Network:default\n'
        'SSH to GCE VM:testinggcloud\n')

    self.AssertErrEquals(expected_responses, normalize_space=True)
