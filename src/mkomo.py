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
        
        
class NotFoundException(Exception):
    def __init__(self,message='The page you requested does not exit.'):
        self.message = message
        
        
class MavRequestHandler(webapp.RequestHandler):
    def get(self):
        try:
            mav = self.get_model_and_view()
            if mav is not None:
                self.render(mav)
        except NotFoundException, ex:
            self.response.set_status(404)
            self.render(ModelAndView(view='error.html',
                                model={'message': ex.message}))
    
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
            
            
#class BasePage(db.Model):
#    uri = db.StringProperty()
#    title = db.StringProperty()
#    description = db.StringProperty()
#    keywords = db.StringProperty()

class Page(db.Model):
    uri = db.StringProperty()
    title = db.StringProperty()
    description = db.StringProperty()
    keywords = db.StringProperty()
    headline = db.StringProperty()
    content = db.TextProperty()
    date_last_edited = db.DateTimeProperty(auto_now_add=True)
    

class List(db.Model):
    id = db.StringProperty()
    title = db.StringProperty()
    description = db.StringProperty()
    keywords = db.StringProperty()
    headline = db.StringProperty()


class Entry(db.Model):
    uri = db.StringProperty()
    title = db.StringProperty()
    description = db.StringProperty()
    keywords = db.StringProperty()
    list_id = db.StringProperty()
    headline = db.StringProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    precedence = db.FloatProperty()

    
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
            raise NotFoundException

  
class ListPage(MavRequestHandler):
    def get_model_and_view(self):
        list_and_entry = self.request.path[3:].partition('/')
        if len(list_and_entry[0]) == 0:
            raise NotFoundException
        elif len(list_and_entry[2]) == 0:
            list_id = list_and_entry[0]
            list = List.gql("where id=:1", list_id).get()
            if list is None:
                raise NotFoundException('There\'s no list with id "%s"'%list_id)
            elif list_and_entry[1] != '/':
                self.redirect('/m/%s/' % list_and_entry[0])
                return
            q = Entry.all()
            q.filter('list_id =', list_id)
            q.order('-precedence')
            entries = q.fetch(100)
            return ModelAndView(view='list.html',
                                model={'list': list,
                                       'entries': entries})
        else:
            list_id = list_and_entry[0]
            uri = list_and_entry[2]
            entry = Entry.gql("where list_id=:1 and uri=:2", list_id, uri).get()
            if entry is None:
                raise NotFoundException
            return ModelAndView(view='standard.html',
                                model={'page': entry})
                
    
class AssetRequestHandler(webapp.RequestHandler):
    def get(self):
        uri = self.request.path[8:]
        asset = Asset.gql("where uri=:1", uri).get()
        if asset is not None:
            self.response.headers['Content-Type'] = mimetypes.guess_type(uri)[0]
            self.response.out.write(asset.payload)
        else:
            self.error(404)

    
application = webapp.WSGIApplication([('/assets/.*', AssetRequestHandler),
                                      ('/m/.*', ListPage),
                                      ('/.*', StandardPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()