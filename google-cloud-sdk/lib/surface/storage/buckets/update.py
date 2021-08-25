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
"""Implementation of update command for updating bucket settings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base

_CORS_HELP_TEXT = """
Sets the Cross-Origin Resource Sharing (CORS) configuration on a bucket.
An example CORS JSON document looks like the following:

  [
    {
      "origin": ["http://origin1.example.com"],
      "responseHeader": ["Content-Type"],
      "method": ["GET"],
      "maxAgeSeconds": 3600
    }
  ]

For more information about supported endpoints for CORS, see
[Cloud Storage CORS support]
(https://cloud.google.com/storage/docs/cross-origin#server-side-support).
"""
_LABELS_HELP_TEXT = """
Sets the label configuration for the bucket. An example label JSON document
looks like the following:

  {
    "your_label_key": "your_label_value",
    "your_other_label_key": "your_other_label_value"
  }
"""
_LIFECYCLE_HELP_TEXT = """
Sets the lifecycle management configuration on a bucket. For example,
The following lifecycle management configuration JSON document
specifies that all objects in this bucket that are more than 365 days
old are deleted automatically:

  {
    "rule":
    [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
"""


@base.Hidden
class Update(base.Command):
  """Update bucket settings."""

  detailed_help = {
      'DESCRIPTION':
          """
      Update a bucket.
      """,
      'EXAMPLES':
          """

      The following command updates the retention period of a Cloud Storage
      bucket named "my-bucket" to one year and thirty-six minutes:

        $ {command} gs://my-bucket --retention 1y36m

      The following command clears the retention period of a bucket:

        $ {command} gs://my-bucket --clear-retention
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', type=str, help='The URL of the bucket to update.')
    parser.add_argument('--cors-file', help=_CORS_HELP_TEXT)
    parser.add_argument(
        '--default-storage-class',
        help='Sets the default storage class for the bucket.')
    parser.add_argument(
        '--default-encryption-key',
        help='Set the default KMS key for the bucket.')
    parser.add_argument(
        '--clear-default-encryption-key',
        action='store_true',
        help="Clears the bucket's default encryption key.")
    parser.add_argument('--labels-file', help=_LABELS_HELP_TEXT)
    parser.add_argument(
        '--update-labels',
        metavar='LABEL_KEYS_AND_VALUES',
        type=arg_parsers.ArgDict(),
        help='Add or update labels. Example:'
        ' --update-labels=key1=value1,key2=value2')
    parser.add_argument(
        '--remove-labels',
        metavar='LABEL_KEYS',
        type=arg_parsers.ArgList(),
        help='Remove labels by their key names.')
    parser.add_argument(
        '--clear-labels',
        action='store_true',
        help='Clear all labels associated with a bucket.')
    parser.add_argument('--lifecycle-file', help=_LIFECYCLE_HELP_TEXT)
    parser.add_argument(
        '--clear-lifecycle',
        action='store_true',
        help='Removes all lifecycle configuration for the bucket.')
    parser.add_argument(
        '--log-bucket',
        help='Enables usage logging of the bucket, outputting log files to the'
        " specified logging_bucket in this flag. Cloud Storage doesn't validate"
        ' the existence of the bucket receiving logs. In addition to enabling'
        ' logging on your bucket, you will also need to grant'
        ' cloud-storage-analytics@google.com write access to the log bucket.')
    parser.add_argument(
        '--clear-log-bucket',
        action='store_true',
        help="Clears logging bucket receiving the usage current bucket's data.")
    parser.add_argument(
        '--log-object-prefix',
        help='Specifies the object prefix for logging activity to the log'
        ' bucket. The default prefix is the bucket name. All read and write'
        ' activity to objects in the bucket will be logged for objects matching'
        ' the prefix.')
    parser.add_argument(
        '--clear-log-object-prefix',
        action='store_true',
        help='Clears prefix used to determine what usage data to send to'
        ' logging bucket.')
    parser.add_argument(
        '--requester-pays',
        action=arg_parsers.StoreTrueFalseAction,
        help='Allows you to configure a Cloud Storage bucket so that the'
        ' requester pays all costs related to accessing the bucket and its'
        ' objects.')
    parser.add_argument(
        '--retention',
        help='Minimum [retention period](https://cloud.google.com'
        '/storage/docs/bucket-lock#retention-periods)'
        ' for objects stored in the bucket, for example'
        ' ``--retention-period=1Y1M1D5S\'\'. Objects added to the bucket'
        ' cannot be deleted until they\'ve been stored for the specified'
        ' length of time. Default is no retention period. Only available'
        ' for Cloud Storage using the JSON API.')
    parser.add_argument(
        '--clear-retention',
        action='store_true',
        help='Clears the object retention period for a bucket.')
    parser.add_argument(
        '--lock-retention',
        action=arg_parsers.StoreTrueFalseAction,
        help='Locks an unlocked retention policy on the buckets. Caution: A'
        ' locked retention policy cannot be removed from a bucket or reduced in'
        ' duration. Once locked, deleting the bucket is the only way to'
        ' "remove" a retention policy.')
    parser.add_argument(
        '--default-event-based-hold',
        action=arg_parsers.StoreTrueFalseAction,
        help='Sets the default value for an event-based hold on the bucket.'
        ' By setting the default event-based hold on a bucket, newly-created'
        ' objects inherit that value as their event-based hold (it is not'
        ' applied retroactively).')
    parser.add_argument(
        '--versioning',
        action=arg_parsers.StoreTrueFalseAction,
        help='Allows you to configure a Cloud Storage bucket to keep old'
        ' versions of objects.')
    parser.add_argument(
        '--uniform-bucket-level-access',
        action=arg_parsers.StoreTrueFalseAction,
        help='Enables or disables [uniform bucket-level access]'
        '(https://cloud.google.com/storage/docs/bucket-policy-only)'
        ' for the buckets.')
    parser.add_argument(
        '--web-main-page-suffix',
        help='Cloud Storage allows you to configure a bucket to behave like a'
        ' static website. A subsequent GET bucket request through a custom'
        ' domain serves the specified "main" page instead of performing the'
        ' usual bucket listing.')
    parser.add_argument(
        '--web-error-page',
        help='Cloud Storage allows you to configure a bucket to behave like a'
        ' static website. A subsequent GET bucket request through a custom'
        ' domain for a non-existent object serves the specified error page'
        ' instead of the standard Cloud Storage error.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
