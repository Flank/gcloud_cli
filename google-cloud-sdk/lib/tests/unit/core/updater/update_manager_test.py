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
from __future__ import absolute_import
from __future__ import unicode_literals
import io
import os
import platform
import re
import shlex
import subprocess
import sys
import time

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.updater import installers
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import schemas
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.updater import update_check
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.updater import util
import mock


class UpdateManagerTests(util.Base,
                         sdk_test_base.WithOutputCapture,
                         test_case.WithInput):

  def SetUp(self):
    properties.VALUES.experimental.fast_component_update.Set(False)
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.component_manager.disable_update_check.Set(False)
    self.release_notes_file = self.Touch(self.root_path, 'release_notes', """
# Release Notes

## 1 (date)

*   Note

## HEAD (date)

*   Note
""")
    # We don't want this accidentally restarting during the test.
    self.restart_bundled_mock = self.StartObjectPatch(
        update_manager.UpdateManager, '_RestartIfUsingBundledPython')
    # Do this so we can test the warnings for removing bundled Python
    self.StartObjectPatch(update_manager.UpdateManager,
                          'IsPythonBundled').return_value = True
    self.postprocess_mock = self.StartObjectPatch(
        update_manager.UpdateManager, '_PostProcess')

  @test_case.Filters.DoNotRunIf(
      not util.FilesystemSupportsUnicodeEncodedPaths(),
      'updater not tested with a UNICODE encoded installation directory.')
  def testFilesystemSupportsUnicodeEncodedPaths(self):
    # This test is a log check. If it is skipped then the filesystem does not
    # support UNICODE encoded paths and the updater/installer will not be
    # tested on a UNICODE encoded installation directory under this test runner.
    self.assertTrue(util.FilesystemSupportsUnicodeEncodedPaths())

  def testFixedSDKVersion(self):
    properties.VALUES.component_manager.fixed_sdk_version.Set('0.0.0')
    for warn in [True, False]:
      manager = update_manager.UpdateManager(
          self.sdk_root_path,
          'file://some/path/components.json,'
          'file://another/path/components.json',
          warn=warn)
      self.assertEqual(
          'file://some/path/components-v0.0.0.json,'
          'file://another/path/components.json',
          manager._GetEffectiveSnapshotURL())
      self.AssertErrContains(
          'WARNING: You are using an overridden snapshot URL',
          success=warn)
      self.AssertErrContains(
          'WARNING: You have configured your Cloud SDK installation to be '
          'fixed to version',
          success=warn)
      with self.assertRaisesRegex(
          update_manager.MismatchedFixedVersionsError,
          r'be fixed to version \[0\.0\.0\] but are attempting to install '
          r'components at\nversion \[1\]\.'):
        manager._GetEffectiveSnapshotURL(version='1')
      self.ClearErr()

  def testAdditionalRepos(self):
    properties.VALUES.component_manager.additional_repositories.Set(
        'REPO1,REPO2')
    for warn in [True, False]:
      manager = update_manager.UpdateManager(
          self.sdk_root_path,
          'file://some/path/components.json',
          warn=warn)
      self.assertEqual(
          'file://some/path/components.json,REPO1,REPO2',
          manager._GetEffectiveSnapshotURL())
      self.AssertErrContains(
          'WARNING: You are using additional component repository',
          success=warn)
      self.ClearErr()

  def testSnapshotFetchErrors(self):
    manager = update_manager.UpdateManager(
        self.sdk_root_path,
        'file://some/path/components.json')
    with self.assertRaises(snapshots.URLFetchError):
      manager._GetLatestSnapshot(version='2')
    self.AssertErrContains(
        'The component listing for Cloud SDK version [2] could not be')
    self.ClearErr()

    properties.VALUES.component_manager.fixed_sdk_version.Set('1')
    manager = update_manager.UpdateManager(
        self.sdk_root_path,
        'file://some/path/components.json')
    with self.assertRaises(snapshots.URLFetchError):
      manager._GetLatestSnapshot()
    self.AssertErrContains(
        'You have configured your Cloud SDK installation to be fixed to '
        'version [1].')

  def testMissingComponent(self):
    # initial install
    component_tuples = [('a', 1, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    with self.assertRaisesRegex(update_manager.InvalidComponentError,
                                r'The following components are unknown \[b\]'):
      manager.Update(['b'])
    self.AssertErrNotContains('no longer exists')

    with self.assertRaisesRegex(update_manager.InvalidComponentError,
                                r'The following components are unknown \[b\]'):
      manager.Update(['b', 'pkg-core'])
    self.AssertErrContains('no longer exists')
    self.ClearErr()

    manager.Update(['a', 'pkg-core'])
    self.AssertErrContains('no longer exists')
    self.ClearErr()

    manager.Update(['a', 'gae-python'])
    self.AssertErrContains('no longer exists')
    self.AssertErrContains(
        'The standalone App Engine SDKs are no longer distributed through the '
        'Cloud SDK')

  def testSimpleUpdate(self):
    self.StartPatch('googlecloudsdk.core.config.INSTALLATION_CONFIG.version',
                    new='HEAD')

    # empty
    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], list(install_state.InstalledComponents().keys()))
    self.assertEqual(None, install_state.BackupDirectory())

    # initial install
    component_tuples = [('a', 1, [])]
    snapshot, paths1 = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples,
                                                      self.release_notes_file))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    manager.Update(['a'])
    self.assertTrue(self.restart_bundled_mock.called)
    self.assertTrue(self.postprocess_mock.called)
    self.CheckPathsExist(paths1['a'], exists=True)
    self.assertEqual(['a'], list(install_state.InstalledComponents().keys()))
    self.assertNotEqual(None, install_state.BackupDirectory())
    self.AssertErrContains('Your current Cloud SDK version is: ' +
                           config.INSTALLATION_CONFIG.version)
    self.AssertErrContains('Installing components from version: 1')
    self.AssertErrNotContains('bundled installation of Python')
    # We registered the release notes file, check that it prints the diff.
    rendered_notes = io.StringIO()
    # Actually user the renderer for testing the output because it renders
    # differently on different platforms.
    render_document.RenderDocument('text',
                                   io.StringIO('## 1 (date)\n\n*   Note'),
                                   rendered_notes)
    self.AssertErrContains("""\
The following release notes are new in this upgrade.
Please read carefully for information about new features, breaking changes,
and bugs fixed.  The latest full release notes can be viewed at:
  {0}

{1}
""".format(config.INSTALLATION_CONFIG.release_notes_url,
           rendered_notes.getvalue()))
    self.AssertErrNotContains(
        'To revert your SDK to the previously installed version')
    self.ClearErr()

    # create updated snapshot
    component_tuples = [('a', 2, [])]
    snapshot, paths2 = (
        self.CreateSnapshotFromComponentsGenerateTars(2, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    # Make sure it still works if we can't caluclate the CWD.
    self.StartPatch('os.getcwd').side_effect = OSError()
    manager.Update()
    self.CheckPathsExist(paths1['a'], exists=False)
    self.CheckPathsExist(paths2['a'], exists=True)
    self.assertEqual(['a'], list(install_state.InstalledComponents().keys()))
    self.assertNotEqual(None, install_state.BackupDirectory())
    self.CheckPathsExist(paths1['a'], exists=True,
                         alt_root=install_state.BackupDirectory())
    self.CheckPathsExist(paths2['a'], exists=False,
                         alt_root=install_state.BackupDirectory())
    # We did not register a valid release notes file, check that the generic
    # message shows.
    self.AssertErrContains(
        'For the latest full release notes, please visit:\n  ' +
        config.INSTALLATION_CONFIG.release_notes_url)
    self.AssertErrContains('Your current Cloud SDK version is: ' +
                           config.INSTALLATION_CONFIG.version)
    self.AssertErrContains('You will be upgraded to version: 2')
    self.AssertErrContains(
        'To revert your SDK to the previously installed version')
    self.AssertErrContains(
        '  $ gcloud components update --version HEAD')

    # create updated snapshot with new dependency
    component_tuples = [('a', 3, ['b']), ('b', 1, []), ('c', 1, [])]
    snapshot, paths3 = (
        self.CreateSnapshotFromComponentsGenerateTars(3, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    manager.Update(['a'])
    self.CheckPathsExist(paths1['a'], exists=False)
    self.CheckPathsExist(paths2['a'], exists=False)
    self.CheckPathsExist(paths3['a'], exists=True)
    self.CheckPathsExist(paths3['b'], exists=True)
    self.CheckPathsExist(paths3['c'], exists=False)
    self.assertEqual(set(['a', 'b']),
                     set(install_state.InstalledComponents().keys()))
    self.assertNotEqual(None, install_state.BackupDirectory())
    self.CheckPathsExist(paths1['a'], exists=False,
                         alt_root=install_state.BackupDirectory())
    self.CheckPathsExist(paths2['a'], exists=True,
                         alt_root=install_state.BackupDirectory())
    self.CheckPathsExist(paths3['a'], exists=False,
                         alt_root=install_state.BackupDirectory())
    self.CheckPathsExist(paths3['b'], exists=False,
                         alt_root=install_state.BackupDirectory())
    self.CheckPathsExist(paths3['c'], exists=False,
                         alt_root=install_state.BackupDirectory())

    manager.Update(['c'])
    self.CheckPathsExist(paths3['a'], exists=True)
    self.CheckPathsExist(paths3['b'], exists=True)
    self.CheckPathsExist(paths3['c'], exists=True)
    self.assertEqual(set(['a', 'b', 'c']),
                     set(install_state.InstalledComponents().keys()))
    self.assertNotEqual(None, install_state.BackupDirectory())
    self.CheckPathsExist(paths1['a'], exists=False,
                         alt_root=install_state.BackupDirectory())
    self.CheckPathsExist(paths2['a'], exists=False,
                         alt_root=install_state.BackupDirectory())
    self.CheckPathsExist(paths3['a'], exists=True,
                         alt_root=install_state.BackupDirectory())
    self.CheckPathsExist(paths3['b'], exists=True,
                         alt_root=install_state.BackupDirectory())
    self.CheckPathsExist(paths3['c'], exists=False,
                         alt_root=install_state.BackupDirectory())

    component_tuples = [('a', 4, []), ('c', 1, []), ('d', 1, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(4, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    diffs, _, _ = manager.List()
    self.assertEqual(4, len(diffs))
    diffs = dict((d.id, d) for d in diffs)
    self.assertEqual(snapshots.ComponentState.UPDATE_AVAILABLE,
                     diffs['a'].state)
    self.assertEqual(snapshots.ComponentState.REMOVED, diffs['b'].state)
    self.assertEqual(snapshots.ComponentState.UP_TO_DATE, diffs['c'].state)
    self.assertEqual(snapshots.ComponentState.NEW, diffs['d'].state)

  def testInstall(self):
    self.StartPatch('googlecloudsdk.core.config.INSTALLATION_CONFIG.version',
                    new='1')

    # Empty
    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], list(install_state.InstalledComponents().keys()))
    self.assertEqual(None, install_state.BackupDirectory())

    # Initial install
    component_tuples = [('a', 1, []), ('b', 1, [])]
    snapshot, paths1 = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples,
                                                      self.release_notes_file))
    url = self.URLFromFile(
        self.CreateTempSnapshotFileFromSnapshot(snapshot, versioned=True))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    with self.assertRaisesRegex(update_manager.InvalidComponentError,
                                'You must specify components to install'):
      manager.Install([])
    self.restart_bundled_mock.reset_mock()

    # Check invalid component.
    with self.assertRaisesRegex(
        update_manager.InvalidComponentError,
        r'The following components are unknown \[junk\].'):
      manager.Install(['junk'])
    self.restart_bundled_mock.reset_mock()

    manager.Install(['a'])
    self.assertTrue(self.restart_bundled_mock.called)
    self.assertTrue(self.postprocess_mock.called)
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=False)
    self.AssertErrNotContains(
        'To revert your SDK to the previously installed version')
    self.ClearErr()

    # No-op if already installed.
    manager.Install(['a'])
    self.AssertErrContains('All components are up to date.')
    self.ClearErr()

    self.assertEqual({'a': '1'}, manager.GetCurrentVersionsInformation())
    manager.Install(['b'])
    self.assertEqual({'a': '1', 'b': '1'},
                     manager.GetCurrentVersionsInformation())

    # Create updated snapshot
    component_tuples = [('a', 2, []), ('b', 2, []), ('c', 1, [])]
    snapshot, paths2 = (
        self.CreateSnapshotFromComponentsGenerateTars(2, component_tuples))
    snapshot.ComponentFromId('b').is_hidden = True
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)

    # Installing b should install from version 1 even though we are now pointing
    # at version 2 (since our config says we are on version 1).
    manager.Install(['b'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=True)
    self.CheckPathsExist(paths2['a'], exists=False)
    self.CheckPathsExist(paths2['b'], exists=False)
    self.ClearErr()

    # Check that we get a good error when trying to update to a component that
    # doesn't exist at our current version.
    with self.assertRaisesRegex(
        update_manager.InvalidComponentError,
        r'The following components are unknown \[junk\]\. The following '
        r'components are not available for your current SDK version \[c\]\. '
        r'Please run `gcloud components update` to update your SDK\.'):
      manager.Install(['junk', 'c'])
    with self.assertRaisesRegex(
        update_manager.InvalidComponentError,
        r'The following components are not available for your current SDK '
        r'version \[c\]\. Please run `gcloud components update` to update your '
        r'SDK\.'):
      manager.Install(['c'])

    # Calling update with the same version should have no effect.
    manager.Update(['b'], version='1')
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=True)
    self.CheckPathsExist(paths2['a'], exists=False)
    self.CheckPathsExist(paths2['b'], exists=False)
    self.ClearErr()

    # Calling update without the version should trigger update to latest.
    manager.Update(['a', 'b'])
    self.CheckPathsExist(paths1['a'], exists=False)
    self.CheckPathsExist(paths1['b'], exists=False)
    self.CheckPathsExist(paths2['a'], exists=True)
    self.CheckPathsExist(paths2['b'], exists=True)
    self.ClearErr()

    self.assertEqual({'a': '2'}, manager.GetCurrentVersionsInformation())

  def testInstallWithAdditionalRepos(self):
    self.StartPatch('googlecloudsdk.core.config.INSTALLATION_CONFIG.version',
                    new='1')
    component_tuples = [('a', 1, []), ('b', 1, [])]
    snapshot, _ = self.CreateSnapshotFromComponentsGenerateTars(
        1, component_tuples, self.release_notes_file)
    url = self.URLFromFile(
        self.CreateTempSnapshotFileFromSnapshot(snapshot, versioned=True))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    update_mock = self.StartObjectPatch(manager, 'Update')

    # When there are no extra repos, allow the install to go through.
    manager.Install(['a'])
    update_mock.assert_called_once_with(
        ['a'], throw_if_unattended=False, allow_no_backup=False, version='1',
        restart_args=None)
    update_mock.reset_mock()

    # When there are extra repos, do a normal update instead of an install.
    properties.VALUES.component_manager.additional_repositories.Set('foo')
    manager.Install(['a'])
    self.AssertErrContains('Running `update` instead of `install`')
    update_mock.assert_called_once_with(
        ['a'], throw_if_unattended=False, allow_no_backup=False, version=None,
        restart_args=None)

  def testUninstall(self):
    install_state = local_state.InstallationState(self.sdk_root_path)

    # initial install
    # Use 'bundled-python' to test for warning message
    component_tuples = [
        ('a', 1, ['bundled-python']),
        ('bundled-python', 1, []),
        ('c', 1, [])]
    snapshot, paths1 = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    manager.Update(['a'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['bundled-python'], exists=True)
    self.CheckPathsExist(paths1['c'], exists=False)
    self.assertEqual(set(['a', 'bundled-python']),
                     set(install_state.InstalledComponents().keys()))
    manager.Update(['a', 'c'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['bundled-python'], exists=True)
    self.CheckPathsExist(paths1['c'], exists=True)
    self.assertEqual(set(['a', 'bundled-python', 'c']),
                     set(install_state.InstalledComponents().keys()))

    # uninstall
    self.restart_bundled_mock.reset_mock()
    self.postprocess_mock.reset_mock()
    manager.Remove(['c'])
    self.assertTrue(self.restart_bundled_mock.called)
    self.assertTrue(self.postprocess_mock.called)
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['bundled-python'], exists=True)
    self.CheckPathsExist(paths1['c'], exists=False)
    self.assertEqual(set(['a', 'bundled-python']),
                     set(install_state.InstalledComponents().keys()))
    self.restart_bundled_mock.reset_mock()
    manager.Remove(['bundled-python'])
    self.assertTrue(self.restart_bundled_mock.called)
    self.AssertErrContains('bundled installation of Python')
    self.CheckPathsExist(paths1['a'], exists=False)
    self.CheckPathsExist(paths1['bundled-python'], exists=False)
    self.CheckPathsExist(paths1['c'], exists=False)
    self.assertEqual([], list(install_state.InstalledComponents().keys()))

  def testUninstallPlatformSpecific(self):
    install_state = local_state.InstallationState(self.sdk_root_path)

    # Initial install, this simulates a platform specific wrapper script
    # component.
    component_tuples = [('a', 1, ['b']), ('b', 1, [])]
    snapshot, paths1 = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    self.ChangePlatformForComponents(
        snapshot, ['a'],
        platforms.Platform(platforms.OperatingSystem.WINDOWS, None))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    platf = platforms.Platform(platforms.OperatingSystem.WINDOWS, None)
    manager = update_manager.UpdateManager(self.sdk_root_path, url,
                                           platform_filter=platf)
    manager.Update(['a'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=True)
    self.assertEqual(set(['a', 'b']),
                     set(install_state.InstalledComponents().keys()))

    manager.Remove(['b'])
    self.CheckPathsExist(paths1['a'], exists=False)
    self.CheckPathsExist(paths1['b'], exists=False)
    self.assertEqual(set([]), set(install_state.InstalledComponents().keys()))

  def testTwoSnapshotUpdate(self):
    # empty
    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], list(install_state.InstalledComponents().keys()))
    self.assertEqual(None, install_state.BackupDirectory())

    # initial install
    component_tuples1 = [('a', 1, []), ('b', 1, [])]
    snapshot1, paths1 = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples1))
    url1 = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot1))

    component_tuples2 = [('b', 2, []), ('c', 2, [])]
    snapshot2, paths2 = (
        self.CreateSnapshotFromComponentsGenerateTars(2, component_tuples2))
    url2 = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot2))

    manager = update_manager.UpdateManager(self.sdk_root_path,
                                           ','.join([url1, url2]))
    manager.Update(['a', 'b', 'c'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=False)
    self.CheckPathsExist(paths2['b'], exists=True)
    self.CheckPathsExist(paths2['c'], exists=True)
    self.assertEqual(set(['a', 'b', 'c']),
                     set(install_state.InstalledComponents().keys()))

    # create updated snapshot
    component_tuples3 = [('b', 2, []), ('c', 3, [])]
    snapshot3, paths3 = (
        self.CreateSnapshotFromComponentsGenerateTars(2, component_tuples3))
    url3 = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot3))
    manager = update_manager.UpdateManager(self.sdk_root_path,
                                           ','.join([url1, url3]))
    manager.Update(['c'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=False)
    self.CheckPathsExist(paths2['b'], exists=True)
    self.CheckPathsExist(paths2['c'], exists=False)
    self.CheckPathsExist(paths3['c'], exists=True)
    self.assertEqual(set(['a', 'b', 'c']),
                     set(install_state.InstalledComponents().keys()))

  def testUpdateToFixedVersion_RemovedBundledPython(self):
    # empty
    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], list(install_state.InstalledComponents().keys()))
    self.assertEqual(None, install_state.BackupDirectory())

    component_tuples1 = [('bundled-python', 1, [])]
    snapshot1, paths1 = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples1))
    file1 = self.CreateTempSnapshotFileFromSnapshot(snapshot1)
    url1 = self.URLFromFile(file1)

    component_tuples2 = []
    snapshot2, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(2, component_tuples2))
    file2 = self.CreateTempSnapshotFileFromSnapshot(snapshot2)
    url2 = self.URLFromFile(file2)

    # Initial install, make sure snapshot 1 components are present.
    manager = update_manager.UpdateManager(self.sdk_root_path, url1)
    manager.Update(['bundled-python'])
    self.AssertErrNotContains('bundled installation of Python')
    self.CheckPathsExist(paths1['bundled-python'], exists=True)
    self.assertEqual(set(['bundled-python']),
                     set(install_state.InstalledComponents().keys()))

    # Update, make sure snapshot 2 components are present.
    manager = update_manager.UpdateManager(self.sdk_root_path, url2)
    manager.Update(['bundled-python'])
    self.AssertErrContains('bundled installation of Python')
    self.CheckPathsExist(paths1['bundled-python'], exists=False)
    self.assertEqual(set(),
                     set(install_state.InstalledComponents().keys()))

  def testUpdateToFixedVersion(self):
    # empty
    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], list(install_state.InstalledComponents().keys()))
    self.assertEqual(None, install_state.BackupDirectory())

    component_tuples1 = [('a', 1, []), ('b', 1, [])]
    snapshot1, paths1 = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples1))
    file1 = self.CreateTempSnapshotFileFromSnapshot(snapshot1)
    url1 = self.URLFromFile(file1)

    component_tuples2 = [('b', 2, []), ('c', 2, [])]
    snapshot2, paths2 = (
        self.CreateSnapshotFromComponentsGenerateTars(2, component_tuples2))
    file2 = self.CreateTempSnapshotFileFromSnapshot(snapshot2)
    url2 = self.URLFromFile(file2)

    # Initial install, make sure snapshot 1 components are present.
    manager = update_manager.UpdateManager(self.sdk_root_path, url1)
    manager.Update(['a', 'b'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=True)
    self.CheckPathsExist(paths2['b'], exists=False)
    self.CheckPathsExist(paths2['c'], exists=False)
    self.assertEqual(set(['a', 'b']),
                     set(install_state.InstalledComponents().keys()))

    # Update, make sure snapshot 2 components are present.
    manager = update_manager.UpdateManager(self.sdk_root_path, url2)
    manager.Update(['a', 'b', 'c'])
    self.CheckPathsExist(paths1['a'], exists=False)
    self.CheckPathsExist(paths1['b'], exists=False)
    self.CheckPathsExist(paths2['b'], exists=True)
    self.CheckPathsExist(paths2['c'], exists=True)
    self.assertEqual(set(['b', 'c']),
                     set(install_state.InstalledComponents().keys()))

    # Rename the 1st snapshot to match a fixed version format.
    new_file1 = os.path.join(
        os.path.dirname(file1),
        update_manager.UpdateManager.VERSIONED_SNAPSHOT_FORMAT.format('0.0.0'))
    os.rename(file1, new_file1)

    # Do a fixed version update to the original and make sure things get
    # down-graded.
    self.ClearErr()
    properties.VALUES.component_manager.fixed_sdk_version.Set('0.0.0')
    manager = update_manager.UpdateManager(self.sdk_root_path, url1)
    manager.List()
    self.AssertErrContains('Your current Cloud SDK version is: ' +
                           config.INSTALLATION_CONFIG.version)
    self.AssertErrNotContains('The latest available version is')
    manager.Update(['a', 'b', 'c'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=True)
    self.CheckPathsExist(paths2['b'], exists=False)
    self.CheckPathsExist(paths2['c'], exists=False)
    self.assertEqual(set(['a', 'b']),
                     set(install_state.InstalledComponents().keys()))

  def testRestoreBackup(self):
    # empty
    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], list(install_state.InstalledComponents().keys()))
    self.assertEqual(None, install_state.BackupDirectory())

    # initial install
    component_tuples = [('a', 1, []), ('b', 1, [])]
    snapshot, paths1 = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    manager.Update(['a'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=False)
    self.assertEqual(['a'], list(install_state.InstalledComponents().keys()))
    self.assertNotEqual(None, install_state.BackupDirectory())

    # install the second component
    manager.Update(['b'])
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=True)
    self.assertEqual(set(['a', 'b']),
                     set(install_state.InstalledComponents().keys()))
    self.assertNotEqual(None, install_state.BackupDirectory())

    self.restart_bundled_mock.reset_mock()
    self.postprocess_mock.reset_mock()
    # restore the backup
    manager.Restore()
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=False)
    self.assertEqual(['a'], list(install_state.InstalledComponents().keys()))
    # The backup installation directory doesn't have bundled-python installed,
    # and we've mocked out IsPythonBundled to return True, so this message will
    # print.
    self.AssertErrContains('bundled installation of Python')
    # no more backup after you restore a backup
    self.assertEqual(None, install_state.BackupDirectory())
    self.assertTrue(self.restart_bundled_mock.called)
    self.assertTrue(self.postprocess_mock.called)

  def testRemoveRequiredComponent(self):
    # empty
    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], list(install_state.InstalledComponents().keys()))

    # initial install
    component_tuples = [('a', 1, []), ('req_b', 1, [])]
    snapshot, paths = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    manager.Update(['a', 'req_b'])
    self.CheckPathsExist(paths['a'], exists=True)
    self.CheckPathsExist(paths['req_b'], exists=True)
    self.assertEqual(set(['a', 'req_b']),
                     set(install_state.InstalledComponents().keys()))

    # should be able to remove a since its not a required component
    manager.Remove(['a'])
    self.CheckPathsExist(paths['a'], exists=False)
    self.CheckPathsExist(paths['req_b'], exists=True)
    self.assertEqual(set(['req_b']),
                     set(install_state.InstalledComponents().keys()))

    # req_b should not get removed because it is a required component
    with self.assertRaisesRegex(update_manager.InvalidComponentError,
                                r'are required and cannot be removed'):
      manager.Remove(['req_b'])
    self.CheckPathsExist(paths['a'], exists=False)
    self.CheckPathsExist(paths['req_b'], exists=True)
    self.assertEqual(set(['req_b']),
                     set(install_state.InstalledComponents().keys()))

  def testHiddenComponent(self):
    # initial install
    component_tuples = [('componentA', 1, []), ('componentB', 1, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    snapshot.ComponentFromId('componentA').is_hidden = True
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    components, _, _ = manager.List()
    components = [c.id for c in components]
    self.assertNotIn('componentA', components)
    self.assertIn('componentB', components)

  def testReinstall(self):
    # empty
    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], list(install_state.InstalledComponents().keys()))
    self.assertEqual(None, install_state.BackupDirectory())

    # initial install
    component_tuples = [('a', 1, []), ('b', 1, [])]
    snapshot, paths1 = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    self.restart_bundled_mock.reset_mock()
    manager.Update(['a', 'b'])
    self.assertTrue(self.restart_bundled_mock.called)
    self.CheckPathsExist(paths1['a'], exists=True)
    self.CheckPathsExist(paths1['b'], exists=True)
    self.assertEqual({'a', 'b'},
                     set(install_state.InstalledComponents().keys()))
    self.assertNotEqual(None, install_state.BackupDirectory())

    properties_contents = """\
[core]
project = cloudsdktest
"""
    with open(os.path.join(install_state.sdk_root, 'properties'),
              'w') as prop_out:
      prop_out.write(properties_contents)

    tar_file = self.CreateTempTar(
        self.staging_path,
        ['root/bin/bootstrapping/install.py', 'root/newfile'],
        file_contents='contents')

    # increment schema version
    schema_version = config.INSTALLATION_CONFIG.snapshot_schema_version + 1
    snapshot.sdk_definition.schema_version = schemas.SchemaVersion(
        schema_version, False, 'UpdateMessage', self.URLFromFile(tar_file))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)

    # Reinstall shells out to the install script of the SDK.  Mock this because
    # when using FakeFS, the python executable is not available.
    popen_mock = self.StartObjectPatch(subprocess, 'Popen')
    popen_mock.return_value.wait.return_value = 0

    manager.Update(['a'])
    self.AssertErrContains('UpdateMessage')
    installer_path = os.path.realpath(os.path.join(
        install_state._InstallationState__sdk_staging_root,
        'bin', 'bootstrapping', 'install.py'))
    env = dict(os.environ)
    encoding.SetEncodedValue(env, 'CLOUDSDK_REINSTALL_COMPONENTS', 'a,b')
    # No assert_called_once_with! console_attr may call tput on some systems.
    popen_mock.assert_any_call([sys.executable, '-S', installer_path], env=env)

    self.CheckPathsExist(paths1['a'], exists=False)
    self.CheckPathsExist(paths1['b'], exists=False)
    self.AssertFileExistsWithContents(
        'contents', self.sdk_root_path,
        os.path.join('bin', 'bootstrapping', 'install.py'))
    self.AssertFileExistsWithContents(
        'contents', self.sdk_root_path, 'newfile')
    self.AssertFileExistsWithContents(properties_contents,
                                      self.sdk_root_path,
                                      'properties')
    self.assertNotEqual(None, install_state.BackupDirectory())

  def testForceReinstall(self):
    component_tuples = [('a', 1, []), ('b', 1, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))

    snapshot.sdk_definition.schema_version = schemas.SchemaVersion(
        config.INSTALLATION_CONFIG.snapshot_schema_version, False,
        'UpdateMessage', 'https://fake.com')

    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    manager.Update(['a', 'b'])

    install_mock = self.StartObjectPatch(manager, '_DoFreshInstall')
    manager.Reinstall()
    install_mock.assert_called_once_with('UpdateMessage', False,
                                         'https://fake.com')

  def testMappingErrorMessages(self):
    unavailable_components_mapping = {'test_unav': 'unavailable'}
    actual_components_mapping = {
        'cbt': 'google-cloud-sdk-cbt',
        'cloud-datastore-emulator': 'google-cloud-sdk-datastore-emulator'
    }

    components_mapping = actual_components_mapping.copy()
    components_mapping.update(unavailable_components_mapping)

    commands_mapping = {
        'install':
            'sudo apt-get install {package}',
        'update':
            'sudo apt-get install {package}',
        'remove':
            'sudo apt-get remove {package}',
        'update-all': ('sudo apt-get update && sudo apt-get --only-upgrade'
                       ' install {package}')
    }
    mapping_mock = self.StartObjectPatch(update_manager.UpdateManager,
                                         '_GetMappingFile')

    config.INSTALLATION_CONFIG.disable_updater = True

    snapshot, _ = self.CreateSnapshotFromComponentsGenerateTars(1, [])
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)

    update_all_message = manager._ComputeMappingMessage(
        command='update-all',
        components_map=components_mapping,
        commands_map=commands_mapping)

    for component in actual_components_mapping.values():
      self.assertRegexpMatches(update_all_message, component)

    # Test update-all command message.
    self.assertRegexpMatches(
        manager._ComputeMappingMessage(
            command='update-all',
            components_map=components_mapping,
            commands_map=commands_mapping),
        'update && sudo apt-get --only-upgrade install')

    # Test unavailable components message.
    self.assertRegexpMatches(
        manager._ComputeMappingMessage(
            command='install',
            components_map=components_mapping,
            commands_map=commands_mapping,
            components=['test_unav']),
        'test_unav component\(s\) is unavailable through')  # pylint: disable=anomalous-backslash-in-string

    # Test remove cbt.
    self.assertRegexpMatches(
        manager._ComputeMappingMessage(
            command='remove',
            components_map=components_mapping,
            commands_map=commands_mapping,
            components=['cbt']), 'get remove google-cloud-sdk-cbt')

    # Test install cbt.
    self.assertRegexpMatches(
        manager._ComputeMappingMessage(
            command='install',
            components_map=components_mapping,
            commands_map=commands_mapping,
            components=['cbt']), 'get install google-cloud-sdk-cbt')

    # Test install multiple components found in map.
    self.assertRegexpMatches(
        manager._ComputeMappingMessage(
            command='install',
            components_map=components_mapping,
            commands_map=commands_mapping,
            components=['cbt', 'cloud-datastore-emulator']),
        'install google-cloud-sdk-cbt google-cloud-sdk-dat')

    # Test install components not found in map.
    self.assertRegexpMatches(
        manager._ComputeMappingMessage(
            command='install',
            components_map=components_mapping,
            commands_map=commands_mapping,
            components=['fake_component', 'other_fake_component']),
        '"fake_component, other_fake_component" are not valid')

    # Test install one component found in map and one not found.
    self.assertRegexpMatches(
        manager._ComputeMappingMessage(
            command='install',
            components_map=components_mapping,
            commands_map=commands_mapping,
            components=['cbt', 'abc']), 'sdk-cbt\n\n"abc"')

    # Test default error message for restore.
    with self.assertRaisesRegex(update_manager.UpdaterDisabledError,
                                'consider using a separate installation'):
      mapping_mock.side_effect = [commands_mapping, components_mapping]
      manager.Restore()
    self.ClearErr()

    # Test non-default case throws error as well.
    with self.assertRaisesRegex(update_manager.UpdaterDisabledError,
                                'get install google-cloud-sdk-cbt'):
      mapping_mock.side_effect = [commands_mapping, components_mapping]
      manager.Update(['cbt'])
    self.ClearErr()

    config.INSTALLATION_CONFIG.disable_updater = False

  def testUpdatesAvailable(self):
    snapshot = self.CreateSnapshotFromComponents(
        20000101000001, [],
        None,
        notifications=[{
            'id': 'test',
            'condition': {
                'check_components': True
            }
        }])
    with update_check.UpdateCheckData() as checker:
      checker.SetFromSnapshot(snapshot, True)
      checker._SaveData()

    config.INSTALLATION_CONFIG.disable_updater = True
    properties.VALUES.component_manager.disable_update_check.Set(False)
    self.assertFalse(update_manager.UpdateManager.UpdatesAvailable())

    config.INSTALLATION_CONFIG.disable_updater = False
    properties.VALUES.component_manager.disable_update_check.Set(True)
    self.assertFalse(update_manager.UpdateManager.UpdatesAvailable())

    config.INSTALLATION_CONFIG.disable_updater = True
    properties.VALUES.component_manager.disable_update_check.Set(True)
    self.assertFalse(update_manager.UpdateManager.UpdatesAvailable())

    config.INSTALLATION_CONFIG.disable_updater = False
    properties.VALUES.component_manager.disable_update_check.Set(False)
    self.assertTrue(update_manager.UpdateManager.UpdatesAvailable())

  def testUpdateChecker(self):
    default_notifications = [{'id': 'default'}]
    component_tuples = [('a', 1, ['b']), ('b', 1, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(
            1, component_tuples, notifications=default_notifications))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)

    freq = update_check.UpdateCheckData.UPDATE_CHECK_FREQUENCY_IN_SECONDS
    half_freq = freq / 2

    t = self.StartObjectPatch(time, 'time', return_value=freq)
    # Has never checked for updates before
    self.assertEqual(
        freq, update_check.UpdateCheckData().SecondsSinceLastUpdateCheck())
    manager._PerformUpdateCheck(command_path='gcloud.foo')
    # Actually did the check and updated state
    self.assertEqual(
        0, update_check.UpdateCheckData().SecondsSinceLastUpdateCheck())

    t.return_value = freq + half_freq
    manager.Update(['a'])
    # Force updated the state after install
    self.assertEqual(
        0, update_check.UpdateCheckData().SecondsSinceLastUpdateCheck())
    self.assertFalse(update_check.UpdateCheckData().UpdatesAvailable())

    t.return_value = freq * 2
    manager._PerformUpdateCheck(command_path='gcloud.foo')
    # Did not actually do the update since time had not expired
    self.assertEqual(
        half_freq,
        update_check.UpdateCheckData().SecondsSinceLastUpdateCheck())
    manager._PerformUpdateCheck(command_path='gcloud.foo', force=True)
    # forced update
    self.assertEqual(
        0,
        update_check.UpdateCheckData().SecondsSinceLastUpdateCheck())

    component_tuples = [('a', 2, ['b']), ('b', 1, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(
            2, component_tuples, notifications=default_notifications))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)

    t.return_value = freq * 4
    manager._PerformUpdateCheck(command_path='gcloud.foo')
    # Time expired, update was done
    self.assertEqual(
        0,
        update_check.UpdateCheckData().SecondsSinceLastUpdateCheck())

    # We didn't explicitly do an update check, but the update cleared out the
    # previous updates.
    t.return_value = freq * 5
    manager.Update(['a'])
    self.assertFalse(update_check.UpdateCheckData().UpdatesAvailable())
    self.assertEqual(
        0,
        update_check.UpdateCheckData().SecondsSinceLastUpdateCheck())

    # Check that an incompatible schema is marked as available updates.
    schema_version = config.INSTALLATION_CONFIG.snapshot_schema_version + 1
    snapshot.sdk_definition.schema_version.version = schema_version
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    t.return_value = freq * 6
    manager._PerformUpdateCheck(command_path='gcloud.foo')
    self.assertEqual(
        0,
        update_check.UpdateCheckData().SecondsSinceLastUpdateCheck())

  def testNag(self):
    t = self.StartObjectPatch(time, 'time', return_value=0)
    default_notifications = [{'id': 'default'}]

    def SecondsSinceLastNag():
      return (
          time.time() -
          update_check.UpdateCheckData()._data.last_nag_times.get('default', 0))

    # Install a component.
    component_tuples = [('a', 1, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(
            1, component_tuples, notifications=default_notifications))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    manager.Update(['a'])

    # Component now has a new version.
    component_tuples = [('a', 2, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(
            2, component_tuples, notifications=default_notifications))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)

    base_time = update_check.UpdateCheckData.UPDATE_CHECK_FREQUENCY_IN_SECONDS
    freq = schemas.Trigger.DEFAULT_NAG_FREQUENCY

    # Updates available, but don't nag because stdout is not a tty.
    t.return_value = base_time + freq
    manager._PerformUpdateCheck(command_path='gcloud.foo')
    self.assertEqual(base_time + freq, SecondsSinceLastNag())
    self.AssertErrNotContains(
        'Updates are available for some Cloud SDK components')
    self.ClearErr()

    self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True

    # Updates available, do nag, update last nag time.
    t.return_value = base_time + freq
    manager._PerformUpdateCheck(command_path='gcloud.foo')
    self.assertEqual(0, SecondsSinceLastNag())
    self.AssertErrContains(
        'Updates are available for some Cloud SDK components')
    self.ClearErr()

    # Still updates but no nag, don't update last nag time.
    t.return_value = base_time + freq * 1.5
    manager._PerformUpdateCheck(command_path='gcloud.foo')
    self.assertEqual(freq / 2, SecondsSinceLastNag())
    self.AssertErrNotContains(
        'Updates are available for some Cloud SDK components')
    self.ClearErr()

    # Still updates but enough time has passed to re-nag.
    t.return_value = base_time + freq * 2
    manager._PerformUpdateCheck(command_path='gcloud.foo')
    self.assertEqual(0, SecondsSinceLastNag())
    self.AssertErrContains(
        'Updates are available for some Cloud SDK components')

  def testNagCommandFilter(self):
    t = self.StartObjectPatch(time, 'time', return_value=0)
    self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True
    default_notifications = [{'id': 'default',
                              'condition': {'check_components': False},
                              'trigger': {'command_regex': 'foo'}}]

    def SecondsSinceLastNag():
      return (
          time.time() -
          update_check.UpdateCheckData()._data.last_nag_times.get('default', 0))

    # Install a component.
    component_tuples = [('a', 1, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(
            1, component_tuples, notifications=default_notifications))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)

    base_time = update_check.UpdateCheckData.UPDATE_CHECK_FREQUENCY_IN_SECONDS
    freq = schemas.Trigger.DEFAULT_NAG_FREQUENCY

    # Updates available, but wrong command, don't nag.
    t.return_value = base_time + freq
    manager._PerformUpdateCheck(command_path='bar')
    self.assertEqual(base_time + freq, SecondsSinceLastNag())
    self.AssertErrNotContains(
        'Updates are available for some Cloud SDK components')
    self.ClearErr()

    # Updates available, correct command.
    manager._PerformUpdateCheck(command_path='foo')
    self.assertEqual(0, SecondsSinceLastNag())
    self.AssertErrContains(
        'Updates are available for some Cloud SDK components')
    self.ClearErr()

  def testBadURL(self):
    url = 'http://google.com/404'
    manager = update_manager.UpdateManager(
        sdk_root=self.sdk_root_path, url=url)
    with self.assertRaises(snapshots.URLFetchError):
      manager.List()

  def testBadDatasourceURLs(self):
    component_tuples = [('a', 2, [])]
    snapshot = self.CreateSnapshotFromComponentsGenerateTars(
        2, component_tuples)[0]
    snapshot.components['a'].data.source = 'http://google.com/404'
    path = self.CreateTempSnapshotFileFromSnapshot(snapshot)
    manager = update_manager.UpdateManager(
        sdk_root=self.sdk_root_path, url=self.URLFromFile(path))
    with self.assertRaises(installers.ComponentDownloadFailedError):
      manager.Update(['a'])

  def testPermissionsWhenRemoving(self):
    # initial install
    component_tuples = [('a', 1, [])]
    snapshot, unused_paths = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)
    manager.Update(['a'])

    # pin a file with bad permissions
    os.chmod(os.path.join(self.sdk_root_path, 'lib', 'a-1', 'file1.py'), 0)

    with self.assertRaises(local_state.PermissionsError):
      # uninstall
      manager.Remove(['a'])

  def testPermissionsWhenUpdating(self):
    # initial install
    component_tuples = [('a', 1, [])]
    snapshot, unused_paths = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))

    orig_has_write_access = files.HasWriteAccessInDir
    def HasWriteAccessInDir(path):
      return (os.path.realpath(path) != os.path.realpath(self.sdk_root_path)
              and orig_has_write_access(path))

    with mock.patch('googlecloudsdk.core.util.files.HasWriteAccessInDir',
                    side_effect=HasWriteAccessInDir):
      with self.assertRaises(exceptions.RequiresAdminRightsError):
        manager = update_manager.UpdateManager(self.sdk_root_path, url)
        manager.Update(['a'])

  def testToolsOnPath(self):
    # Create files that match commands in bin directory.
    temp_dir = self.CreateTempDir()
    path_dir = os.path.join(temp_dir, 'bin')
    self.Touch(path_dir, 'b-1.py', makedirs=True)
    self.Touch(path_dir, '.DS_Store')

    # Add duplicate command inside the SDK installation.
    platform_dir = os.path.join(self.sdk_root_path, 'platform')
    self.Touch(platform_dir, 'a-1.py', makedirs=True)

    component_tuples = [('a', 1, []), ('b', 1, [])]
    snapshot, _ = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)

    path = os.pathsep.join(
        (os.path.join(self.sdk_root_path,
                      update_manager.UpdateManager.BIN_DIR_NAME),
         path_dir,
         platform_dir
        ))
    self.assertEqual(set(), manager.FindAllOldToolsOnPath(path=path))
    self.assertEqual(set(), manager.FindAllDuplicateToolsOnPath(path=path))

    # Add a component that has an old version on the $PATH.
    manager.Update(['b'])
    self.assertEqual(
        set([os.path.realpath(os.path.join(path_dir, 'b-1.py'))]),
        manager.FindAllOldToolsOnPath(path=path))
    self.assertEqual(set(), manager.FindAllDuplicateToolsOnPath(path=path))

    # Add a component that has a duplicate version on the $PATH inside the SDK
    # installation.
    manager.Update(['a'])
    self.assertEqual(
        set([os.path.realpath(os.path.join(path_dir, 'b-1.py'))]),
        manager.FindAllOldToolsOnPath(path=path))
    self.assertEqual(
        set([os.path.realpath(os.path.join(platform_dir, 'a-1.py'))]),
        manager.FindAllDuplicateToolsOnPath(path=path))

  def testEnsureInstalled(self):
    self.StartPatch('googlecloudsdk.core.config.INSTALLATION_CONFIG.version',
                    new='1')

    component_tuples = [('a', 1, []), ('b', 1, [])]
    snapshot, paths = (
        self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
    url = self.URLFromFile(
        self.CreateTempSnapshotFileFromSnapshot(snapshot, versioned=True))
    manager = update_manager.UpdateManager(self.sdk_root_path, url)

    # Install 'a'
    manager.Update(['a'])
    self.CheckPathsExist(paths['a'], exists=True)
    self.CheckPathsExist(paths['b'], exists=False)

    # Does nothing because 'a' is installed already.
    restart_mock = self.StartObjectPatch(update_manager, 'RestartCommand')
    self.assertTrue(manager._EnsureInstalledAndRestart(['a'], msg='my message'))
    self.AssertOutputNotContains('my message')
    self.assertFalse(restart_mock.called)
    self.CheckPathsExist(paths['a'], exists=True)
    self.CheckPathsExist(paths['b'], exists=False)

    # Require 'b' but say no to installation prompt.
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('n\n')
    with self.assertRaisesRegex(update_manager.MissingRequiredComponentsError,
                                r'The following components are required'):
      manager._EnsureInstalledAndRestart(['b'], msg='my message')
    self.assertFalse(restart_mock.called)
    self.CheckPathsExist(paths['a'], exists=True)
    self.CheckPathsExist(paths['b'], exists=False)
    # Shouldn't check for bundled Python when _EnsureInstalledAndRestart is
    # directly invoked

    self.restart_bundled_mock.reset_mock()
    # Actually go through with it this time.
    properties.VALUES.core.disable_prompts.Set(True)
    self.assertEqual(None, manager._EnsureInstalledAndRestart(['b']))
    self.AssertErrContains('This action requires the installation')
    self.assertTrue(restart_mock.called)
    self.CheckPathsExist(paths['a'], exists=True)
    self.CheckPathsExist(paths['b'], exists=True)
    self.restart_bundled_mock.assert_called_once_with(
        args=['components', 'install', 'b'])

  def testEnsureInstalledWrapper(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value='asdf')
    func_mock = self.StartObjectPatch(update_manager.UpdateManager,
                                      '_EnsureInstalledAndRestart')
    properties.VALUES.component_manager.snapshot_url.Set('notused')
    update_manager.UpdateManager.EnsureInstalledAndRestart(['a'], msg='foo')
    func_mock.assert_called_once_with(['a'], 'foo', None)

  def testFastUpdateCwdInsideSdkRoot(self):
    manager = update_manager.UpdateManager(self.sdk_root_path, 'dummy url')
    cwd = os.path.join(self.sdk_root_path, 'inside_dir')
    self.StartPatch('os.getcwd').return_value = cwd

    with self.assertRaises(update_manager.InvalidCWDError):
      manager._ShouldDoFastUpdate(fast_mode_impossible=True)

  def testFastUpdateCwdWithSdkRootAsPrefix(self):
    manager = update_manager.UpdateManager(self.sdk_root_path, 'dummy url')
    cwd = self.sdk_root_path + '-suffix'
    self.StartPatch('os.getcwd').return_value = cwd

    try:
      manager._ShouldDoFastUpdate(fast_mode_impossible=True)
    except update_manager.InvalidCWDError:
      self.fail('Should not raise exception since CWD is outside sdk root')


class UpdateManagerPostProcessTests(util.Base, sdk_test_base.WithOutputCapture):

  def TearDown(self):
    self.JoinAllThreads()

  def testPostProcess(self):
    exec_mock = self.StartObjectPatch(execution_utils, 'Exec')
    exec_mock.return_value = 0

    # Success case.
    manager = update_manager.UpdateManager(
        self.sdk_root_path,
        'file://some/path/components.json')
    manager._PostProcess()
    exec_mock.assert_called_once_with(
        [execution_utils.GetPythonExecutable(),
         config.GcloudPath(),
         'components', 'post-process'],
        no_exit=True,
        out_func=log.file_only_logger.debug,
        err_func=log.file_only_logger.debug)
    self.AssertErrContains('Performing post processing steps')
    self.AssertErrNotContains('Post processing failed')

    # Non-zero exit code.
    exec_mock.reset_mock()
    exec_mock.return_value = 1
    self.ClearErr()

    manager._PostProcess()
    exec_mock.assert_called_once_with(
        [execution_utils.GetPythonExecutable(),
         config.GcloudPath(),
         'components', 'post-process'],
        no_exit=True,
        out_func=log.file_only_logger.debug,
        err_func=log.file_only_logger.debug)
    self.AssertErrContains('Performing post processing steps')
    self.AssertErrContains('Post processing failed')

  def testPostProcessMissingCommand(self):
    # The entire command does not exist.
    args_mock = self.StartObjectPatch(execution_utils, 'ArgsForPythonTool')
    args_mock.return_value = ['does not exist']
    manager = update_manager.UpdateManager(
        self.sdk_root_path,
        'file://some/path/components.json')
    manager._PostProcess()
    self.AssertErrContains('Performing post processing steps')
    self.AssertErrContains('Post processing failed')

  def testPostProcessWithSnapshot(self):
    exec_mock = self.StartObjectPatch(execution_utils, 'Exec')
    exec_mock.return_value = 0

    manager = update_manager.UpdateManager(
        self.sdk_root_path,
        'file://some/path/components.json')
    sdk_definition = schemas.SDKDefinition(
        revision=-1, schema_version=None, release_notes_url=None, version=None,
        gcloud_rel_path='blah.py', post_processing_command='foo bar baz',
        components=[], notifications={})
    snapshot = snapshots.ComponentSnapshot(sdk_definition)

    manager._PostProcess(snapshot=snapshot)
    exec_mock.assert_called_once_with(
        [execution_utils.GetPythonExecutable(),
         os.path.realpath(os.path.join(self.sdk_root_path, 'blah.py')),
         'foo', 'bar', 'baz'],
        no_exit=True,
        out_func=log.file_only_logger.debug,
        err_func=log.file_only_logger.debug)
    self.AssertErrContains('Performing post processing steps')
    self.AssertErrNotContains('Post processing failed')


class UpdateManagerRestartTests(util.Base,
                                sdk_test_base.WithOutputCapture):

  def testInstallComponentBundledPython(self):
    current_os_mock = self.StartObjectPatch(platforms.OperatingSystem,
                                            'Current')
    current_os_mock.return_value = platforms.OperatingSystem.WINDOWS
    self.StartObjectPatch(console_io, 'CanPrompt').return_value = True

    # This file/directory needs to exist, since that's where we're claiming the
    # current Python is located.
    python_path = os.path.join(self.sdk_root_path, 'python-dir', 'python')
    self.Touch(os.path.basename(python_path), python_path, makedirs=True)

    old_executable = sys.executable
    try:
      sys.executable = python_path
      component_tuples = [('a', 1, [])]
      snapshot, _ = (
          self.CreateSnapshotFromComponentsGenerateTars(1, component_tuples))
      url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
      manager = update_manager.UpdateManager(self.sdk_root_path, url)
      restart_mock = self.StartObjectPatch(update_manager, 'RestartCommand')
      copy_python_mock = self.StartObjectPatch(update_manager, 'CopyPython')
      copy_python_mock.return_value = '/tmp/python.exe'

      with self.assertRaisesRegex(SystemExit, '0'):
        manager.Update(['a'])
      self.assertTrue(copy_python_mock.called)
      self.assertTrue(restart_mock.called)
      self.assertEqual(restart_mock.call_args[1],
                       {'python': '/tmp/python.exe', 'block': False,
                        'command': None,
                        'args': None})
    finally:
      sys.executable = old_executable

  def testRestartIfUsingBundledPython_UsingBundledPython(self):
    current_os_mock = self.StartObjectPatch(platforms.OperatingSystem,
                                            'Current')
    current_os_mock.return_value = platforms.OperatingSystem.WINDOWS
    self.StartObjectPatch(console_io, 'CanPrompt').return_value = True

    # This file/directory needs to exist, since that's where we're claiming the
    # current Python is located.
    python_path = os.path.join(self.sdk_root_path, 'python-dir', 'python')
    self.Touch(os.path.basename(python_path), python_path, makedirs=True)

    restart_command_mock = self.StartObjectPatch(update_manager,
                                                 'RestartCommand')
    copy_python_mock = self.StartObjectPatch(update_manager, 'CopyPython')
    copy_python_mock.return_value = 'python.exe'

    old_executable = sys.executable
    try:
      sys.executable = python_path
      manager = update_manager.UpdateManager(self.sdk_root_path, 'dummy url')
      with self.assertRaisesRegex(SystemExit, '0'):
        manager._RestartIfUsingBundledPython(args=['args'])
    finally:
      sys.executable = old_executable
    restart_command_mock.assert_called_once_with(args=['args'],
                                                 python='python.exe',
                                                 command=None,
                                                 block=False)

  def testRestartIfUsingBundledPython_UsingBundledPythonNonInteractive(self):
    current_os_mock = self.StartObjectPatch(platforms.OperatingSystem,
                                            'Current')
    current_os_mock.return_value = platforms.OperatingSystem.WINDOWS
    self.StartObjectPatch(console_io, 'CanPrompt').return_value = False

    # This file/directory needs to exist, since that's where we're claiming the
    # current Python is located.
    python_path = os.path.join(self.sdk_root_path, 'python-dir', 'python')
    self.Touch(os.path.basename(python_path), python_path, makedirs=True)

    restart_command_mock = self.StartObjectPatch(update_manager,
                                                 'RestartCommand')
    copy_python_mock = self.StartObjectPatch(update_manager, 'CopyPython')
    copy_python_mock.return_value = 'python.exe'

    old_executable = sys.executable
    try:
      sys.executable = python_path
      manager = update_manager.UpdateManager(self.sdk_root_path, 'dummy url')
      with self.assertRaisesRegex(SystemExit, '1'):
        manager._RestartIfUsingBundledPython(args=['args'])
    finally:
      sys.executable = old_executable
    self.AssertErrContains('Cannot use bundled Python installation to update')
    self.AssertErrContains('non-interactive mode')
    self.AssertErrContains('FOR /F "delims="')
    self.AssertErrContains('copy-bundled-python')
    self.assertFalse(restart_command_mock.called)

  def testRestartIfUsingBundledPython_DifferentCommand(self):
    current_os_mock = self.StartObjectPatch(platforms.OperatingSystem,
                                            'Current')
    current_os_mock.return_value = platforms.OperatingSystem.WINDOWS
    self.StartObjectPatch(console_io, 'CanPrompt').return_value = True

    # This file/directory needs to exist, since that's where we're claiming the
    # current Python is located.
    python_path = os.path.join(self.sdk_root_path, 'python-dir', 'python')
    self.Touch(os.path.basename(python_path), python_path, makedirs=True)

    restart_command_mock = self.StartObjectPatch(update_manager,
                                                 'RestartCommand')
    copy_python_mock = self.StartObjectPatch(update_manager, 'CopyPython')
    copy_python_mock.return_value = 'python.exe'

    old_executable = sys.executable
    try:
      sys.executable = python_path
      manager = update_manager.UpdateManager(self.sdk_root_path, 'dummy url')
      with self.assertRaisesRegex(SystemExit, '0'):
        manager._RestartIfUsingBundledPython(args=['args'], command='foo.py')
    finally:
      sys.executable = old_executable
    restart_command_mock.assert_called_once_with(args=['args'],
                                                 python='python.exe',
                                                 command='foo.py',
                                                 block=False)

  def testRestartIfUsingBundledPython_NotUsingBundledPython(self):
    current_os_mock = self.StartObjectPatch(platforms.OperatingSystem,
                                            'Current')
    current_os_mock.return_value = platforms.OperatingSystem.WINDOWS

    # This is a platform-independent way to get the filesystem root.
    # We need our professed Python path to *not* be inside the SDK installation
    # directory (ex. in case we're running tests with bundled Python).
    filesystem_root = os.path.abspath(os.path.sep)
    python_path = os.path.join(filesystem_root, 'python.exe')

    restart_command_mock = self.StartObjectPatch(update_manager,
                                                 'RestartCommand')
    copy_python_mock = self.StartObjectPatch(update_manager, 'CopyPython')

    old_executable = sys.executable
    try:
      sys.executable = python_path
      manager = update_manager.UpdateManager(self.sdk_root_path, 'dummy url')
      manager._RestartIfUsingBundledPython('command')
    finally:
      sys.executable = old_executable
    self.assertFalse(copy_python_mock.called)
    self.assertFalse(restart_command_mock.called)

  def testRestartIfUsingBundledPython_NotUsingWindows(self):
    current_os_mock = self.StartObjectPatch(platforms.OperatingSystem,
                                            'Current')
    current_os_mock.return_value = platforms.OperatingSystem.LINUX

    # This file/directory needs to exist, since that's where we're claiming the
    # current Python is located.
    python_path = os.path.join(self.sdk_root_path, 'python-dir', 'python')
    self.Touch(os.path.basename(python_path), python_path, makedirs=True)

    restart_command_mock = self.StartObjectPatch(update_manager,
                                                 'RestartCommand')
    copy_python_mock = self.StartObjectPatch(update_manager, 'CopyPython')

    old_executable = sys.executable
    try:
      sys.executable = python_path
      manager = update_manager.UpdateManager(self.sdk_root_path, 'dummy url')
      manager._RestartIfUsingBundledPython('command')
    finally:
      sys.executable = old_executable
    self.assertFalse(copy_python_mock.called)
    self.assertFalse(restart_command_mock.called)


class HashRcFilesTest(util.Base):
  rcfiles = [
      'completion.bash.inc',
      'completion.zsh.inc',
      'path.bash.inc',
      'path.fish.inc',
      'path.zsh.inc',
      'gcfilesys.bash.inc'
  ]

  def SetUp(self):
    for name in self.rcfiles:
      if name == 'path.zsh.inc':
        continue
      self.Touch(self.temp_path, name, contents=name)

  def testHashRcFilesNoChange(self):
    manager = update_manager.UpdateManager(self.temp_path, url='notused')
    md5dict1 = manager._HashRcfiles(self.rcfiles)
    md5dict2 = manager._HashRcfiles(self.rcfiles)
    self.assertTrue(md5dict1 == md5dict2)

  def testHashRcFilesChange(self):
    manager = update_manager.UpdateManager(self.temp_path, url='notused')
    md5dict1 = manager._HashRcfiles(self.rcfiles)
    fname = os.path.join(self.temp_path, 'gcfilesys.bash.inc')
    with open(fname, 'a') as f:
      f.write('foobar\n')
    md5dict2 = manager._HashRcfiles(self.rcfiles)
    self.assertFalse(md5dict1 == md5dict2)


class ExecutionTests(sdk_test_base.SdkBase):

  DEFAULT_EXPECTED_ARGS = ['a', 'b c™', 'd']
  WINDOWS_CMD_PATTERN = (r'cmd\.exe /c "(?P<args>.*) & pause"')

  def SetUp(self):
    self.old_args = sys.argv
    sys.argv = ['gcloud', 'a', 'b c™', 'd']
    self.exec_mock = self.StartObjectPatch(execution_utils, 'Exec')
    self.current_os_mock = self.StartObjectPatch(platforms.OperatingSystem,
                                                 'Current')
    # for consistency
    self.current_os_mock.return_value = platforms.OperatingSystem.LINUX
    self.StartObjectPatch(encoding, '_GetEncoding', return_value='utf-8')
    self.old_executable = sys.executable
    sys.executable = 'current/python'

  def TearDown(self):
    sys.argv = self.old_args
    sys.executable = self.old_executable

  def _MakeSureArgsOk(self, args, python_path=None,
                      command='gcloud.py', expected_args=None):
    self.assertEqual(args[0], python_path or sys.executable)
    self.assertTrue(args[1].endswith(command))
    expected_args = expected_args or self.DEFAULT_EXPECTED_ARGS
    expected_args = [encoding.Encode(a) for a in expected_args]
    self.assertEqual(args[2:], expected_args)

  def testRestartCommand(self):
    update_manager.RestartCommand()

    self.assertEqual(self.exec_mock.call_count, 1)
    self._MakeSureArgsOk(self.exec_mock.call_args[0][0])

  def testRestartCommandSpecifyCommand(self):
    update_manager.RestartCommand('/path/to/other.py')
    self._MakeSureArgsOk(self.exec_mock.call_args[0][0],
                         command='/path/to/other.py')

  def testRestartCommandSpecifyCommandAndArgs(self):
    update_manager.RestartCommand('/path/to/other.py', args=['foo', 'bar'])
    self._MakeSureArgsOk(self.exec_mock.call_args[0][0],
                         command='/path/to/other.py',
                         expected_args=['foo', 'bar'])

  def testRestartCommandNonBlocking(self):
    # Store the current machine via a mock because in python3, os.popen shells
    # out to subprocess.Popen, so mocking Popen later will break
    # platform.machine().
    machine = platform.machine()
    self.StartObjectPatch(platform, 'machine', return_value=machine)

    popen_mock = self.StartObjectPatch(subprocess, 'Popen')

    update_manager.RestartCommand(block=False)

    self.assertEqual(popen_mock.call_count, 1)
    (args,), kwargs = popen_mock.call_args
    self._MakeSureArgsOk(args)
    self.assertEqual(kwargs['shell'], True)

  def testRestartCommandBlockingWindowsInteractive(self):
    self.current_os_mock.return_value = platforms.OperatingSystem.WINDOWS
    # Store the current machine via a mock because in python3, os.popen shells
    # out to subprocess.Popen, so mocking Popen later will break
    # platform.machine().
    machine = platform.machine()
    self.StartObjectPatch(platform, 'machine', return_value=machine)
    self.StartObjectPatch(console_io, 'CanPrompt', return_value=True)
    popen_mock = self.StartObjectPatch(subprocess, 'Popen')

    update_manager.RestartCommand(block=False)

    self.assertEqual(popen_mock.call_count, 1)
    (args,), kwargs = popen_mock.call_args
    match = re.match(self.WINDOWS_CMD_PATTERN, args)
    self.assertIsNotNone(match)
    # This is a string, rather than a list as in other cases
    args_group = match.group('args')
    # shlex only handles utf-8 encoding.
    self._MakeSureArgsOk(shlex.split(encoding.Encode(args_group, 'utf-8')))
    self.assertEqual(kwargs, {'shell': True,
                              'close_fds': True,
                              'creationflags': 0x208})

  def testRestartCommandBlockingWindowsNonInteractive(self):
    self.current_os_mock.return_value = platforms.OperatingSystem.WINDOWS
    # Store the current machine via a mock because in python3, os.popen shells
    # out to subprocess.Popen, so mocking Popen later will break
    # platform.machine().
    machine = platform.machine()
    self.StartObjectPatch(platform, 'machine', return_value=machine)
    self.StartObjectPatch(console_io, 'CanPrompt', return_value=False)
    popen_mock = self.StartObjectPatch(subprocess, 'Popen')

    update_manager.RestartCommand(block=False)

    self.assertEqual(popen_mock.call_count, 1)
    (args,), kwargs = popen_mock.call_args
    self.assertIs(type(args), list)
    self.assertNotIn('cmd.exe', args)  # we don't want to spawn a new window
    self._MakeSureArgsOk(args)
    self.assertEqual(kwargs, {'shell': True})

  def testRestartCommandOverridePython(self):
    update_manager.RestartCommand(python='/path/to/other/python')

    self.assertEqual(self.exec_mock.call_count, 1)
    args = self.exec_mock.call_args[0][0]
    self._MakeSureArgsOk(args, python_path='/path/to/other/python')


class CopyPythonTests(sdk_test_base.SdkBase):

  def SetUp(self):
    self.copytree_mock = self.StartPatch('shutil.copytree')
    self.temp_dir = files.TemporaryDirectory()
    self.StartObjectPatch(files,
                          'TemporaryDirectory').return_value = self.temp_dir
    self.old_executable = sys.executable
    sys.executable = os.path.join('C:', 'Python27', 'python.exe')

  def TearDown(self):
    sys.executable = self.old_executable

  def testCopyPython(self):
    new_python = update_manager.CopyPython()
    self.assertEqual(self.copytree_mock.call_count, 1)
    (src,
     dst), _ = self.copytree_mock.call_args  # pylint: disable=unpacking-non-sequence
    self.assertTrue(src.endswith('Python27'))
    self.assertEqual(os.path.join(self.temp_dir.path, 'python'), dst)
    self.assertTrue(new_python.startswith(dst))
    self.assertTrue(new_python.endswith('python.exe'))

if __name__ == '__main__':
  test_case.main()
