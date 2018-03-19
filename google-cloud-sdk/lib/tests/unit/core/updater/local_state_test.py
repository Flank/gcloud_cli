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

import os
import tempfile
import urllib
import urllib2

from googlecloudsdk.core import properties
from googlecloudsdk.core import url_opener
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.updater import installers
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.core.updater import util
import mock
from oauth2client import client as oauth2client


class LocalStateTestsFS(util.Base):

  def testLocalState(self):
    snapshot = self.CreateSnapshotFromStrings(1, 'a,b', '')

    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual({}, install_state.InstalledComponents())

    component_ids = snapshot.components.keys()
    for i in range(0, len(component_ids)):
      install_state.Install(snapshot, component_ids[i])
      self.assertEqual(i + 1, len(install_state.InstalledComponents()))
    self.assertEqual(component_ids, install_state.InstalledComponents().keys())

    for i in range(0, len(component_ids)):
      install_state.Uninstall(component_ids[i])
      self.assertEqual(len(component_ids) - i - 1,
                       len(install_state.InstalledComponents()))
    self.assertEqual([], install_state.InstalledComponents().keys())

  def testCloningReplaceRestore(self):
    snapshot = self.CreateSnapshotFromStrings(1, 'a,b', '')

    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual({}, install_state.InstalledComponents())

    install_state.Install(snapshot, 'a')
    install_state.Install(snapshot, 'b')
    self.assertEqual(set(['a', 'b']),
                     set(install_state.InstalledComponents().keys()))

    callback_mock = mock.MagicMock()
    other_state = install_state.CloneToStaging(progress_callback=callback_mock)
    self.assertNotEqual(install_state.sdk_root, other_state.sdk_root)
    self.assertEqual(set(['a', 'b']),
                     set(other_state.InstalledComponents().keys()))
    # 3 directory cleanups, root directory, .install, .download.
    self.assertEqual(6, callback_mock.call_count)

    other_state.Uninstall('b')
    self.assertEqual(set(['a']), set(other_state.InstalledComponents().keys()))
    install_state.ReplaceWith(other_state)

    self.assertEqual(set(['a']),
                     set(install_state.InstalledComponents().keys()))
    self.assertTrue(install_state.HasBackup())
    self.assertFalse(os.path.exists(other_state.sdk_root))

    install_state.RestoreBackup()
    self.assertEqual(set(['a', 'b']),
                     set(install_state.InstalledComponents().keys()))
    self.assertFalse(install_state.HasBackup())

  def testCreateStagingFromDownload(self):
    install_state = local_state.InstallationState(self.sdk_root_path)
    properties_contents = '[core]\nproject = cloudsdktest\n'
    with open(os.path.join(install_state.sdk_root, 'properties'),
              'w') as prop_out:
      prop_out.write(properties_contents)

    tar_file = self.CreateTempTar(
        self.staging_path,
        [os.path.join('root', 'bin', 'bootstrapping', 'install.py'),
         os.path.join('root', 'newfile')],
        file_contents='contents')
    callback_mock = mock.MagicMock()
    staging_stage = install_state.CreateStagingFromDownload(
        self.URLFromFile(tar_file), progress_callback=callback_mock)

    # Ensure that the new SDK was downloaded.
    self.AssertFileExistsWithContents('contents',
                                      staging_stage.sdk_root, 'newfile')
    # Ensure the properties file was copied correctly.
    self.AssertFileExistsWithContents(properties_contents,
                                      self.sdk_root_path,
                                      'properties')
    # Make sure the progress bar was updated and finished.
    self.assertGreater(callback_mock.call_count, 2)
    callback_mock.assert_called_with(1)

  def testInstallationManifest_NonExistentComponent(self):
    snapshot = self.CreateSnapshotFromStrings(
        revision=1, component_string='a,b', dependency_string='')
    install_manifest = local_state.InstallationManifest(
        state_dir=self.sdk_root_path, component_id='non-existent-component')
    with self.assertRaises(ValueError):
      install_manifest.MarkInstalled(snapshot, files=[])

  def testInstallationManifest_NormalizedFiles(self):
    snapshot = self.CreateSnapshotFromStrings(
        revision=1, component_string='a,b', dependency_string='')
    install_manifest = local_state.InstallationManifest(
        state_dir=self.sdk_root_path, component_id='a')
    file_list = ['z/', 'z/a/b', 'x/', 'x/2', 'x/1', 'y//']
    install_manifest.MarkInstalled(snapshot, files=file_list)
    with open(install_manifest.manifest_file) as f:
      manifest_files = f.read().strip().split('\n')
    self.assertEqual(['x/1', 'x/2', 'y/', 'z/a/b'], manifest_files)
    self.assertEqual({'x', 'z', 'z/a', 'y'},
                     install_manifest.InstalledDirectories())


class LocalStateTests(util.Base, test_case.WithOutputCapture):

  def testCompilePython(self):
    self.SetEncoding('utf8')
    py_file_contents = 'a = 1 + 1'
    to_compile = [
        os.path.join('bin', 'bootstrapping', 'foo.py'),
        os.path.join('bin', 'bootstrapping', 'bar', 'foo.py'),
        os.path.join('lib', 'foo.py'),
        os.path.join('lib', 'bar', 'foo.py'),
        os.path.join('platform', 'foo.py'),
        os.path.join('platform', 'bar', 'foo.py'),
    ]
    no_compile = [
        # Not python.
        'a',
        # Don't compile things in the root.
        'b.py',
        # Don't compile things directly in bin.
        os.path.join('bin', 'c.py'),
        # Some other random directory.
        os.path.join('notincluded', 'd.py'),
        # This file will have invalid contents.
        'junk.py'
    ]
    for f in to_compile:
      self.Touch(self.sdk_root_path, f, py_file_contents, makedirs=True)
    for f in no_compile:
      self.Touch(self.sdk_root_path, f, py_file_contents, makedirs=True)
    self.Touch(self.sdk_root_path, 'junk.py', ':')
    self.SetEncoding('ascii')

    install_state = local_state.InstallationState(self.sdk_root_path)
    install_state.CompilePythonFiles()

    for f in to_compile:
      self.AssertFileExists(os.path.join(self.sdk_root_path, f) + 'c')
    for f in no_compile:
      if f.endswith('.py'):
        self.AssertFileNotExists(os.path.join(self.sdk_root_path, f) + 'c')
      else:
        self.AssertFileNotExists(os.path.join(self.sdk_root_path, f) + '.pyc')

    # Ensure this doesn't crash when one of the directories is missing
    files.RmTree(os.path.join(self.sdk_root_path, 'platform'))
    install_state.CompilePythonFiles()


class InstallerTests(util.Base):

  def testSimpleTarInstall(self):
    component_tuples = [('a', 1, [])]
    snapshot, paths = (self.CreateSnapshotFromComponentsGenerateTars(
        1, component_tuples))

    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], install_state.InstalledComponents().keys())

    callback_mock = mock.MagicMock()
    install_state.Install(snapshot, 'a', progress_callback=callback_mock)
    self.CheckPathsExist(paths['a'], exists=True)
    self.assertEqual(['a'], install_state.InstalledComponents().keys())
    # 5 files, 5 directories, 2 'dones', 1 download block.
    self.assertEqual(13, callback_mock.call_count)

    callback_mock.reset_mock()
    install_state.CloneToStaging(progress_callback=callback_mock)
    # 3 directory cleanups, 5 directories, root dir, .install, and .backup.
    self.assertEqual(11, callback_mock.call_count)

    callback_mock.reset_mock()
    install_state.Uninstall('a', progress_callback=callback_mock)
    self.CheckPathsExist(paths['a'], exists=False)
    self.assertEqual([], install_state.InstalledComponents().keys())
    # 5 files, 0 empty directories.
    self.assertEqual(5, callback_mock.call_count)

  def SetupSymlinkTest(self):
    tar_dir = tempfile.mkdtemp(dir=self.staging_path)
    target = os.path.join(tar_dir, 'realdir/realfile')
    self.Touch(tar_dir, 'realdir/realfile', contents='file', makedirs=True)

    link = os.path.join(tar_dir, 'realdir/linkfile')
    rel_path = os.path.relpath(target, os.path.dirname(link))
    os.symlink(rel_path, link)

    link = os.path.join(tar_dir, 'realdir/zlinkfile')
    rel_path = os.path.relpath(target, os.path.dirname(link))
    os.symlink(rel_path, link)

    target = os.path.join(tar_dir, 'realdir')
    # Name must be longer than realdir so it removed first.
    link = os.path.join(tar_dir, 'somelinkdir')
    rel_path = os.path.relpath(target, os.path.dirname(link))
    os.symlink(rel_path, link)

    tar_file = self.CreateTempTarFromDir(self.staging_path, tar_dir)

    new_tuples = [('a', '1', [],
                   self.URLFromFile(urllib.pathname2url(tar_file)))]
    snapshot = self.CreateSnapshotFromComponents('1', new_tuples)
    return snapshot

  @test_case.Filters.DoNotRunOnWindows
  def testSymlinkUninstallLeaveBehind(self):
    """Tests that all symlinks are removed correctly.

    This test is based off bug: b/13584849.  It is dependent on the order that
    links are attempted to be removed.  This test tests that case where files
    are left behind because their targets are removed first.
    """
    snapshot = self.SetupSymlinkTest()

    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], install_state.InstalledComponents().keys())
    install_state.Install(snapshot, 'a')

    # This is how we remove the target before the link.
    installed_files = ['somelinkdir', 'realdir/', 'realdir/linkfile',
                       'realdir/realfile', 'realdir/zlinkfile']
    self.StartObjectPatch(local_state.InstallationManifest,
                          'InstalledPaths', return_value=installed_files)
    install_state.Uninstall('a')
    self.CheckPathsExist(['realdir', 'somelinkdir'], exists=False)

  @test_case.Filters.DoNotRunOnWindows
  def testSymlinkUninstallSymlinkDir(self):
    """Tests that symlink directories can be removed correctly.

    This test is based off bug: b/13584849.  It is dependent on the order that
    links are attempted to be removed.  This test tests that if all the
    underlying links are actually cleaned up correctly, that a top level
    directory link is also cleaned up correctly.
    """
    snapshot = self.SetupSymlinkTest()

    install_state = local_state.InstallationState(self.sdk_root_path)
    self.assertEqual([], install_state.InstalledComponents().keys())
    install_state.Install(snapshot, 'a')

    # Remove the targets first, allows links to be cleaned up.
    installed_files = ['somelinkdir', 'realdir/', 'realdir/linkfile',
                       'realdir/zlinkfile', 'realdir/realfile']
    self.StartObjectPatch(local_state.InstallationManifest,
                          'InstalledPaths', return_value=installed_files)
    install_state.Uninstall('a')
    self.CheckPathsExist(['realdir', 'somelinkdir'], exists=False)

  def testACLTarInstall(self):
    component_tuples = [('a', 1, [])]
    snapshot, _ = (self.CreateSnapshotFromComponentsGenerateTars(
        1, component_tuples))
    # Point the location to something that looks like GCS
    fake_url = (installers.ComponentInstaller.GCS_BROWSER_DL_URL +
                'some/file.tar.gz')
    snapshot.ComponentFromId('a').data.source = fake_url

    # Always raise a 403 error when accessing
    fake_error = urllib2.HTTPError(fake_url, code=403, msg='Forbidden', hdrs={},
                                   fp=None)
    # pylint: disable=unused-argument

    def RaiseError(*_, **__):
      raise fake_error
    self.StartObjectPatch(url_opener,
                          'urlopen',
                          side_effect=RaiseError)

    install_state = local_state.InstallationState(self.sdk_root_path)

    # You must have an account set to get credentials.
    with self.assertRaisesRegexp(
        installers.ComponentDownloadFailedError,
        'You do not currently have an active account selected.'):
      install_state.Install(snapshot, 'a')

    # Load up some bogus credentials.
    self.StartObjectPatch(
        store, 'Load', return_value=oauth2client.OAuth2Credentials(
            'accesstoken', None, None, None, None, None, None))
    self.StartObjectPatch(oauth2client.OAuth2Credentials, 'refresh',
                          return_value=None)
    properties.VALUES.core.account.Set('someaccount')
    # You must have valid credentials.
    with self.assertRaisesRegexp(
        installers.ComponentDownloadFailedError,
        r'\[someaccount\] does not have permission to install this component.'):
      install_state.Install(snapshot, 'a')


if __name__ == '__main__':
  test_case.main()
