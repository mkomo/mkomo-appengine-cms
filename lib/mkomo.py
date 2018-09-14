import os
import mimetypes
import yaml
import string

# retrieved using instructions: https://github.com/GoogleCloudPlatform/Data-Pipeline
import sys
sys.path.append("./lib")

import markdown

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
        except Exception, ex:
            self.response.set_status(500)
            self.render(ModelAndView(view='error.html',
                                model={'message': ex,
                                       'uri': self.request.path}))

    def post(self):
        mav = self.post_model_and_view()
        if mav is not None:
            self.render(mav)

    def render(self, mav):
        path = os.path.join(os.path.dirname(__file__), '..', 'templates', mav.view)
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

    def load(self, **entries):
        self.__dict__.update(entries)


class List(db.Model):
    id = db.StringProperty()
    title = db.StringProperty()
    description = db.StringProperty()
    keywords = db.StringProperty()
    headline = db.StringProperty()

    def __init__(self, **entries):
        self.__dict__.update(entries)


class Asset(db.Model):
    uri = db.StringProperty()
    payload = db.BlobProperty()


class StandardPage(MavRequestHandler):
    def get_model_and_view(self):
        uri = self.request.path

        #handle static page
        filename = uri[1:] + '.html' if len(uri) > 1 else 'index.html'
        static_page_path = os.path.join(os.path.dirname(__file__), '..', 'content', 'pages', filename)
        if os.path.isfile(static_page_path):
            return ModelAndView(view = static_page_path, model = {})

        #handle datastore page
        page = Page.gql("where uri=:1", uri).get()
        if page is not None and (page.is_public or users.is_current_user_admin()):
            return ModelAndView(view='standard.html',
                                model={'page': page})
        else:
            return self.get_list()

    def get_list(self):
        list_id = self.request.path[1:]
        lst = List.gql("where id=:1", list_id).get()
        if lst is None:
            return self.get_list_fs()
        q = Page.all()
        q.filter('list_id =', list_id)
        if not users.is_current_user_admin():
            q.filter('is_public',True)
        q.order('-precedence')
        pages = q.fetch(100)
        return ModelAndView(view='list.html',
                            model={'list': lst,
                                   'pages': pages})

    def get_list_fs(self):
        list_id = self.request.path[1:]
        filename = list_id + ".yaml"
        list_yaml_path = os.path.join(os.path.dirname(__file__), '..', 'content', 'lists', filename)
        if os.path.isfile(list_yaml_path):
            stream = open(list_yaml_path, 'r')
            listspec = yaml.load(stream)
            lst = List(**listspec)
            pages = []
            for entry in listspec['entries']:
                page = self.get_page_from_entry(entry)
                pages.append(page)

            return ModelAndView(view='list.html',
                                model={
                                       'list': lst,
                                       'request': self.request,
                                       'pages': pages
                                })
        else:
            return self.get_list_fs_item()

    def get_list_fs_item(self):
        if self.request.path[1:].rfind('/') > 1:
            list_id = self.request.path[1:self.request.path.rfind('/')]
            item_id = self.request.path[self.request.path.rfind('/')+1:]
            #self.response.out.write(list_id + ";" +item_id)
            listspec = self.get_fs_list_spec(list_id)
            if listspec != None:
                lst = List(**listspec)
                for entry in listspec['entries']:
                    if '_headline' in entry and self.get_slug(entry['_headline']) == item_id:
                        page = self.get_page_from_entry(entry)
                        return ModelAndView(view='list-item.html',
                                            model={
                                               'list': lst,
                                               'page': page})
        raise NotFoundException

    def get_slug(self, headline):
        exclude = set(string.punctuation)
        s = ''.join(ch for ch in headline if ch not in exclude)
        return s.lower().replace(" ", "-")

    def get_fs_list_spec(self, list_id):
        filename = list_id + ".yaml"
        list_yaml_path = os.path.join(os.path.dirname(__file__), '..', 'content', 'lists', filename)
        if os.path.isfile(list_yaml_path):
            stream = open(list_yaml_path, 'r')
            listspec = yaml.load(stream)
            return listspec
        else:
            return None

    def get_page_from_entry(self, entry):
        page = Page()
        if '_uri' not in entry or entry['_uri'] == None:
            entry['_uri'] = self.request.path + "/" + self.get_slug(entry['_headline'])
        if ('_snippet_markdown' in entry):
            entry['_snippet'] = markdown.markdown(entry['_snippet_markdown'])
            #, extensions=[MyExtension(), 'path.to.my.ext', 'markdown.extensions.footnotes']

        page.load(**entry)
        page.static = True
        return page

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
                                      ('/.*', StandardPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
