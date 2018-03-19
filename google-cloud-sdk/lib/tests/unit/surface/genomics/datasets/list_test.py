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

"""Tests for genomics datasets list command."""

import textwrap
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.genomics import base


class ListTest(base.GenomicsUnitTest):
  """Unit tests for genomics datasets list command."""

  def testDatasetsList(self):
    num_datasets = 10
    self.mocked_client.datasets.List.Expect(
        request=self.messages.GenomicsDatasetsListRequest(projectId=
                                                          self.Project(),),
        response=self.messages.ListDatasetsResponse(
            datasets=[self.messages.Dataset(id=str(1000 + i),
                                            name='dataset-name' + str(i))
                      for i in range(num_datasets)]))
    self.RunGenomics(
        ['datasets', 'list'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID    NAME
      1000  dataset-name0
      1001  dataset-name1
      1002  dataset-name2
      1003  dataset-name3
      1004  dataset-name4
      1005  dataset-name5
      1006  dataset-name6
      1007  dataset-name7
      1008  dataset-name8
      1009  dataset-name9
      """), normalize_space=True)

  def testDatasetsList_EmptyList(self):
    self.mocked_client.datasets.List.Expect(
        request=self.messages.GenomicsDatasetsListRequest(projectId=
                                                          self.Project(),),
        response=self.messages.ListDatasetsResponse())
    self.RunGenomics(
        ['datasets', 'list'])
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testDatasetsList_Limit_InvalidLow(self):
    limit = -1
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit: Value must be greater than or equal to 1; received: -1'):
      self.RunGenomics(
          ['datasets', 'list', '--limit', str(limit)])

  def testDatasetsList_Limit(self):
    num_datasets = 10
    limit = 5
    self.mocked_client.datasets.List.Expect(
        request=self.messages.GenomicsDatasetsListRequest(projectId=
                                                          self.Project(),
                                                          pageSize=limit,),
        response=self.messages.ListDatasetsResponse(
            datasets=[self.messages.Dataset(id=str(1000 + i),
                                            name='dataset-name' + str(i))
                      for i in range(num_datasets)]))
    self.RunGenomics(
        ['datasets', 'list', '--limit', str(limit)])
    self.AssertOutputEquals(textwrap.dedent("""\
      ID    NAME
      1000  dataset-name0
      1001  dataset-name1
      1002  dataset-name2
      1003  dataset-name3
      1004  dataset-name4
      """), normalize_space=True)

  def testInaccessibleProject(self):
    self.mocked_client.datasets.List.Expect(
        request=self.messages.GenomicsDatasetsListRequest(projectId=
                                                          'secret-project',),
        exception=http_error.MakeHttpError(
            403, 'Permission denied; need GET permission'))

    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied; need GET permission'):
      self.RunGenomics(['datasets', 'list', '--project', 'secret-project'])

if __name__ == '__main__':
  test_case.main()
