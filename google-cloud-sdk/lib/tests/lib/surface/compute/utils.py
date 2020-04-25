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
"""Module for compute test utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import client_adapter
from googlecloudsdk.core import resources

import mock


SAMPLE_WRAPPED_CSEK_KEY = ('ea2QS4AIhWKprsmuk/mh7g3vdBDGiTcSynFASvJC/rs/3BmOnW'
                           'G8/kBsy/Ql9AnLaQ/EQtkCQgyUZcLlM+OmEqduWuoCkorp8xG8'
                           'h9Y5UrlVz4AZbmQd99UhPejuH2L1+qmU1bGmGVhV4mcJtZNDwO'
                           'o4rCHdMuu9czHCsvDQZtseJQmnjZO2e8NGOa0rd6CZkJtammM1'
                           '7wYEAixZ+DbLgvAvtl16p1FMsLQ8ArsjrNBd9ll9pb/+9dKMCy'
                           'NXyY/jOKRDrtg+AyKWjg0FifmjCvzZ0pYC+DCM6jJIc9IsX6Kp'
                           '4gNhJTPfzXCvhviqUNGM6xMMXUvq4fCaBoaHOdm66w==')

DEBIAN_IMAGE_FAMILY = 'debian-10'


class CsekKeyStore(object):
  """Keeps track of resource keys."""

  def __init__(self):
    self._keys = []

  def AddKey(self, uri, key=None, key_type='raw'):
    if key_type == 'rsa-encrypted':
      key = SAMPLE_WRAPPED_CSEK_KEY
    elif key is None:
      raise ValueError('Must provide key for raw key type')
    self._keys.append({
        'uri': uri,
        'key': key,
        'key-type': key_type
    })

  def AsString(self):
    return json.dumps(self._keys)

  def WriteToFile(self, filename):
    with open(filename, 'w') as f:
      json.dump(self._keys, f)


class BatchResponder(object):
  """Emulates batch reqiests responses."""

  def __init__(self):
    self._batches = []

  def _GetKeyForRequest(self, request):
    service, method, payload = request
    return (service.__module__ + '.' + service.__class__.__name__,
            method,
            encoding.MessageToJson(payload))

  def ExpectBatch(self, batch):
    batch_dict = {}
    for request, response in batch:
      request_key = self._GetKeyForRequest(request)
      if request_key in batch_dict:
        raise AssertionError('Duplicate request {}'.format(request))
      batch_dict[request_key] = response
    self._batches.append(batch_dict)

  def AssertDone(self):
    if self._batches:
      raise AssertionError('Expecting the following batch requests {0}'
                           .format(self._batches))

  def BatchRequests(self, requests, errors_to_collect=None):
    """Simulates compute adapter.BatchRequest method behaviour."""
    if not self._batches:
      raise AssertionError('No more request were expected but got {0}'
                           .format(requests))
    batch = self._batches.pop(0)
    responses = []

    for r in requests:
      request_key = self._GetKeyForRequest(r)
      if request_key not in batch:
        raise AssertionError('Unexpected request {}, expecting {}'.format(
            r, list(batch.keys())))
      response = batch.pop(request_key)
      if isinstance(response, Exception):
        errors_to_collect.append(response)
        responses.append({})
      else:
        responses.append(response)
    return responses


class ComputeApiMock(object):
  """Mocks compute api adapter."""

  def __init__(self, api_version='v1', project=None, region=None, zone=None):
    self.api_version = api_version
    self.project = project
    self.zone = zone
    self.region = region
    self._cleanups = []

  def __enter__(self):
    return self.Start()

  def Start(self):
    """Starts this mock."""
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.adapter = client_adapter.ClientAdapter(self.api_version, no_http=True)
    self.messages = self.adapter.messages

    self.batch_responder = BatchResponder()
    self.adapter.BatchRequests = self.batch_responder.BatchRequests

    make_requests_patch = mock.patch.object(self.adapter, 'MakeRequests')
    self._cleanups.append(make_requests_patch.stop)
    self.make_requests = make_requests_patch.start()

    adapter_patch = mock.patch(
        'googlecloudsdk.api_lib.compute.client_adapter.ClientAdapter',
        return_value=self.adapter)
    self._cleanups.append(adapter_patch.stop)
    adapter_patch.start()

    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_type is None:
      self.Cleanup()

  def Stop(self):
    for cleanup in self._cleanups:
      cleanup()
