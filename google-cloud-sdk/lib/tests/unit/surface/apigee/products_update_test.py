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
"""Tests that exercise the 'gcloud apigee products update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_base
from tests.lib.surface.apigee import base


class ProductsUpdateTest(base.ApigeeSurfaceTest, base.WithJSONBodyValidation):

  def canned_product(self):
    return {
        "name": "updated-product",
        "displayName": "gCloud Test",
        "approvalType": "auto",
        "attributes": [{
            "name": "access",
            "value": "public",
        }, {
            "name": "cool-feature",
            "value": "cool-detail"
        }],
        "description": "Testing product creation",
        "apiResources": ["/gcloud-test1c", "/gcloud-test1"],
        "environments": ["prod", "test"],
        "quota": "7",
        "quotaInterval": "1",
        "quotaTimeUnit": "minute"
    }

  def _AddDummyGetResponse(self, data=None):
    if not data:
      data = self.canned_product()
    url = "https://apigee.googleapis.com/v1/organizations/test-org/apiproducts/"
    url += data["name"]
    self.AddHTTPResponse(url, body=json.dumps(data))

  def _AddDummyPutResponse(self, data=None):
    data = data or self.canned_product()
    url = "https://apigee.googleapis.com/v1/organizations/test-org/apiproducts/"
    url += data["name"]
    self.AddHTTPResponse(
        url,
        expected_body=e2e_base.IGNORE,
        expected_json_body=data,
        body=json.dumps(data),
        request_headers={"Content-Type": "application/json"})

  def _RunUpdate(self, command):
    return self.RunApigee("products update updated-product --format=json "
                          "--organization=test-org " + command)

  def testChangeNothing(self):
    self._AddDummyGetResponse()
    # With no changes specified on the command line, the API product should
    # remain exactly the same.
    self._AddDummyPutResponse()
    self._RunUpdate("")

  def testChangeEverythingToSame(self):
    self._AddDummyGetResponse()
    # The command line changes should put the product back the way it was.
    self._AddDummyPutResponse()
    self._RunUpdate("--remove-api=bogeyman --automatic-approval "
                    "--quota=7 --quota-interval=1 --quota-unit=minute "
                    "--add-environment=test --add-resource=/gcloud-test1 "
                    "--remove-resource=/gcloud-test1 --clear-oauth-scopes "
                    "--remove-environment=test --display-name='gCloud Test' "
                    "--add-attribute=cool-feature=cool-detail --public-access")

  def testModifyAttributes(self):
    canned_product = self.canned_product()
    canned_product["attributes"].append({"name": "fun", "value": "games"})
    self._AddDummyGetResponse(canned_product)
    canned_product["attributes"] = [
        {
            "name": "access",
            "value": "public"
        },
        {
            "name": "fun",
            "value": "james"
        },
        {
            "name": "new",
            "value": "adventure"
        },
    ]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--add-attribute=new=adventure,fun=james "
                    "--remove-attribute=cool-feature")

  def testClearAttributes(self):
    self._AddDummyGetResponse()
    canned_product = self.canned_product()
    canned_product["attributes"] = [canned_product["attributes"][0]]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--clear-attributes")

  def testInvalidAccessDeletion(self):
    self._AddDummyGetResponse()
    with self.assertRaises(exceptions.BadArgumentException):
      self._RunUpdate("--remove-attribute=access")

  def testInvalidAccessUpdate(self):
    self._AddDummyGetResponse()
    with self.assertRaises(exceptions.BadArgumentException):
      self._RunUpdate("--add-attribute=access=free")

  def testResourcesChange(self):
    self._AddDummyGetResponse()
    canned_product = self.canned_product()
    canned_product["apiResources"] = ["/gcloud-test%s" % idx for idx in "1234"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--add-resource='/gcloud-test2#/gcloud-test3' "
                    "--remove-resource=/gcloud-test1c "
                    "--add-resource=/gcloud-test4")

  def testResourcesClear(self):
    self._AddDummyGetResponse()
    canned_product = self.canned_product()
    del canned_product["apiResources"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--all-resources")

  def testResourcesCreate(self):
    canned_product = self.canned_product()
    del canned_product["apiResources"]
    self._AddDummyGetResponse(canned_product)
    canned_product["apiResources"] = ["/v0/larry", "/v0/bob"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--add-resource=/v0/larry --add-resource=/v0/bob")

  def testProxiesChange(self):
    canned_product = self.canned_product()
    canned_product["proxies"] = ["larry", "bob"]
    self._AddDummyGetResponse(canned_product)
    canned_product["proxies"] = ["larry", "jerry"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--add-api=jerry --remove-api=bob")

  def testProxiesClear(self):
    canned_product = self.canned_product()
    canned_product["proxies"] = ["larry", "bob"]
    self._AddDummyGetResponse(canned_product)
    self._AddDummyPutResponse()
    self._RunUpdate("--all-apis")

  def testProxiesCreate(self):
    self._AddDummyGetResponse()
    canned_product = self.canned_product()
    canned_product["proxies"] = ["larry", "bob"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--add-api=larry,bob")

  def testScopesChange(self):
    canned_product = self.canned_product()
    canned_product["scopes"] = ["update", "read"]
    self._AddDummyGetResponse(canned_product)
    canned_product["scopes"] = ["write", "read"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--add-oauth-scope=write --remove-oauth-scope=update")

  def testScopesClear(self):
    canned_product = self.canned_product()
    canned_product["scopes"] = ["update", "read"]
    self._AddDummyGetResponse(canned_product)
    del canned_product["scopes"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--clear-oauth-scopes")

  def testScopesCreate(self):
    self._AddDummyGetResponse()
    canned_product = self.canned_product()
    canned_product["scopes"] = ["like", "subscribe"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--add-oauth-scope=^-^like-subscribe")

  def testEnvironmentsChange(self):
    self._AddDummyGetResponse()
    canned_product = self.canned_product()
    canned_product["environments"] = ["prod", "beta"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--remove-environment=test --add-environment=beta")

  def testEnvironmentsClear(self):
    self._AddDummyGetResponse()
    canned_product = self.canned_product()
    del canned_product["environments"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--all-environments")

  def testEnvironmentsCreate(self):
    canned_product = self.canned_product()
    del canned_product["environments"]
    self._AddDummyGetResponse(canned_product)
    canned_product["environments"] = ["egg", "bacon", "spam", "sausage"]
    self._AddDummyPutResponse(canned_product)
    self._RunUpdate("--add-environment=egg,bacon "
                    "--add-environment=spam,sausage")

  def testAccidentalResourcesClear(self):
    self._AddDummyGetResponse()
    with self.assertRaises(exceptions.BadArgumentException):
      self._RunUpdate("--remove-resource='/gcloud-test1#/gcloud-test1c'")

  def testAccidentalProxiesClear(self):
    product = self.canned_product()
    product["proxies"] = ["manilla"]
    self._AddDummyGetResponse(product)
    with self.assertRaises(exceptions.BadArgumentException):
      self._RunUpdate("--remove-api=manilla")

  def testAccidentalEnvironmentsClear(self):
    self._AddDummyGetResponse()
    with self.assertRaises(exceptions.BadArgumentException):
      self._RunUpdate("--remove-environment=test --remove-environment=prod")

  def testAccidentalScopesClear(self):
    product = self.canned_product()
    product["scopes"] = ["read", "search"]
    self._AddDummyGetResponse(product)
    self._AddDummyPutResponse()
    self._RunUpdate("--remove-oauth-scope=read,search")

  def testApprovalUpdate(self):
    self._AddDummyGetResponse()
    product = self.canned_product()
    product["approvalType"] = "manual"
    self._AddDummyPutResponse(product)
    self._RunUpdate("--manual-approval")

  def testAccessUpdateDuringAttributeUpdate(self):
    self._AddDummyGetResponse()
    product = self.canned_product()
    product["attributes"][0]["value"] = "private"
    self._AddDummyPutResponse(product)
    self._RunUpdate("--add-attribute=access=private")

  def testAbnormalServerStateFailsafes(self):
    product = self.canned_product()
    del product["attributes"]
    self._AddDummyGetResponse(product)
    product["attributes"] = [{"name": "foo", "value": "bar"}]
    self._AddDummyPutResponse(product)
    self._RunUpdate("--add-attribute=foo=bar")

  def testQuotaChange(self):
    self._AddDummyGetResponse()
    product = self.canned_product()
    product["quota"] = "100"
    product["quotaTimeUnit"] = "hour"
    self._AddDummyPutResponse(product)
    self._RunUpdate("--quota=100 --quota-unit=hour")

  def testQuotaAdd(self):
    product = self.canned_product()
    del product["quota"]
    del product["quotaInterval"]
    del product["quotaTimeUnit"]
    self._AddDummyGetResponse(product)
    product["quota"] = "7"
    product["quotaInterval"] = "5"
    product["quotaTimeUnit"] = "minute"
    self._AddDummyPutResponse(product)
    self._RunUpdate("--quota=7 --quota-interval=5 --quota-unit=minute")
    pass

  def testQuotaClear(self):
    self._AddDummyGetResponse()
    product = self.canned_product()
    del product["quota"]
    del product["quotaInterval"]
    del product["quotaTimeUnit"]
    self._AddDummyPutResponse(product)
    self._RunUpdate("--clear-quota")

  def testQuotaWithMissingInterval(self):
    product = self.canned_product()
    del product["quota"]
    del product["quotaInterval"]
    del product["quotaTimeUnit"]
    self._AddDummyGetResponse(product)
    with self.assertRaises(exceptions.RequiredArgumentException):
      self._RunUpdate("--quota=100 --quota-unit=hour")

  def testQuotaWithMissingAmount(self):
    product = self.canned_product()
    del product["quota"]
    del product["quotaInterval"]
    del product["quotaTimeUnit"]
    self._AddDummyGetResponse(product)
    with self.assertRaises(exceptions.RequiredArgumentException):
      self._RunUpdate("--quota-interval=100 --quota-unit=hour")

  def testQuotaWithMissingUnits(self):
    product = self.canned_product()
    del product["quota"]
    del product["quotaInterval"]
    del product["quotaTimeUnit"]
    self._AddDummyGetResponse(product)
    with self.assertRaises(exceptions.RequiredArgumentException):
      self._RunUpdate("--quota-interval=100 --quota=1")

  def testDescriptionUpdate(self):
    self._AddDummyGetResponse()
    product = self.canned_product()
    product["description"] = "bar baz quux. dolorem ipsum dolor"
    self._AddDummyPutResponse(product)
    self._RunUpdate("--description='bar baz quux. dolorem ipsum dolor'")

  def testDisplayNameUpdate(self):
    product = self.canned_product()
    product["displayName"] = "mycool"
    self._AddDummyGetResponse()
    product["displayName"] = "cooler"
    self._AddDummyPutResponse(product)
    self._RunUpdate("--display-name=cooler")

  def testDescriptionClear(self):
    product = self.canned_product()
    product["description"] = "bar baz quux. dolorem ipsum dolor"
    self._AddDummyGetResponse(product)
    product["description"] = ""
    self._AddDummyPutResponse(product)
    self._RunUpdate("--description=")

  def testDisplayNameEmpty(self):
    self._AddDummyGetResponse()
    with self.assertRaises(exceptions.BadArgumentException):
      self._RunUpdate("--display-name=")
