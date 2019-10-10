# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Tests for core url_opener."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core import url_opener
from googlecloudsdk.core.util import files as file_utils
from tests.lib import test_case

import httplib2
import mock
import six


class UrlOpenerTest(test_case.Base):

  def SetUp(self):
    self.connection_handler = url_opener.HttplibConnectionHandler()
    self.do_open_mock = self.StartObjectPatch(self.connection_handler,
                                              'do_open')

  def testHttplibConnectionHandler_HTTP(self):
    self.connection_handler.http_open('test_req')

    ((build_function, req), _) = self.do_open_mock.call_args
    self.assertEqual('test_req', req)
    connection = build_function('test_host™️', timeout=10)
    self.assertTrue(isinstance(connection, httplib2.HTTPConnectionWithTimeout))
    self.assertEqual('test_hosttm', connection.host)
    self.assertEqual(10, connection.timeout)

  def testHttplibConnectionHandler_HTTPS(self):
    self.connection_handler.https_open('test_req')

    ((build_function, req), _) = self.do_open_mock.call_args
    self.assertEqual('test_req', req)
    connection = build_function('test_host™️', timeout=10)
    self.assertTrue(isinstance(connection, httplib2.HTTPSConnectionWithTimeout))
    self.assertEqual('test_hosttm', connection.host)
    self.assertEqual(10, connection.timeout)

  def testHttplibConnectionHandler_CACert(self):
    with file_utils.TemporaryDirectory() as tmp_dir:
      ca_cert_path = self.Touch(tmp_dir)
      properties.VALUES.core.custom_ca_certs_file.Set(ca_cert_path)
      self.connection_handler.https_open('test_req™️')
      ((build_function, _), _) = self.do_open_mock.call_args
      if six.PY3:
        with mock.patch('ssl.SSLContext'):
          connection = build_function('test_host™️', timeout=10)
      else:
        connection = build_function('test_host™️', timeout=10)
    self.assertTrue(isinstance(connection, httplib2.HTTPSConnectionWithTimeout))
    self.assertEqual('test_hosttm', connection.host)
    self.assertEqual(10, connection.timeout)


if __name__ == '__main__':
  test_case.main()
