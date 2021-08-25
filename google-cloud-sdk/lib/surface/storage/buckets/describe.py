# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of buckets describe command for getting info on buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
class Describe(base.ListCommand):
  """Describes Cloud Storage buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      Describe a Cloud Storage bucket.
      """,
      'EXAMPLES':
          """

      Describe a Google Cloud Storage bucket named "my-bucket":

        $ *{command}* gs://my-bucket

      Desribe bucket with JSON formatting, only returning the "name" key:

        $ *{command}* gs://my-bucket --format=json(name)
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', help='Specifies URL of bucket to describe.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
