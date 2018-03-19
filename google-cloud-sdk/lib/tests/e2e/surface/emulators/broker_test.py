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
"""Integration tests for the broker library."""

import datetime
import errno
import httplib
import logging
import os
import StringIO
import subprocess
import tempfile
import time

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.emulators import broker
from googlecloudsdk.command_lib.emulators import pubsub_util
from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core.util import retry
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from mock import patch


def Remove(path, wait_secs=3):
  """Removes a file, retrying on failure."""
  deadline = time.time() + wait_secs
  while True:
    try:
      os.remove(path)
    except OSError:
      if time.time() >= deadline:
        raise
    else:
      break

    time.sleep(0.1)


def ThreadDumpPrefix():
  """Returns the name prefix for a debug file containing thread stack traces."""
  timestamp = datetime.datetime.utcnow().strftime(e2e_utils.TIMESTAMP_FORMAT)
  return 'broker_test-{0}.{1}.threaddump-'.format(timestamp, os.getpid())


class BrokerTestBase(sdk_test_base.BundledBase,
                     sdk_test_base.WithLogCapture):
  """Base class for tests in this module."""

  def SetUp(self):
    # Create and start the watchdog.
    self._watchdog = e2e_utils.WatchDog(timeout_cb=self._WriteThreadDump)
    self._watchdog.start()
    self.addCleanup(self._Cleanup)

  def _WriteThreadDump(self):
    """Writes the dump of current thread stacks to the system temp dir."""
    stacks = StringIO.StringIO()
    e2e_utils.PrintAllThreadStacks(out=stacks)

    prefix = ThreadDumpPrefix()
    with tempfile.NamedTemporaryFile(prefix=prefix, delete=False) as dump:
      dump.write('==== THREAD STACKS ====\n')
      dump.write(stacks.getvalue())
      dump.write('==== STDOUT ====\n')
      dump.write(self.GetOutput())
      dump.write('==== STDERR ====\n')
      dump.write(self.GetErr())
      logging.info('Wrote thread dump: %s', dump.name)

    # Also write thread stacks to stderr, in case it is captured.
    os.stderr.write(stacks.getvalue())

  def _Cleanup(self):
    self._watchdog.Stop()
    self._watchdog.join(timeout=1.0)

  # All tests should call this to construct a Broker instance, instead of
  # constructing one directly, so that started processes are properly cleaned
  # up.
  def _NewBroker(self, *args, **kwargs):
    """Returns a new Broker whose subprocesses are registered to this test."""
    test = self

    class BrokerWithProcessRegistration(broker.Broker):

      def Start(self, *args, **kwargs):
        # Disable file logging.
        kwargs['logtostderr'] = True

        super(BrokerWithProcessRegistration, self).Start(*args, **kwargs)
        if self._process:
          test.RegisterProcess(self._process)

    return BrokerWithProcessRegistration(*args, **kwargs)

  def _BrokerAddress(self):
    """Returns an address for the broker server."""
    return 'localhost:%s' % test_case.Base.GetPort()

  def _WriteDefaultBrokerConfig(self):
    port = test_case.Base.GetPort()
    config = '''{
        "port_ranges":[
          {"begin":%s, "end":%d}
        ],
        "default_emulator_start_deadline":{"seconds":20}
      }''' % (port, int(port) + 1)

    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(config)
    f.flush()
    f.close()

    self.addCleanup(lambda: Remove(f.name))
    return f.name

  def _CreateDummyEmulator(self, b, emulator_id, resolved_host=None):
    """Adds a dummy emulator (unstartable) configuration to Broker b."""
    b.CreateEmulator(emulator_id,
                     '/some/path',
                     [],
                     [],
                     resolved_host=resolved_host)

  def _CreatePubSubEmulator(self, b):
    """Adds the Pub/Sub emulator configuration to Broker b."""
    pubsub_root = pubsub_util.GetPubSubRoot()
    args = ['--rule_id=google.pubsub',
            '%s/bin/cloud-pubsub-emulator' % pubsub_root,
            '--port={port:pubsub}']
    b.CreateEmulator('google.pubsub', '{dir:broker}/launcher', args, [])

  def _HttpGet(self, host, url):
    """Returns the GET content, or raises an exception."""
    conn = httplib.HTTPConnection(host)
    try:
      conn.request('GET', url)
      resp = conn.getresponse()
      if resp.status != httplib.OK:
        raise Exception('GET {0} failed: {1}'.format(url, resp.reason))
      data = resp.read()
      return data
    finally:
      conn.close()

  # TODO(b/36057253): Move this to test_case.TestCase?
  def _AssertDead(self, process, wait_secs=2):
    """Asserts that the Popen process is dead, or dies within wait_secs."""
    retryer = retry.Retryer(max_wait_ms=wait_secs * 1000)

    try:
      if self.IsOnLinux():
        try:
          # Workaround for poll() returning None forever on certain platforms,
          # meaning it is not reliable enough for use. Check for the process to
          # "change status", which should mean it terminated. WNOHANG means the
          # waitpid() call should return immediately instead of blocking.
          # See http://bugs.python.org/issue2475 .
          retryer.RetryOnResult(os.waitpid, args=[process.pid, os.WNOHANG],
                                should_retry_if=(0, 0), sleep_ms=200)
        except OSError as e:
          # The child process no longer exists (or never existed). This is a
          # successful exit condition.
          self.assertEquals(errno.ECHILD, e.errno)
      else:
        retryer.RetryOnResult(process.poll, should_retry_if=None, sleep_ms=200)
    except retry.WaitException as e:
      self.fail('Process did not die: %s' % e)


class BrokerTest(BrokerTestBase):

  def testInit(self):
    valid_addresses = ['', 'host', 'host:8080']
    for address in valid_addresses:
      self._NewBroker(address)

  def testInit_WithBadAddress(self):
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self._NewBroker('bad:add:ress')

  def testStart(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

  def testStart_WithBadConfigFile(self):
    b = self._NewBroker(self._BrokerAddress(), config_file='/no/such/config')
    with self.assertRaises(broker.BrokerError):
      b.Start(wait_secs=2)
    self.assertFalse(b.IsRunning())

  def testStart_WhenAlreadyStartedByThis(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    b.Start()  # Doesn't raise.

  def testStart_WhenAlreadyStartedByOther(self):
    address = self._BrokerAddress()
    other = self._NewBroker(address)
    other.Start()
    self.assertTrue(other.IsRunning())

    b = self._NewBroker(address)
    b.Start()  # Doesn't raise.

  def testStart_WhenTimedOut(self):
    b = self._NewBroker(self._BrokerAddress())

    class MockSubprocess(object):
      """Decorates Popen() to capture the returned object."""

      def Popen(self, *args, **kwargs):
        self.p = subprocess.Popen(*args, **kwargs)
        return self.p

    mock_subprocess = MockSubprocess()

    # When Start() times-out, it must terminate the process it tried to
    # start. We patch IsRunning() to return False to force a timeout. We also
    # patch the subprocess module so we can inspect the process object later.
    with patch.object(b, 'IsRunning', return_value=False, autospec=True):
      with patch.object(broker, 'subprocess', mock_subprocess):
        with self.assertRaises(broker.BrokerError):
          b.Start(wait_secs=0)

    self.assertFalse(b.IsRunning())

    # The process must be dead or die soon.
    self._AssertDead(mock_subprocess.p, wait_secs=2)

  def testIsRunning_AfterShutdown(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    b.Shutdown()
    self.assertFalse(b.IsRunning())

  def testShutdown_WhenTimedOut(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    with self.assertRaises(broker.BrokerError):
      b.Shutdown(wait_secs=0)

  def testShutdown_WhenStartedByOther(self):
    address = self._BrokerAddress()
    other = self._NewBroker(address)
    other.Start()
    self.assertTrue(other.IsRunning())

    b = self._NewBroker(address)
    self.assertTrue(b.IsRunning())

    b.Shutdown()
    self.assertFalse(b.IsRunning())
    self.assertFalse(other.IsRunning())

  def testCreateEmulator(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    b.CreateEmulator('some.emulator', '/some/path', ['arg1', 'arg2'],
                     ['target1', 'target2'])
    emulators = b.ListEmulators()
    self.assertEquals(1, len(emulators))
    emulator = emulators[0]
    self.assertEquals('some.emulator', emulator['emulator_id'])
    self.assertEquals('/some/path', emulator['start_command']['path'])
    self.assertEquals('arg1', emulator['start_command']['args'][0])
    self.assertEquals('arg2', emulator['start_command']['args'][1])
    self.assertEquals('target1', emulator['rule']['target_patterns'][0])
    self.assertEquals('target2', emulator['rule']['target_patterns'][1])

  def testCreateEmulator_WhenBrokerNotRunning(self):
    b = self._NewBroker(self._BrokerAddress())
    with self.assertRaises(broker.BrokerNotRunningError):
      b.CreateEmulator('some.emulator', 'path', [], [])

  def testCreateEmulator_WhenAlreadyExists(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    b.CreateEmulator('some.emulator', '/some/path', [], [])
    with self.assertRaises(broker.BrokerError):
      b.CreateEmulator('some.emulator', '/some/path', [], [])

  def testGetEmulator(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    # Add an emulator with a resolved_host.
    emulator_id = 'some.emulator'
    self._CreateDummyEmulator(b, emulator_id, resolved_host='foo:123')
    emulator = b.GetEmulator(emulator_id)
    self.assertEquals(emulator_id, emulator['emulator_id'])
    self.assertEquals('foo:123', emulator['rule']['resolved_host'])

  def testGetEmulator_WhenBrokerNotRunning(self):
    b = self._NewBroker(self._BrokerAddress())
    with self.assertRaises(broker.BrokerNotRunningError):
      b.GetEmulator('some.emulator')

  def testGetEmulator_WhenNoSuchEmulator(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    with self.assertRaises(broker.BrokerError):
      b.GetEmulator('no.such.emulator')

  def testListEmulators_WhenBrokerNotRunning(self):
    b = self._NewBroker(self._BrokerAddress())
    with self.assertRaises(broker.BrokerNotRunningError):
      b.ListEmulators()

  def testStartEmulator_WhenBrokerNotRunning(self):
    b = self._NewBroker(self._BrokerAddress())
    with self.assertRaises(broker.BrokerNotRunningError):
      b.StartEmulator('some.emulator')

  def testStartEmulator_WhenNoSuchEmulator(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    with self.assertRaises(broker.BrokerError):
      b.StartEmulator('no.such.emulator')

  def testStartEmulator_WhenEmulatorFailsToStart(self):
    config_file = self._WriteDefaultBrokerConfig()
    b = self._NewBroker(self._BrokerAddress(), config_file=config_file)
    b.Start()
    self.assertTrue(b.IsRunning())

    emulator_id = 'some.emulator'
    self._CreateDummyEmulator(b, emulator_id)
    with self.assertRaises(broker.BrokerError):
      b.StartEmulator(emulator_id)

  def testStopEmulator_WhenBrokerNotRunning(self):
    b = self._NewBroker(self._BrokerAddress())
    with self.assertRaises(broker.BrokerNotRunningError):
      b.StopEmulator('some.emulator')

  def testStopEmulator_WhenNoSuchEmulator(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    with self.assertRaises(broker.BrokerError):
      b.StopEmulator('no.such.emulator')

  def testStopEmulator_WhenAlreadyStopped(self):
    b = self._NewBroker(self._BrokerAddress())
    b.Start()
    self.assertTrue(b.IsRunning())

    emulator_id = 'some.emulator'
    self._CreateDummyEmulator(b, emulator_id)
    b.StopEmulator(emulator_id)


@test_case.Filters.RunOnlyWithEnv('BROKER_JAVA_TESTS_ENABLED',
                                  reason='b/27999425')
@test_case.Filters.skip('Fails not just on windows.', 'b/29634555')
class BrokerJavaTest(BrokerTestBase):

  def SetUp(self):
    # Verify that Java is installed or skip these tests
    with self.SkipTestIfRaises(java.JavaError):
      java.RequireJavaInstalled('test')

  @test_case.Filters.SkipOnWindows('Too flaky', 'b/29634555')
  def testStopEmulator(self):
    config_file = self._WriteDefaultBrokerConfig()
    b = self._NewBroker(self._BrokerAddress(), config_file=config_file)
    b.Start()
    self.assertTrue(b.IsRunning())

    # Add the Pub/Sub emulator.
    self._CreatePubSubEmulator(b)

    b.StartEmulator('google.pubsub')
    emulators = b.ListEmulators()
    self.assertEquals(1, len(emulators))
    self.assertEquals(2, emulators[0]['state'])  # ONLINE

    b.StopEmulator('google.pubsub')
    emulators = b.ListEmulators()
    self.assertEquals(1, len(emulators))
    if 'state' in emulators[0]:
      self.assertEquals(0, emulators[0]['state'])  # OFFLINE

  def testStartEmulator_WhenAlreadyStarted(self):
    config_file = self._WriteDefaultBrokerConfig()
    b = self._NewBroker(self._BrokerAddress(), config_file=config_file)
    b.Start()
    self.assertTrue(b.IsRunning())

    # Add the Pub/Sub emulator.
    self._CreatePubSubEmulator(b)

    b.StartEmulator('google.pubsub')
    emulators = b.ListEmulators()
    self.assertEquals(1, len(emulators))
    self.assertEquals(2, emulators[0]['state'])  # ONLINE

    with self.assertRaises(broker.BrokerError):
      b.StartEmulator('google.pubsub')

  def testStartEmulator(self):
    config_file = self._WriteDefaultBrokerConfig()
    b = self._NewBroker(self._BrokerAddress(), config_file=config_file)
    b.Start()
    self.assertTrue(b.IsRunning())

    # Add the Pub/Sub emulator.
    self._CreatePubSubEmulator(b)

    emulators = b.ListEmulators()
    self.assertEquals(1, len(emulators))
    if 'state' in emulators[0]:
      self.assertEquals(0, emulators[0]['state'])  # OFFLINE

    b.StartEmulator('google.pubsub')
    emulators = b.ListEmulators()
    self.assertEquals(1, len(emulators))
    self.assertEquals(2, emulators[0]['state'])  # ONLINE

  def testShutdown_StopsEmulators(self):
    config_file = self._WriteDefaultBrokerConfig()
    b = self._NewBroker(self._BrokerAddress(), config_file=config_file)
    b.Start()
    self.assertTrue(b.IsRunning())

    # Add the Pub/Sub emulator.
    self._CreatePubSubEmulator(b)

    b.StartEmulator('google.pubsub')

    # Ensure the emulator is running. We'll use the same check to verify that
    # the emulator is stopped after broker shutdown.
    resolved_host = b.GetEmulator('google.pubsub')['rule']['resolved_host']
    self.assertIsNotNone(resolved_host)
    self.assertEquals('Ok', self._HttpGet(resolved_host, '/').rstrip())

    b.Shutdown()

    # The emulator will shutdown soon.
    with self.assertRaises(Exception):
      deadline = time.time() + 2
      while time.time() < deadline:
        self._HttpGet(resolved_host, '/')
        time.sleep(0.2)


if __name__ == '__main__':
  test_case.main()
