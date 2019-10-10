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

"""Unit tests for the cloudbuild filter expression rewrite module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import filter_rewrite
from googlecloudsdk.core.util import times
from tests.lib import subtests
from tests.lib import test_case


class ContainerBuildsFilterRewriteTest(subtests.Base):

  def SetUp(self):
    self.rewrite = filter_rewrite.Backend().Rewrite
    now = times.ParseDateTime('2016-09-26T23:31:29-0400')
    self.StartObjectPatch(times, 'Now', side_effect=lambda tzinfo=None: now)

  def RunSubTest(self, expression):
    return self.rewrite(expression)

  def testResourceFilterBackend(self):

    def T(expected, expression, exception=None):
      self.Run(expected, expression, depth=2, exception=exception)

    T((None,
       None),
      '')

    T((None,
       'create_time<"2016-09-27T03:31:29.000Z"'),
      'createTime<2016-09-26T23:31:29-0400')
    T((None,
       'start_time<="2016-09-27T06:31:00.000Z"'),
      'startTime<=2016-09-26T23:31-0700')
    T((None,
       'finish_time="2016-09-26T00:00:00.000Z"'),
      'finishTime=2016-09-26T00:00Z')
    T((None,
       'create_time="2016-09-27T03:31:29.000Z"'),
      'createTime:2016-09-26T23:31:29-0400')
    T((None,
       'start_time>="2016-09-27T03:31:29.000Z"'),
      'startTime>=2016-09-26T23:31:29-0400')
    T((None,
       'finish_time>"2016-09-27T03:31:29.000Z"'),
      'finishTime>2016-09-26T23:31:29-0400')

    T((None,
       'create_time<"2015-09-27T03:31:29.000Z"'),
      'createTime<-P1Y')
    T((None,
       'start_time<="2016-09-13T03:31:29.000Z"'),
      'startTime<=-P14D')
    T((None,
       'finish_time>="2016-12-27T03:31:29.000Z"'),
      'finishTime>=P3M')
    T((None,
       'create_time>"2017-09-27T03:31:29.000Z"'),
      'createTime>P1Y')

    T((None,
       'start_time>="2016-09-27T03:21:29.000Z"'
       ' AND (status="WORKING" OR status="QUEUED")'),
      'startTime>=-PT10M AND status:(WORKING,QUEUED)')
    T((None,
       'finish_time<="2016-09-26T19:31:29.000Z"'
       ' AND NOT (status="WORKING" OR status="QUEUED")'),
      'finishTime<=-P8H AND -status:(WORKING,QUEUED)')
    T((None,
       'finish_time<="2016-09-26T19:31:29.000Z" AND status!="SUCCESS"'),
      'finishTime<=-P8H status!=SUCCESS')
    T((None,
       'finish_time<="2016-09-26T19:31:29.000Z" AND NOT status="SUCCESS"'),
      'finishTime<=-P8H NOT status=SUCCESS')
    T((None,
       'finish_time<="2016-09-26T19:31:29.000Z" AND NOT status="SUCCESS"'),
      'finishTime<=-P8H -status=SUCCESS')
    T(('finish_time<=-P8H status!=SUCCESS id:1234567890',
       'finish_time<="2016-09-26T19:31:29.000Z" AND status!="SUCCESS"'),
      'finish_time<=-P8H status!=SUCCESS id:1234567890')
    T(('finishTime<=-P8H -status:SUCCESS id:1234567890',
       'finish_time<="2016-09-26T19:31:29.000Z" AND NOT status="SUCCESS"'),
      'finishTime<=-P8H -status:SUCCESS id:1234567890')

    T(('status~FAIL',
       None),
      'status~FAIL')

    T((None,
       None),
      'create_time>=aint-nobody-got-time-for-this)',
      exception=ValueError)

    T((None, 'build_id="X"'),
      'buildId=X')
    T((None, 'images="X"'),
      'images=X')
    T((None, 'options.requested_verify_option="X"'),
      'options.requestedVerifyOption=X')
    T((None, 'project_id="X"'),
      'projectId=X')
    T((None, 'results.images.digest="X"'),
      'results.images.digest=X')
    T((None, 'results.images.name="X"'),
      'results.images.name=X')
    T((None, 'source_provenance.resolved_repo_source.commit_sha="X"'),
      'sourceProvenance.resolvedRepoSource.commitSha=X')
    T((None, 'source.repo_source.branch_name="X"'),
      'source.repoSource.branchName=X')
    T((None, 'source.repo_source.commit_sha="X"'),
      'source.repoSource.commitSha=X')
    T((None, 'source.repo_source.repo_name="X"'),
      'source.repoSource.repoName=X')
    T((None, 'source.repo_source.tag_name="X"'),
      'source.repoSource.tagName=X')
    T((None, 'source.storage_source.bucket="X"'),
      'source.storageSource.bucket=X')
    T((None, 'source.storage_source.object="X"'),
      'source.storageSource.object=X')
    T((None, 'status="X"'),
      'status=X')
    T((None, 'tags="X"'),
      'tags=X')
    T((None, 'trigger_id="X"'),
      'triggerId=X')

    T(('unknown.fieldName=X', None), 'unknown.fieldName=X')


class ContainerBuildsFilterRewriteTestWithOngoing(subtests.Base):

  def SetUp(self):
    self.rewrite = filter_rewrite.Backend(ongoing=True).Rewrite
    now = times.ParseDateTime('2016-09-26T23:31:29-0400')
    self.StartObjectPatch(times, 'Now', side_effect=lambda tzinfo=None: now)

  def RunSubTest(self, expression):
    return self.rewrite(expression)

  def testResourceFilterBackend(self):

    def T(expected, expression, exception=None):
      self.Run(expected, expression, depth=2, exception=exception)

    T((None,
       'status="WORKING" OR status="QUEUED"'),
      '')

    T((None,
       'create_time<"2016-09-27T03:31:29.000Z"'
       ' AND (status="WORKING" OR status="QUEUED")'),
      'createTime<2016-09-26T23:31:29-0400')
    T((None,
       'start_time<="2016-09-27T06:31:00.000Z"'
       ' AND (status="WORKING" OR status="QUEUED")'),
      'startTime<=2016-09-26T23:31-0700')
    T((None,
       'finish_time="2016-09-26T00:00:00.000Z"'
       ' AND (status="WORKING" OR status="QUEUED")'),
      'finishTime=2016-09-26T00:00Z')
    T((None,
       'create_time="2016-09-27T03:31:29.000Z"'
       ' AND (status="WORKING" OR status="QUEUED")'),
      'createTime:2016-09-26T23:31:29-0400')
    T((None,
       'start_time>="2016-09-27T03:31:29.000Z"'
       ' AND (status="WORKING" OR status="QUEUED")'),
      'startTime>=2016-09-26T23:31:29-0400')
    T((None,
       'finish_time>"2016-09-27T03:31:29.000Z"'
       ' AND (status="WORKING" OR status="QUEUED")'),
      'finishTime>2016-09-26T23:31:29-0400')

if __name__ == '__main__':
  test_case.main()
