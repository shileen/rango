from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page

def index(request):
    #Obtain the context from HTTP request
    context = RequestContext(request)
    
    # Query db for a list of ALL cats
    # Arrange in desc ord of likes
    # Retrieve the top 5 only - or all if less than 5
    # Place the list in our context_dict dictionary which will be passed to temp engine
    category_list=Category.objects.order_by('-likes')[:5]
    
    context_dict= {'categories': category_list}
    
    for category in category_list:
        category.url = category.name.replace(' ','_')
        
    return render_to_response('rango/index.html', context_dict,context)



def about(request):
    context= RequestContext(request)
    context_dict={'boldmessage':"This is about bold font"}
    return render_to_response('rango/about.html', context_dict, context)

def category(request, category_name_url):
    context=RequestContext(request)
    
    # Change underscores in category name to spaces.
    # URL don't handle spaces well, so encode them as underscores
    # we can then replace underscore with spaces again
    
    category_name = category_name_url.replace('_',' ')
    
     # Create a context dictionary which we can pass to the template rendering engine.
    # We start by containing the name of the category passed by the user.
    context_dict = {'category_name': category_name}
    try:
        # try to find cat with given name
        # if not then raise a doesnt exist exception
        category= Category.objects.get(name=category_name)
        
        # retrieve assoc pages
        pages = Page.objects.filter(category=category)
        
        # adds our result list to template context under name pages
        context_dict['pages']=pages
        
         # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
        
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass
    
    return render_to_response('rango/category.html',context_dict,context)
