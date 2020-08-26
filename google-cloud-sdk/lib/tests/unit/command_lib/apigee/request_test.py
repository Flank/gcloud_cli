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
"""Tests for googlecloudsdk.command_lib.apigee.request."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import re

from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.command_lib.apigee import request
from googlecloudsdk.core import properties
from tests.lib.surface.apigee import base


class RequestTest(base.ApigeeIsolatedTest):
  _sample_identifiers = {"environmentsId": "a", "apisId": "b"}

  def testCollection(self):
    test_data = {"what": ["a", "B", 3], "test": "testCollection"}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        body=json.dumps(test_data))
    response = request.ResponseToApiRequest(self._sample_identifiers,
                                            ["environment"], "api")
    self.assertEqual(test_data, response,
                     "Must receive the same data structure sent in response.")

  def testExactObject(self):
    test_data = {"what": ["a", "B", 3], "test": "testExactObject"}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis/b",
        body=json.dumps(test_data))
    response = request.ResponseToApiRequest(self._sample_identifiers,
                                            ["environment", "api"])
    self.assertEqual(test_data, response,
                     "Must receive the same data structure sent in response.")

  def testOtherResponseFormats(self):
    test_data = {"what": ["a", "B", 3], "test": "testOtherResponseFormats"}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        body=json.dumps(test_data)[3:],
        request_headers={"Accept": "application/json"})
    response = request.ResponseToApiRequest(
        self._sample_identifiers, ["environment"],
        "api",
        accept_mimetype="application/json")
    self.assertEqual(
        json.dumps(test_data)[3:], response,
        "Must receive the same binary data sent in response.")

  def testNonstandardEndpont(self):
    test_data = ["hello", "world"]
    properties.VALUES.api_endpoint_overrides.apigee.Set(
        "https://api.enterprise.apigee.com/")
    self.AddHTTPResponse(
        "https://api.enterprise.apigee.com/v1/organizations",
        body=json.dumps(test_data))
    response = request.ResponseToApiRequest({}, [], "organization")
    self.assertEqual(test_data, response)

  def testQueryParameters(self):
    test_data = {"what": ["a", "B", 3], "test": "testOtherResponseFormats"}
    params = {"verbose": "true", "another": "3"}
    param_values = {key: [params[key]] for key in params}

    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        expected_params=param_values,
        body=json.dumps(test_data))
    response = request.ResponseToApiRequest({"environmentsId": "a"},
                                            ["environment"],
                                            "api",
                                            query_params=params)
    self.assertEqual(test_data, response,
                     "Must receive the same data structure sent in response.")

  def testUnparseableResponse(self):
    test_data = {"what": ["a", "B", 3], "test": "testUnparseableResponse"}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        body=json.dumps(test_data)[3:])
    self.AssertRaisesExceptionMatches(errors.ResponseNotJSONError,
                                      "Failed to parse api",
                                      request.ResponseToApiRequest,
                                      self._sample_identifiers, ["environment"],
                                      "api")

  def testDetailedError(self):
    test_data = {
        "error": {
            "code": 400,
            "status": "INVALID_ARGUMENT",
            "details": [
                {
                    "@type":
                        "type.googleapis.com/edge.configstore.bundle.BadBundle",
                    "violations": [{
                        "description": "Error foo in somefile.xml",
                        "filename": "somefile.xml"
                    }, {
                        "description": "Bar violation in resource file blah",
                        "filename": "resources/java/blah.jar"
                    }]
                },
                {
                    "@type":
                        "type.googleapis.com/google.rpc.QuotaFailure",
                    "violations": [{
                        "description":
                            "Limit of Data Collectors used in a single "
                            "environment (100) exceeded.",
                        "subject": "apigee.googleapis.com/bling/blong"
                    }]
                },
            ],
            "message": "very generic error"
        }
    }
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        body=json.dumps(test_data),
        status=400)

    expected_text = ".*".join([
        "Error foo in somefile.xml", "Bar violation in resource file blah",
        r"Limit of Data Collectors used in a single environment \(100\)"
    ])
    expected_pattern = re.compile(expected_text, re.DOTALL)
    self.AssertRaisesExceptionRegexp(errors.RequestError, expected_pattern,
                                     request.ResponseToApiRequest,
                                     self._sample_identifiers, ["environment"],
                                     "api")

  def testUnparseableError(self):
    test_data = {"what": ["a", "B", 3], "test": "testUnparseableResponse"}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        status=404,
        body=json.dumps(test_data)[3:])
    self.AssertRaisesExceptionMatches(errors.EntityNotFoundError,
                                      "does not exist",
                                      request.ResponseToApiRequest,
                                      self._sample_identifiers, ["environment"],
                                      "api")

  def testForbiddenResource(self):
    test_data = {"what": ["a", "B", 3], "test": "testForbiddenResource"}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        body=json.dumps(test_data),
        status=401)
    self.AssertRaisesExceptionMatches(errors.UnauthorizedRequestError,
                                      "Insufficient privileges",
                                      request.ResponseToApiRequest,
                                      self._sample_identifiers, ["environment"],
                                      "api")

  def testMissingResource(self):
    test_data = {"what": ["a", "B", 3], "test": "testMissingResource"}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        body=json.dumps(test_data),
        status=404)
    self.AssertRaisesExceptionMatches(errors.EntityNotFoundError,
                                      "does not exist",
                                      request.ResponseToApiRequest,
                                      self._sample_identifiers, ["environment"],
                                      "api")

  def testMalfunctioningServer(self):
    test_data = {"what": ["a", "B", 3], "test": "testMalfunctioningServer"}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        body=json.dumps(test_data),
        status=500)
    self.AssertRaisesExceptionMatches(errors.RequestError, "Failed",
                                      request.ResponseToApiRequest,
                                      self._sample_identifiers, ["environment"],
                                      "api")

  def testMissingIdentifier(self):
    self.AssertRaisesExceptionMatches(errors.MissingIdentifierError,
                                      "Command requires a environment",
                                      request.ResponseToApiRequest,
                                      {"apisId": "b"}, ["environment"], "api")
    self.AssertRaisesExceptionMatches(errors.MissingIdentifierError,
                                      "Command requires a environment",
                                      request.ResponseToApiRequest,
                                      {"apisId": "b"}, ["environment", "api"])
    self.AssertRaisesExceptionMatches(errors.MissingIdentifierError,
                                      "Command requires a api",
                                      request.ResponseToApiRequest,
                                      {"environmentsId": "a"},
                                      ["environment", "api"])

  def testRequestBody(self):
    test_data = {"what": ["a", "B", 3], "test": "testRequestBody"}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/environments/a/apis",
        body=json.dumps(test_data),
        expected_body="abadede",
        request_headers={"Content-Type": "text/plain"})
    response = request.ResponseToApiRequest(
        self._sample_identifiers, ["environment"],
        "api",
        body="abadede",
        body_mimetype="text/plain")
    self.assertEqual(test_data, response,
                     "Must receive the same data structure sent in response.")
