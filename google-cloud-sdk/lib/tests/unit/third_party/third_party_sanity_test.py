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
"""Unit test to check sanity of grpc setup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import sdk_test_base
from tests.lib import test_case

has_grpc = False
try:
  import grpc  # pylint: disable=g-import-not-at-top,unused-import
  has_grpc = True
except ImportError:
  pass


class GrpcTest(test_case.TestCase):

  @test_case.Filters.RunOnlyIf(has_grpc, 'b/78118402')
  def testCanLoadExtension(self):
    # pylint: disable=g-import-not-at-top
    from grpc._cython import cygrpc
    # This code doesn't do much but makes sure the native extension is loaded.
    metadata = cygrpc.Operation()
    del metadata

  @sdk_test_base.Filters.RunOnlyWithBundledPython(
      'crcmod extension is only available in bundled Python.')
  def testCrcmodCompiledExtension(self):
    try:
      # pylint: disable=g-import-not-at-top,unused-import
      from crcmod import _crcfunext
    except ImportError as e:
      self.fail(e)


if __name__ == '__main__':
  test_case.main()


