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
"""Unit tests for the broker library."""

import httplib
import socket

from googlecloudsdk.command_lib.emulators import broker
from tests.lib import test_case
import httplib2
import mock


def AllRequestErrors():
  conn_reset = broker.RequestSocketError()
  conn_reset.errno = broker.SocketConnResetErrno()
  conn_refused = broker.RequestSocketError()
  conn_refused.errno = broker.SocketConnRefusedErrno()
  return (broker.RequestTimeoutError(), conn_reset, conn_refused,
          broker.RequestError())


class BrokerTest(test_case.TestCase):

  def testSendJsonResponse_RequestRaisesSocketTimeout(self):
    with mock.patch.object(broker, 'httplib2') as mock_httplib2:
      mock_client = mock.create_autospec(httplib2.Http)
      mock_httplib2.Http.return_value = mock_client

      with self.assertRaises(broker.RequestTimeoutError):
        mock_client.request.side_effect = socket.timeout('Timed-out')
        b = broker.Broker('host:1234', broker_dir='dir')
        b._SendJsonRequest('GET', '/')

  def testSendJsonResponse_RequestRaisesResponseNotReady(self):
    with mock.patch.object(broker, 'httplib2') as mock_httplib2:
      mock_client = mock.create_autospec(httplib2.Http)
      mock_httplib2.Http.return_value = mock_client

      with self.assertRaises(broker.RequestTimeoutError):
        mock_client.request.side_effect = httplib.ResponseNotReady('Not ready')
        b = broker.Broker('host:1234', broker_dir='dir')
        b._SendJsonRequest('GET', '/')

  def testSendJsonResponse_RequestRaisesSocketError(self):
    with mock.patch.object(broker, 'httplib2') as mock_httplib2:
      mock_client = mock.create_autospec(httplib2.Http)
      mock_httplib2.Http.return_value = mock_client

      with self.assertRaises(broker.RequestSocketError) as ar_context:
        conn_reset = socket.error(broker.SocketConnResetErrno(), 'Conn reset')
        mock_client.request.side_effect = conn_reset
        b = broker.Broker('host:1234', broker_dir='dir')
        b._SendJsonRequest('GET', '/')
      self.assertEquals(broker.SocketConnResetErrno(),
                        ar_context.exception.errno)

  def testSendJsonResponse_RequestRaisesHTTPException(self):
    with mock.patch.object(broker, 'httplib2') as mock_httplib2:
      mock_client = mock.create_autospec(httplib2.Http)
      mock_httplib2.Http.return_value = mock_client

      with self.assertRaises(broker.RequestError):
        mock_client.request.side_effect = httplib.HTTPException()
        b = broker.Broker('host:1234', broker_dir='dir')
        b._SendJsonRequest('GET', '/')

  def testSendJsonResponse_RequestRaisesHttpLib2Error(self):
    with mock.patch.object(broker, 'httplib2') as mock_httplib2:
      mock_client = mock.create_autospec(httplib2.Http)
      mock_httplib2.Http.return_value = mock_client
      mock_httplib2.HttpLib2Error = httplib2.HttpLib2Error

      with self.assertRaises(broker.RequestError):
        mock_client.request.side_effect = httplib2.HttpLib2Error()
        b = broker.Broker('host:1234', broker_dir='dir')
        b._SendJsonRequest('GET', '/')

  def testIsRunning_WhenRequestErrorsRaised(self):
    b = broker.Broker('host:1234', broker_dir='dir')
    with mock.patch.object(b, '_SendJsonRequest') as send:
      for error in AllRequestErrors():
        send.side_effect = error
        self.assertFalse(b.IsRunning())

  def testShutdown_WhenRequestErrorsRaised(self):
    b = broker.Broker('host:1234', broker_dir='dir')
    with mock.patch.object(b, '_SendJsonRequest') as send:
      for error in AllRequestErrors():
        send.side_effect = error
        if (isinstance(error, broker.RequestSocketError)
            and error.errno in (broker.SocketConnResetErrno(),
                                broker.SocketConnRefusedErrno())):
          # RequestSocketError for connection resets and refusals special cases
          # that doesn't raise.
          b.Shutdown()
        else:
          with self.assertRaises(broker.BrokerError):
            b.Shutdown()

  def testCreateEmulator_WhenRequestErrorsRaised(self):
    b = broker.Broker('host:1234', broker_dir='dir')
    with mock.patch.object(b, 'IsRunning', return_value=True):
      with mock.patch.object(b, '_SendJsonRequest') as send:
        for error in AllRequestErrors():
          send.side_effect = error
          with self.assertRaises(broker.RequestError):
            b.CreateEmulator('id', 'path', [], [])

  def testGetEmulator_WhenRequestErrorsRaised(self):
    b = broker.Broker('host:1234', broker_dir='dir')
    with mock.patch.object(b, 'IsRunning', return_value=True):
      with mock.patch.object(b, '_SendJsonRequest') as send:
        for error in AllRequestErrors():
          send.side_effect = error
          with self.assertRaises(broker.RequestError):
            b.GetEmulator('id')

  def testListEmulators_WhenRequestErrorsRaised(self):
    b = broker.Broker('host:1234', broker_dir='dir')
    with mock.patch.object(b, 'IsRunning', return_value=True):
      with mock.patch.object(b, '_SendJsonRequest') as send:
        for error in AllRequestErrors():
          send.side_effect = error
          with self.assertRaises(broker.RequestError):
            b.GetEmulator('id')

  def testStartEmulator_WhenRequestErrorsRaised(self):
    b = broker.Broker('host:1234', broker_dir='dir')
    with mock.patch.object(b, 'IsRunning', return_value=True):
      with mock.patch.object(b, '_SendJsonRequest') as send:
        for error in AllRequestErrors():
          send.side_effect = error
          with self.assertRaises(broker.RequestError):
            b.StartEmulator('id')

  def testStopEmulator_WhenRequestErrorsRaised(self):
    b = broker.Broker('host:1234', broker_dir='dir')
    with mock.patch.object(b, 'IsRunning', return_value=True):
      with mock.patch.object(b, '_SendJsonRequest') as send:
        for error in AllRequestErrors():
          send.side_effect = error
          with self.assertRaises(broker.RequestError):
            b.StopEmulator('id')


if __name__ == '__main__':
  test_case.main()
