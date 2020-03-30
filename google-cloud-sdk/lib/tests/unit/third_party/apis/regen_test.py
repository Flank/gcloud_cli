# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests to make sure that checked in apitools clients are uptodate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

import googlecloudsdk
from tests.lib import test_case
from tests.lib.tools import regen_base

# Project root directory.
_BASE_DIR = os.path.dirname(os.path.dirname(googlecloudsdk.__file__))
_CONFIG = os.path.join(
    _BASE_DIR, 'googlecloudsdk', 'third_party', 'regen_apis_config.yaml')


@test_case.Filters.DoNotRunOnPy3('b/138241113')
class ClientGenCliTest(test_case.TestCase):
  pass


regen_base.MakeTestsFrom(_BASE_DIR, _CONFIG, ClientGenCliTest)


if __name__ == '__main__':
  test_case.main()
