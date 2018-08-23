# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for api_lib.runtime_config.transforms."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import transforms
from tests.lib import test_case


class TransformsTest(test_case.TestCase):

  def testWaiterStatus(self):
    status = transforms.TransformWaiterStatus

    undef = 'UNDEFINED'
    self.assertEqual(undef, status('foobar', undefined=undef))
    self.assertEqual('WAITING', status({}))
    self.assertEqual('WAITING', status({'done': False}))
    self.assertEqual('SUCCESS', status({'done': True}))
    self.assertEqual('TIMEOUT', status({
        'done': True,
        'error': {
            'code': 4,
            'message': 'timeout'
        }
    }))
    self.assertEqual('FAILURE', status({
        'done': True,
        'error': {
            'code': 9,
            'message': 'something else'
        }
    }))


if __name__ == '__main__':
  test_case.main()
