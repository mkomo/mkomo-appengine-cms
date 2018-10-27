import os
import mimetypes
import yaml
import string
import traceback
from sets import Set

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

INDEX_LIST_ID='index'


class ModelAndView():
    def __init__(self,model,view):
        self.model = model
        self.view = view


class NotFoundException(Exception):
    def __init__(self,message='The page you requested does not exist.'):
        self.message = message


class MavRequestHandler(webapp.RequestHandler):
    def get(self):
        try:
            mav = self.get_model_and_view()
            if mav is not None:
                self.render(mav)
            else:
                self.response.set_status(500)
                self.render(ModelAndView(view='error.html',
                                    model={'message': 'mav returned None',
                                           'uri': self.request.path}))
        except NotFoundException, ex:
            self.response.set_status(404)
            self.render(ModelAndView(view='error.html',
                                model={'message': ex.message,
                                       'uri': self.request.path}))
        except Exception, ex:
            self.response.set_status(500)
            self.render(ModelAndView(view='error.html',
                                model={'message': traceback.format_exc(),
                                       'uri': self.request.path}))

    def post(self):
        mav = self.post_model_and_view()
        if mav is not None:
            self.render(mav)

    def render(self, mav):
        if 'yaml' in self.request.params:
            yam_string = yaml.dump(mav, default_flow_style=False, default_style='|')
            self.response.headers['Content-Type'] = "text/plain; charset=UTF-8"
            self.response.out.write(yam_string)
        else:
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
    date_last_edited = db.DateTimeProperty()
    headline = db.StringProperty()
    img = db.StringProperty()
    img_square_css = db.StringProperty()
    list_display = db.StringProperty()

    # see https://cdnjs.com/libraries/highlight.js/ for list
    syntaxes = db.StringProperty()
    def get_syntax_list(self):
        return get_syntax_list([self])
    snippet = db.TextProperty()
    snippet_is_markdown = db.BooleanProperty(default=True)
    content = db.TextProperty()
    content_is_markdown = db.BooleanProperty(default=True)

    def display_date(self):
        if self.date:
            if self.date_last_edited:
                return '{} (updated {})'.format(self.date, self.date_last_edited)
            else:
                return self.date
        elif self.date_last_edited:
            return 'updated {}'.format(self.date_last_edited)
        else:
            return None


    def display_date_short(self):
        if self.date_last_edited:
            return 'updated ' + self.date_last_edited.split('-')[0]
        elif self.date:
            return self.date.split('-')[0]
        else:
            return None

    def get_snippet(self):
        if self.snippet:
            return self.snippet
        elif not self.content:
            return None
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
    is_public = db.BooleanProperty(default=False)

    def load(self, **entries):
        self.__dict__.update(entries)


class List(db.Model):
    id = db.StringProperty()
    title = db.StringProperty()
    description = db.StringProperty()
    keywords = db.StringProperty()
    headline = db.StringProperty()
    is_index = db.BooleanProperty()

    def get_container_type(self):
        return 'dynamic-width' if self.is_index  else 'fixed-width'

    def get_display_type(self):
        return 'mkpf-box' if self.is_index  else 'mkpf-list'

    def show_short_date(self):
        return self.get_display_type() == 'mkpf-box'

    def __init__(self, **entries):
        self.__dict__.update(entries)


def hydrate(page):
    if page.snippet_is_markdown and page.snippet is not None:
        page.snippet = markdown.markdown(page.snippet)
    if page.content_is_markdown and page.content is not None:
        page.content = markdown.markdown(page.content)

def get_syntax_list(pages):
    syntaxes = Set([])
    for page in pages:
        if page.syntaxes:
            for syntax in page.syntaxes.split(","):
                syntaxes.add(syntax)

    if len(syntaxes) > 0:
        return syntaxes
    else:
        return False

class Asset(db.Model):
    uri = db.StringProperty()
    payload = db.BlobProperty()


class StandardPage(MavRequestHandler):
    def get_model_and_view(self):
        """load a page from content/pages/ or from the datastore. If none found, fall through to list"""
        uri = self.request.path

        #handle datastore page
        page = Page.gql("where uri=:1", uri).get()
        if page is not None and (page.is_public or users.is_current_user_admin()):
            hydrate(page)
            return ModelAndView(view='standard.html',
                                model={
                                    'page': page,
                                    'syntax_list': get_syntax_list([page])
                                })
        else:
            #handle static page
            filename = uri[1:] + '.html' if len(uri) > 1 else 'index.html'
            static_page_path = os.path.join(os.path.dirname(__file__), '..', 'content', 'pages', filename)
            if os.path.isfile(static_page_path):
                return ModelAndView(view = static_page_path, model = {})

        return self.get_list()

    def get_list(self):
        """retrieve a list from the datastore. If none found, fall through to content/lists dir."""
        list_id = self.request.path[1:]
        if len(list_id) <= 0:
            list_id = INDEX_LIST_ID
        lst = List.gql("where id=:1", list_id).get()
        if lst is not None:
            q = Page.all()
            q.filter('list_id =', list_id)
            if not users.is_current_user_admin():
                q.filter('is_public',True)
            q.order('-precedence')
            pages = q.fetch(100)
            for page in pages:
                hydrate(page)
            return ModelAndView(view='list.html',
                                model={'list': lst,
                                       'pages': pages,
                                       'syntax_list': get_syntax_list(pages)})
        else:
            return self.get_list_fs(list_id)

    def get_list_fs(self, list_id):
        """retrieve a yaml-based list from content/lists. If none found, fall through to list item"""
        listspec = self.get_fs_list_spec(list_id)
        if listspec is not None:
            lst = List(**listspec)
            lst.is_index = list_id == INDEX_LIST_ID
            pages = []
            for entry in listspec['entries']:
                page = self.get_page_from_entry(entry)
                pages.append(page)

            return ModelAndView(view='list.html',
                            model={
                                   'list': lst,
                                   'request': self.request,
                                   'pages': pages,
                                   'syntax_list': get_syntax_list(pages)
                            })

        return self.get_list_fs_item()


    def get_list_fs_item(self):
        """retrieve an item from yaml-based list"""
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
                                               'page': page,
                                               'syntax_list': get_syntax_list([page])})
        raise NotFoundException

    def get_slug(self, headline):
        """generate a url-safe string for a given headline"""
        exclude = set(string.punctuation)
        s = ''.join(ch for ch in headline if ch not in exclude)
        return s.lower().replace(" ", "-")

    def get_fs_list_spec(self, list_id, filter=None):
        filename = list_id + ".yaml"
        list_yaml_path = os.path.join(os.path.dirname(__file__), '..', 'content', 'lists', filename)
        if os.path.isfile(list_yaml_path):
            stream = open(list_yaml_path, 'r')
            listspec = yaml.load(stream)
            filtered_entries = []
            for entry in listspec['entries']:
                if filter is None or ('_list_id' in entry and entry['_list_id'] == filter):
                    filtered_entries.append(entry)
            if len(filtered_entries) == 0 and filter is not None:
                return None
            else:
                listspec['entries'] = filtered_entries
                listspec['_id'] = filter
                return listspec
        elif list_id != INDEX_LIST_ID:
            return self.get_fs_list_spec(INDEX_LIST_ID, list_id)
        else:
            return None

    def get_page_from_entry(self, entry):
        """generate a page object from an entry dict (usu originating in yaml)"""
        page = Page()
        if '_uri' not in entry or entry['_uri'] is None:
            prefix = '' if '_list_id' not in entry or entry['_list_id'] is None else ('/' + entry['_list_id'])
            entry['_uri'] = prefix + "/" + self.get_slug(entry['_headline'])
        page.load(**entry)
        hydrate(page)
        page.static = True
        return page

class AssetRequestHandler(webapp.RequestHandler):
    def get(self):
        uri = self.request.path[8:]
        asset = Asset.gql("where uri=:1", uri).get()
        if asset is not None:
            type = mimetypes.guess_type(uri)[0]
            if type == "text/plain":
                type = type + "; charset=UTF-8"
            self.response.headers['Content-Type'] = type

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
