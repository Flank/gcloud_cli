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


@parameterized.parameters(calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class UtilTest(base.KubectlShellingUnitTest, parameterized.TestCase):

  def SetUp(self):
    self.field_mask_prefix = 'field.mask.prefix'

    self.mock_gke_client = api_mock.Client(
        core_apis.GetClientClass('container', command_util.GKE_API_VERSION))
    self.gke_messages = core_apis.GetMessagesModule(
        'container', command_util.GKE_API_VERSION)
    self.mock_gke_client.Mock()
    self.addCleanup(self.mock_gke_client.Unmock)

  def testBuildPartialUpdate_Clear(self, track):
    self.SetTrack(track)
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={},
        clear=True)

  def testBuildPartialUpdate_Set(self, track):
    self.SetTrack(track)
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

  def testBuildPartialUpdate_Remove(self, track):
    self.SetTrack(track)
    remove_keys = ['remove_me_too', 'to_be_removed']
    expected_field_mask = ','.join([
        '{}.{}'.format(self.field_mask_prefix, suffix) for suffix in remove_keys
    ])
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=expected_field_mask,
        expected_patch={},
        clear=False,
        remove_keys=remove_keys)

  def testBuildPartialUpdate_RemoveWithDuplicate(self, track):
    self.SetTrack(track)
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

  def testBuildPartialUpdate_ClearRemove(self, track):
    self.SetTrack(track)
    remove_keys = ['to_be_removed', 'remove_me_too']
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={},
        clear=True,
        remove_keys=remove_keys)

  def testBuildPartialUpdate_ClearSet(self, track):
    self.SetTrack(track)
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={'thisis': 'set'},
        clear=True,
        set_entries={'thisis': 'set'})

  def testBuildPartialUpdate_RemoveSet(self, track):
    self.SetTrack(track)
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

  def testBuildPartialUpdate_ClearRemoveSet(self, track):
    self.SetTrack(track)
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={'ignored': 'not'},
        clear=True,
        remove_keys=['ignored', 'notignored'],
        set_entries={'ignored': 'not'})

  def testBuildPartialUpdate_AcceptsNoneRemoveSet(self, track):
    self.SetTrack(track)
    self._BuildPartialUpdateTestHelper(
        expected_field_mask=self.field_mask_prefix,
        expected_patch={},
        clear=True,
        remove_keys=None,
        set_entries=None)

  def testBuildFullMapUpdate_Clear(self, track):
    self.SetTrack(track)
    self._BuildFullMapUpdateTestHelper(
        initial_entries={'name': 'val'}, expected_patch={}, clear=True)

  def testBuildFullMapUpdate_Set(self, track):
    self.SetTrack(track)
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

  def testBuildFullMapUpdate_Remove(self, track):
    self.SetTrack(track)
    remove_keys = ['remove_me_too', 'to_be_removed']
    self._BuildFullMapUpdateTestHelper(
        initial_entries={
            'remove_me_too': 'val',
            'to_be_removed': 'val'
        },
        expected_patch={},
        clear=False,
        remove_keys=remove_keys)

  def testBuildFullMapUpdate_RemoveWithDuplicate(self, track):
    self.SetTrack(track)
    remove_keys_with_dupe = ['duplicated', 'duplicated', 'remove_me_too']
    self._BuildFullMapUpdateTestHelper(
        initial_entries={
            'duplicated': 'val',
            'remove_me_too': 'val'
        },
        expected_patch={},
        clear=False,
        remove_keys=remove_keys_with_dupe)

  def testBuildFullMapUpdate_ClearRemove(self, track):
    self.SetTrack(track)
    remove_keys = ['remove', 'remove_me_too']
    self._BuildFullMapUpdateTestHelper(
        initial_entries={
            'remove': 'val',
            'remove_me_too': 'val'
        },
        expected_patch={},
        clear=True,
        remove_keys=remove_keys)

  def testBuildFullMapUpdate_ClearSet(self, track):
    self.SetTrack(track)
    self._BuildFullMapUpdateTestHelper(
        initial_entries={'remove': 'val'},
        expected_patch={'set': 'val'},
        clear=True,
        set_entries={'set': 'val'})

  def testBuildFullMapUpdate_RemoveSet(self, track):
    self.SetTrack(track)
    self._BuildFullMapUpdateTestHelper(
        initial_entries={
            'remove_and_update': 'val',
            'remove': 'val'
        },
        expected_patch={'remove_and_update': 'new_val'},
        clear=False,
        remove_keys=['remove_and_update', 'remove'],
        set_entries={'remove_and_update': 'new_val'})

  def testBuildFullMapUpdate_AcceptsNoneRemoveSet(self, track):
    self.SetTrack(track)
    self._BuildFullMapUpdateTestHelper(
        initial_entries={},
        expected_patch={},
        clear=True,
        remove_keys=None,
        set_entries=None)

  def testBuildFullMapUpdate_OverridesInitialEntries(self, track):
    self.SetTrack(track)
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

  def testExtractGkeClusterLocationIdDefaultsToEnvLocation(self, track):
    """Tests that the environment config location takes precedence."""
    self.SetTrack(track)
    config_zone = 'configZone'
    self._ExtractGkeClusterLocationIdHelper(
        config_zone, [(self.TEST_ENVIRONMENT_ID, 'listZone')], config_zone)

  def testExtractGkeClusterLocationIdFallsBackToSingletonList(self, track):
    self.SetTrack(track)
    matching_zone = 'matchingZone'
    self._ExtractGkeClusterLocationIdHelper(
        None,
        # Mix in some non-matching cluster IDs and make sure they're ignored.
        [(self.TEST_GKE_CLUSTER + '2', 'badZone'),
         (self.TEST_GKE_CLUSTER, matching_zone),
         (self.TEST_GKE_CLUSTER + '2', 'badZone')],
        matching_zone)

  def testExtractGkeClusterLocationIdFallsBackToFirstInList(self, track):
    self.SetTrack(track)
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
    self.assertEquals(expected_location,
                      command_util.ExtractGkeClusterLocationId(env_obj))

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunKubectlCommand_Success(self, track, exec_mock,
                                    tmp_kubeconfig_mock):
    self.SetTrack(track)
    kubectl_args = ['exec', '-it', 'airflow-worker12345', 'bash']
    expected_args = [self.TEST_KUBECTL_PATH] + kubectl_args

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, lambda args, **_: self.assertEqual(expected_args, args))
    command_util.RunKubectlCommand(kubectl_args)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testRunKubectlCommand_KubectlError(self, track, exec_mock,
                                         tmp_kubeconfig_mock):
    self.SetTrack(track)
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
      self, track, exec_mock, tmp_kubeconfig_mock, config_paths_mock,
      find_executable_mock):
    self.SetTrack(track)
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
  def testGetGkePod_Success(self, track, exec_mock, tmp_kubeconfig_mock):
    self.SetTrack(track)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0,
        self.MakeGetPodsCallback([('airflow-worker12345', 'running'),
                                  ('airflow-scheduler00001', 'running')]))

    pod = command_util.GetGkePod('airflow-worker')
    self.assertEqual('airflow-worker12345', pod)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testGetGkePod_PodNotFound(self, track, exec_mock, tmp_kubeconfig_mock):
    self.SetTrack(track)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, self.MakeGetPodsCallback([('pod1', 'running'), ('pod2', 'running')]))

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Desired GKE pod not found'):
      command_util.GetGkePod('pod3')
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testGetGkePod_PodNotRunning(self, track, exec_mock, tmp_kubeconfig_mock):
    self.SetTrack(track)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    fake_exec.AddCallback(
        0, self.MakeGetPodsCallback([('pod1', 'creating'), ('pod2',
                                                            'creating')]))

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'No running GKE pods found.'):
      command_util.GetGkePod('pod1')
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.command_lib.composer.util.TemporaryKubeconfig')
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testGetGkePod_KubectlError(self, track, exec_mock, tmp_kubeconfig_mock):
    self.SetTrack(track)
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    tmp_kubeconfig_mock.side_effect = self.FakeTemporaryKubeconfig

    # kubectl returns with nonzero exit code
    fake_exec.AddCallback(0, lambda *_, **__: 1)

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Error retrieving GKE pods'):
      command_util.GetGkePod('pod1')
    fake_exec.Verify()

  def testParseRequirementsFileNoVersionMatch(self, track):
    """Tests parsing pypi requirements without a version."""
    self.SetTrack(track)
    requirements_file = self.Touch(self.root_path, contents='numpy')
    actual_entries = command_util.ParseRequirementsFile(requirements_file)
    self.assertEqual({'numpy': ''}, actual_entries)

  def testParseRequirementsFileDuplicateKey(self, track):
    """Tests error when parsing pypi requirements with duplicate package."""
    self.SetTrack(track)
    requirements_file = self.Touch(
        self.root_path, contents='package>0.1\npackage\n')
    with self.assertRaises(command_util.Error):
      command_util.ParseRequirementsFile(requirements_file)

  def testParseRequirementsFileStripsLines(self, track):
    """Tests parsing requirements file with leading and trailing whitespace."""
    self.SetTrack(track)
    requirements_file = self.Touch(
        self.root_path, contents=' package  \n package2[extra1]\t\n')
    actual_entries = command_util.ParseRequirementsFile(requirements_file)
    self.assertEqual({'package': '', 'package2': '[extra1]'}, actual_entries)

  def testParseRequirementsFileIgnoreWhitespaceLines(self, track):
    """Tests parsing requirements file skips lines with only whitespace."""
    self.SetTrack(track)
    requirements_file = self.Touch(
        self.root_path, contents='\n \npackage\n  \t\npackage2[extra1]\n \n')
    actual_entries = command_util.ParseRequirementsFile(requirements_file)
    self.assertEqual({'package': '', 'package2': '[extra1]'}, actual_entries)

  def testSplitRequirementSpecifierNoPackage(self, track):
    """Tests error splitting requirements specifier with no package name."""
    self.SetTrack(track)
    with self.assertRaises(command_util.Error):
      command_util.SplitRequirementSpecifier('[extra1]==1')

  def testSplitRequirementSpecifierPackageNameOnly(self, track):
    """Tests splitting requirements specifier with only package name."""
    self.SetTrack(track)
    actual_entry = command_util.SplitRequirementSpecifier('package')
    self.assertEqual(('package', ''), actual_entry)

  def testSplitRequirementSpecifierExtras(self, track):
    """Tests splitting requirements specifier with extras."""
    self.SetTrack(track)
    actual_entry = command_util.SplitRequirementSpecifier(
        'package[extra1,extra2]')
    self.assertEqual(('package', '[extra1,extra2]'), actual_entry)

  def testSplitRequirementSpecifierExtrasWithWhitespace(self, track):
    """Tests splitting requirements specifier with whitespace in version.

    Args:
      track: base.ReleaseTrack, the release track to use when testing Composer
      commands.
    """
    self.SetTrack(track)
    actual_entry = command_util.SplitRequirementSpecifier(
        'package[ extra1 , extra2 ]')
    self.assertEqual(('package', '[ extra1 , extra2 ]'), actual_entry)

  def testSplitRequirementSpecifierVersion(self, track):
    """Tests splitting requirements specifier with version."""
    self.SetTrack(track)
    actual_entry = command_util.SplitRequirementSpecifier('package==1')
    self.assertEqual(('package', '==1'), actual_entry)

  def testSplitRequirementSpecifierVersionWithWhitespace(self, track):
    """Tests splitting requirements specifier with whitespace in version."""
    self.SetTrack(track)
    actual_entry = command_util.SplitRequirementSpecifier('package== 1')
    self.assertEqual(('package', '== 1'), actual_entry)

  def testSplitRequirementSpecifierExtrasAndVersion(self, track):
    """Tests splitting requirements specifier with extras and version."""
    self.SetTrack(track)
    actual_entry = command_util.SplitRequirementSpecifier(
        'package[extra1,extra2]==1')
    self.assertEqual(('package', '[extra1,extra2]==1'), actual_entry)

  def testSplitRequirementSpecifierStripsComponents(self, track):
    """Tests splitting requirements specifier strips package name and tail."""
    self.SetTrack(track)
    actual_entry = command_util.SplitRequirementSpecifier(
        'package [ extra1, extra2 ] == 1 ')
    self.assertEqual(('package', '[ extra1, extra2 ] == 1'), actual_entry)

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
        entry_cls=UtilTest._FakeEntry,
        env_builder=UtilTest._FakePatchBuilder)
    self.assertEquals(expected_field_mask, actual_field_mask)
    self.assertEquals(expected_patch, actual_patch)

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
            UtilTest._FakeEntry(key=key, value=value)
            for key, value in six.iteritems(initial_entries or {})
        ],
        entry_cls=UtilTest._FakeEntry,
        env_builder=UtilTest._FakePatchBuilder)
    self.assertEquals(expected_patch, actual_patch)
