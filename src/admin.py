import os
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms

from src.mkomo import Page, Story, Asset, ModelAndView, MavRequestHandler

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
    def get_model_and_view(self, page_form=None):
        if page_form is None:
            key = self.request.get('key')
            if (len(key) > 0):
                page_form = PageForm(instance=Page.get(key))
            else:
                page_form = PageForm(instance=Page())                
        identifier = 'new page' if page_form.instance.uri is None \
                                else page_form.instance.uri
        return ModelAndView(view='admin/object-edit.html', 
                            model={'object': page_form.instance,
                                   'identifier': identifier,
                                   'object_form': page_form})
        
    def post_model_and_view(self):        
        key = self.request.get('key')
        if (len(key) > 0):
            page = Page.get(key)
        else:
            page = Page()
        data = PageForm(data=self.request.POST, instance=page)
        if data.is_valid():
            # Save the data, and redirect to the view page
            entity = data.save()
            entity.put()
            self.redirect('/admin/pages')
        else:
            # Reprint the form
            return self.get_model_and_view(data)
    
    
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
    def get_model_and_view(self, asset_form=None):
        if asset_form is None:
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
            return self.get_model_and_view(data)
            
            
application = webapp.WSGIApplication([('/admin/pages/edit', EditPage),
                                      ('/admin/pages/delete', DeletePage),
                                      ('/admin/pages.*', ListPages),
                                      ('/admin/assets/edit', EditAsset),
                                      ('/admin/assets/delete', DeleteAsset),
                                      ('/admin/assets.*', ListAssets)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()