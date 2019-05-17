# End-to-end tests for Dataproc jobs

This directory contains the end-to-end gcloud tests for Dataproc jobs. They
create real clusters and jobs. To run all tests in this directory locally:

```
$ blaze test third_party/py/googlecloudsdk:tests/e2e/surface/dataproc/jobs_test --test_output=streamed
```

Depending on the test definition, the command will run against the v1 API or the
v1beta2 API.

TODO(gcobb): We could also define a YAML file in this directory to point to
other environments like the sandbox development clusters as described
[here](https://g3doc.corp.google.com/cloud/sdk/g3doc/contributors/dev_guide/testing/running_tests.md#testing-against-other-environments).

Full instructions on running tests can be found in the
[main gcloud site](https://g3doc.corp.google.com/cloud/sdk/g3doc/contributors/dev_guide/testing/running_tests.md)

