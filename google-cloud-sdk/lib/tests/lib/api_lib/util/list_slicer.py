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

"""A utility for generate slices and page_tokens from a list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin


def _Pairs(iterable):
  return zip(iterable[:-1], iterable[1:])


def SliceList(full_list, page_size):
  slice_points = list(range(0, len(full_list), page_size)) + [None]
  slices = itertools.starmap(slice, _Pairs(slice_points))
  tokens = ['TOKEN{}'.format(s) if s else None for s in slice_points]
  token_pairs = _Pairs(tokens)
  return slices, token_pairs
