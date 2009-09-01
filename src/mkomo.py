import os
import mimetypes
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
    

class Entry(db.Model):
    headline = db.StringProperty()
    body = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    tags = db.ListProperty(db.Category)
    
class Asset(db.Model):
    uri = db.StringProperty()
    payload = db.BlobProperty()
    
class StandardPage(MavRequestHandler):
    def get_model_and_view(self):
        uri = self.request.path
        page = Page.gql("where uri=:1", uri).get()
        if page is not None:
            return ModelAndView(view='standard.html',
                                model={'page': page})
        else:
            self.response.set_status(404)
            return ModelAndView(view='error.html',
                                model={'uri': uri})

  
class ProjectPage(MavRequestHandler):
    def get_model_and_view(self):
        offset = self.request.get('offset')
        if offset is None or len(offset) < 1: 
            offset = 0
        else:
            offset = int(offset)
        q = Entry.all()
        q.order('-date').order('-__key__')
        entries = q.fetch(100, offset)
        headline = "my life's work (or my distractions from it)"
        return ModelAndView(view='entries.html',
                            model={'entries': entries,
                                   'headline': headline})
        
    
class AssetReq(webapp.RequestHandler):
    def get(self):
        uri = self.request.path[8:]
        asset = Asset.gql("where uri=:1", uri).get()
        if asset is not None:
            self.response.headers['Content-Type'] = mimetypes.guess_type(uri)[0]
            self.response.out.write(asset.payload)
        else:
            self.error(404)

    
application = webapp.WSGIApplication([('/assets/.*', AssetReq),
                                      #('/projects', ProjectPage),
                                      ('/.*', StandardPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()