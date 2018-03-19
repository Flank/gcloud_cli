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

"""Test session test base."""


from tests.lib import sdk_test_base
from tests.lib import session_test_base


class TestSessionTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self._http_mock = session_test_base.SessionHttpMock(self)

  def testBatchRequestsWithNonDeterministicOrdering(self):
    base_headers = [
        'Header: value',
        'Content-Type: application/json;',
    ]
    headers = [
        '\n'.join(['GET /uri/1 HTTP/1.1'] + base_headers + ['Unique1: Value1']),
        '\n'.join(['GET /uri/2 HTTP/1.1'] + base_headers + ['Unique2: Value2']),
    ]
    base_headers = '\n'.join(base_headers)
    boundary = '--===============boundary=='
    request_headers = {
        'RequestHeader1': 'value1',
        'content-type': 'multipart/mixed; boundary="{}"'.format(boundary[2:]),
    }
    content = [
        'unique content 1',
        'unique content 2',
    ]

    def _GetRequest(headers, content):
      return '\n\n'.join([
          boundary + '\n' + base_headers, headers[0], content[0],
          boundary + '\n' + base_headers, headers[1], content[1],
          boundary + '--'
      ])

    request_1 = _GetRequest(headers, content)
    headers.reverse()
    content.reverse()
    request_2 = _GetRequest(headers, content)
    result_1 = self._http_mock._SplitBatchRequest(
        'http://foo.bar', 'GET', request_1, request_headers)
    result_2 = self._http_mock._SplitBatchRequest(
        'http://foo.bar', 'GET', request_2, request_headers)
    self.assertEquals(len(result_1), 2)
    self.assertEquals(len(result_2), 2)
    for r1, r2 in zip(result_1, result_2):
      self.assertEquals(r1[0].strip(), base_headers)
      self.assertEquals(r2[0].strip(), base_headers)
      r1[1].AssertSessionEquals(r2[1])
      r2[1].AssertSessionEquals(r1[1])
      self.assertEquals(r1[2], r2[2])  # body


if __name__ == '__main__':
  sdk_test_base.main()
