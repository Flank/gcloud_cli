# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Fetch the IAM policy for an authority."""

from googlecloudsdk.api_lib.container.binauthz import iam
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags


class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for an authority.

  Returns an empty policy if the resource does not have an existing IAM policy
  set.

  ## EXAMPLES

  The following command gets the IAM policy for the authority `my_authority`:

    $ {command} my_authority
  """

  @staticmethod
  def Args(parser):
    flags.AddConcepts(
        parser,
        flags.GetAuthorityPresentationSpec(
            positional=True,
            group_help='The authority whose IAM policy will be fetched.',
        ),
    )

  def Run(self, args):
    authority_ref = args.CONCEPTS.authority.Parse()
    return iam.Client().Get(authority_ref)
