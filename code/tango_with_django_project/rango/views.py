from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from rango.bing_search import run_query

def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__startswith=starts_with)
    else:
        cat_list = Category.objects.all()

    if max_results > 0:
        if (len(cat_list) > max_results):
            cat_list = cat_list[:max_results]

    for cat in cat_list:
        cat.url = encode(cat.name)
    
    return cat_list



def search(request):
    context= RequestContext(request)
    result_list=[]
    if request.method=='POST':
        query=request.POST['query'].strip()
        if query:
            result_list=run_query(query)
    return render_to_response('rango/search.html',{'result_list':result_list}, context)

def index(request):
    #Obtain the context from HTTP request
    context = RequestContext(request)
    
    
    # Query db for a list of ALL cats
    # Arrange in desc ord of likes
    # Retrieve the top 5 only - or all if less than 5
    # Place the list in our context_dict dictionary which will be passed to temp engine
    category_list=Category.objects.order_by('-likes')[:5]
    page_list=Page.objects.order_by('-views')[:5]
    context_dict= {'categories': category_list, 'pages':page_list}
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    for category in category_list:
        category.url = category.name.replace(' ','_')
    
    if request.session.get('last_visit'):
        last_visit_time=request.session.get('last_visit')
        visits=request.session.get('visits',0)
        
        if(datetime.now()-datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
            request.session['visits']=visits+1
            request.session['last_visit']=str(datetime.now())
    else:
        request.session['last_visit']=str(datetime.now())
        request.session['visits']=1
    
    
    return render_to_response('rango/index.html', context_dict,context)
   
    
    


def about(request):
    context= RequestContext(request)
    
    if request.session.get('visits'):
        count=request.session.get('visits')
    else:
        count=0
    context_dict={'visits':count}
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    return render_to_response('rango/about.html', context_dict, context)

def category(request, category_name_url):
    context=RequestContext(request)
    
    # Change underscores in category name to spaces.
    # URL don't handle spaces well, so encode them as underscores
    # we can then replace underscore with spaces again
    
    category_name = decode(category_name_url)
    
     # Create a context dictionary which we can pass to the template rendering engine.
    # We start by containing the name of the category passed by the user.
    context_dict = {'category_name': category_name, 'category_name_url': category_name_url}
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
    cat_list = get_category_list()

    context_dict['cat_list'] = cat_list
    return render_to_response('rango/category.html',context_dict,context)

@login_required
def add_category(request):
    context=RequestContext(request)
   
    
    if request.method=='POST':
        form=CategoryForm(request.POST)
        
        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    
    else:
        form=CategoryForm()
    
    context_dict={'form':form}
    cat_list = get_category_list()

    context_dict['cat_list'] = cat_list
    return render_to_response('rango/add_category.html',context_dict,context)

@login_required
def add_page(request, category_name_url):
    context=RequestContext(request)
    
    category_name=decode(category_name_url)
    if request.method=='POST':
        form=PageForm(request.POST)
        
        if form.is_valid():
            page=form.save(commit=False) #can't commit straightaway, not all fields are auto populated!
            try:
                cat=Category.objects.get(name=category_name)
                page.category=cat
            except Category.DoesNotExist:
                return render_to_response('rango/add_category.html', {}, context)
            page.views=0
            page.save()
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form=PageForm()
    context_dict={'category_name_url':category_name_url, 'category_name':category_name,'form':form}
    
    cat_list = get_category_list()

    context_dict['cat_list'] = cat_list
    return render_to_response('rango/add_page.html',context_dict,context)
                
def register(request):
    context=RequestContext(request)
    registered=False
    if request.method=='POST':
        user_form=UserForm(data=request.POST)
        profile_form=UserProfileForm(data=request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user=user_form.save()
            user.set_password(user.password)
            user.save()
            
            profile=profile_form.save(commit=False)
            profile.user=user
            if 'picture' in request.FILES:
                profile.picture=request.FILES['picture']
            profile.save()
            registered=True
            
        else:
            print user_form.errors, profile_form.errors
    else:
        user_form=UserForm()
        profile_form=UserProfileForm()
    context_dict={'user_form':user_form,'profile_form':profile_form, 'registered':registered}
    cat_list = get_category_list()

    context_dict['cat_list'] = cat_list
    
    return render_to_response('rango/register.html', context_dict,
            context)


def user_login(request):
    context=RequestContext(request)
    cat_list=get_category_list()
    context_dict={}
    context_dict['cat_list']=cat_list
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        
        user=authenticate(username=username,password=password)
        if user:
            if user.is_active:
                login(request,user)
                return HttpResponseRedirect('/rango/')
            else:
                context_dict['disabled_account'] = True
                return render_to_response('rango/login.html', context_dict, context)
        else:
            print "Invalid login details: {0},{1}".format(username, password)
            context_dict['bad_details'] = True
            return render_to_response('rango/login.html', context_dict, context)
    else:
        return render_to_response('rango/login.html', context_dict, context)
    
@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')


def encode(raw_url):
	return raw_url.replace(' ', '_')

def decode(cooked_url):
	return cooked_url.replace('_', ' ')