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
"""Implementation of sign url command for Cloud Storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import textwrap

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import sign_url_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core import properties


@functools.lru_cache(maxsize=None)
def _get_region_with_cache(scheme, bucket_name):
  api_client = api_factory.get_api(scheme)
  try:
    bucket_resource = api_client.get_bucket(bucket_name)
  except api_errors.CloudApiError:
    raise command_errors.Error(
        'Failed to auto-detect the region for {}. Please ensure you have'
        " storage.buckets.get permission on the bucket, or specify the bucket's"
        " region using the '--region' flag.".format(bucket_name),
    )
  return bucket_resource.location


def _get_region(args, resource):
  if args.region:
    return args.region

  if resource.storage_url.is_bucket():
    raise command_errors.Error(
        'Generating signed URLs for creating buckets requires a region to'
        ' be specified using the --region flag.'
    )

  return _get_region_with_cache(
      resource.storage_url.scheme, resource.storage_url.bucket_name
  )


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SignUrl(base.Command):
  """Generate a URL with embedded authentication that can be used by anyone."""

  detailed_help = {
      'DESCRIPTION': """
      *{command}* will generate a signed URL that embeds authentication data so
      the URL can be used by someone who does not have a Google account. Please
      see the [Signed URLs documentation](https://cloud.google.com/storage/docs/access-control/signed-urls)
      for background about signed URLs.

      Note, `{command}` does not support operations on sub-directories. For
      example, unless you have an object named `some-directory/` stored inside
      the bucket `some-bucket`, the following command returns an error:
      `{command} gs://some-bucket/some-directory/`.
      """,
      'EXAMPLES': """
      To create a signed url for downloading an object valid for 10 minutes:

        $ {command} gs://my-bucket/file.txt --duration=10m --private-key-file=key.json

      To create a signed url that will bill to my-billing-project:

        $ {command} gs://my-bucket/file.txt --query-params=userProject=my-billing-project --private-key-file=key.json

      To create a signed url without a private key, using a service account's
      credentials:

        $ {command} gs://my-bucket/file.txt --duration=10m --use-service-account

      To create a signed url, valid for one hour, for uploading a plain text
      file via HTTP PUT:

        $ {command} gs://my-bucket --http-verb=PUT --duration=1h --headers=content-type=text/plain --private-key-file=key.json
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='The URLs to be signed. May contain wildcards.')
    parser.add_argument(
        '--private-key-file',
        required=True,
        help=textwrap.dedent("""\
            The service account private key used to generate the cryptographic
            signature for the generated URL. Must be in PKCS12 or JSON format.
            If encrypted, will prompt for the passphrase used to protect the
            private key file (default ``notasecret'')."""),
    )
    parser.add_argument(
        '-d',
        '--duration',
        default=600,  # 10 minutes.
        type=arg_parsers.Duration(),
        help=textwrap.dedent(
            """\
            Specifies the duration that the signed url should be valid for,
            default duration is 1 hour. For example 10s for 10 seconds.
            See $ gcloud topic datetimes for information on duration formats.

            The max duration allowed is 7 days when PRIVATE_KEY_FILE is used."""
        ),
    )
    parser.add_argument(
        '--headers',
        default={},
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
        help=textwrap.dedent("""\
            Specifies the headers to be used in the signed request.
            Possible headers are listed in the XML API's documentation:
            https://cloud.google.com/storage/docs/xml-api/reference-headers#headers
            """),
    )
    parser.add_argument(
        '-m',
        '--http-verb',
        default='GET',
        help=textwrap.dedent("""\
            Specifies the HTTP verb to be authorized for use with the signed
            URL, default is GET. When using a signed URL to start
            a resumable upload session, you will need to specify the
            ``x-goog-resumable:start'' header in the request or else signature
            validation will fail."""),
    )
    parser.add_argument(
        '-p',
        '--private-key-password',
        help='Specifies the private key password instead of prompting.',
    )
    parser.add_argument(
        '--query-params',
        default={},
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
        help=textwrap.dedent("""\
            Specifies the query parameters to be used in the signed request.
            Possible query parameters are listed in the XML API's documentation:
            https://cloud.google.com/storage/docs/xml-api/reference-headers#query
            """),
    )
    parser.add_argument(
        '-r',
        '--region',
        help=textwrap.dedent("""\
            Specifies the region in which the resources for which you are
            creating signed URLs are stored.

            Default value is ``auto'' which will cause {command} to fetch the
            region for the resource. When auto-detecting the region, the current
            user's credentials, not the credentials from PRIVATE_KEY_FILE,
            are used to fetch the bucket's metadata."""),
    )

  def Run(self, args):
    client_id, key = sign_url_util.get_signing_information_from_file(
        args.private_key_file, args.private_key_password
    )

    # Signed URLs always hit the XML API, regardless of what API is preferred
    # for other operations.
    host = properties.VALUES.storage.gs_xml_endpoint_url.Get()

    for url_string in args.url:
      url = storage_url.storage_url_from_string(url_string)
      if wildcard_iterator.contains_wildcard(url_string):
        resources = wildcard_iterator.get_wildcard_iterator(url_string)
      else:
        resources = [resource_reference.UnknownResource(url)]

      for resource in resources:
        if resource.storage_url.is_bucket():
          path = '/{}'.format(resource.storage_url.bucket_name)
        else:
          path = '/{}/{}'.format(
              resource.storage_url.bucket_name, resource.storage_url.object_name
          )

        parameters = dict(args.query_params)
        if url.generation:
          parameters['generation'] = url.generation

        region = _get_region(args, resource)

        sign_url_util.get_signed_url(
            client_id=client_id,
            duration=args.duration,
            headers=args.headers,
            host=host,
            key=key,
            verb=args.http_verb,
            parameters=parameters,
            path=path,
            region=region,
        )

        sign_url_util.probe_access_to_resource(
            client_id=client_id,
            host=host,
            key=key,
            path=path,
            region=region,
            requested_headers=args.headers,
            requested_http_verb=args.http_verb,
            requested_parameters=parameters,
            requested_resource=resource,
        )
        # TODO(b/282927259): Yield output and format it correctly.
