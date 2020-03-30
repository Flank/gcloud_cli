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
"""Unit tests for environments run."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.composer import util as command_util
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base
from tests.lib.surface.composer import kubectl_util
import mock


class EnvironmentsRunGATest(base.KubectlShellingUnitTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.GA)

  TEST_POD = 'airflow-worker'
  TEST_CONTAINER = 'airflow-worker'
  TEST_SUBCOMMAND = 'version'

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunEnvironmentNotFound(self, exec_mock, *_):
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))

    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: NOT_FOUND'):
      self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                           self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                           self.TEST_SUBCOMMAND)
    self.assertFalse(exec_mock.called)

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunCreatingState(self, exec_mock, *_):
    test_env_object = self.MakeEnvironmentWithStateAndClusterLocation(
        self.messages.Environment.StateValueValuesEnum.CREATING)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=test_env_object)
    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Must be RUNNING.'):
      self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                           self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                           self.TEST_SUBCOMMAND)
    self.assertFalse(exec_mock.called)

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunFetchKubectlNamespaceFail(self, exec_mock, tmp_kubeconfig_mock):
    test_env_object = self.MakeEnvironmentWithStateAndClusterLocation(
        self.messages.Environment.StateValueValuesEnum.RUNNING)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=test_env_object)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    def _FailedFetchKubectlNamespaceCallback(*unused_args, **unused_kwargs):
      return 1

    fake_exec.AddCallback(0, _FailedFetchKubectlNamespaceCallback)

    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'kubectl returned non-zero status code'):
      self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                           self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                           self.TEST_SUBCOMMAND)
    self.assertEqual(1, exec_mock.call_count)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunGetPodsFail(self, exec_mock, tmp_kubeconfig_mock):
    test_env_object = self.MakeEnvironmentWithStateAndClusterLocation(
        self.messages.Environment.StateValueValuesEnum.RUNNING)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=test_env_object)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    def _FailedGetPodsCallback(*unused_args, **unused_kwargs):
      return 1

    fake_exec.AddCallback(
        0, self.MakeFetchKubectlNamespaceCallback([('default', 'Active')]))
    fake_exec.AddCallback(1, _FailedGetPodsCallback)

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Error retrieving GKE pods'):
      self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                           self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                           self.TEST_SUBCOMMAND)
    self.assertEqual(2, exec_mock.call_count)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunEmptyPodList(self, exec_mock, tmp_kubeconfig_mock):
    test_env_object = self.MakeEnvironmentWithStateAndClusterLocation(
        self.messages.Environment.StateValueValuesEnum.RUNNING)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=test_env_object)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, self.MakeFetchKubectlNamespaceCallback([('default', 'Active')]))
    fake_exec.AddCallback(1, self.MakeGetPodsCallback([]))

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'No running GKE pods found'):
      self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                           self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                           self.TEST_SUBCOMMAND)
    self.assertEqual(2, exec_mock.call_count)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunMissingDesiredPod(self, exec_mock, tmp_kubeconfig_mock):
    test_env_object = self.MakeEnvironmentWithStateAndClusterLocation(
        self.messages.Environment.StateValueValuesEnum.RUNNING)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=test_env_object)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, self.MakeFetchKubectlNamespaceCallback([('default', 'Active')]))
    fake_exec.AddCallback(
        1, self.MakeGetPodsCallback([('pod1', 'running'), ('pod2', 'running')]))

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Desired GKE pod not found'):
      self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                           self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                           self.TEST_SUBCOMMAND)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunWithoutArgs(self, exec_mock, tmp_kubeconfig_mock):
    test_env_object = self.MakeEnvironmentWithStateAndClusterLocation(
        self.messages.Environment.StateValueValuesEnum.RUNNING)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=test_env_object)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, self.MakeFetchKubectlNamespaceCallback([('default', 'Active')]))
    fake_exec.AddCallback(
        1, self.MakeGetPodsCallback([(self.TEST_POD, 'running')]))
    fake_exec.AddCallback(2, self.MakeKubectlExecCallback(self.TEST_POD))

    self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                         self.TEST_SUBCOMMAND)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunWithArgs(self, exec_mock, tmp_kubeconfig_mock):
    test_env_object = self.MakeEnvironmentWithStateAndClusterLocation(
        self.messages.Environment.StateValueValuesEnum.RUNNING)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=test_env_object)
    subcmd_args = ['--arg1', '--arg2', 'val2']

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, self.MakeFetchKubectlNamespaceCallback([('default', 'Active')]))
    fake_exec.AddCallback(
        1, self.MakeGetPodsCallback([(self.TEST_POD, 'running')]))
    fake_exec.AddCallback(
        2, self.MakeKubectlExecCallback(self.TEST_POD, subcmd_args=subcmd_args))

    self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                         self.TEST_SUBCOMMAND, '--', *subcmd_args)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testSubcommandRun_DeleteDag(self, exec_mock, tmp_kubeconfig_mock):
    test_env_object = self.MakeEnvironmentWithStateAndClusterLocation(
        self.messages.Environment.StateValueValuesEnum.RUNNING)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=test_env_object)

    subcmd = 'delete_dag'
    subcmd_args = []

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, self.MakeFetchKubectlNamespaceCallback([('default', 'Active')]))
    fake_exec.AddCallback(
        1, self.MakeGetPodsCallback([(self.TEST_POD, 'running')]))

    # Ensure that the '--yes' argument is added to the list of 'delete_dag' args
    # if it is not present.
    fake_exec.AddCallback(
        2,
        self.MakeKubectlExecCallback(
            self.TEST_POD, subcmd=subcmd, subcmd_args=subcmd_args + ['--yes']))

    self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID, subcmd,
                         '--', *subcmd_args)

    fake_exec.Verify()

  def MakeKubectlExecCallback(self,
                              pod,
                              subcmd=TEST_SUBCOMMAND,
                              subcmd_args=None):

    def _KubectlExecCallback(args, **_):
      expected_args = command_util.AddKubectlNamespace(
          self.TEST_KUBECTL_DEFAULT_NAMESPACE, [
              self.TEST_KUBECTL_PATH, 'exec', pod, '-tic', self.TEST_CONTAINER,
              'airflow', subcmd
          ])
      if subcmd_args:
        expected_args.extend(['--'] + subcmd_args)
      self.assertEqual(expected_args, args)
      return 0

    return _KubectlExecCallback

  def MakeCredentialFetchCallback(self, zone, retval):

    def _CredentialFetchCallback(args, **_):
      kubectl_util.AssertListHasPrefix(
          self, args,
          [self.TEST_GCLOUD_PATH, 'container', 'clusters', 'get-credentials'])
      kubectl_util.AssertContainsAllSublists(
          self, args, ['--project', self.TEST_PROJECT], ['--zone', zone])
      self.assertIn(self.TEST_GKE_CLUSTER, args)

      return retval

    return _CredentialFetchCallback

  @staticmethod
  def _FakeFindExecutableOnPath(executable, path=None):
    if executable == 'gcloud':
      return EnvironmentsRunGATest.TEST_GCLOUD_PATH
    elif executable == 'kubectl':
      return EnvironmentsRunGATest.TEST_KUBECTL_PATH
    else:
      return None


class EnvironmentsRunBetaTest(EnvironmentsRunGATest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)

  TEST_SUBCOMMAND = 'version'

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunFetchKubectlNamespaceFailPrivate(self, exec_mock,
                                              tmp_kubeconfig_mock):
    private_environment_config = self.messages.PrivateEnvironmentConfig(
        enablePrivateEnvironment=True)
    test_env_object = self.MakeEnvironmentWithStateAndClusterLocation(
        self.messages.Environment.StateValueValuesEnum.RUNNING)
    test_env_object.config.privateEnvironmentConfig = private_environment_config
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=test_env_object)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    def _FailedFetchKubectlNamespaceCallback(*unused_args, **unused_kwargs):
      return 1

    fake_exec.AddCallback(0, _FailedFetchKubectlNamespaceCallback)

    with self.AssertRaisesExceptionMatches(
        command_util.Error,
        'enable access to your private Cloud Composer environment'):
      self.RunEnvironments('run', '--project', self.TEST_PROJECT, '--location',
                           self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                           self.TEST_SUBCOMMAND)
    self.assertEqual(1, exec_mock.call_count)
    fake_exec.Verify()


class EnvironmentsRunAlphaTest(EnvironmentsRunBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)
