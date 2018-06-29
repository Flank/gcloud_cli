# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Testing resources for logging."""

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime

from apitools.base.py import extra_types

from googlecloudsdk.api_lib.util import apis as core_apis

MOCK_UTC_TIME = datetime.datetime(2015, 6, 30, 12)


def CreateLogEntry(payload, payload_type='text', severity='default'):
  """Create a log entry instance.

  Args:
    payload: payload of the log.
    payload_type: payload type, one of 'text' or 'struct'.
    severity: string representation of the log severity.

  Returns:
    Complete log entry instance.
  """
  msgs = core_apis.GetMessagesModule('logging', 'v2')
  severity_enum = getattr(msgs.LogEntry.SeverityValueValuesEnum,
                          severity.upper())

  entry = msgs.LogEntry(
      resource=msgs.MonitoredResource(type='global'),
      severity=severity_enum)

  if payload_type == 'struct':
    struct = msgs.LogEntry.JsonPayloadValue()
    struct.additionalProperties = [
        msgs.LogEntry.JsonPayloadValue.AdditionalProperty(
            key='message',
            value=extra_types.JsonValue(string_value=payload))
    ]
    entry.jsonPayload = struct
  else:
    entry.textPayload = payload
  return entry


# Class that provides a fixed date for datetime.datetime.utcnow().
class FakeDatetime(datetime.datetime):

  @classmethod
  def utcnow(cls):  # We cannot change the name, so pylint: disable=g-bad-name
    return MOCK_UTC_TIME
