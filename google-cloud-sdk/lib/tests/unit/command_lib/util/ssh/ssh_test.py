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

"""Tests for googlecloudsdk.command_lib.ssh."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import retry
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock
import six


class EnvironmentTest(test_case.TestCase):
  """Tests that SSH binaries are picked up correctly."""

  def _assertEndswith(self, message, ending):
    """Assert that message ends with a certain ending."""
    self.assertTrue(message.endswith(ending),
                    msg='[{0}] should end with [{1}]'
                    .format(message, ending))

  @test_case.Filters.DoNotRunOnWindows('Commands on Mac and Linux')
  def testNixCommandSet(self):
    env = ssh.Environment.Current()
    self._assertEndswith(env.ssh, '/ssh')
    self._assertEndswith(env.ssh_term, '/ssh')
    self._assertEndswith(env.scp, '/scp')
    self._assertEndswith(env.keygen, '/ssh-keygen')

  @test_case.Filters.RunOnlyOnWindows('Commands on Windows')
  def testWindowsCommandSet(self):
    env = ssh.Environment.Current()
    self._assertEndswith(env.ssh, r'\bin\sdk\plink.exe')
    self._assertEndswith(env.ssh_term, r'\bin\sdk\putty.exe')
    self._assertEndswith(env.scp, r'\bin\sdk\pscp.exe')
    self._assertEndswith(env.keygen, r'\bin\sdk\winkeygen.exe')

  def testRequireSSH(self):
    self.StartObjectPatch(files, 'FindExecutableOnPath', return_value='/path')
    env = ssh.Environment(ssh.Suite.PUTTY, '/nowhere')
    env.RequireSSH()  # Doesn't error out

  def testRequireSSH_MissingCommand(self):
    self.StartObjectPatch(
        files, 'FindExecutableOnPath',
        side_effect=lambda cmd, path: None if cmd == 'winkeygen' else cmd)
    env = ssh.Environment(ssh.Suite.PUTTY, '/nowhere')
    with self.assertRaises(ssh.MissingCommandError):
      env.RequireSSH()


class KeysTest(sdk_test_base.WithTempCWD,
               sdk_test_base.WithOutputCapture,
               test_case.WithInput):

  def SetUp(self):
    self.key_file = 'key_file'  # Name of key file

  def _EnsureKeysExist(self, overwrite=None):
    keys = ssh.Keys(self.key_file)
    keys.EnsureKeysExist(overwrite)
    return keys

  def _ExpectGenKey(self):
    def KeygenRunCallback(keygen_command, unused_env=None):
      self.assertTrue(keygen_command.allow_passphrase)
      self._CreateFile(keygen_command.identity_file + '.pub',
                       'ssh-rsa KEY_VALUE COMMENT')
    self.StartObjectPatch(ssh.KeygenCommand, 'Run', KeygenRunCallback)

  def _CreateFile(self, name, content):
    with open(name, 'w') as f:
      f.write(content)

  def testAbsentKeys(self):
    self._ExpectGenKey()
    self._EnsureKeysExist()
    self.AssertErrContains('You do not have an SSH key for gcloud')

  def testPresentKeys(self):
    private_key = self.key_file
    public_key = private_key + '.pub'
    ppk_key = private_key + '.ppk'
    self._CreateFile(private_key, 'private key')
    self._CreateFile(public_key, 'ssh-rsa KEY_VALUE')
    self._CreateFile(ppk_key, 'PuTTY file')  # if test is run on windows
    keys = self._EnsureKeysExist()
    self.assertEqual(keys.GetPublicKey().ToEntry(), 'ssh-rsa KEY_VALUE')

  def testMissingPrivateKey_Abort(self):
    private_key = self.key_file
    public_key = private_key+'.pub'
    ppk_key = private_key + '.ppk'
    # no private key
    self._CreateFile(public_key, 'public key')
    self._CreateFile(ppk_key, 'PuTTY file')  # if test is run on windows
    self.WriteInput('n')
    with self.assertRaises(console_io.OperationCancelledError):
      self._EnsureKeysExist()
    self.AssertErrMatches('private.*NOT FOUND')
    self.AssertErrMatches('public.*'+public_key)
    self.AssertErrContains('We are going to overwrite all above files')

  def testMissingPublicKey_Continue(self):
    private_key = self.key_file
    ppk_key = private_key + '.ppk'
    self._CreateFile(private_key, 'private key')
    # no public key
    self._CreateFile(ppk_key, 'PuTTY file')  # if test is run on windows
    self._ExpectGenKey()
    self.WriteInput('y')
    keys = self._EnsureKeysExist()
    self.assertEqual(keys.GetPublicKey().ToEntry(True),
                     'ssh-rsa KEY_VALUE COMMENT')
    self.AssertErrMatches('public.*NOT FOUND')
    self.AssertErrMatches('private.*'+private_key)
    self.AssertErrContains('We are going to overwrite all above files')

  def testMissingPublicKey_DontContinueWithDefault(self):
    """Ensures that pressing enter equals no."""
    private_key = self.key_file
    ppk_key = private_key + '.ppk'
    self._CreateFile(private_key, 'private key')
    # no public key
    self._CreateFile(ppk_key, 'PuTTY file')  # if test is run on windows
    self.WriteInput('')  # No
    with self.assertRaises(console_io.OperationCancelledError):
      self._EnsureKeysExist()
    self.AssertErrMatches('public.*NOT FOUND')
    self.AssertErrMatches('private.*'+private_key)
    self.AssertErrContains('We are going to overwrite all above files')

  def testMissingPublicKey_NonInteractive(self):
    self.StartObjectPatch(console_io, 'IsInteractive', return_value=False)
    private_key = self.key_file
    ppk_key = private_key + '.ppk'
    self._CreateFile(private_key, 'private key')
    # no public key
    self._CreateFile(ppk_key, 'PuTTY file')  # if test is run on windows
    # no write input, action as if 'n' was provided
    with self.assertRaises(console_io.OperationCancelledError):
      self._EnsureKeysExist()
    self.AssertErrMatches('public.*NOT FOUND')
    self.AssertErrMatches('private.*'+private_key)
    self.AssertErrContains('We are going to overwrite all above files')

  def testMissingPublicKey_PromptsDisabled(self):
    # TODO(b/34511192): If prompting is simplified, only one non-interactive
    # test should be required.
    self.StartObjectPatch(
        properties.VALUES.core.disable_prompts, 'GetBool', return_value=True)
    private_key = self.key_file
    ppk_key = private_key + '.ppk'
    self._CreateFile(private_key, 'private key')
    # no public key
    self._CreateFile(ppk_key, 'PuTTY file')  # if test is run on windows
    # no write input, action as if 'n' was provided
    with self.assertRaises(console_io.OperationCancelledError):
      self._EnsureKeysExist()
    self.AssertErrMatches('public.*NOT FOUND')
    self.AssertErrMatches('private.*'+private_key)
    self.AssertErrContains('We are going to overwrite all above files')

  def testBrokenPublicKey_ForceOverwrite(self):
    private_key = self.key_file
    public_key = private_key+'.pub'
    ppk_key = private_key + '.ppk'
    self._CreateFile(private_key, 'private key')
    self._CreateFile(public_key, 'BROKENCONTENT')
    self._CreateFile(ppk_key, 'PuTTY file')  # if test is run on windows
    self._ExpectGenKey()
    keys = self._EnsureKeysExist(overwrite=True)
    # no write input, flag is present
    self.assertEqual(keys.GetPublicKey().ToEntry(True),
                     'ssh-rsa KEY_VALUE COMMENT')
    self.AssertErrMatches('public.*BROKEN')
    self.AssertErrMatches('private.*'+private_key)
    self.AssertErrContains('We are going to overwrite all above files')
    # check if deprecation warning is not present

  def testMissingPublicKey_NoForceOverwrite(self):
    private_key = self.key_file
    ppk_key = private_key + '.ppk'
    self._CreateFile(private_key, 'private key')
    # no public key
    self._CreateFile(ppk_key, 'PuTTY file')  # if test is run on windows
    self._ExpectGenKey()
    # no write input, flag is present
    with self.assertRaisesRegex(
        console_io.OperationCancelledError,
        '(?s)private.*{}.*public.*?NOT FOUND'.format(private_key)):
      self._EnsureKeysExist(overwrite=False)

  def testMissingPublicKey_ForceOverwrite_FileDisappeared(self):
    # TODO(b/33467618): Is this test really necessary?
    private_key = self.key_file
    ppk_key = private_key + '.ppk'
    self._CreateFile(private_key, 'private key')
    # no public key
    self._CreateFile(ppk_key, 'PuTTY file')  # if test is run on windows
    self._ExpectGenKey()
    keys = self._EnsureKeysExist(overwrite=True)
    # file will disappear just before RemoveKeyFilesIfPermittedOrFail
    function = ssh.Keys.RemoveKeyFilesIfPermittedOrFail
    def NewFunction(*args):
      os.remove(private_key)
      function(*args)  # forward
    self.StartObjectPatch(ssh.Keys,
                          'RemoveKeyFilesIfPermittedOrFail',
                          NewFunction)
    # no write input, flag is present
    self.assertEqual(keys.GetPublicKey().ToEntry(True),
                     'ssh-rsa KEY_VALUE COMMENT')
    self.AssertErrMatches('public.*NOT FOUND')
    self.AssertErrMatches('private.*'+private_key)
    self.AssertErrContains('We are going to overwrite all above files')

  def testInvalidPublicKey(self):
    """Public key broken, EnsureKeysExist hasn't been called."""
    public_key = self.key_file + '.pub'
    self._CreateFile(public_key, 'BROKENCONTENT')
    keys = ssh.Keys(self.key_file)
    with self.assertRaisesRegex(
        ssh.InvalidKeyError, r'Public key \[BROKENCONTENT\] is invalid\.'):
      keys.GetPublicKey()

  def testPublicKeyToEntry(self):
    key = ssh.Keys.PublicKey('ssh-rsa', 'KEY_VALUE')
    self.assertEqual(key.ToEntry(), 'ssh-rsa KEY_VALUE')
    self.assertEqual(key.ToEntry(True), 'ssh-rsa KEY_VALUE')

  def testPublicKeyWithCommentToEntry(self):
    key = ssh.Keys.PublicKey('ssh-rsa', 'KEY_VALUE', comment='COMMENT')
    self.assertEqual(key.ToEntry(), 'ssh-rsa KEY_VALUE')
    self.assertEqual(key.ToEntry(True), 'ssh-rsa KEY_VALUE COMMENT')

  def testPublicKeyFromKeystring(self):
    key_string = 'ssh-rsa KEY_VALUE'
    key = ssh.Keys.PublicKey.FromKeyString(key_string)
    self.assertEqual(key.key_type, 'ssh-rsa')
    self.assertEqual(key.key_data, 'KEY_VALUE')
    self.assertEqual(key.comment, '')

  def testPublicKeyWithCommentFromKeystring(self):
    key_string = 'ssh-rsa KEY_VALUE   hi from me@myhost '
    key = ssh.Keys.PublicKey.FromKeyString(key_string)
    self.assertEqual(key.key_type, 'ssh-rsa')
    self.assertEqual(key.key_data, 'KEY_VALUE')
    self.assertEqual(key.comment, 'hi from me@myhost')

  def testInvalidPublicKeyString(self):
    """Very simple validation -- just use fewer than two components."""
    key_string = 'BROKENCONTENT'
    with self.assertRaisesRegex(
        ssh.InvalidKeyError, r'Public key \[BROKENCONTENT\] is invalid\.'):
      ssh.Keys.PublicKey.FromKeyString(key_string)


class RemoteTest(test_case.TestCase):
  """Tests for ssh.Remote class."""

  def testFromArg(self):
    """Check that remotes are correctly instantiated from string args."""
    remote = ssh.Remote.FromArg('h')  # Single letter host
    self.assertEqual(remote.host, 'h')
    self.assertEqual(remote.user, None)

    remote = ssh.Remote.FromArg('host')
    self.assertEqual(remote.host, 'host')
    self.assertEqual(remote.user, None)

    remote = ssh.Remote.FromArg('sub.host')
    self.assertEqual(remote.host, 'sub.host')
    self.assertEqual(remote.user, None)

    remote = ssh.Remote.FromArg('user@host')
    self.assertEqual(remote.host, 'host')
    self.assertEqual(remote.user, 'user')

    remote = ssh.Remote.FromArg('user/name@sub.host')  # Valid
    self.assertEqual(remote.host, 'sub.host')
    self.assertEqual(remote.user, 'user/name')

  def testFromMalformedArg(self):
    """Check that these are not valid remote args."""
    self.assertEqual(ssh.Remote.FromArg(''), None)
    self.assertEqual(ssh.Remote.FromArg('.host'), None)
    self.assertEqual(ssh.Remote.FromArg('user/name'), None)
    self.assertEqual(ssh.Remote.FromArg('user@@host'), None)
    self.assertEqual(ssh.Remote.FromArg('us:er@host'), None)
    self.assertEqual(ssh.Remote.FromArg('user@ho:st'), None)
    self.assertEqual(ssh.Remote.FromArg('user@ho/st'), None)
    self.assertEqual(ssh.Remote.FromArg(r'user@ho\st'), None)

  def testToArg(self):
    """Check that remotes are exported to strings correctly."""
    self.assertEqual(ssh.Remote('host').ToArg(), 'host')
    self.assertEqual(ssh.Remote('host', user='user').ToArg(), 'user@host')

  def testEquality(self):
    """Check that the equality operator works."""
    # With user
    self.assertEqual(ssh.Remote('host', user='me'),
                     ssh.Remote('host', user='me'))
    self.assertNotEqual(ssh.Remote('host', user='user'),
                        ssh.Remote('host', user='user2'))
    # Without user
    self.assertEqual(ssh.Remote('host'),
                     ssh.Remote('host'))
    self.assertNotEqual(ssh.Remote('host'),
                        ssh.Remote('host2'))

  def testSets(self):
    """Put remotes in sets and perform set operations."""
    # Two sets, where the first has a duplicate (de-duped by set)
    s1 = {ssh.Remote('host', user='me'), ssh.Remote('host'), ssh.Remote('host')}
    s2 = {ssh.Remote('host', user='me'), ssh.Remote('host')}
    self.assertEqual(s1, s2)
    self.assertEqual(len(s1), 2)

    # Add other remote (making them unequal)
    s1.add(ssh.Remote('newhost', user='other_me'))
    self.assertNotEqual(s1, s2)

    # Take the diff, should contain new remote only
    diff = s1 - s2
    self.assertEqual(diff, {ssh.Remote('newhost', user='other_me')})


class CommandTestBase(test_case.TestCase):
  """Utilities for other command tests."""

  def SetUp(self):

    # A typical Unix environment
    self.openssh = ssh.Environment(ssh.Suite.OPENSSH)
    self.openssh.ssh = 'ssh'
    self.openssh.ssh_term = 'ssh'
    self.openssh.scp = 'scp'
    self.openssh.keygen = 'ssh-keygen'

    # A typical Windows environment
    self.putty = ssh.Environment(ssh.Suite.PUTTY)
    self.putty.ssh = 'plink'
    self.putty.ssh_term = 'putty'
    self.putty.scp = 'pscp'
    self.putty.keygen = 'winkeygen'

    # A couple of Remote instances
    self.remote = ssh.Remote('myhost')
    self.remote_user = ssh.Remote('myhost', user='me')

    # A few FileReference instances
    self.ref_remote_1 = ssh.FileReference('remote_1', self.remote)
    self.ref_remote_2 = ssh.FileReference('remote_2', self.remote_user)
    self.ref_remote_2_2 = ssh.FileReference('remote_2/other', self.remote_user)
    self.ref_local_1 = ssh.FileReference('local_1')
    self.ref_local_2 = ssh.FileReference('local_2')

    self.remote = ssh.Remote('myhost')

  def SplitIfString(self, arg):
    """If `arg` is a string, split it into an array.

    Args:
      arg: str, [str] or None

    Returns:
      - If arg is None: return None
      - If arg is str, return [str]
      - If arg is [str]: return [str]
    """
    if isinstance(arg, six.string_types):
      return arg.split()
    else:
      return arg

  def AssertCommandBuild(self, command, expected_openssh, expected_putty):
    """Check that command results in the expected invocations for each env.

    Args:
      command: ssh.SSHCommand or ssh.SCPCommand, Command to build.
      expected_openssh: str, [str] or None; The expected command. Cases:
          - str is split on whitespace into [str]
          - [str] is compared element-by-element against the actual command
            array. Useful if an arg contains a string.
          - None means N/A for this suite. Useful if only one of the suites are
            applicable to the test.
      expected_putty: str, [str] or None: See `expected_openssh`.
    """
    if expected_openssh:
      expected = self.SplitIfString(expected_openssh)
      self.assertEqual(expected, command.Build(self.openssh))
    if expected_putty:
      expected = self.SplitIfString(expected_putty)
      self.assertEqual(expected, command.Build(self.putty))


class KeygenCommandBuildTest(CommandTestBase):
  """Checks that keygen commands are constructed appropriately."""

  def SetUp(self):
    self.can_prompt = self.StartObjectPatch(console_io, 'CanPrompt',
                                            return_value=False)

  def testNonInteractive(self):
    """Test building non-interactive."""
    self.AssertCommandBuild(
        ssh.KeygenCommand('/key/file'),
        ['ssh-keygen', '-N', '', '-t', 'rsa', '-f', '/key/file'],
        'winkeygen /key/file')

  def testInteractive(self):
    self.can_prompt.return_value = True
    self.AssertCommandBuild(
        ssh.KeygenCommand('/key/file'),
        'ssh-keygen -t rsa -f /key/file',
        'winkeygen /key/file')

  def testInteractiveNoPassphrase(self):
    self.can_prompt.return_value = True
    self.AssertCommandBuild(
        ssh.KeygenCommand('/key/file', allow_passphrase=False),
        ['ssh-keygen', '-N', '', '-t', 'rsa', '-f', '/key/file'],
        'winkeygen /key/file')


class KeygenCommandRunTest(CommandTestBase):
  """Checks KeygenCommand dispatch to execution_utils."""

  def SetUp(self):
    self.can_prompt = self.StartObjectPatch(console_io, 'CanPrompt',
                                            return_value=True)
    self.exec_mock = self.StartObjectPatch(
        execution_utils, 'Exec', autospec=True, return_value=0)

  def testRunSuccess(self):
    """Run a succesful keygen command."""
    ssh.KeygenCommand('/key/file').Run(self.openssh)

    self.exec_mock.assert_called_once_with(
        ['ssh-keygen', '-t', 'rsa', '-f', '/key/file'], no_exit=True)

  def testRunSuccessPutty(self):
    """Run a succesful keygen command under PuTTY."""
    ssh.KeygenCommand('/key/file').Run(self.putty)

    self.exec_mock.assert_called_once_with(
        ['winkeygen', '/key/file'], no_exit=True)

  def testRunFailure(self):
    """Keygen command exits with non-zero."""
    self.exec_mock.return_value = 1

    with self.assertRaises(ssh.CommandError):
      ssh.KeygenCommand('/key/file').Run(self.openssh)

    self.exec_mock.assert_called_once_with(
        ['ssh-keygen', '-t', 'rsa', '-f', '/key/file'], no_exit=True)


class KeygenCommandExecuteTest(CommandTestBase, sdk_test_base.WithTempCWD):
  """Runs the external keygen command and verifies side effects."""

  def SetUp(self):
    self.can_prompt = self.StartObjectPatch(console_io, 'CanPrompt',
                                            return_value=True)

  @test_case.Filters.DoNotRunOnWindows('Command on Mac and Linux')
  def testOpenSSH(self):
    cmd = ssh.KeygenCommand('id_rsa')
    cmd.Run()
    self.AssertFileExists('id_rsa')
    self.AssertFileExists('id_rsa.pub')
    self.AssertFileNotExists('id_rsa.ppk')

  @test_case.Filters.RunOnlyOnWindows('Command on Windows')
  def testPuTTY(self):
    cmd = ssh.KeygenCommand('id_rsa')
    cmd.Run()
    self.AssertFileExists('id_rsa')
    self.AssertFileExists('id_rsa.pub')
    self.AssertFileExists('id_rsa.ppk')


class SSHCommandTest(CommandTestBase):
  """Checks that SSH commands are constructed appropriately."""

  def testHost(self):
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote),
        'ssh -t myhost',
        'putty -t myhost')

  def testUserHost(self):
    remote = ssh.Remote('myhost', user='me')
    self.AssertCommandBuild(
        ssh.SSHCommand(remote),
        'ssh -t me@myhost',
        'putty -t me@myhost')

  def testPort(self):
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, port='8080'),
        'ssh -t -p 8080 myhost',
        'putty -t -P 8080 myhost')

  def testKeyFile(self):
    """Make sure we append `.ppk` for PuTTY if not present."""
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, identity_file='/path/to/key'),
        'ssh -t -i /path/to/key myhost',
        'putty -t -i /path/to/key.ppk myhost')

  def testKeyFileWithPPK(self):
    """Don't append `.ppk` if already there."""
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, identity_file='/path/to/key.ppk'),
        None,  # Not applicable with OpenSSH
        'putty -t -i /path/to/key.ppk myhost')

  def testOptions(self):
    """Ensure we add options using `-o` but not for PuTTY."""
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, options={'Opt': 123, 'Other': 'yes'}),
        'ssh -t -o Opt=123 -o Other=yes myhost',
        'putty -t myhost')

  def testRemoteCommand(self):
    """Check that remote command turns off tty and adds `--` appropriately."""
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, remote_command=['echo', 'hello']),
        'ssh -T myhost -- echo hello',
        'plink -T myhost echo hello')

  def testRemainder(self):
    """Check that remainder is respected and appended at the end.

    Note that the remainder is legacy and not recommended. But we still want to
    support it in order to not break users of `compute ssh`.
    """
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, remainder=['-b', '/bin/sh']),
        'ssh -t myhost -b /bin/sh',
        'putty -t myhost -b /bin/sh')

  def testRemainderAndRemoteCommand(self):
    """Check that remainder works with remote command.

    Note that the remainder is legacy and not recommended. But we still want to
    support it in order to not break users of `compute ssh`.
    """
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, remote_command=['/bin/sh'],
                       remainder=['-vvv']),
        'ssh -T myhost -vvv -- /bin/sh',
        'plink -T myhost -vvv /bin/sh')

  def testQuotedRemoteCommand(self):
    """Check that spaces in remote command args are respected.

    This is the equivalent of running `ssh ... -- echo "hello world"` in bash.
    """
    # Note that we need to pass an array to AssertCommandBuild to avoid
    # autosplitting on whitespace.
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, remote_command=['echo', 'hello world']),
        ['ssh', '-T', 'myhost', '--', 'echo', 'hello world'],
        ['plink', '-T', 'myhost', 'echo', 'hello world'])

  def testExtraFlags(self):
    """Check that extra flags are appended independent of suite.

    No distinction is made between binary flags (e.g. `-b`) or flags with values
    (e.g. `-k v`). There's no checks in place for adding flags that are already
    managed by the class, e.g. `-T`.
    """
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, extra_flags=['-b', '-k', 'v']),
        'ssh -t -b -k v myhost',
        'putty -t -b -k v myhost')

  def testDisableTTY(self):
    """Check that `tty=False` overrides the lack of a remote_command."""
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, tty=False),
        'ssh -T myhost',
        'plink -T myhost')

  def testRemoteCommandEnforceTTY(self):
    """Check that `tty=True` overrides the presence of a remote_command."""
    self.AssertCommandBuild(
        ssh.SSHCommand(self.remote, remote_command=['echo', 'hello'], tty=True),
        'ssh -t myhost -- echo hello',
        'putty -t myhost echo hello')

  def testAllArgs(self):
    """Test all arguments together in one invocation."""
    remote = ssh.Remote('myhost', user='me')
    options = {'Opt': 123, 'Other': 'no'}
    extra_flags = ['-b', '-k', 'v']
    remote_command = ['echo', 'hello world']
    cmd = ssh.SSHCommand(remote, port='8080',
                         identity_file='/path/to/key', options=options,
                         extra_flags=extra_flags, remote_command=remote_command,
                         tty=False)
    self.AssertCommandBuild(
        cmd,
        ['ssh', '-T', '-p', '8080', '-i', '/path/to/key', '-o', 'Opt=123', '-o',
         'Other=no', '-b', '-k', 'v', 'me@myhost', '--', 'echo', 'hello world'],
        ['plink', '-T', '-P', '8080', '-i', '/path/to/key.ppk', '-b', '-k', 'v',
         'me@myhost', 'echo', 'hello world'])


class SSHCommandRunTest(CommandTestBase):
  """Checking that command dispatching works as intended."""

  def SetUp(self):
    self.exec_mock = self.StartObjectPatch(
        execution_utils, 'Exec', autospec=True, return_value=0)
    self.remote = ssh.Remote('myhost')

  def testSuccessOpenSSH(self):
    """Test running with OpenSSH, everything succeeding."""
    cmd = ssh.SSHCommand(self.remote, remote_command=['echo', 'hello world'])
    return_code = cmd.Run(self.openssh)

    self.assertEqual(0, return_code)
    self.exec_mock.assert_called_once_with(
        ['ssh', '-T', 'myhost', '--', 'echo', 'hello world'],
        no_exit=True, in_str=None)

  def testSuccessPuTTY(self):
    """Test running with PuTTY plink, everything succeeding."""
    cmd = ssh.SSHCommand(self.remote, remote_command=['echo', 'hello world'])
    return_code = cmd.Run(self.putty)

    self.assertEqual(0, return_code)
    self.exec_mock.assert_called_once_with(
        ['plink', '-T', 'myhost', 'echo', 'hello world'],
        no_exit=True, in_str=None)

  def testSuccessPuTTYForceConnect(self):
    """Test running with PuTTY plink, with force_connect which injects 'y'."""
    cmd = ssh.SSHCommand(self.remote, remote_command=['echo', 'hello world'])
    return_code = cmd.Run(self.putty, force_connect=True)

    self.assertEqual(0, return_code)
    self.exec_mock.assert_called_once_with(
        ['plink', '-T', 'myhost', 'echo', 'hello world'],
        no_exit=True, in_str='y\n')

  def testRemoteCommandFailed(self):
    """If a remote command failed, we send the right exit code."""
    self.exec_mock.return_value = 5

    cmd = ssh.SSHCommand(self.remote)
    return_code = cmd.Run(self.openssh)

    self.assertEqual(5, return_code)
    self.exec_mock.assert_called_once_with(
        ['ssh', '-t', 'myhost'],
        no_exit=True, in_str=None)

  def testRunCommandErrorOpenSSH(self):
    """Test that a CommandError is raised when ssh process exits with 255.

    255 is the exit code indicating that an SSH error occurred, rather than
    the remote command failed.
    """
    self.exec_mock.return_value = 255
    cmd = ssh.SSHCommand(self.remote)
    with self.assertRaises(ssh.CommandError):
      cmd.Run(self.openssh)

    self.exec_mock.assert_called_once_with(
        ['ssh', '-t', 'myhost'],
        no_exit=True, in_str=None)

  def testRunCommandErrorPlink(self):
    """Test that a CommandError is raised when plink process exits with 1.

    1 is the plink exit code indicating that an SSH error occurred, rather than
    the remote command failed. Note that `putty` always exits with 0.
    """
    self.exec_mock.return_value = 1
    cmd = ssh.SSHCommand(self.remote, tty=False)
    with self.assertRaises(ssh.CommandError):
      cmd.Run(self.putty)

    self.exec_mock.assert_called_once_with(
        ['plink', '-T', 'myhost'],
        no_exit=True, in_str=None)

  def testRunMissingCommandError(self):
    """Environment is missing the ssh or ssh_term command."""
    self.openssh.ssh_term = None
    cmd = ssh.SSHCommand(self.remote)
    with self.assertRaises(ssh.MissingCommandError):
      cmd.Run(self.openssh)
    self.exec_mock.assert_not_called()


class SSHCommandRunAndExecuteTest(CommandTestBase):
  """Actual invocations without mocking."""

  def testRunSSH(self):
    """Expect failure when connecting to bogus host."""
    remote = ssh.Remote('bogushost')
    cmd = ssh.SSHCommand(remote, remote_command=['true'])
    with self.assertRaises(ssh.CommandError):
      exit_code = cmd.Run()
      raise ValueError('Run() exited with unexpected status [{}]'
                       .format(exit_code))
    # TODO(b/34886006): Once WithCommandOutputCapture exists, check stderr
    # for appropriate message.


class SCPCommandTest(CommandTestBase):
  """Checks that SCP commands are constructed appropriately."""

  def testVerifyCalled(self):
    """Check once that SCPCommand.Verify is called in Build."""
    verify = self.StartObjectPatch(ssh.SCPCommand, 'Verify')
    cmd = ssh.SCPCommand(self.ref_local_1, self.ref_remote_1)
    cmd.Build(self.openssh)
    verify.assert_called_once_with([self.ref_local_1], self.ref_remote_1,
                                   env=self.openssh)

  def testSingleLocalToRemote(self):
    self.AssertCommandBuild(
        ssh.SCPCommand(self.ref_local_1, self.ref_remote_1),
        'scp local_1 myhost:remote_1',
        'pscp local_1 myhost:remote_1')

  def testMultipleLocalToRemote(self):
    self.AssertCommandBuild(
        ssh.SCPCommand([self.ref_local_1, self.ref_local_2], self.ref_remote_1),
        'scp local_1 local_2 myhost:remote_1',
        'pscp local_1 local_2 myhost:remote_1')

  def testSingleRemoteToLocal(self):
    self.AssertCommandBuild(
        ssh.SCPCommand(self.ref_remote_1, self.ref_local_1),
        'scp myhost:remote_1 local_1',
        'pscp myhost:remote_1 local_1')

  def testMultipleRemotesToLocal(self):
    srcs = [self.ref_remote_1, self.ref_remote_2]
    dst = self.ref_local_1
    cmd = ssh.SCPCommand(srcs, dst)
    self.AssertCommandBuild(
        cmd,
        'scp myhost:remote_1 me@myhost:remote_2 local_1',
        None)
    with self.assertRaisesRegex(
        ssh.InvalidConfigurationError, 'Multiple remote sources not supported'):
      ssh.SCPCommand.Verify(srcs, dst, env=self.putty)

  def testMultipleRemotesToLocalSingleRemote(self):
    """Make sure that enforcing a single remote works with single remote."""
    srcs = [self.ref_remote_2, self.ref_remote_2_2]
    dst = self.ref_local_1
    # Passes for OpenSSH
    ssh.SCPCommand.Verify(srcs, dst, single_remote=True, env=self.openssh)
    with self.assertRaisesRegex(
        ssh.InvalidConfigurationError, 'Multiple remote sources not supported'):
      ssh.SCPCommand.Verify(srcs, dst, single_remote=True, env=self.putty)

  def testMultipleRemotesToLocalSingleRemoteFails(self):
    """Enforcing a single remote fails with multiple remotes."""
    srcs = [self.ref_remote_1, self.ref_remote_2]
    dst = self.ref_local_1
    with self.assertRaisesRegex(
        ssh.InvalidConfigurationError, 'Multiple remote sources not supported'):
      ssh.SCPCommand.Verify(srcs, dst, single_remote=True, env=self.putty)
    with self.assertRaisesRegex(
        ssh.InvalidConfigurationError, 'sources must refer to the same remote'):
      ssh.SCPCommand.Verify(srcs, dst, single_remote=True, env=self.openssh)

  def testMixedSourcesToRemote(self):
    """Mix of remote and local sources, should raise."""
    srcs = [self.ref_remote_1, self.ref_local_1]
    dst = self.ref_remote_2
    with self.assertRaisesRegex(
        ssh.InvalidConfigurationError, 'All sources must be local'):
      ssh.SCPCommand.Verify(srcs, dst, env=self.openssh)

  def testLocalSourceToLocal(self):
    """Mix of remote and local sources, should raise."""
    srcs = [self.ref_local_1]
    dst = self.ref_local_2
    with self.assertRaisesRegex(
        ssh.InvalidConfigurationError, 'Source\\(s\\) must be remote'):
      ssh.SCPCommand.Verify(srcs, dst, env=self.openssh)

  def testMixedSourcesToLocal(self):
    """Mix of remote and local sources, should raise."""
    srcs = [self.ref_remote_1, self.ref_local_2]
    dst = self.ref_local_1
    with self.assertRaisesRegex(
        ssh.InvalidConfigurationError, 'Source\\(s\\) must be remote'):
      ssh.SCPCommand.Verify(srcs, dst, env=self.openssh)

  def testNoSources(self):
    """Require at least one source."""
    cmd = ssh.SCPCommand([], self.ref_remote_2)
    with self.assertRaisesRegex(
        ssh.InvalidConfigurationError, 'No sources'):
      cmd.Build(self.openssh)

  def testUserHost(self):
    self.AssertCommandBuild(
        ssh.SSHCommand(self.ref_remote_2),
        'ssh -t me@myhost:remote_2',
        'putty -t me@myhost:remote_2')

  def testRecursive(self):
    self.AssertCommandBuild(
        ssh.SCPCommand(self.ref_local_1, self.ref_remote_1, recursive=True),
        'scp -r local_1 myhost:remote_1',
        'pscp -r local_1 myhost:remote_1')

  def testCompress(self):
    self.AssertCommandBuild(
        ssh.SCPCommand(self.ref_local_1, self.ref_remote_1, compress=True),
        'scp -C local_1 myhost:remote_1',
        'pscp -C local_1 myhost:remote_1')

  def testPort(self):
    self.AssertCommandBuild(
        ssh.SCPCommand(self.ref_local_1, self.ref_remote_1, port='8080'),
        'scp -P 8080 local_1 myhost:remote_1',
        'pscp -P 8080 local_1 myhost:remote_1')

  def testKeyFile(self):
    """Make sure we append `.ppk` for PuTTY if not present."""
    self.AssertCommandBuild(
        ssh.SCPCommand(self.ref_local_1, self.ref_remote_1,
                       identity_file='/path/to/key'),
        'scp -i /path/to/key local_1 myhost:remote_1',
        'pscp -i /path/to/key.ppk local_1 myhost:remote_1')

  def testKeyFileWithPPK(self):
    """Don't append `.ppk` if already there."""
    self.AssertCommandBuild(
        ssh.SCPCommand(self.ref_local_1, self.ref_remote_1,
                       identity_file='/path/to/key.ppk'),
        None,  # Not applicable with OpenSSH
        'pscp -i /path/to/key.ppk local_1 myhost:remote_1')

  def testOptions(self):
    """Ensure we add options using `-o` but not for PuTTY."""
    self.AssertCommandBuild(
        ssh.SCPCommand(self.ref_local_1, self.ref_remote_1,
                       options={'Opt': 123, 'Other': 'yes'}),
        'scp -o Opt=123 -o Other=yes local_1 myhost:remote_1',
        'pscp local_1 myhost:remote_1')

  def testExtraFlags(self):
    """Check that extra flags are appended independent of suite.

    No distinction is made between binary flags (e.g. `-b`) or flags with values
    (e.g. `-k v`). There's no checks in place for adding flags that are already
    managed by the class, e.g. `-T`.
    """
    self.AssertCommandBuild(
        ssh.SCPCommand(self.ref_local_1, self.ref_remote_1,
                       extra_flags=['-b', '-k', 'v']),
        'scp -b -k v local_1 myhost:remote_1',
        'pscp -b -k v local_1 myhost:remote_1')

  def testAllArgs(self):
    """Test all arguments together in one invocation."""

    options = {'Opt': 123, 'Other': 'no'}
    extra_flags = ['-b', '-k', 'v']
    cmd = ssh.SCPCommand([self.ref_local_1, self.ref_local_2],
                         self.ref_remote_2, recursive=True, port='8080',
                         identity_file='/path/to/key', options=options,
                         extra_flags=extra_flags)
    self.AssertCommandBuild(
        cmd,
        'scp -r -P 8080 -i /path/to/key -o Opt=123 -o Other=no -b -k v '
        'local_1 local_2 me@myhost:remote_2',
        'pscp -r -P 8080 -i /path/to/key.ppk -b -k v '
        'local_1 local_2 me@myhost:remote_2')


class SCPCommandRunTest(CommandTestBase):
  """Checking that command dispatching works as intended."""

  def SetUp(self):
    self.exec_mock = self.StartObjectPatch(
        execution_utils, 'Exec', autospec=True, return_value=0)
    self.cmd = ssh.SCPCommand(self.ref_local_1, self.ref_remote_1)

  def testSuccessOpenSSH(self):
    """Test running with OpenSSH, everything succeeding."""
    self.cmd.Run(self.openssh)
    self.exec_mock.assert_called_once_with(
        ['scp', 'local_1', 'myhost:remote_1'],
        no_exit=True, in_str=None)

  def testSuccessPuTTY(self):
    """Test running with PuTTY pscp, everything succeeding."""
    self.cmd.Run(self.putty)
    self.exec_mock.assert_called_once_with(
        ['pscp', 'local_1', 'myhost:remote_1'],
        no_exit=True, in_str=None)

  def testSuccessPuTTYForceConnect(self):
    """Test running with PuTTY pscp, with force_connect which injects 'y'."""
    self.cmd.Run(self.putty, force_connect=True)
    self.exec_mock.assert_called_once_with(
        ['pscp', 'local_1', 'myhost:remote_1'],
        no_exit=True, in_str='y\n')

  def testScpFailed(self):
    """If scp command failed, we raise."""
    self.exec_mock.return_value = 5
    with self.assertRaises(ssh.CommandError):
      self.cmd.Run(self.openssh)  # Same for PuTTY
    self.exec_mock.assert_called_once_with(
        ['scp', 'local_1', 'myhost:remote_1'],
        no_exit=True, in_str=None)

  def testRunMissingCommandError(self):
    """Environment is missing the scp command."""
    self.openssh.scp = None
    with self.assertRaises(ssh.MissingCommandError):
      self.cmd.Run(self.openssh)
    self.exec_mock.assert_not_called()


class SCPCommandRunAndExecuteTest(CommandTestBase):
  """Actual invocations without mocking."""

  def testRunSCP(self):
    """Expect failure when connecting to bogus host."""
    remote = ssh.Remote('bogushost')
    ref_remote = ssh.FileReference('bogusfile', remote=remote)
    cmd = ssh.SCPCommand(self.ref_local_1, ref_remote)
    with self.assertRaises(ssh.CommandError):
      exit_code = cmd.Run()
      raise ValueError('Run() exited with unexpected status [{}]'
                       .format(exit_code))
    # TODO(b/34886006): Once WithCommandOutputCapture exists, check stderr
    # for appropriate message.


class FileReferenceTest(test_case.TestCase):
  """Tests for ssh.FileReference class."""

  def _AssertRemote(self, path, file_path, host, user=None):
    """Assert that a given path is considered a remote path.

    Args:
      path: str, The path to evaluate.
      file_path: str, Expected path on the ref object.
      host: str, Expected host on the remote of the ref object.
      user: str or None, Expected user on the remote of the ref object.
    """
    ref = ssh.FileReference.FromPath(path)
    self.assertEqual(ref.path, file_path)
    self.assertEqual(ref.remote.user, user)
    self.assertEqual(ref.remote.host, host)

  def _AssertLocal(self, path):
    """Assert that a given path is considered a local path.

    Args:
      path: str, The path to evaluate.
    """
    ref = ssh.FileReference.FromPath(path)
    self.assertEqual(ref.path, path)
    self.assertEqual(ref.remote, None)

  def testFromLocalPath(self):
    """Check that local paths are evaluated as such."""
    self._AssertLocal('myfile')
    self._AssertLocal(r'.')
    self._AssertLocal(r'.a:b')
    self._AssertLocal(r'/pdq')
    self._AssertLocal(r'\pdq')
    self._AssertLocal(r'/p:q')
    self._AssertLocal(r'\p:q')
    self._AssertLocal(r'/.xyz')
    self._AssertLocal(r'.:\xyz')
    self._AssertLocal(r'.:xyz')
    self._AssertLocal(r'\.xyz')

  def testFromRemotePath(self):
    """Check that remote paths are evaluated as such."""
    self._AssertRemote(r'CC:\bbb\z',
                       file_path=r'\bbb\z', host='CC')
    self._AssertRemote('host:/aaa/z',
                       file_path='/aaa/z', host='host')
    self._AssertRemote(r'host:\aaa\z',
                       file_path=r'\aaa\z', host='host')
    self._AssertRemote(r'user@host:aaa/z',
                       file_path='aaa/z', host='host', user='user')
    self._AssertRemote(r'user@host:aaa\z',
                       file_path=r'aaa\z', host='host', user='user')
    self._AssertRemote(r'user@host:',  # Empty paths are allowed
                       file_path='', host='host', user='user')

  def testLocalWindowsPaths(self):
    """Check that presence of drive always indicates local."""

    # Emulate windows drive letters
    self.StartObjectPatch(os.path, 'splitdrive', return_value=('C:', 'unused'))

    self._AssertLocal(r'C:/aaa/z')
    self._AssertLocal(r'C:aaa/z')
    self._AssertLocal(r'C:bbb')
    self._AssertLocal(r'C:/bbb/z')
    self._AssertLocal(r'C:\bbb\z')
    self._AssertLocal(r'C:bbb\z')

  def testLocalWindowsPathsOnUnix(self):
    """Drive letters have no power in unix, so they are considered remote."""

    # Emulate unix, no drive letters
    self.StartObjectPatch(os.path, 'splitdrive', return_value=('', 'unused'))

    self._AssertRemote(r'C:/aaa/z', file_path='/aaa/z', host='C')
    self._AssertRemote(r'C:aaa/z', file_path='aaa/z', host='C')
    self._AssertRemote(r'C:bbb', file_path='bbb', host='C')
    self._AssertRemote(r'C:/bbb/z', file_path='/bbb/z', host='C')
    self._AssertRemote(r'C:\bbb\z', file_path=r'\bbb\z', host='C')
    self._AssertRemote(r'C:bbb\z', file_path=r'bbb\z', host='C')

  def testToArgRemote(self):
    """Check outputs from the `ToArg` method on remote ref."""
    remote = ssh.Remote('host')
    ref = ssh.FileReference(path='~', remote=remote)
    self.assertEqual(ref.ToArg(), 'host:~')
    self.assertIsInstance(ref.remote, ssh.Remote)

  def testToArgRemoteWithUser(self):
    """Check outputs from the `ToArg` method on remote ref with user."""
    remote = ssh.Remote('host', user='user')
    ref = ssh.FileReference(path=r'\path', remote=remote)
    self.assertEqual(ref.ToArg(), r'user@host:\path')
    self.assertIsInstance(ref.remote, ssh.Remote)

  def testToArgLocal(self):
    """Check outputs from the `ToArg` method on local ref."""
    ref = ssh.FileReference(path=r'C:\local\path')
    self.assertEqual(ref.ToArg(), r'C:\local\path')
    self.assertIsNone(ref.remote)

  def testEquality(self):
    """Check that the equality operator works."""
    remote_1 = ssh.Remote('host', user='me')
    remote_2 = ssh.Remote('host')
    self.assertEqual(ssh.FileReference('mypath', remote=remote_1),
                     ssh.FileReference('mypath', remote=remote_1))
    self.assertEqual(ssh.FileReference('mypath'),
                     ssh.FileReference('mypath'))
    self.assertNotEqual(ssh.FileReference('mypath', remote=remote_1),
                        ssh.FileReference('mypath', remote=remote_2))
    self.assertNotEqual(ssh.FileReference('mypath', remote=remote_1),
                        ssh.FileReference('otherpath', remote=remote_1))


class SSHPollerTest(CommandTestBase):
  """Emulates local time and ensures that retry logic works as intended."""

  def SetUp(self):
    # Mock out the base commands Run method to emulate the SSH server response
    # The method is already tested in other unit tests
    self.ssh_run_mock = self.StartObjectPatch(ssh.SSHCommand, 'Run')

    # Retryer checks time prior to each actual call, and after the last call,
    # meaning that this is always called one more time than `Run()`.
    self.time_ms = self.StartObjectPatch(retry, '_GetCurrentTimeMs')

    self.poller = ssh.SSHPoller(self.remote)
    self.command_error = ssh.CommandError('ssh', message='err')

  def testBuildBasic(self):
    self.AssertCommandBuild(
        self.poller.ssh_command,
        'ssh -T myhost -- true',
        'plink -T myhost true')

  def testBuildAllArgs(self):
    remote = ssh.Remote('myhost', user='me')
    options = {'Opt': 123, 'Other': 'no'}
    extra_flags = ['-b', '-k', 'v']
    poller = ssh.SSHPoller(remote, port='8080',
                           identity_file='/path/to/key', options=options,
                           extra_flags=extra_flags)
    self.AssertCommandBuild(
        poller.ssh_command,
        ('ssh -T -p 8080 -i /path/to/key -o Opt=123 -o Other=no -b -k v '
         'me@myhost -- true'),
        'plink -T -P 8080 -i /path/to/key.ppk -b -k v me@myhost true')

  def testPollFirstSuccess(self):
    """Run the poller and succeed at once."""
    self.time_ms.return_value = 0
    self.poller.Poll()
    self.ssh_run_mock.assert_called_once_with(env=None, force_connect=False)
    self.assertEqual(self.time_ms.call_count, 2)

  def testPollEventualSuccess(self):
    """Run the poller and succeed eventually."""
    self.time_ms.side_effect = [0, 53*1000, 54*1000]  # Time left for 2nd call
    self.ssh_run_mock.side_effect = [self.command_error, 0]  # (fail, success)
    self.poller.Poll()
    call = mock.call(env=None, force_connect=False)
    self.assertEqual(self.time_ms.call_count, 3)
    self.assertEqual(
        self.ssh_run_mock.call_args_list,
        [call, call])

  def testPollTimeout(self):
    """Run the poller and fail with timeout."""
    self.time_ms.side_effect = [0, 30*1000, 57*1000]  # No time for last call
    self.ssh_run_mock.side_effect = [self.command_error, self.command_error]

    with self.assertRaises(retry.WaitException):
      self.poller.Poll()

    call = mock.call(env=None, force_connect=False)
    self.assertEqual(self.time_ms.call_count, 3)
    self.assertEqual(
        self.ssh_run_mock.call_args_list,
        [call, call])

  def testPollWithArgsAndCustomTimeout(self):
    """Args are relayed to the base class, and custom timeout works."""
    self.time_ms.side_effect = [0, 31*1000]  # Custom timeout passed
    self.ssh_run_mock.side_effect = [self.command_error]

    poller = ssh.SSHPoller(self.remote, max_wait_ms=30*1000, sleep_ms=4*1000)
    with self.assertRaises(retry.WaitException):
      poller.Poll(env='fake-env', force_connect=True)

    self.assertEqual(self.time_ms.call_count, 2)
    self.ssh_run_mock.assert_called_once_with(
        env='fake-env', force_connect=True)


if __name__ == '__main__':
  test_case.main()
