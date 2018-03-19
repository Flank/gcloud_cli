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

import time
import urllib2

from googlecloudsdk.core import url_opener
from googlecloudsdk.core.updater import installers
from tests.lib.core.updater import util


class InstallersTest(util.Base):

  def SetUp(self):
    self.StartObjectPatch(time, 'sleep')

  def testRetryExceeded404(self):
    fake_url = 'https://google.com/junk'
    fake_error = urllib2.HTTPError(
        fake_url, code=404, msg='Not Found', hdrs={}, fp=None)
    urlopen_mock = self.StartObjectPatch(
        url_opener, 'urlopen', side_effect=fake_error)

    with self.assertRaisesRegexp(urllib2.HTTPError,
                                 'HTTP Error 404: Not Found'):
      installers.ComponentInstaller.MakeRequest(fake_url, command_path='junk')
    # Original request and 3 retries for 404 errors.
    self.assertEqual(4, urlopen_mock.call_count)

  def testRetry404(self):
    fake_url = 'https://google.com/junk'
    fake_error = urllib2.HTTPError(
        fake_url, code=404, msg='Not Found', hdrs={}, fp=None)
    request = object()
    urlopen_mock = self.StartObjectPatch(
        url_opener, 'urlopen', side_effect=[fake_error, fake_error, request])

    result = installers.ComponentInstaller.MakeRequest(
        fake_url, command_path='junk')
    self.assertEqual(result, request)
    self.assertEqual(3, urlopen_mock.call_count)

  def testNoRetry403(self):
    fake_url = 'https://google.com/junk'
    fake_error = urllib2.HTTPError(
        fake_url, code=403, msg='Denied', hdrs={}, fp=None)
    urlopen_mock = self.StartObjectPatch(
        url_opener, 'urlopen', side_effect=fake_error)

    with self.assertRaisesRegexp(urllib2.HTTPError, 'HTTP Error 403: Denied'):
      installers.ComponentInstaller.MakeRequest(fake_url, command_path='junk')
    # No retry should occur for 403 errors.
    urlopen_mock.assert_called_once()

  def testNoRetryLocalFile(self):
    fake_url = self.URLFromFile(self.root_path, 'missing_file')
    # This still calls urlopen, but it lets us assert it how many times it was
    # called.
    urlopen_mock = self.StartObjectPatch(
        url_opener, 'urlopen', side_effect=url_opener.urlopen)

    # Local files don't get retried because there is no 404 error
    # Linux and windows return different error messages so wildcard the match.
    with self.assertRaisesRegexp(urllib2.URLError, r'urlopen error \[.+2\]'):
      installers.ComponentInstaller.MakeRequest(fake_url, command_path='junk')
    urlopen_mock.assert_called_once()

    # It works once the file exists.
    self.Touch(self.root_path, 'missing_file', 'contents')
    result = installers.ComponentInstaller.MakeRequest(
        fake_url, command_path='junk')
    self.assertEqual('contents', result.read())
    result.close()
