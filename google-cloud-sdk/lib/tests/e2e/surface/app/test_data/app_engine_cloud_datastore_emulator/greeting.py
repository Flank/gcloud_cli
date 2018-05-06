"""A demo app for basic read and write operations on datastore."""

import webapp2

from google.appengine.ext import ndb


class Greeting(ndb.Model):
  content = ndb.TextProperty()


class ReadCountOfEntitiesHandler(webapp2.RequestHandler):

  def get(self):
    """Writes the number of Greeting entities in response."""
    self.response.write(len(Greeting.query().fetch()))


class WriteEntityHandler(webapp2.RequestHandler):

  def get(self):
    """Write one Greeting entity to datastore."""
    Greeting(content='no content').put()
    self.response.write('Successfully wrote data.')


app = webapp2.WSGIApplication(
    [('/read', ReadCountOfEntitiesHandler), ('/write', WriteEntityHandler)])
