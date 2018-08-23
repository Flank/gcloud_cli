# -*- coding: utf-8 -*- #
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
"""Tests that exercise build listing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class ListTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.StartObjectPatch(times, 'Now', return_value=times.ParseDateTime(
        '2016-05-26T00:05:00.000000Z'))
    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)

    properties.VALUES.core.project.Set('my-project')

    self.cloudbuild_v1_messages = core_apis.GetMessagesModule(
        'cloudbuild', 'v1')

    self._statuses = self.cloudbuild_v1_messages.Build.StatusValueValuesEnum

  def _Run(self, args):
    self.Run(['alpha']+args)

  def testNoBuilds(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageToken=None,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[],
        )
    )
    self._Run(['container', 'builds', 'list'])
    self.AssertErrContains('Listed 0 items.')

  def testSomeBuilds(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageToken=None,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    finishTime='2016-05-26T00:05:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    source=self.cloudbuild_v1_messages.Source(
                        repoSource=self.cloudbuild_v1_messages.RepoSource(
                            repoName='default',
                            branchName='master',
                        ),
                    ),
                    results=self.cloudbuild_v1_messages.Results(
                        images=[
                            self.cloudbuild_v1_messages.BuiltImage(
                                name='gcr.io/myproject/myimage-1'
                            ),
                            self.cloudbuild_v1_messages.BuiltImage(
                                name='gcr.io/myproject/myimage-2'
                            )
                        ]
                    ),
                    status=self._statuses.SUCCESS,
                ),
            ],
        )
    )
    self._Run(['container', 'builds', 'list'])
    self.AssertOutputContains("""\
ID CREATE_TIME DURATION SOURCE IMAGES STATUS
123-456-789  2016-05-26T00:00:00+00:00  4M59S default@master gcr.io/myproject/myimage-1 (+1 more) SUCCESS
""", normalize_space=True)

  def testURI(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageToken=None,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    projectId='my-project',
                    createTime='2016-05-26T00:00:00.000000Z',
                    finishTime='2016-05-26T00:05:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    status=self._statuses.SUCCESS,
                ),
            ],
        )
    )
    self._Run(['container', 'builds', 'list', '--uri'])
    self.AssertOutputContains("""\
https://cloudbuild.googleapis.com/v1/projects/my-project/builds/123-456-789
""", normalize_space=True)

  def testOngoing(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageToken=None,
            projectId='my-project',
            filter='status="WORKING" OR status="QUEUED"',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    status=self._statuses.WORKING,
                ),
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    status=self._statuses.QUEUED,
                ),
            ],
        )
    )
    self._Run(['container', 'builds', 'list', '--ongoing'])
    self.AssertOutputContains("""\
ID CREATE_TIME DURATION SOURCE IMAGES STATUS
123-456-789  2016-05-26T00:00:00+00:00  4M59S - - WORKING
123-456-789  2016-05-26T00:00:00+00:00  -     - - QUEUED
""", normalize_space=True)

  def testOngoingPageout(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageToken=None,
            projectId='my-project',
            filter='status="WORKING" OR status="QUEUED"',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    status=self._statuses.WORKING,
                ),
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    status=self._statuses.QUEUED,
                ),
            ],
            nextPageToken='123',
        )
    )
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageToken='123',
            projectId='my-project',
            filter='status="WORKING" OR status="QUEUED"',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-25T00:00:00.000000Z',
                    finishTime='2016-05-25T00:05:00.000000Z',
                    startTime='2016-05-25T00:00:01.000000Z',
                    status=self._statuses.WORKING,
                ),
            ],
            nextPageToken=None,
        )
    )
    # The next page is not fetched because one of the entries in the previous
    # page was too old.

    self._Run(['container', 'builds', 'list', '--ongoing'])
    self.AssertOutputContains("""\
ID CREATE_TIME DURATION SOURCE IMAGES STATUS
123-456-789  2016-05-26T00:00:00+00:00  4M59S - - WORKING
123-456-789  2016-05-26T00:00:00+00:00  -     - - QUEUED
123-456-789  2016-05-25T00:00:00+00:00  4M59S - - WORKING
""", normalize_space=True)

  def testListLimit(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageToken=None,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    finishTime='2016-05-26T00:05:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    status=self._statuses.SUCCESS,
                ),
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    status=self._statuses.WORKING,
                ),
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    status=self._statuses.QUEUED,
                ),
            ],
            nextPageToken='123',
        )
    )
    # The next page is not fetched because the limit has been reached.

    self._Run(['container', 'builds', 'list', '--limit=2'])
    self.AssertOutputContains("""\
ID CREATE_TIME DURATION SOURCE IMAGES STATUS
123-456-789  2016-05-26T00:00:00+00:00  4M59S - - SUCCESS
123-456-789  2016-05-26T00:00:00+00:00  4M59S - - WORKING
""", normalize_space=True)

  def testListPageSize(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageSize=1,
            pageToken=None,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    finishTime='2016-05-26T00:05:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    status=self._statuses.SUCCESS,
                ),
            ],
        )
    )
    # The next page is not fetched because the limit has been reached.
    self._Run(['container', 'builds', 'list', '--limit=1', '--page-size=1'])
    self.AssertOutputContains("""\
ID           CREATE_TIME                DURATION  SOURCE  IMAGES  STATUS
123-456-789  2016-05-26T00:00:00+00:00  4M59S     -       -       SUCCESS
""", normalize_space=True)

  def testListPageSizeTwoPages(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageSize=1,
            pageToken=None,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    status=self._statuses.QUEUED,
                ),
            ],
            nextPageToken='next-page-please',
        )
    )
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageSize=1,
            pageToken='next-page-please',
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='987-654-321',
                    createTime='2016-05-26T00:00:00.000000Z',
                    status=self._statuses.QUEUED,
                ),
            ],
        )
    )
    # The next page is fetched until the limit has been reached.
    self._Run(['container', 'builds', 'list', '--limit=2', '--page-size=1'])
    self.AssertOutputContains("""\
ID           CREATE_TIME                DURATION  SOURCE  IMAGES  STATUS
123-456-789  2016-05-26T00:00:00+00:00  -         -       -       QUEUED
ID           CREATE_TIME                DURATION  SOURCE  IMAGES  STATUS
987-654-321  2016-05-26T00:00:00+00:00  -         -       -       QUEUED
""", normalize_space=True)

  def testListPageSizeReturnsMoreThanRequested(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageSize=1,
            pageToken=None,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    createTime='2016-05-26T00:00:00.000000Z',
                    status=self._statuses.QUEUED,
                ),
                self.cloudbuild_v1_messages.Build(
                    id='987-654-321',
                    createTime='2016-05-26T00:00:00.000000Z',
                    status=self._statuses.QUEUED,
                ),
            ],
        )
    )
    # The next page is not fetched because the limit has been reached.
    # If the server responds with more builds than requested, only --page-size
    # will be shown.
    self._Run(['container', 'builds', 'list', '--limit=1', '--page-size=1'])
    self.AssertOutputContains("""\
ID           CREATE_TIME                DURATION  SOURCE  IMAGES  STATUS
123-456-789  2016-05-26T00:00:00+00:00  -         -       -       QUEUED
""", normalize_space=True)

if __name__ == '__main__':
  test_case.main()
