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

"""Tests for genomics callsets create command."""

from tests.lib import test_case
from tests.lib.surface.genomics import base


class CreateTest(base.GenomicsUnitTest):
  """Unit tests for genomics callsets create command."""

  def testCallsetsCreate(self):
    request = self.messages.CallSet(name='callset-name', variantSetIds=['123'],)
    response = self.messages.CallSet(id='1000',
                                     name='callset-name',
                                     variantSetIds=['123'],)
    self.mocked_client.callsets.Create.Expect(
        request=request,
        response=response,
    )
    self.RunGenomics(['callsets', 'create', '--name', 'callset-name',
                      '--variant-set-id', '123'])
    self.AssertOutputEquals('')
    self.AssertErrEquals('Created call set [callset-name, id: 1000].\n')


if __name__ == '__main__':
  test_case.main()
