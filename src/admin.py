import os
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms

from src.mkomo import Page, ModelAndView, MavRequestHandler

class PageForm(djangoforms.ModelForm):
  class Meta:
    model = Page
    exclude = []
    
    
class ListPages(MavRequestHandler):
    def get_model_and_view(self):
        pages = Page.all()
        return ModelAndView(view='pages/page-list.html', 
                            model={'pages': pages})
   
    
class DeletePage(MavRequestHandler):
    def get_model_and_view(self):
        key = self.request.get('key')
        page = Page.get(key)
        page.delete()
        self.redirect('/admin/list')
        
            
class EditPage(MavRequestHandler):
    def get_model_and_view(self):
        key = self.request.get('key')
        if (len(key) > 0):
            page = Page.get(key)
        else:
            page = Page()
        return ModelAndView(view='pages/page-edit.html', 
                            model={'page': page,
                                   'page_form': PageForm(instance=page)})
        
    def post(self):        
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
            self.redirect('/admin/list')
        else:
            # Reprint the form
            return ModelAndView(view='pages/page-edit.html', 
                                model={'page': page,
                                       'page_form': PageForm(instance=page)})
            
            
application = webapp.WSGIApplication([('/admin/edit', EditPage),
                                      ('/admin/delete', DeletePage),
                                      ('/admin/.*', ListPages)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()