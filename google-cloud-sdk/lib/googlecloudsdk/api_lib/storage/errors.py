# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API interface for interacting with cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.core import exceptions as core_exceptions


class CloudApiError(core_exceptions.Error):
  pass


class GcsApiError(CloudApiError, api_exceptions.HttpException):
  pass


class NotFoundError(CloudApiError):
  """Error raised when the requested resource does not exist.

  Both GCS and S3 APIs should raise this same error if a resource
  does not exist so that the caller can handle the error in an API agnostic
  manner.
  """
  pass


class S3ApiError(CloudApiError):
  # TODO(b/169133490): Add docstring describing error and error_format.

  def __init__(self, error, error_format=None):
    super().__init__(str(error))
    self.error = error
    self.error_format = error_format

  def __eq__(self, other):
    return (str(self.error) == str(other.error) and
            self.error_format == other.error_format)


# Modified version of api_lib.util.exceptions.CatchHTTPErrorRaiseHTTPException
def catch_http_error_raise_gcs_api_error(format_str=None):
  """Decorator catches HttpError and returns GcsApiError with custom message.

  Args:
    format_str (str): A googlecloudsdk.api_lib.util.exceptions.HttpErrorPayload
        format string. Note that any properties that are accessed here are on
        the HttpErrorPayload object, not the object returned from the server.

  Returns:
    A decorator that catches apitools.HttpError and returns GcsApiError with a
        customizable error message.

  Example:
    @catch_http_error_raise_gcs_api_error('Error [{status_code}]')
    def some_func_that_might_throw_an_error():
      ...
  """

  def catch_http_error_raise_gcs_api_error_decorator(function):
    # Need to define a secondary wrapper to get an argument to the outer
    # decorator.
    def wrapper(*args, **kwargs):
      try:
        return function(*args, **kwargs)
      except apitools_exceptions.HttpError as error:
        gcs_error = GcsApiError(error, format_str)
        core_exceptions.reraise(gcs_error)
    return wrapper

  return catch_http_error_raise_gcs_api_error_decorator
