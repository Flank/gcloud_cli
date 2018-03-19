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
"""gcloud ml products catalogs list command."""

from googlecloudsdk.api_lib.ml.products import product_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml.products import util as products_command_util


class List(base.ListCommand):
  """List all Cloud Product Search Catalogs.

  This command list all Cloud Product Search Catalogs.

  {alpha_list_note}
  """

  detailed_help = {'alpha_list_note': products_command_util.ALPHA_LIST_NOTE}

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(products_command_util.CATALOG_LIST_FORMAT)

  def Run(self, args):
    api_client = product_util.ProductsClient()
    return api_client.ListCatalogs()

