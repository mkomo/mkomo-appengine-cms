from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from lib import djangoforms

try:
  from mkomo import Page, Asset, List, ModelAndView, MavRequestHandler
except ImportError:
  from src.mkomo import Page, Asset, List, ModelAndView, MavRequestHandler


"""*************************************************"""
"""******************** pages **********************"""
"""*************************************************"""
class PageForm(djangoforms.ModelForm):
  class Meta:
    model = Page
    exclude = []


class ListPages(MavRequestHandler):
    def get_model_and_view(self):
        pages = Page.all()
        return ModelAndView(view='admin/page-list.html',
                            model={'pages': pages})


class DeletePage(MavRequestHandler):
    def get_model_and_view(self):
        key = self.request.get('key')
        page = Page.get(key)
        page.delete()
        self.redirect('/admin/pages')


class EditPage(MavRequestHandler):
    def get_model_and_view(self, page_form=None, key=None):
        success, failure = False, False
        if page_form is not None:
            failure = True
        elif key is not None:
            success = True
            page_form = PageForm(instance=Page.get(key))
        else:
            key = self.request.get('key')
            if (len(key) > 0):
                page = Page.get(key)
            else:
                page = Page()
                uri = self.request.get('uri')
                if len(uri) > 0:
                    page.uri = uri
            page_form = PageForm(instance=page)

        identifier = 'new page' if page_form.instance.uri is None \
                                else page_form.instance.uri
        return ModelAndView(view='admin/object-edit.html',
                            model={'object': page_form.instance,
                                   'identifier': identifier,
                                   'object_form': page_form,
                                   'success': success,
                                   'failure': failure})

    def post_model_and_view(self):
        key = self.request.get('key')
        if (len(key) > 0):
            page = Page.get(key)
        else:
            page = Page()
        page_form = PageForm(data=self.request.POST, instance=page)
        if page_form.is_valid():
            # Save the data, and redirect to the view page
            entity = page_form.save()
            entity.put()
            return self.get_model_and_view(key=entity.key())
        else:
            return self.get_model_and_view(page_form)

"""*************************************************"""
"""******************* lists ^^*********************"""
"""*************************************************"""
class ListForm(djangoforms.ModelForm):
  class Meta:
    model = List


class ListLists(MavRequestHandler):
    def get_model_and_view(self):
        lists = List.all()
        return ModelAndView(view='admin/list-list.html',
                            model={'lists': lists})


class DeleteList(MavRequestHandler):
    def get_model_and_view(self):
        key = self.request.get('key')
        list = List.get(key)
        list.delete()
        self.redirect('/admin/lists')


class EditList(MavRequestHandler):
    def get_model_and_view(self, list_form=None):
        if list_form is None:
            key = self.request.get('key')
            if (len(key) > 0):
                list_form = ListForm(instance=List.get(key))
            else:
                list_form = ListForm(instance=List())
        identifier = 'new list' if list_form.instance.id is None \
                                else list_form.instance.id
        return ModelAndView(view='admin/object-edit.html',
                            model={'object': list_form.instance,
                                   'identifier': identifier,
                                   'object_form': list_form})

    def post_model_and_view(self):
        key = self.request.get('key')
        if (len(key) > 0):
            list = List.get(key)
        else:
            list = List()
        data = ListForm(data=self.request.POST, instance=list)
        if data.is_valid():
            # Save the data, and redirect to the view page
            entity = data.save()
            entity.put()
            self.redirect('/admin/lists')
        else:
            # Reprint the form
            return self.get_model_and_view(data)


"""*************************************************"""
"""******************* assets **********************"""
"""*************************************************"""
class ListAssets(MavRequestHandler):
    def get_model_and_view(self):
        assets = Asset.all()
        return ModelAndView(view='admin/asset-list.html',
                            model={'assets': assets})


class DeleteAsset(MavRequestHandler):
    def get_model_and_view(self):
        key = self.request.get('key')
        asset = Asset.get(key)
        asset.delete()
        self.redirect('/admin/assets')


class EditAsset(MavRequestHandler):
    def get_model_and_view(self):
        key = self.request.get('key')
        if (len(key) > 0):
            uri = Asset.get(key).uri
        else:
            uri = ''
        identifier = 'new asset' if uri == '' \
                                else uri
        return ModelAndView(view='admin/edit-asset.html',
                            model={'identifier': identifier,
                                   'uri': uri})

    def post_model_and_view(self):
        key = self.request.get('key')
        if (len(key) > 0):
            asset = Asset.get(key)
        else:
            asset = Asset()
        uri = self.request.get('uri')
        if uri != '':
            # Save the data, and redirect to the view page
            asset.uri = uri
            asset.payload = db.Blob(self.request.get("payload"))
            asset.put()
            self.redirect('/admin/assets')
        else:
            # Reprint the form
            return self.get_model_and_view()


class ListAdminPages(MavRequestHandler):
    def get_model_and_view(self):
        content_list = ['<div><a href="%(url)s">%(url)s</a></div>' %
                        {'url': a[0].replace('.*','')} for a in url_mapping]

        p = {'headline' : "admin url mapping",
             'content' : ''.join(content_list),
             'static' : True}
        return ModelAndView(view='standard.html',
                                model={'page': p})

url_mapping =[('/admin/pages/edit', EditPage),
              ('/admin/pages/delete', DeletePage),
              ('/admin/pages.*', ListPages),
              ('/admin/lists/edit', EditList),
              ('/admin/lists/delete', DeleteList),
              ('/admin/lists.*', ListLists),
              ('/admin/assets/edit', EditAsset),
              ('/admin/assets/delete', DeleteAsset),
              ('/admin/assets.*', ListAssets),
              ('/admin/.*', ListAdminPages)]

application = webapp.WSGIApplication(url_mapping, debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
