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

"""Flags and helpers for the blueprints command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import util as functions_api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def AddLabelsFlag(parser):
  """Add --labels flag."""

  help_text = """\
Labels to apply to the deployment. Existing values are overwritten. To retain
the existing labels on a deployment, do not specify this flag.

Examples:

Update labels for an existing deployment:

  $ {command} --source="./blueprint" --labels="env=prod,team=finance" existing-deployment

Clear labels for an existing deployment:

  $ {command} --source="./blueprint" --labels="" existing-deployment

Add a label to an existing deployment:

  First, fetch the current labels using the `describe` command, then follow the
  preceding example for updating labels.
"""

  parser.add_argument(
      '--labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=help_text
  )


def AddAsyncFlag(parser):
  """Add --async flag."""
  base.ASYNC_FLAG.AddToParser(parser)


def AddSourceFlag(parser):
  """Add --source and related flags."""

  source_help_text = """\
Source of a blueprint. It can represent one of three locations:

- Local filesystem
- Google Cloud Storage bucket
- Git repository

Local files are uploaded to the storage bucket specified by `--stage-bucket`;
see that flag for more information.

When uploading local files, matches in the `.gcloudignore` file are skipped. For
more information, see `gcloud topic gcloudignore`. By default, `.git` and
`.gitignore` are ignored, meaning they are be uploaded with your blueprint.

Git repositories can either be a private Cloud Source Repositories (CSR)
repository (in which case you must have permission to access it) or a public Git
repository (e.g. on GitHub). Each takes the form `_URL_@_REF_`:
  * Example CSR `_URL_`: https://source.cloud.google.com/my-project/my-csr-repository
  * Example GitHub `_URL_`: https://github.com/google/repository
  * `@` is a literal `@` character. `_REF_` is a commit hash, branch, or tag.

For CSR repositories in the same project as the deployment, no extra permissions
need to be granted. For CSR repositories in separate projects, the 'Cloud Build'
service account must hold the `source.repos.get` permission. The role
`roles/source.reader` contains this permission. Here is an example of how to add
the role to project `project-with-csr-repository` for a project whose project
number is `1234`:

  $ gcloud projects add-iam-policy-binding project-with-csr-repository --member=serviceAccount:1234@cloudbuild.gserviceaccount.com --role=roles/source.reader

See `source-git-subdir` for how to specify a subdirectory within a Git
repository.

`--source` is interpreted as a storage bucket if it begins with `gs://`. It is
interpreted as a Git repository if it begins with `https://` (`http://` is not
allowed). If neither case is met, it is treated as a local path.

Examples:

Create a deployment from local files:

  $ {command} [...] new-deployment --source="./path/to/blueprint"

Create a deployment from a storage bucket:

  $ {command} [...] new-deployment --source="gs://my-bucket"

Update a deployment to use a GitHub repository:

  $ {command} [...] existing-deployment --source="https://github.com/google/repository@mainline"
"""

  stage_bucket_help_text = """\
Use in conjunction with `--source` to specify a destination storage bucket for
uploading local files.

If unspecified, the bucket defaults to `gs://PROJECT_NAME_blueprints`. Uploaded
content will appear in the `source` object under a name comprised of the
timestamp and a UUID. The final output destination looks like this:
`gs://_BUCKET_/source/1615850562.234312-044e784992744951b0cd71c0b011edce/`

Examples:

Create a deployment from local files and specify the staging bucket:

  $ {command} [...] new-deployment --source="./path/to/blueprint" --stage-bucket="gs://my-bucket"
"""

  source_git_subdir_help = """\
Use in conjunction with `--source` to specify which subdirectory to pull
blueprint contents from

This defaults to `./`, meaning the root of the specified given repository is
used.

Examples:

Create a deployment from the "blueprints/compute" folder:

  $ {command} [...] existing-deployment --source="https://github.com/google/repository"
    --source-git-subdir="blueprints/compute"
"""

  parser.add_argument(
      '--source',
      required=True,
      help=source_help_text
  )

  # If the "--source" flag represents a local directory, then "--stage-bucket"
  # can be specified. However, if it represents a Git repository, then
  # "--source-git-subdir" can be specified. Only one such argument should be
  # provided at a time.
  source_details = parser.add_mutually_exclusive_group()

  # Note: we cannot specify a default here since the default value we would WANT
  # to use is dynamic; it includes the project ID.
  source_details.add_argument(
      '--stage-bucket',
      help=stage_bucket_help_text,

      # This will ensure that "--stage-bucket" takes on the form
      # "gs://my-bucket/".
      type=functions_api_util.ValidateAndStandarizeBucketUriOrRaise,
  )

  source_details.add_argument(
      '--source-git-subdir',
      help=source_git_subdir_help,
  )


def AddIgnoreFileFlag(parser, hidden=False):
  """Add --ignore-file flag."""
  parser.add_argument(
      '--ignore-file',
      hidden=hidden,
      help='Override the `.gcloudignore` file and use the specified file '
      'instead. See `gcloud topic gcloudignore` for more information.')
