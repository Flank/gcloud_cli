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

"""Tests for genomics operations delete command."""

import textwrap
from googlecloudsdk.api_lib.genomics.exceptions import GenomicsError
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base


class CancelTest(base.GenomicsUnitTest):
  """Unit tests for genomics operations cancel command."""

  def expectGetRequest(self):
    self.mocked_client.operations.Get.Expect(
        request=self.messages.GenomicsOperationsGetRequest(
            name='operations/operation-name'),
        response=self.messages.Operation(name='operations/operation-name',
                                         done=False))

  def testOperationsCancel(self):
    self.WriteInput('y\n')
    self.expectGetRequest()
    self.mocked_client.operations.Cancel.Expect(
        request=self.messages.GenomicsOperationsCancelRequest(
            cancelOperationRequest=None,
            name='operations/operation-name'),
        response={})
    self.RunGenomics(['operations', 'cancel', 'operation-name'])

    # Check that the operation is emitted before the prompt
    self.AssertErrContains('done: false')
    self.AssertErrContains('name: operations/')
    self.AssertErrContains('This operation will be canceled')

    # Verify that the operation cancel message is emitted
    self.AssertErrContains('Canceled [operations/operation-name].')

  def testOperationsCancelWithOperationsPrefix(self):
    self.WriteInput('y\n')
    self.expectGetRequest()
    self.mocked_client.operations.Cancel.Expect(
        request=self.messages.GenomicsOperationsCancelRequest(
            cancelOperationRequest=None,
            name='operations/operation-name'),
        response={})
    self.RunGenomics(['operations', 'cancel', 'operations/operation-name'])

    # Check that the operation is emitted before the prompt
    self.AssertErrContains('done: false')
    self.AssertErrContains('name: operations/')
    self.AssertErrContains('This operation will be canceled')

    # Verify that the operation cancel message is emitted
    self.AssertErrContains('Canceled [operations/operation-name].')

  def testOperationsCancelAborted(self):
    self.WriteInput('n\n')
    self.expectGetRequest()
    with self.assertRaisesRegex(GenomicsError, 'Cancel aborted by user.'):
      self.RunGenomics(['operations', 'cancel', 'operation-name'])

    # Check that the operation is emitted before the prompt
    self.AssertErrContains('done: false')
    self.AssertErrContains('name: operations/')
    self.AssertErrContains('This operation will be canceled')

    # Verify that the operation cancel message is emitted
    self.AssertErrContains('Cancel aborted by user')

  def testOperationsCancelQuiet(self):
    self.expectGetRequest()
    self.mocked_client.operations.Cancel.Expect(
        request=self.messages.GenomicsOperationsCancelRequest(
            cancelOperationRequest=None,
            name='operations/operation-name'),
        response={})
    self.RunGenomics(['operations', 'cancel', 'operation-name'], ['--quiet'])

    # Verfiy that only the cancel is emitted (no prompting)
    self.AssertOutputEquals('')
    self.AssertErrEquals(textwrap.dedent("""\
      Canceled [operations/operation-name].
      """))

  def testOperationsCancelNotExists(self):
    self.expectGetRequest()
    self.mocked_client.operations.Cancel.Expect(
        request=self.messages.GenomicsOperationsCancelRequest(
            cancelOperationRequest=None,
            name='operations/operation-name'),
        exception=self.MakeHttpError(
            404, 'Operation not found: operations/operation-name'))
    with self.assertRaisesRegex(
        exceptions.HttpException,
        'Operation not found: operations/operation-name'):
      self.RunGenomics(['operations', 'cancel', 'operation-name'], ['--quiet'])


if __name__ == '__main__':
  test_case.main()
