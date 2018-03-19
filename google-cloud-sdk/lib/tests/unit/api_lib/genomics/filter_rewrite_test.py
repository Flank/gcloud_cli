# Copyright 2016 Google Inc. All Rights Reserved.
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

from googlecloudsdk.api_lib.genomics import filter_rewrite
from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.core.util import times
from tests.lib import subtests
from tests.lib import test_case


class GenomicsFilterRewriteTest(subtests.Base):

  def SetUp(self):
    self.rewrite = filter_rewrite.Backend().Rewrite
    now = times.ParseDateTime('2016-09-26T23:31:29-0400')
    self.StartObjectPatch(genomics_util, 'GetProjectId',
                          side_effect=lambda: 'genomics-test-project')
    self.StartObjectPatch(times, 'Now', side_effect=lambda tzinfo=None: now)

  def RunSubTest(self, expression):
    return self.rewrite(expression)

  def testResourceFilterBackend(self):

    def T(expected, expression, exception=None):
      self.Run(expected, expression, depth=2, exception=exception)

    T((None, 'projectId=genomics-test-project'),
      '')

    T((None, 'createTime <= 1474947088 AND projectId=genomics-test-project'),
      'createTime < 2016-09-26T23:31:29-0400')
    T((None, 'createTime <= 1474947089 AND projectId=genomics-test-project'),
      'createTime <= 2016-09-26T23:31:29-0400')
    T((None, 'createTime = 1474947089 AND projectId=genomics-test-project'),
      'createTime = 2016-09-26T23:31:29-0400')
    T((None, 'createTime = 1474947089 AND projectId=genomics-test-project'),
      'createTime:2016-09-26T23:31:29-0400')
    T((None, 'createTime >= 1474947089 AND projectId=genomics-test-project'),
      'createTime >= 2016-09-26T23:31:29-0400')
    T((None, 'createTime >= 1474947090 AND projectId=genomics-test-project'),
      'createTime > 2016-09-26T23:31:29-0400')

    T((None, 'createTime <= 1443324688 AND projectId=genomics-test-project'),
      'createTime<-P1Y')
    T((None, 'createTime <= 1473737489 AND projectId=genomics-test-project'),
      'createTime<=-P14D')
    T((None, 'createTime >= 1482809489 AND projectId=genomics-test-project'),
      'createTime>=P3M')
    T((None, 'createTime >= 1506483090 AND projectId=genomics-test-project'),
      'createTime>P1Y')

    T(('createTime>=2016-09-26T23:31:29-0400 AND status:RUNNING',
       'createTime >= 1474947089 AND projectId=genomics-test-project'),
      'createTime>=2016-09-26T23:31:29-0400 AND status:RUNNING')

    T(('createTime>=2016-09-26T23:31:29-0400 status:RUNNING',
       'createTime >= 1474947089 AND projectId=genomics-test-project'),
      'createTime>=2016-09-26T23:31:29-0400 status:RUNNING')

    T(('createTime!=P1Y', 'projectId=genomics-test-project'),
      'createTime!=P1Y')

    T((None, ''),
      'createTime >= aint-nobody-got-time-for-this',
      exception=times.DateTimeSyntaxError)


if __name__ == '__main__':
  test_case.main()
