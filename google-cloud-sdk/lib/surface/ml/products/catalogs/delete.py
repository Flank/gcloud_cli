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
"""gcloud ml products catalogs delete command."""

from googlecloudsdk.api_lib.ml.products import product_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml.products import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a Cloud Product Search Catalog.


  This command deletes a Cloud Product Search Catalog.

  """

  @staticmethod
  def Args(parser):
    flags.AddCatalogResourceArg(parser, verb='to delete')

  def Run(self, args):
    catalog_ref = args.CONCEPTS.catalog.Parse()
    console_io.PromptContinue(
        'Catalog [{}] and all related ReferenceImages will be deleted.'.format(
            catalog_ref.Name()),
        cancel_on_no=True)
    api_client = product_util.ProductsClient()
    result = api_client.DeleteCatalog(catalog_ref.RelativeName())
    log.DeletedResource(catalog_ref.Name(), kind='Catalog')
    return result
