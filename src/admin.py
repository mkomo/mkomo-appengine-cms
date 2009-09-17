import os
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms

from src.mkomo import Page, Entry, Asset, ModelAndView, MavRequestHandler

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

"""*************************************************"""
"""******************* entries *********************"""
"""*************************************************"""
class EntryForm(djangoforms.ModelForm):
  class Meta:
    model = Entry
    exclude = ['tags']
    
    
class ListEntries(MavRequestHandler):
    def get_model_and_view(self):
        entries = Entry.all()
        return ModelAndView(view='admin/entry-list.html', 
                            model={'entries': entries})
   
    
class DeleteEntry(MavRequestHandler):
    def get_model_and_view(self):
        key = self.request.get('key')
        entry = Entry.get(key)
        entry.delete()
        self.redirect('/admin/entries')
        
            
class EditEntry(MavRequestHandler):
    def get_model_and_view(self, entry_form=None):
        if entry_form is None:
            key = self.request.get('key')
            if (len(key) > 0):
                entry_form = EntryForm(instance=Entry.get(key))
            else:
                entry_form = EntryForm(instance=Entry())                
        identifier = 'new entry' if entry_form.instance.headline is None \
                                else entry_form.instance.headline
        return ModelAndView(view='admin/object-edit.html', 
                            model={'object': entry_form.instance,
                                   'identifier': identifier,
                                   'object_form': entry_form})
        
    def post_model_and_view(self):        
        key = self.request.get('key')
        if (len(key) > 0):
            entry = Entry.get(key)
        else:
            entry = Entry()
        data = EntryForm(data=self.request.POST, instance=entry)
        if data.is_valid():
            # Save the data, and redirect to the view page
            entity = data.save()
            entity.put()
            self.redirect('/admin/entries')
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
        

class ListAdminPages(MavRequestHandler):
    def get_model_and_view(self):
        p = {'headline' : "admin url mapping"}
        content_list = ['<div><a href="%(url)s">%(url)s</a></div>' %
                        {'url': a[0].replace('.*','')} for a in url_mapping] 
        p['content'] = ''.join(content_list)
        return ModelAndView(view='standard.html',
                                model={'page': p})
        
url_mapping =[('/admin/entries/edit', EditEntry),
              ('/admin/entries/delete', DeleteEntry),
              ('/admin/entries.*', ListEntries),
              ('/admin/assets/edit', EditAsset),
              ('/admin/assets/delete', DeleteAsset),
              ('/admin/assets.*', ListAssets),
              ('/admin/pages/edit', EditPage),
              ('/admin/pages/delete', DeletePage),
              ('/admin/.*', ListAdminPages)]

application = webapp.WSGIApplication(url_mapping, debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()