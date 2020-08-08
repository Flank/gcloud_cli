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
"""Tests for googlecloudsdk.unit.api_lib.logging.tailing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from tests.lib import test_case
import mock


def OnlyWithGrpc(func):
  def Wrapped(*args, **kwargs):
    try:
      # pylint: disable=g-import-not-at-top,unused-import
      import grpc
      from googlecloudsdk.api_lib.logging import tailing
      from googlecloudsdk.third_party.logging_v2.proto import log_entry_pb2
      from googlecloudsdk.third_party.logging_v2.proto import logging_pb2
      # pylint: enable=g-import-not-at-top,unused-import
      return func(*args, **kwargs)
    except ImportError:
      return
  return Wrapped


@OnlyWithGrpc
def _EntryWithId(insert_id):
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.third_party.logging_v2.proto import log_entry_pb2
  # pylint: enable=g-import-not-at-top
  entry = log_entry_pb2.LogEntry()
  entry.insert_id = insert_id
  return entry


@OnlyWithGrpc
def _ResponseWithEntries(entries):
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.third_party.logging_v2.proto import logging_pb2
  # pylint: enable=g-import-not-at-top
  response = logging_pb2.TailLogEntriesResponse()
  for entry in entries:
    response.entries.append(entry)
  return response


@OnlyWithGrpc
def _ResponseWithSuppression(rate_limited=0, not_consumed=0):
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.third_party.logging_v2.proto import logging_pb2
  # pylint: enable=g-import-not-at-top
  response = logging_pb2.TailLogEntriesResponse()
  if rate_limited:
    response.suppression_info.add(
        reason=logging_pb2.TailLogEntriesResponse.SuppressionInfo.Reason
        .RATE_LIMIT,
        suppressed_count=rate_limited)
  if not_consumed:
    response.suppression_info.add(
        reason=logging_pb2.TailLogEntriesResponse.SuppressionInfo.Reason
        .NOT_CONSUMED,
        suppressed_count=not_consumed)
  return response


class TailingTest(test_case.TestCase):

  def __init__(self, *args, **kwargs):
    super(TailingTest, self).__init__(*args, **kwargs)
    self._current_time = datetime.datetime(2000, 1, 1)
    self._warning_messages = []
    self._warning = self._warning_messages.append
    self._error_messages = []
    self._error = self._error_messages.append
    self._debug_messages = []
    self._debug = self._debug_messages.append
    self._kwargs = {
        'output_warning': self._warning,
        'output_error': self._error,
        'output_debug': self._debug,
        'get_now': self._get_now
    }

  def _get_now(self):
    return self._current_time

  def _advance_time_seconds(self, seconds):
    self._current_time += datetime.timedelta(seconds=seconds)

  @OnlyWithGrpc
  def testSendsCorrectRequest(self):
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.api_lib.logging import tailing
    from googlecloudsdk.third_party.logging_v2.proto import logging_pb2
    # pylint: enable=g-import-not-at-top
    tail_stub = mock.Mock()
    tail_stub.is_active = True

    def Recv():
      tail_stub.is_active = False
      return logging_pb2.TailLogEntriesResponse()

    tail_stub.recv.side_effect = Recv

    expected_resource_names = ['blah', 'blah2']
    expected_logs_filter = 'only cool logs'
    expected_buffer_window_seconds = 45
    for _ in tailing.TailLogs(
        tail_stub,
        expected_resource_names,
        expected_logs_filter,
        buffer_window_seconds=expected_buffer_window_seconds,
        **self._kwargs):
      pass

    tail_stub.send.assert_called_once()
    request = tail_stub.send.call_args[0][0]
    self.assertEqual(request.buffer_window.ToTimedelta().total_seconds(),
                     expected_buffer_window_seconds)
    self.assertCountEqual(request.resource_names, expected_resource_names)
    self.assertEqual(request.filter, expected_logs_filter)

  @OnlyWithGrpc
  def testOpensAndClosesStub(self):
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.api_lib.logging import tailing
    from googlecloudsdk.third_party.logging_v2.proto import logging_pb2
    # pylint: enable=g-import-not-at-top
    tail_stub = mock.Mock()
    tail_stub.is_active = True

    def Recv():
      tail_stub.is_active = False
      return logging_pb2.TailLogEntriesResponse()

    tail_stub.recv.side_effect = Recv
    for _ in tailing.TailLogs(tail_stub, ['projects/irrelevant'],
                              'textPayload:*', **self._kwargs):
      pass

    tail_stub.open.assert_called_once()
    tail_stub.close.assert_called_once()

  @OnlyWithGrpc
  def testYieldsEntriesFromStream(self):
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.api_lib.logging import tailing
    # pylint: enable=g-import-not-at-top
    expected_entries = [_EntryWithId(id) for id in 'abcdefgh']
    responses = [
        _ResponseWithEntries(expected_entries[:3]),
        _ResponseWithEntries(expected_entries[3:5]),
        _ResponseWithEntries(expected_entries[5:]),
    ]
    tail_stub = mock.Mock()
    tail_stub.is_active = True

    def Recv():
      Recv.responses_remaining -= 1
      if Recv.responses_remaining == 0:
        tail_stub.is_active = False
      return responses[Recv.responses_remaining]

    Recv.responses_remaining = len(responses)
    tail_stub.recv.side_effect = Recv

    entries = list(
        entry
        for entry in tailing.TailLogs(tail_stub, ['projects/fake-resource'],
                                      'filterstring', **self._kwargs))
    self.assertCountEqual(entries, expected_entries)

  @OnlyWithGrpc
  def testPeriodicallyWarnsAboutSuppression(self):
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.api_lib.logging import tailing
    # pylint: enable=g-import-not-at-top
    responses = [
        _ResponseWithSuppression(rate_limited=5),
        _ResponseWithSuppression(not_consumed=8),
        _ResponseWithSuppression(rate_limited=8, not_consumed=11),
        _ResponseWithSuppression(rate_limited=5),
        _ResponseWithSuppression(rate_limited=5),
        _ResponseWithSuppression(rate_limited=8),
    ]
    elapsed_seconds = [4, 4, 4, 0, 0, 3]
    tail_stub = mock.Mock()
    tail_stub.is_active = True

    def Recv():
      self._advance_time_seconds(elapsed_seconds[Recv.i])
      Recv.i += 1
      if Recv.i == len(responses):
        tail_stub.is_active = False
      return responses[Recv.i - 1]

    Recv.i = 0
    tail_stub.recv.side_effect = Recv

    for _ in tailing.TailLogs(tail_stub, ['projects/irrelevant'],
                              'textPayload:*', **self._kwargs):
      pass

    rate_limited_messages = 3
    # Expect that the final three rate limited messages are all combined.
    not_consumed_messages = 2
    self.assertEqual(
        len(self._error_messages),
        rate_limited_messages + not_consumed_messages)

  @OnlyWithGrpc
  def testFlushesFinalSuppressionCounts(self):
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.api_lib.logging import tailing
    # pylint: enable=g-import-not-at-top
    responses = [
        _ResponseWithSuppression(rate_limited=5),
        _ResponseWithSuppression(not_consumed=8),
        _ResponseWithSuppression(rate_limited=8, not_consumed=11),
        _ResponseWithSuppression(rate_limited=5),
        _ResponseWithSuppression(rate_limited=5),
        _ResponseWithSuppression(rate_limited=8),
    ]
    elapsed_seconds = [4, 4, 4, 0, 0, 3]
    tail_stub = mock.Mock()
    tail_stub.is_active = True

    def Recv():
      self._advance_time_seconds(elapsed_seconds[Recv.i])
      Recv.i += 1
      if Recv.i == len(responses):
        tail_stub.is_active = False
      return responses[Recv.i - 1]

    Recv.i = 0
    tail_stub.recv.side_effect = Recv

    for _ in tailing.TailLogs(tail_stub, ['projects/irrelevant'],
                              'textPayload:*', **self._kwargs):
      pass

    # Expect just two cumulative messages at the end, one for each suppression
    # type received. Also expect the help message.
    expected_cumulative_count_messages = 2
    expected_help_messages = 1
    self.assertEqual(
        len(self._warning_messages),
        expected_cumulative_count_messages + expected_help_messages)

  @OnlyWithGrpc
  def testGracefullyHandlesOutOfRangeError(self):
    # pylint: disable=g-import-not-at-top
    import grpc
    from googlecloudsdk.api_lib.logging import tailing
    # pylint: enable=g-import-not-at-top
    tail_stub = mock.Mock()
    tail_stub.is_active = True

    def Recv():
      error = grpc.RpcError()
      error.code = lambda: grpc.StatusCode.OUT_OF_RANGE
      error.details = lambda: 'Did not work...'
      raise error

    tail_stub.recv.side_effect = Recv

    try:
      for _ in tailing.TailLogs(tail_stub, ['projects/irrelevant'],
                                'textPayload:*', **self._kwargs):
        pass
    except grpc.RpcError:
      self.fail()
    self.assertEqual(len(self._warning_messages), 1)
    self.assertEqual(len(self._debug_messages), 1)

  @OnlyWithGrpc
  def testGracefullyHandlesPermissionError(self):
    # pylint: disable=g-import-not-at-top
    import grpc
    from googlecloudsdk.api_lib.logging import tailing
    # pylint: enable=g-import-not-at-top
    tail_stub = mock.Mock()
    tail_stub.is_active = True

    def Recv():
      error = grpc.RpcError()
      error.code = lambda: grpc.StatusCode.PERMISSION_DENIED
      error.details = lambda: 'Did not work...'
      raise error

    tail_stub.recv.side_effect = Recv

    try:
      for _ in tailing.TailLogs(tail_stub, ['projects/irrelevant'],
                                'textPayload:*', **self._kwargs):
        pass
    except grpc.RpcError:
      self.fail()
    self.assertEqual(len(self._warning_messages), 1)
    self.assertEqual(len(self._debug_messages), 1)

  @OnlyWithGrpc
  def testGracefullyHandlesInvalidArgument(self):
    # pylint: disable=g-import-not-at-top
    import grpc
    from googlecloudsdk.api_lib.logging import tailing
    # pylint: enable=g-import-not-at-top
    tail_stub = mock.Mock()
    tail_stub.is_active = True

    def Recv():
      error = grpc.RpcError()
      error.code = lambda: grpc.StatusCode.INVALID_ARGUMENT
      error.details = lambda: 'Did not work...'
      raise error

    tail_stub.recv.side_effect = Recv

    try:
      for _ in tailing.TailLogs(tail_stub, ['projects/irrelevant'],
                                'textPayload:*', **self._kwargs):
        pass
    except grpc.RpcError:
      self.fail()
    self.assertEqual(len(self._warning_messages), 1)
    self.assertEqual(len(self._debug_messages), 1)


if __name__ == '__main__':
  test_case.main()
