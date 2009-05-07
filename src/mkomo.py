import os
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app


class ModelAndView():
    def __init__(self,model,view):
        self.model = model
        self.view = view
        

class MavRequestHandler(webapp.RequestHandler):
    def get(self):
        mav = self.get_model_and_view()
        if mav is not None:
            self.render(mav)
    
    def post(self):
        mav = self.post_model_and_view()
        if mav is not None:
            self.render(mav)
            
    def render(self, mav):
        path = os.path.join(os.path.abspath('..'), 'pages', mav.view)
        model = mav.model
        if users.is_current_user_admin():
            model['is_admin'] = True
            model['logout_url'] = users.create_logout_url('/') 
        self.response.out.write(template.render(path, model))
            

class Page(db.Model):
    uri = db.StringProperty()
    title = db.StringProperty()
    description = db.StringProperty()
    keywords = db.StringProperty()
    headline = db.StringProperty()
    content = db.TextProperty()
    date_last_edited = db.DateTimeProperty(auto_now_add=True)
    

class Story(db.Model):
    headline = db.StringProperty()
    snippet = db.StringProperty()
    thumbnail_url = db.LinkProperty()
    continue_link_url = db.LinkProperty()
    continue_link_text = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    tags = db.ListProperty(db.Category)
    
    
class StandardPage(MavRequestHandler):
    def get_model_and_view(self):
        uri = self.request.path
        page = Page.gql("where uri=:1", uri).get()
        if page is not None:
            return ModelAndView(view='standard.html',
                                model={'page': page})
        else:
            return ModelAndView(view='error.html',
                                model={'uri': uri})
            

application = webapp.WSGIApplication([('/.*', StandardPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()