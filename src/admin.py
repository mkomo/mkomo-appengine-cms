import os
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms

from src.mkomo import Page, Story, ModelAndView, MavRequestHandler

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
        identifier = 'new page' if page_form.instance.url is None \
                                else page_form.instance.url
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
            

class StoryForm(djangoforms.ModelForm):
  class Meta:
    model = Story
    exclude = ['tags']
    
    
class ListStories(MavRequestHandler):
    def get_model_and_view(self):
        stories = Story.all()
        return ModelAndView(view='admin/story-list.html', 
                            model={'stories': stories})
   
    
class DeleteStory(MavRequestHandler):
    def get_model_and_view(self):
        key = self.request.get('key')
        story = Story.get(key)
        story.delete()
        self.redirect('/admin/stories')
        
            
class EditStory(MavRequestHandler):
    def get_model_and_view(self, story_form=None):
        if story_form is None:
            key = self.request.get('key')
            if (len(key) > 0):
                story_form = StoryForm(instance=Story.get(key))
            else:
                story_form = StoryForm(instance=Story())
        identifier = 'new story' if story_form.instance.headline is None \
                                 else story_form.instance.headline.join('"'*2)
        return ModelAndView(view='admin/object-edit.html', 
                            model={'object': story_form.instance,
                                   'identifier': identifier,
                                   'object_form': story_form})
        
    def post_model_and_view(self):        
        key = self.request.get('key')
        if (len(key) > 0):
            story = Story.get(key)
        else:
            story = Story()
        data = StoryForm(data=self.request.POST, instance=story)
        if data.is_valid():
            # Save the data, and redirect to the view page
            entity = data.save()
            entity.put()
            self.redirect('/admin/stories')
        else:
            return self.get_model_and_view(data)
            
            
application = webapp.WSGIApplication([('/admin/pages/edit', EditPage),
                                      ('/admin/pages/delete', DeletePage),
                                      ('/admin/pages.*', ListPages),
                                      ('/admin/stories/edit', EditStory),
                                      ('/admin/stories/delete', DeleteStory),
                                      ('/admin/stories.*', ListStories)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()