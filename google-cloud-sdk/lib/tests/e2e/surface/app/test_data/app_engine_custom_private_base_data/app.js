var express = require('express');
var app = express();

app.get('/*', function(req, res) {
  // Return the test_token environment variable.
  res.end('Hello, node world!');
});

app.listen(8080);
