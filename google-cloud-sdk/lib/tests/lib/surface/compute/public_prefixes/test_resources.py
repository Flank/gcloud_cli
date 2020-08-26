# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Resources that are shared by two or more tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'


def MakePublicAdvertisedPrefixes(msgs, api):
  """Creates a set of public advertised prefixes messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing public advertised prefixes.
  """
  prefix = _COMPUTE_PATH + '/' + api
  status_enum = msgs.PublicAdvertisedPrefix.StatusValueValuesEnum
  return [
      msgs.PublicAdvertisedPrefix(
          description='My PAP 1',
          kind='compute#publicAdvertisedPrefix',
          name='my-pap1',
          selfLink=(prefix + '/projects/my-project/'
                    'publicAdvertisedPrefixes/my-pap1'),
          ipCidrRange='1.2.3.0/24',
          dnsVerificationIp='1.2.3.4',
          sharedSecret='vader is luke\'s father',
          status=status_enum.VALIDATED),
      msgs.PublicAdvertisedPrefix(
          description='My PAP number two',
          kind='compute#publicAdvertisedPrefix',
          name='my-pap2',
          selfLink=(prefix + '/projects/my-project/'
                    'publicAdvertisedPrefixes/my-pap2'),
          ipCidrRange='100.66.0.0/16',
          dnsVerificationIp='100.66.20.1',
          sharedSecret='longsecretisbestsecret',
          status=status_enum.PTR_CONFIGURED),
  ]


PUBLIC_ADVERTISED_PREFIXES_ALPHA = MakePublicAdvertisedPrefixes(
    alpha_messages, 'alpha')


def MakePublicDelegatedPrefixes(msgs, api):
  """Creates a set of public delegated prefixes messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing public delegated prefixes.
  """
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.PublicDelegatedPrefix(
          description='My global PDP 1',
          fingerprint=b'1234',
          ipCidrRange='1.2.3.128/25',
          kind='compute#globalPublicDelegatedPrefix',
          name='my-pdp1',
          selfLink=(prefix + '/projects/my-project/global/'
                    'publicDelegatedPrefixes/my-pdp1'),
          parentPrefix=(prefix + '/projects/my-project/global/'
                        'publicAdvertisedPrefixes/my-pap1')
      ),
      msgs.PublicDelegatedPrefix(
          description='My PDP 2',
          fingerprint=b'12345',
          ipCidrRange='1.2.3.12/30',
          kind='compute#publicDelegatedPrefix',
          name='my-pdp2',
          selfLink=(prefix + '/projects/my-project/regions/us-central1/'
                             'publicDelegatedPrefixes/my-pdp2'),
          parentPrefix=(prefix + '/projects/my-project/global/'
                                 'publicAdvertisedPrefixes/my-pap1')
      ),
      msgs.PublicDelegatedPrefix(
          description='My PDP 3',
          fingerprint=b'123456',
          ipCidrRange='1.2.3.40/30',
          kind='compute#publicDelegatedPrefix',
          name='my-pdp3',
          selfLink=(prefix + '/projects/my-project/regions/us-east1/'
                             'publicDelegatedPrefixes/my-pdp3'),
          parentPrefix=(prefix + '/projects/my-project/global/'
                                 'publicAdvertisedPrefixes/my-pap1')
      )
  ]


PUBLIC_DELEGATED_PREFIXES_ALPHA = MakePublicDelegatedPrefixes(
    alpha_messages, 'alpha')
