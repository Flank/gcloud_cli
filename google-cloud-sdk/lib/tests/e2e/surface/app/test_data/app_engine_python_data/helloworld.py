# Copyright 2013 Google Inc. All Rights Reserved.

import webapp2


class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.write('Hello, Python World!')


app = webapp2.WSGIApplication([('/', MainPage)],
                              debug=True)
