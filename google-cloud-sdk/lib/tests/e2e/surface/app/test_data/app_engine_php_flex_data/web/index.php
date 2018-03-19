<?php

require_once __DIR__ . '/../vendor/autoload.php';

$app = new Silex\Application();

$app->get('/', function () {
  return 'Hello World';
});

$app->get('/goodbye', function () {
  return 'Goodbye World';
});

if (PHP_SAPI != 'cli') {
  $app->run();
}

return $app;
