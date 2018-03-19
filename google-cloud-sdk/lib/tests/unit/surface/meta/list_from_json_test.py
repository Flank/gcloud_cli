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
"""Tests for gcloud meta list-from-json."""

import json
import os
import sys

from googlecloudsdk.calliope import exceptions
from tests.lib import cli_test_base


RESOURCES = [
    {
        'creationTimestamp': '2015-07-23T15:15:53.851-07:00',
        'id': '1234567890',
        'kind': 'compute#instance',
        'labels': {
            'env': 'prod',
            'tier': 'backend'
        },
        'machineType': 'n1-standard-2',
        'name': 'test-windows',
        'status': 'RUNNING',
        'tags': {
            'fingerprint': '123456789abcdef='
        },
        'zone': 'us-central2-a'
    },
    {
        'creationTimestamp': '2015-07-24T14:01:05.376-07:00',
        'id': '2345678901',
        'kind': 'compute#instance',
        'labels': {
            'env': 'dev',
            'tier': 'backend'
        },
        'machineType': 'n1-standard-1',
        'name': 'test-unix',
        'status': 'CRAWLING',
        'tags': {
            'fingerprint': 'f123456789abcde='
        },
        'zone': 'asia-east1-a'
    },
    {
        'id': '3456789012',
        'kind': 'compute#instance',
        'labels': {
            'env': 'test',
            'tier': 'frontend'
        },
        'machineType': 'n2-standard-1',
        'name': 'test-mac',
        'status': 'STOPPED',
        'tags': {
            'fingerprint': 'ef123456789abcd='
        },
        'zone': 'asia-east1-a'
    }
]


class ListFromJsonTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.json_file = os.path.join(self.temp_path, 'test.json')
    with open(self.json_file, 'w') as f:
      json.dump(RESOURCES, f)

  def testListFromJson(self):
    self.Run(['meta', 'list-from-json', self.json_file])
    expected = """\
[
  {
    "creationTimestamp": "2015-07-23T15:15:53.851-07:00",
    "id": "1234567890",
    "kind": "compute#instance",
    "labels": {
      "env": "prod",
      "tier": "backend"
    },
    "machineType": "n1-standard-2",
    "name": "test-windows",
    "status": "RUNNING",
    "tags": {
      "fingerprint": "123456789abcdef="
    },
    "zone": "us-central2-a"
  },
  {
    "creationTimestamp": "2015-07-24T14:01:05.376-07:00",
    "id": "2345678901",
    "kind": "compute#instance",
    "labels": {
      "env": "dev",
      "tier": "backend"
    },
    "machineType": "n1-standard-1",
    "name": "test-unix",
    "status": "CRAWLING",
    "tags": {
      "fingerprint": "f123456789abcde="
    },
    "zone": "asia-east1-a"
  },
  {
    "id": "3456789012",
    "kind": "compute#instance",
    "labels": {
      "env": "test",
      "tier": "frontend"
    },
    "machineType": "n2-standard-1",
    "name": "test-mac",
    "status": "STOPPED",
    "tags": {
      "fingerprint": "ef123456789abcd="
    },
    "zone": "asia-east1-a"
  }
]
"""
    self.AssertOutputEquals(expected)

  def testListFromJsonFilter(self):
    self.Run(['meta', 'list-from-json', self.json_file,
              '--filter=-name:test-windows AND machineType:n1-*',
             ])
    expected = """\
[
  {
    "creationTimestamp": "2015-07-24T14:01:05.376-07:00",
    "id": "2345678901",
    "kind": "compute#instance",
    "labels": {
      "env": "dev",
      "tier": "backend"
    },
    "machineType": "n1-standard-1",
    "name": "test-unix",
    "status": "CRAWLING",
    "tags": {
      "fingerprint": "f123456789abcde="
    },
    "zone": "asia-east1-a"
  }
]
"""
    self.AssertOutputEquals(expected)

  def testListFromJsonFormat(self):
    self.Run(['meta', 'list-from-json', self.json_file,
              '--format=table(name:sort=1, machineType)',
             ])
    expected = """\
NAME          MACHINE_TYPE
test-mac      n2-standard-1
test-unix     n1-standard-1
test-windows  n1-standard-2
"""
    self.AssertOutputEquals(expected)

  def testListFromJsonFilterFormat(self):
    self.Run(['meta', 'list-from-json', self.json_file,
              '--filter=-name:test-windows AND machineType:n1-*',
              '--format=table(name:sort=1, machineType)',
             ])
    expected = """\
NAME       MACHINE_TYPE
test-unix  n1-standard-1
"""
    self.AssertOutputEquals(expected)

  def testListFromJsonAggregate(self):
    self.Run(['meta', 'list-from-json', self.json_file,
              '--format=table(labels:format=json)',
             ])
    expected = """\
[
  {
    "env": "prod",
    "tier": "backend"
  },
  {
    "env": "dev",
    "tier": "backend"
  },
  {
    "env": "test",
    "tier": "frontend"
  }
]
"""
    self.AssertOutputEquals(expected)

  def testListFromJsonAggregateFormat(self):
    self.Run(['meta', 'list-from-json', self.json_file,
              '--format=table(labels:format="table(env, tier)")',
             ])
    expected = """\
ENV   TIER
prod  backend
dev   backend
test  frontend
"""
    self.AssertOutputEquals(expected)

  def testListFromJsonAggregateFormatStdin(self):
    try:
      sys_stdin = sys.stdin
      sys.stdin = open(self.json_file, 'r')
      self.Run(['meta', 'list-from-json',
                '--format=table(labels:format="table(env, tier)")'])
    finally:
      sys.stdin = sys_stdin

    expected = """\
ENV   TIER
prod  backend
dev   backend
test  frontend
"""
    self.AssertOutputEquals(expected)

  def testListFromJsonFileNotFound(self):
    with self.assertRaisesRegexp(
        exceptions.BadFileException,
        r'Cannot read \[unknown.unknown]:'):
      self.Run(['meta', 'list-from-json', 'unknown.unknown'])

  def testListFromJsonFileEmpty(self):
    with self.assertRaisesRegexp(
        exceptions.BadFileException,
        r'Cannot read \[.*]: No JSON object could be decoded'):
      self.Run(['meta', 'list-from-json', os.devnull])

  def testListFromJsonStdinEmpty(self):
    try:
      sys_stdin = sys.stdin
      sys.stdin = open(os.devnull, 'r')
      with self.assertRaisesRegexp(
          exceptions.BadFileException,
          'Cannot read the standard input: No JSON object could be decoded'):
        self.Run(['meta', 'list-from-json'])
    finally:
      sys.stdin = sys_stdin


class ListFromJsonTestResourceNotIterable(cli_test_base.CliTestBase):

  def SetUp(self):
    self.json_file = os.path.join(self.temp_path, 'test.json')
    with open(self.json_file, 'w') as f:
      json.dump(RESOURCES[0], f)

  def testListFromJsonFilterResourceNotIterable(self):
    self.Run(['meta', 'list-from-json', self.json_file,
              '--filter=name:test-windows',
             ])
    expected = """\
[
  {
    "creationTimestamp": "2015-07-23T15:15:53.851-07:00",
    "id": "1234567890",
    "kind": "compute#instance",
    "labels": {
      "env": "prod",
      "tier": "backend"
    },
    "machineType": "n1-standard-2",
    "name": "test-windows",
    "status": "RUNNING",
    "tags": {
      "fingerprint": "123456789abcdef="
    },
    "zone": "us-central2-a"
  }
]
"""
    self.AssertOutputEquals(expected)


if __name__ == '__main__':
  cli_test_base.main()
