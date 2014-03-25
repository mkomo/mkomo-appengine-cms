import os
import mimetypes

from google.appengine.api import users
from google.appengine.ext import webapp

from django.template import Context, Template
import django.template.loader

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
                                model={'message': ex.message,
                                       'uri': self.request.path}))
    
    def post(self):
        mav = self.post_model_and_view()
        if mav is not None:
            self.render(mav)
            
    def render(self, mav):
        path = os.path.join(os.path.dirname(__file__), 'pages', mav.view)
        model = mav.model
        if users.is_current_user_admin():
            model['is_admin'] = True
            model['logout_url'] = users.create_logout_url('/')

        template_file = open(path)
        compiled_template = Template(template_file.read())
        template_file.close()
        self.response.out.write(compiled_template.render(Context(model)))

class Page(db.Model):
    uri = db.StringProperty()
    #html metadata
    title = db.StringProperty()
    description = db.StringProperty()
    keywords = db.StringProperty()
    #html content
    date = db.DateTimeProperty()
    headline = db.StringProperty()
    snippet = db.TextProperty()
    content = db.TextProperty()
    def get_snippet(self):
        if self.snippet:
            return self.snippet
        else:
            break_text = '<br id="break"/>'
            index_of_break = self.content.find(break_text)
            if index_of_break < 0:
                return None
            else:
                return self.content[0:index_of_break]
    #organization
    list_id = db.StringProperty()
    precedence = db.FloatProperty(default=1.0)
    date_last_edited = db.DateTimeProperty(auto_now=True)
    is_public = db.BooleanProperty(default=False)
    

class List(db.Model):
    id = db.StringProperty()
    title = db.StringProperty()
    description = db.StringProperty()
    keywords = db.StringProperty()
    headline = db.StringProperty()


class Asset(db.Model):
    uri = db.StringProperty()
    payload = db.BlobProperty()


class StandardPage(MavRequestHandler):
    def get_model_and_view(self):
        uri = self.request.path
        page = Page.gql("where uri=:1", uri).get()
        if page is not None and (page.is_public or users.is_current_user_admin()):
            return ModelAndView(view='standard.html',
                                model={'page': page})
        else:
            return self.get_list()
        
    def get_list(self):
        list_id = self.request.path[1:]
        list = List.gql("where id=:1", list_id).get()
        if list is None:
            raise NotFoundException
        q = Page.all()
        q.filter('list_id =', list_id)
        if not users.is_current_user_admin():
            q.filter('is_public',True)
        q.order('-precedence')
        pages = q.fetch(100)
        return ModelAndView(view='list.html',
                            model={'list': list,
                                   'pages': pages})


class PageCostPerGigabyte(MavRequestHandler):
    def get_model_and_view(self):
        uri = self.request.path
        page = Page.gql("where uri=:1", uri).get()
        return ModelAndView(view='cost-per-gigabyte.html',
                            model={'page': page})


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
                                      ('/cost-per-gigabyte-update', PageCostPerGigabyte),
                                      ('/.*', StandardPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()