# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Unit tests for the genomics filter expression rewrite module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.genomics import filter_rewrite
from googlecloudsdk.core.util import times
from tests.lib import subtests
from tests.lib import test_case


class GenomicsFilterRewriteTest(subtests.Base):

  def SetUp(self):
    self.rewrite = filter_rewrite.OperationsBackend().Rewrite
    now = times.ParseDateTime('2016-09-26T23:31:29.000Z')
    self.StartObjectPatch(times, 'Now', side_effect=lambda tzinfo=None: now)

  def RunSubTest(self, expression):
    return self.rewrite(expression)

  def testResourceFilterBackend(self):

    def T(expected, expression, exception=None):
      self.Run(expected, expression, depth=2, exception=exception)

    T((None, None), '')
    T(('error.message = "test"', None),
      'error.message = "test"')

    T((None, 'metadata.createTime <= "2016-09-26T23:31:29.000Z"'),
      'metadata.createTime <= 2016-09-26T23:31:29.000Z')
    T((None, 'metadata.createTime <= "2016-09-26T23:31:29.000Z"'),
      'metadata.createTime <= "2016-09-26T23:31:29.000Z"')
    T((('metadata.createTime > "2016-09-26T23:31:29.000Z"'
        ' AND error.message = ""'),
       'metadata.createTime > "2016-09-26T23:31:29.000Z"'),
      'metadata.createTime > "2016-09-26T23:31:29.000Z" AND error.message = ""')
    T((None, 'error.code = 9'),
      'error.code = 9')
    T((None,
       'metadata.createTime <= "2016-09-26T23:31:29.000Z" AND error.code = 9'),
      'metadata.createTime <= "2016-09-26T23:31:29.000Z" AND error.code = 9')
    T((None,
       'metadata.create_time <= "2016-09-26T23:31:29.000Z" AND error.code = 9'),
      'metadata.create_time <= "2016-09-26T23:31:29.000Z" AND error.code = 9')
    T((None, 'done = true'),
      'done = true')
    T((None, 'metadata.events : "WorkerReleasedEvent"'),
      'metadata.events : "WorkerReleasedEvent"')
    T((None, 'metadata.labels.key = "value"'),
      'metadata.labels.key = "value"')
    T((None, 'metadata.labels.key : "*"'),
      'metadata.labels.key:*')

    T((None, 'metadata.createTime < "2015-09-26T23:31:29.000Z"'),
      'metadata.createTime < -P1Y')

    T((None, ''),
      'metadata.createTime >= aint-nobody-got-time-for-this',
      exception=times.DateTimeSyntaxError)


if __name__ == '__main__':
  test_case.main()
