# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Utilities for updating values on function code objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six


def set_func_code_location(func, filename=None, line_number=None):
  """Set the filename and line_number on a function's code object.

  Args:
    func: The function to set the location information on.
    filename: The filename to set.
    line_number: The line number to set.
  """
  if six.PY2:
    func.func_code = type(func.func_code)(
        func.func_code.co_argcount,
        func.func_code.co_nlocals,
        func.func_code.co_stacksize,
        func.func_code.co_flags,
        func.func_code.co_code,
        func.func_code.co_consts,
        func.func_code.co_names,
        func.func_code.co_varnames,
        filename or func.func_code.co_filename,
        func.func_code.co_name,
        line_number or func.func_code.co_firstlineno,
        func.func_code.co_lnotab,
        func.func_code.co_freevars,
        func.func_code.co_cellvars
    )
  else:
    func.__code__ = type(func.__code__)(
        func.__code__.co_argcount,
        func.__code__.co_kwonlyargcount,
        func.__code__.co_nlocals,
        func.__code__.co_stacksize,
        func.__code__.co_flags,
        func.__code__.co_code,
        func.__code__.co_consts,
        func.__code__.co_names,
        func.__code__.co_varnames,
        filename or func.__code__.co_filename,
        func.__code__.co_name,
        line_number or func.__code__.co_firstlineno,
        func.__code__.co_lnotab,
        func.__code__.co_freevars,
        func.__code__.co_cellvars
    )
