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

"""ml products catalogs import tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.ml.products import base


class ImportTest(base.MlProductsTestBase):
  """ml products catalogs import command tests."""

  def SetUp(self):
    self.import_success = self.test_resources.GetImportOperationResponse()
    self.StartPatch('time.sleep')

  def testImport(self):
    import_response = self.test_resources.GetTestOperation('import')
    imported_images_response = self.test_resources.GetImportOperationResponse()
    import_response.response = imported_images_response

    import_config = (
        self.messages.GoogleCloudVisionV1alpha1ImportCatalogsInputConfig(
            gcsSource=self.client.import_catalog_src(
                csvFileUri='gs://fake-bucket/catalog.csv')))
    self.mock_client.productSearch_catalogs.Import.Expect(
        self.messages.GoogleCloudVisionV1alpha1ImportCatalogsRequest(
            inputConfig=import_config),
        import_response)
    op_result = self.test_resources.ExpectLongRunningOpResult(
        'operations/import', poll_count=3,
        response_value=self.import_success)

    self.RunProductsCommand(
        'catalogs', 'import gs://fake-bucket/catalog.csv')

    self.assertEqual(op_result.response, self.import_success)
    self.AssertOutputContains('type.googleapis.com/google.cloud.alpha_vision.'
                              'v1alpha1.'
                              'GoogleCloudVisionV1alpha1ImportCatalogsResponse')


if __name__ == '__main__':
  test_case.main()
