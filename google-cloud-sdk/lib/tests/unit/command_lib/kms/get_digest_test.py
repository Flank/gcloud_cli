# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Unit tests for third_party.py.googlecloudsdk.command_lib.kms.get_digest."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import hashlib
import os

from googlecloudsdk.command_lib.kms import get_digest
from tests.lib import test_case
from tests.lib.surface.kms import base


class GetDigestTest(base.KmsMockTest):

  def SetUp(self):
    # The file size should be larger than the get_digest _READ_SIZE, so that the
    # chunked reads are exercised.
    #
    # http://google3/third_party/py/googlecloudsdk/command_lib/kms/get_digest.py?q=symbol:_READ_SIZE
    file_size = 4 * get_digest._READ_SIZE

    # Increase the size limit to accommodate the large file + a bit of
    # filesystem overhead.
    self._dirs_size_limit_method = file_size + 1024

    self.contents = os.urandom(file_size)
    self.file_path = self.Touch(self.temp_path, contents=self.contents)

  def testGetDigestSha256(self):
    digest = get_digest.GetDigest('sha256', self.file_path)
    self.assertEquals(digest.sha256, hashlib.sha256(self.contents).digest())

  def testGetDigestSha384(self):
    digest = get_digest.GetDigest('sha384', self.file_path)
    self.assertEquals(digest.sha384, hashlib.sha384(self.contents).digest())

  def testGetDigestSha512(self):
    digest = get_digest.GetDigest('sha512', self.file_path)
    self.assertEquals(digest.sha512, hashlib.sha512(self.contents).digest())


if __name__ == '__main__':
  test_case.main()
