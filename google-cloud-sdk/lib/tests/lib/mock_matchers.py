# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Classes for matching arguments with which mocks were called."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re


class RegexMatcher(object):

  def __init__(self, regex):
    self._regex = regex

  def __eq__(self, other):
    return bool(re.match(self._regex, other))

  def __repr__(self):
    return self._regex


class TypeMatcher(object):
  """A matcher for matching based on the type of an object.
  """

  def __init__(self, klass):
    """Provide a klass to compare to.

    Args:
      klass: A class to match the type of.
    """
    if not issubclass(klass, object):
      raise TypeError("{} is not a new-style class".format(klass))
    self._c = klass

  def __eq__(self, o):
    return isinstance(o, self._c)

  def __ne__(self, o):
    return not self.__eq__(o)

  def __repr__(self):
    return "<TypeMatcher(%r)>" % self._c
