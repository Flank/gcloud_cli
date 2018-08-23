# -*- coding: utf-8 -*- #
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Tests for the grpc_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import types

from googlecloudsdk.core import grpc_util
from tests.lib import sdk_test_base
from tests.lib import test_case

import six

from google.bigtable.admin.v2 import table_pb2

if six.PY2:
  # TODO(b/78118402): gRPC support on Python 3.
  # This doesn't work on py3. We skip the import here just so tests can load
  # and be skipped without crashing.
  import grpc  # pylint: disable=g-import-not-at-top


@test_case.Filters.SkipOnPy3('Not yet py3 compatible', 'b/78118402')
class GrpcUtilTest(sdk_test_base.WithFakeAuth):

  def testMakeChannel(self):
    target = 'bigtableadmin.googleapis.com:443'
    channel = grpc_util.MakeSecureChannel(target)
    self.assertIsInstance(channel, grpc.Channel)
    del channel

  def testYieldFromList(self):

    class Request(object):

      def __init__(self, name):
        self.page_token = None
        self.name = name

    class Response(object):

      def __init__(self, items, next_page_token=None):
        self.items = items
        self.next_page_token = next_page_token

    expected = [
        table_pb2.Table(name='1'),
        table_pb2.Table(name='2'),
        table_pb2.Table(name='3'),
    ]

    def List(request):
      if request.page_token == 'there is more':
        return Response(items=expected[2:])
      if request.page_token is None:
        return Response(items=expected[0:2], next_page_token='there is more')
      raise Exception('Unexpected request')

    result = grpc_util.YieldFromList(List, Request('fish'), 'items')
    self.assertIsInstance(result, types.GeneratorType)
    self.assertEqual(expected, list(result))


if __name__ == '__main__':
  test_case.main()
