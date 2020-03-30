# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Unit tests for template.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.regen import api_def
from tests.lib import test_case

import six


class ApisMapTemplateTest(test_case.Base):

  def testAPIDefRepr_DisableMTLS(self):
    api_definition = api_def.APIDef('fruits.orange.v1',
                                    'orange_v1_client.OrangeV1',
                                    'orange_v1_messages', True, False, '')

    expected_repr = ('APIDef("fruits.orange.v1", "orange_v1_client.OrangeV1", '
                     '"orange_v1_messages", True, False, "")')

    self.assertEqual(expected_repr, six.text_type(api_definition))

  def testAPIDefRepr_EnableMTLS(self):
    api_definition = api_def.APIDef('fruits.orange.v1',
                                    'orange_v1_client.OrangeV1',
                                    'orange_v1_messages', True, True, '')

    expected_repr = ('APIDef("fruits.orange.v1", "orange_v1_client.OrangeV1", '
                     '"orange_v1_messages", True, True, "")')

    self.assertEqual(expected_repr, six.text_type(api_definition))

  def testAPIDefRepr_EnableMTLS_OverrideEndpoint(self):
    api_definition = api_def.APIDef(
        'fruits.orange.v1', 'orange_v1_client.OrangeV1', 'orange_v1_messages',
        True, True, 'https://compute.mtls.googleapis.com/compute/v1/')

    expected_repr = (
        'APIDef("fruits.orange.v1", "orange_v1_client.OrangeV1", '
        '"orange_v1_messages", True, True, '
        '"https://compute.mtls.googleapis.com/compute/v1/")'
    )

    self.assertEqual(expected_repr, str(api_definition))


if __name__ == '__main__':
  test_case.main()
