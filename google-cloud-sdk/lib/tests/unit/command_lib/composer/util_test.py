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
"""Tests for Composer command util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.container import api_adapter as gke_api_adapter
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib import parameterized
from tests.lib.surface.composer import base
from tests.lib.surface.composer import kubectl_util
import mock
import six


class UtilGATest(base.KubectlShellingUnitTest, parameterized.TestCase):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.GA)

  def SetUp(self):
    self.field_mask_prefix = 'field.mask.prefix'

    self.mock_gke_client = api_mock.Client(
        core_apis.GetClientClass('container', command_util.GKE_API_VERSION))
    self.gke_messages = core_apis.GetMessagesModule(
        'container', command_util.GKE_API_VERSION)
    self.mock_gke_client.Mock()
    self.addCleanup(self.mock_gke_client.Unmock)

  def testBuildPartialUpdate_Clear(self):
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={},
        clear=True)

  def testBuildPartialUpdate_Set(self):
    expected_field_mask = ','.join([
        '{}.{}'.format(self.field_mask_prefix, suffix) for suffix in ['a', 'b']
    ])
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=expected_field_mask,
        expected_patch={
            'a': '1',
            'b': '2'
        },
        clear=False,
        set_entries={
            'a': '1',
            'b': '2'
        })

  def testBuildPartialUpdate_Remove(self):
    remove_keys = ['remove_me_too', 'to_be_removed']
    expected_field_mask = ','.join([
        '{}.{}'.format(self.field_mask_prefix, suffix) for suffix in remove_keys
    ])
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=expected_field_mask,
        expected_patch={},
        clear=False,
        remove_keys=remove_keys)

  def testBuildPartialUpdate_RemoveWithDuplicate(self):
    remove_keys = ['duplicated', 'remove_me_too']
    remove_keys_with_dupe = ['duplicated', 'duplicated', 'remove_me_too']
    expected_field_mask = ','.join([
        '{}.{}'.format(self.field_mask_prefix, suffix) for suffix in remove_keys
    ])
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=expected_field_mask,
        expected_patch={},
        clear=False,
        remove_keys=remove_keys_with_dupe)

  def testBuildPartialUpdate_ClearRemove(self):
    remove_keys = ['to_be_removed', 'remove_me_too']
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={},
        clear=True,
        remove_keys=remove_keys)

  def testBuildPartialUpdate_ClearSet(self):
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={'thisis': 'set'},
        clear=True,
        set_entries={'thisis': 'set'})

  def testBuildPartialUpdate_RemoveSet(self):
    remove_keys = ['ignored', 'notignored']
    expected_field_mask = ','.join([
        '{}.{}'.format(self.field_mask_prefix, suffix) for suffix in remove_keys
    ])
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=expected_field_mask,
        expected_patch={'ignored': 'not'},
        clear=False,
        remove_keys=remove_keys,
        set_entries={'ignored': 'not'})

  def testBuildPartialUpdate_ClearRemoveSet(self):
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={'ignored': 'not'},
        clear=True,
        remove_keys=['ignored', 'notignored'],
        set_entries={'ignored': 'not'})

  def testBuildPartialUpdate_AcceptsNoneRemoveSet(self):
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={},
        clear=True,
        remove_keys=None,
        set_entries=None)

  def testBuildFullMapUpdate_Clear(self):
    self._BuildFullMapUpdateTestHelper(
        initial_entries={'name': 'val'}, expected_patch={}, clear=True)

  def testBuildFullMapUpdate_Set(self):
    self._BuildFullMapUpdateTestHelper(
        initial_entries={},
        expected_patch={
            'a': '1',
            'b': '2'
        },
        clear=False,
        set_entries={
            'a': '1',
            'b': '2'
        })

  def testBuildFullMapUpdate_Remove(self):
    remove_keys = ['remove_me_too', 'to_be_removed']
    self._BuildFullMapUpdateTestHelper(
        initial_entries={
            'remove_me_too': 'val',
            'to_be_removed': 'val'
        },
        expected_patch={},
        clear=False,
        remove_keys=remove_keys)

  def testBuildFullMapUpdate_RemoveWithDuplicate(self):
    remove_keys_with_dupe = ['duplicated', 'duplicated', 'remove_me_too']
    self._BuildFullMapUpdateTestHelper(
        initial_entries={
            'duplicated': 'val',
            'remove_me_too': 'val'
        },
        expected_patch={},
        clear=False,
        remove_keys=remove_keys_with_dupe)

  def testBuildFullMapUpdate_ClearRemove(self):
    remove_keys = ['remove', 'remove_me_too']
    self._BuildFullMapUpdateTestHelper(
        initial_entries={
            'remove': 'val',
            'remove_me_too': 'val'
        },
        expected_patch={},
        clear=True,
        remove_keys=remove_keys)

  def testBuildFullMapUpdate_ClearSet(self):
    self._BuildFullMapUpdateTestHelper(
        initial_entries={'remove': 'val'},
        expected_patch={'set': 'val'},
        clear=True,
        set_entries={'set': 'val'})

  def testBuildFullMapUpdate_RemoveSet(self):
    self._BuildFullMapUpdateTestHelper(
        initial_entries={
            'remove_and_update': 'val',
            'remove': 'val'
        },
        expected_patch={'remove_and_update': 'new_val'},
        clear=False,
        remove_keys=['remove_and_update', 'remove'],
        set_entries={'remove_and_update': 'new_val'})

  def testBuildFullMapUpdate_AcceptsNoneRemoveSet(self):
    self._BuildFullMapUpdateTestHelper(
        initial_entries={},
        expected_patch={},
        clear=True,
        remove_keys=None,
        set_entries=None)

  def testBuildFullMapUpdate_OverridesInitialEntries(self):
    self._BuildFullMapUpdateTestHelper(
        initial_entries={
            'to_keep': 'val',
            'to_remove': 'val',
            'to_update': 'val'
        },
        expected_patch={
            'new_key': 'new_val',
            'to_keep': 'val',
            'to_update': 'new_val'
        },
        clear=False,
        remove_keys=['to_remove', 'nonexistant_key'],
        set_entries={
            'new_key': 'new_val',
            'to_update': 'new_val'
        })

  def testConvertImageVersionToNamespacePrefix(self):
    actual = command_util.ConvertImageVersionToNamespacePrefix(
        'composer-1.2.3-airflow-4.5.6')
    self.assertEqual('composer-1-2-3-airflow-4-5-6', actual)

  def testExtractGkeClusterLocationIdDefaultsToEnvLocation(self):
    """Tests that the environment config location takes precedence."""
    config_zone = 'configZone'
    self._ExtractGkeClusterLocationIdHelper(
        config_zone, [(self.TEST_ENVIRONMENT_ID, 'listZone')], config_zone)

  def testExtractGkeClusterLocationIdFallsBackToSingletonList(self):
    matching_zone = 'matchingZone'
    self._ExtractGkeClusterLocationIdHelper(
        None,
        # Mix in some non-matching cluster IDs and make sure they're ignored.
        [(self.TEST_GKE_CLUSTER + '2', 'badZone'),
         (self.TEST_GKE_CLUSTER, matching_zone),
         (self.TEST_GKE_CLUSTER + '2', 'badZone')],
        matching_zone)

  def testExtractGkeClusterLocationIdFallsBackToFirstInList(self):
    matching_zone = 'matchingZone'
    self._ExtractGkeClusterLocationIdHelper(
        None,
        # Mix in some non-matching cluster IDs and make sure they're ignored.
        [(self.TEST_GKE_CLUSTER, matching_zone),
         (self.TEST_GKE_CLUSTER, matching_zone + '2')],
        matching_zone)

  def _ExtractGkeClusterLocationIdHelper(
      self, env_config_location, list_names_locations, expected_location):
    """Verifies zone extraction for an environment config zone and cluster list.

    This helper constructs a fake Environment whose GKE cluster ID is
    self.TEST_GKE_CLUSTER.

    Args:
      env_config_location: str, the compute location to place in the
          environment's node config
      list_names_locations: (str, str), a list of 2-tuples of cluster IDs and
          locations to return in the GKE ListClusters stub.
      expected_location: str, the expected compute location to be extracted
    """
    env_obj = self.MakeEnvironment(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self.messages.EnvironmentConfig(
            nodeConfig=self.messages.NodeConfig(location=env_config_location),
            gkeCluster=self.TEST_GKE_CLUSTER))

    if not env_config_location:
      properties.VALUES.core.project.Set(self.TEST_PROJECT)
      self.mock_gke_client.projects_locations_clusters.List.Expect(
          self.gke_messages.ContainerProjectsLocationsClustersListRequest(
              parent=gke_api_adapter.ProjectLocation(self.TEST_PROJECT, '-')),
          self.gke_messages.ListClustersResponse(clusters=[
              self.gke_messages.Cluster(name=list_name, location=list_location)
              for list_name, list_location in list_names_locations
          ]))
    self.assertEqual(expected_location,
                     command_util.ExtractGkeClusterLocationId(env_obj))

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testFetchKubectlNamespace(self, exec_mock, tmp_kubeconfig_mock):
    env_image_version = 'composer-1.2.3-airflow-4.5.6'

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    # NOTE: FetchKubectlNamespace() results are returned in asc order by
    #       creation timestamp.

    # Scenario // 2 active namespaces.
    fake_exec.AddCallback(
        0,
        self.MakeFetchKubectlNamespaceCallback(
            [('default', 'Active'),
             ('composer-1-2-3-airflow-4-5-6-aabbccdd', 'Active')]))

    # Scenario // 3 active namespaces.
    fake_exec.AddCallback(
        1,
        self.MakeFetchKubectlNamespaceCallback(
            [('default', 'Active'),
             ('composer-1-2-3-airflow-4-5-6-aabbccdd', 'Active'),
             ('composer-1-2-3-airflow-4-5-6-beeffeed', 'Active')]))

    # Scenario // 3 namespaces;
    # 2 active namespaces, but most recent namespace in 'Terminating' state.
    fake_exec.AddCallback(
        2,
        self.MakeFetchKubectlNamespaceCallback(
            [('default', 'Active'),
             ('composer-1-2-3-airflow-4-5-6-aabbccdd', 'Active'),
             ('composer-1-2-3-airflow-4-5-6-beeffeed', 'Terminating')]))

    # Scenario // 3 namespaces, but none match image-version prefix.
    fake_exec.AddCallback(
        3,
        self.MakeFetchKubectlNamespaceCallback([('foo', 'Active'),
                                                ('bar', 'Terminating'),
                                                ('baz', 'Active')]))

    self.assertEqual('composer-1-2-3-airflow-4-5-6-aabbccdd',
                     command_util.FetchKubectlNamespace(env_image_version))
    self.assertEqual('composer-1-2-3-airflow-4-5-6-beeffeed',
                     command_util.FetchKubectlNamespace(env_image_version))
    self.assertEqual('composer-1-2-3-airflow-4-5-6-aabbccdd',
                     command_util.FetchKubectlNamespace(env_image_version))
    self.assertEqual('default',
                     command_util.FetchKubectlNamespace(env_image_version))

    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunKubectlCommand_Success(self, exec_mock,
                                    tmp_kubeconfig_mock):
    kubectl_args = ['exec', '-it', 'airflow-worker12345', 'bash']
    expected_args = command_util.AddKubectlNamespace(
        self.TEST_KUBECTL_DEFAULT_NAMESPACE,
        [self.TEST_KUBECTL_PATH] + kubectl_args)

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, lambda args, **_: self.assertEqual(expected_args, args))
    command_util.RunKubectlCommand(
        kubectl_args, namespace=self.TEST_KUBECTL_DEFAULT_NAMESPACE)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunKubectlCommand_KubectlError(self, exec_mock,
                                         tmp_kubeconfig_mock):
    kubectl_args = ['exec', '-it', 'airflow-worker12345', 'bash']

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    # kubectl returns with nonzero exit code
    fake_exec.AddCallback(0, lambda *_, **__: 1)
    with self.AssertRaisesExceptionMatches(
        command_util.KubectlError, 'kubectl returned non-zero status code'):
      command_util.RunKubectlCommand(kubectl_args)
    fake_exec.Verify()

  @mock.patch.object(files, 'FindExecutableOnPath')
  @mock.patch('googlecloudsdk.core.config.Paths')
  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunKubectlCommandSearchesEntirePath(
      self, exec_mock, tmp_kubeconfig_mock, config_paths_mock,
      find_executable_mock):
    kubectl_args = ['exec', '-it', 'airflow-worker12345', 'bash']

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig
    fake_exec.AddCallback(0, lambda *_, **__: 0)

    config_paths_mock.sdk_bin_path = self.TEST_GCLOUD_PATH

    # Find the executable only when searching entire path, not just SDK location
    def _FakeFindExecutableOnFullPath(executable, path=None, **_):
      if executable == 'kubectl':
        if path is None:
          return base.KubectlShellingUnitTest.TEST_KUBECTL_PATH
      return None

    find_executable_mock.side_effect = _FakeFindExecutableOnFullPath

    # An error would be thrown if kubectl path was not found
    command_util.RunKubectlCommand(kubectl_args)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testGetGkePod_Success(self, exec_mock, tmp_kubeconfig_mock):
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0,
        self.MakeGetPodsCallback([('airflow-worker12345', 'running'),
                                  ('airflow-scheduler00001', 'running')]))

    pod = command_util.GetGkePod('airflow-worker',
                                 self.TEST_KUBECTL_DEFAULT_NAMESPACE)
    self.assertEqual('airflow-worker12345', pod)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testGetGkePod_PodNotFound(self, exec_mock, tmp_kubeconfig_mock):
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, self.MakeGetPodsCallback([('pod1', 'running'), ('pod2', 'running')]))

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Desired GKE pod not found'):
      command_util.GetGkePod('pod3', self.TEST_KUBECTL_DEFAULT_NAMESPACE)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testGetGkePod_PodNotRunning(self, exec_mock, tmp_kubeconfig_mock):
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, self.MakeGetPodsCallback([('pod1', 'creating'), ('pod2',
                                                            'creating')]))

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'No running GKE pods found.'):
      command_util.GetGkePod('pod1', self.TEST_KUBECTL_DEFAULT_NAMESPACE)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testGetGkePod_KubectlError(self, exec_mock, tmp_kubeconfig_mock):
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    # kubectl returns with nonzero exit code
    fake_exec.AddCallback(0, lambda *_, **__: 1)

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Error retrieving GKE pods'):
      command_util.GetGkePod('pod1', self.TEST_KUBECTL_DEFAULT_NAMESPACE)
    fake_exec.Verify()

  def testParseRequirementsFileNoVersionMatch(self):
    """Tests parsing pypi requirements without a version."""
    requirements_file = self.Touch(self.root_path, contents='numpy')
    actual_entries = command_util.ParseRequirementsFile(requirements_file)
    self.assertEqual({'numpy': ''}, actual_entries)

  def testParseRequirementsFileDuplicateKey(self):
    """Tests error when parsing pypi requirements with duplicate package."""
    requirements_file = self.Touch(
        self.root_path, contents='package>0.1\npackage\n')
    with self.assertRaises(command_util.Error):
      command_util.ParseRequirementsFile(requirements_file)

  def testParseRequirementsFileStripsLines(self):
    """Tests parsing requirements file with leading and trailing whitespace."""
    requirements_file = self.Touch(
        self.root_path, contents=' package  \n package2[extra1]\t\n')
    actual_entries = command_util.ParseRequirementsFile(requirements_file)
    self.assertEqual({'package': '', 'package2': '[extra1]'}, actual_entries)

  def testParseRequirementsFileIgnoreWhitespaceLines(self):
    """Tests parsing requirements file skips lines with only whitespace."""
    requirements_file = self.Touch(
        self.root_path, contents='\n \npackage\n  \t\npackage2[extra1]\n \n')
    actual_entries = command_util.ParseRequirementsFile(requirements_file)
    self.assertEqual({'package': '', 'package2': '[extra1]'}, actual_entries)

  def testParseRequirementsFileInGcs(self):
    """Tests parsing requirements file in GCS file path."""
    requirements_file = 'gs://mybucket/pypi.txt'
    read_object_mock = self.StartObjectPatch(
        storage_api.StorageClient, 'ReadObject')
    command_util.ParseRequirementsFile(requirements_file)
    config_object = storage_util.ObjectReference.FromUrl(requirements_file)
    read_object_mock.assert_called_once_with(config_object)

  def testSplitRequirementSpecifierNoPackage(self):
    """Tests error splitting requirements specifier with no package name."""
    with self.assertRaises(command_util.Error):
      command_util.SplitRequirementSpecifier('[extra1]==1')

  def testSplitRequirementSpecifierPackageNameOnly(self):
    """Tests splitting requirements specifier with only package name."""
    actual_entry = command_util.SplitRequirementSpecifier('package')
    self.assertEqual(('package', ''), actual_entry)

  def testSplitRequirementSpecifierExtras(self):
    """Tests splitting requirements specifier with extras."""
    actual_entry = command_util.SplitRequirementSpecifier(
        'package[extra1,extra2]')
    self.assertEqual(('package', '[extra1,extra2]'), actual_entry)

  def testSplitRequirementSpecifierExtrasWithWhitespace(self):
    """Tests splitting requirements specifier with whitespace in version.
    """
    actual_entry = command_util.SplitRequirementSpecifier(
        'package[ extra1 , extra2 ]')
    self.assertEqual(('package', '[ extra1 , extra2 ]'), actual_entry)

  def testSplitRequirementSpecifierVersion(self):
    """Tests splitting requirements specifier with version."""
    actual_entry = command_util.SplitRequirementSpecifier('package==1')
    self.assertEqual(('package', '==1'), actual_entry)

  def testSplitRequirementSpecifierVersionWithWhitespace(self):
    """Tests splitting requirements specifier with whitespace in version."""
    actual_entry = command_util.SplitRequirementSpecifier('package== 1')
    self.assertEqual(('package', '== 1'), actual_entry)

  def testSplitRequirementSpecifierExtrasAndVersion(self):
    """Tests splitting requirements specifier with extras and version."""
    actual_entry = command_util.SplitRequirementSpecifier(
        'package[extra1,extra2]==1')
    self.assertEqual(('package', '[extra1,extra2]==1'), actual_entry)

  def testSplitRequirementSpecifierStripsComponents(self):
    """Tests splitting requirements specifier strips package name and tail."""
    actual_entry = command_util.SplitRequirementSpecifier(
        'package [ extra1, extra2 ] == 1 ')
    self.assertEqual(('package', '[ extra1, extra2 ] == 1'), actual_entry)

  def testAddKubectlNamespace(self):
    expected_tmpl = '/fake/kubectl --namespace {} get pods'

    # Checks that namespace args have been added.
    test_args = ['/fake/kubectl', 'get', 'pods']
    self.assertEqual(
        expected_tmpl.format(self.TEST_KUBECTL_DEFAULT_NAMESPACE).split(' '),
        command_util.AddKubectlNamespace(self.TEST_KUBECTL_DEFAULT_NAMESPACE,
                                         test_args))

    # Checks that a supplied namespace scope is not overwritten.
    test_args = ['/fake/kubectl', '--namespace', 'foo', 'get', 'pods']
    self.assertEqual(
        expected_tmpl.format('foo').split(' '),
        command_util.AddKubectlNamespace(self.TEST_KUBECTL_DEFAULT_NAMESPACE,
                                         test_args))

  @staticmethod
  def _FakePatchBuilder(entries):
    return dict((e.key, e.value) for e in entries)

  class _FakeEntry(object):

    def __init__(self, key, value):
      self.key = key
      self.value = value

  def _BuildPartialUpdateTestHelper(self,
                                    expected_field_mask,
                                    expected_patch,
                                    clear,
                                    remove_keys=None,
                                    set_entries=None):
    """Helper for testing BuildPartialUpdate.

    Using this helper, one can test that BuildPartialUpdate combines `clear`,
    `remove_keys`, and `set_entries` (in that order) to build a patch object and
    update mask.

    Args:
      expected_field_mask: str, sorted, comma-delimited list of fields expected
          to appear in the patch request's field mask
      expected_patch: dict, a dictionary of the key-value pairs expected to
          be in the patch
      clear: bool, the value of the clear parameter to pass through
      remove_keys: [str], the value of the remove_keys parameter to pass through
      set_entries: {str: str}, the value of the set_entries parameter to pass
          through
    """
    actual_field_mask, actual_patch = command_util.BuildPartialUpdate(
        clear=clear,
        remove_keys=remove_keys,
        set_entries=set_entries,
        field_mask_prefix=self.field_mask_prefix,
        entry_cls=UtilGATest._FakeEntry,
        env_builder=UtilGATest._FakePatchBuilder)
    self.assertEqual(expected_field_mask, actual_field_mask)
    self.assertEqual(expected_patch, actual_patch)

  def _BuildFullMapUpdateTestHelper(self,
                                    expected_patch,
                                    clear,
                                    remove_keys=None,
                                    set_entries=None,
                                    initial_entries=None):
    """Helper for testing BuildFullMapUpdate.

    Using this helper, one can test that BuildFullMapUpdate combines
    `clear`, `remove_keys`, `set_entries`, and `initial_entries` (in that order)
    to build a patch object.

    Args:
      expected_patch: dict, a dictionary of the key-value pairs expected to
          be in the patch
      clear: bool, the value of the clear parameter to pass through
      remove_keys: [str], the value of the remove_keys parameter to pass through
      set_entries: {str: str}, the value of the set_entries parameter to pass
          through
      initial_entries: dict, a dictionary of the key-value pairs in the initial
        entry
    """
    actual_patch = command_util.BuildFullMapUpdate(
        clear=clear,
        remove_keys=remove_keys,
        set_entries=set_entries,
        initial_entries=[
            UtilGATest._FakeEntry(key=key, value=value)
            for key, value in six.iteritems(initial_entries or {})
        ],
        entry_cls=UtilGATest._FakeEntry,
        env_builder=UtilGATest._FakePatchBuilder)
    self.assertEqual(expected_patch, actual_patch)


class UtilBetaTest(UtilGATest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)
