# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Test Data for all ml predict output formatting tests."""

from __future__ import unicode_literals
PREDICT_DICT_FORMAT_RESULT = (
    """\
      X Y
      1 2
      3 4
  """, [
      {
          'x': 1,
          'y': 2
      },
      {
          'x': 3,
          'y': 4
      },
  ]
)
PREDICT_DICT_LIST_FORMAT_RESULT = (
    """\
      X Y
      [1, 2] [2, 3]
      [3, 4] [4, 5]
  """, [
      {
          'x': [1, 2],
          'y': [2, 3]
      },
      {
          'x': [3, 4],
          'y': [4, 5]
      },
  ]
)

PREDICT_DICT_LIST_FLOAT_FORMAT_RESULT = (
    """\
      X Y
      [1, 2] [2, 3]
      [3, 4] [4, 5]
  """, [
      {
          'x': [1, 2],
          'y': [2, 3]
      },
      {
          'x': [3, 4],
          'y': [4, 5]
      },
  ]
)

PREDICT_LIST_INT_FORMAT_RESULT = ('[1, 2, 3]\n', [1, 2, 3])
PREDICT_LIST_FLOAT_FORMAT_RESULT = ('[1.0, 2.0, -3.0]\n', [1.0, 2.0, -3.0])
PREDICT_IN_KEY_FORMAT_RESULT = (
    """\
      KEY  PREDICTIONS
      0    [0.1, 0.2, 0.3]
    """, [{'key': 0, 'predictions': [0.1, 0.2, 0.3]}]
)
PREDICT_SINGLE_VALUE_FORMAT_RESULT = ('{\n"predictions": 42\n}\n', 42)
