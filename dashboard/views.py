from django.shortcuts import render,redirect,get_object_or_404
from . models import Notes
from . forms import *
from django.contrib import messages
from django.views.generic import DetailView
from .models import Notes
from .forms import HomeworkForm
from .models import Homework
from youtubesearchpython import VideosSearch
from .models import Todo
import requests
from .forms import DashboardFom
from .forms import DashboardForm 
import wikipedia
import wikipediaapi
from django.core.cache import cache
from bs4 import BeautifulSoup
import warnings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.views.decorators.http import require_POST


def home(request):
    return render(request,'dashboard/home.html')

@login_required
def notes(request):
    if request.method == "POST":
        form = NotesForm(request.POST)
        if form.is_valid():
            notes = form.save(commit=False)
            notes.user = request.user
            notes.save()
            messages.success(request, f"Notes Added from {request.user.username} Successfully")
        else:
            messages.error(request, "Error adding note. Please check the form.")
    else:
        form = NotesForm()

    notes = Notes.objects.filter(user=request.user)
    context = {'notes': notes, 'form': form}
    return render(request, 'dashboard/notes.html', context)

@login_required
def delete_note(request,pk):
    Notes.objects.get(id=pk).delete()
    return redirect(notes)

class NotesDetailView(DetailView):
    model = Notes
    template_name = 'dashboard/notes_detail.html'
    context_object_name = 'notes'

@login_required
def homework(request):
    if request.method == "POST":
        form = HomeworkForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST.get('is_finished', 'off') == 'on'
            except:
                finished = False
            new_homework = Homework(
                user=request.user,
                subject=request.POST['subject'],
                title=request.POST['title'],
                description=request.POST['description'],
                due=request.POST['due'],
                is_finished=finished
            )
            new_homework.save()
            messages.success(request, f'Homework added by {request.user.username}!')
    else:
        form = HomeworkForm()
    
    homeworks = Homework.objects.filter(user=request.user)
    homework_done = len(homeworks) == 0

    context = {
        'homeworks': homeworks,
        'homework_done': homework_done,
        'form': form,
    }
    return render(request, 'dashboard/homework.html', context)

@login_required
def update_homework(request, pk=None):
    homework = get_object_or_404(Homework, id=pk)
    homework.is_finished = not homework.is_finished
    homework.save()
    return redirect('homework')

@login_required
def delete_homework(request, pk=None):
    Homework.objects.get(id=pk).delete()
    return redirect('homework')
def youtube(request):
    form = DashboardFom(request.POST or None)
    result_list = []

    if request.method == "POST" and form.is_valid():
        text = form.cleaned_data.get('text', '')  # Safely get 'text' from the form data
        
        if text:  # Ensure 'text' is not empty
            video = VideosSearch(text, limit=10)
            
            for i in video.result().get('result', []):
                result_dict = {
                    'input': text,
                    'title': i.get('title', 'N/A'),
                    'duration': i.get('duration', 'N/A'),
                    'thumbnail': i.get('thumbnails', [{}])[0].get('url', 'N/A'),
                    'channel': i.get('channel', {}).get('name', 'N/A'),
                    'link': i.get('link', 'N/A'),
                    'views': i.get('viewCount', {}).get('short', 'N/A'),
                    'published': i.get('publishedTime', 'N/A'),
                    'description': ''.join(desc.get('text', '') for desc in i.get('descriptionSnippet', []))
                }
                result_list.append(result_dict)

    context = {
        'form': form,
        'results': result_list
    }
    
    return render(request, "dashboard/youtube.html", context)

@login_required
def todo(request):
    if request.method == 'POST':
        form = TodoForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST["is_finished"]
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False
            todo = Todo(
                user = request.user,
                title = request.POST['title'],
                is_finished = finished
            )
            todo.save()
            messages.success(request,f"Todo Added from {request.user.username}!!")
    else:
        form = TodoForm()
    todo = Todo.objects.filter(user=request.user)
    if len(todo) == 0:
        todos_done = True
    else:
        todos_done = False
    context = {
        'form':form,
        'todos':todo,
        'todos_done':todos_done
    }
    return render(request,'dashboard/todo.html',context)

@login_required
def update_todo(request,pk=None):
    todo = get_object_or_404(Todo, id=pk)
    is_finished = request.POST.get('is_finished') == 'true'
    todo.is_finished = is_finished
    todo.save()
    return redirect('todo')

@login_required
def delete_todo(request,pk=None):
    Todo.objects.get(id=pk).delete()
    return redirect("todo")

def books(request):
    form = DashboardFom(request.POST or None)
    result_list = []

    if request.method == "POST" and form.is_valid():
        text = form.cleaned_data.get('text', '')  # Safely get 'text' from the form data
        
        if text:  # Ensure 'text' is not empty
            url = f"https://www.googleapis.com/books/v1/volumes?q={text}"
            r = requests.get(url)
            
            if r.status_code == 200:
                answer = r.json()
                items = answer.get('items', [])

                for i in range(min(10, len(items))):
                    volume_info = items[i].get('volumeInfo', {})
                    result_dict = {
                        'title': volume_info.get('title', 'N/A'),
                        'subtitle': volume_info.get('subtitle', 'N/A'),
                        'description': volume_info.get('description', 'N/A'),
                        'count': volume_info.get('pageCount', 'N/A'),
                        'categories': volume_info.get('categories', []),
                        'rating': volume_info.get('averageRating', 'N/A'),
                        'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                        'preview': volume_info.get('previewLink', '')
                    }
                    result_list.append(result_dict)
            else:
                messages.error(request, f"Error fetching data from Google Books API: {r.status_code}")

    context = {
        'form': form,
        'results': result_list
    }
    
    return render(request, "dashboard/books.html", context)

def dictionary(request):
    form = DashboardFom(request.POST or None)
    context = {'form': form}
    
    if request.method == "POST" and form.is_valid():
        text = form.cleaned_data.get('text', '')  # Safely get 'text' from the form data
        
        if text:  # Ensure 'text' is not empty
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en_US/{text}"
            r = requests.get(url)
            
            if r.status_code == 200:
                answer = r.json()
                try:
                    phonetics = answer[0]['phonetics'][0].get('text', 'N/A')
                    audio = answer[0]['phonetics'][0].get('audio', '')
                    definition = answer[0]['meanings'][0]['definitions'][0].get('definition', 'N/A')
                    example = answer[0]['meanings'][0]['definitions'][0].get('example', 'N/A')
                    synonyms = answer[0]['meanings'][0]['definitions'][0].get('synonyms', [])
                    
                    context.update({
                        'input': text,
                        'phonetics': phonetics,
                        'audio': audio,
                        'definition': definition,
                        'example': example,
                        'synonyms': synonyms
                    })
                except (IndexError, KeyError):
                    context.update({
                        'input': text,
                        'error': 'Could not retrieve data for the given word.'
                    })
            else:
                context.update({
                    'input': text,
                    'error': f"Error fetching data from Dictionary API: {r.status_code}"
                })
                
    return render(request, "dashboard/dictionary.html", context)

def wiki(request):
    search_term = request.GET.get('search', '')
    data = None
    if search_term:
        response = requests.get(f'https://en.wikipedia.org/api/rest_v1/page/summary/{search_term}')
        if response.status_code == 200:
            data = response.json()
    return render(request, 'dashboard/wiki.html', {'data': data})


def conversion(request):
    if request.method == "POST":
        form = ConversionForm(request.POST)
        if request.POST['measurement'] == 'length':
            measurement_form = ConversionLengthForm()
            context = {
                'form': form,
                'm_form': measurement_form,
                'input': True
            }
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >= 0:
                    if first == 'yard' and second == 'foot':
                        answer = f'{input} yard = {int(input) * 3} foot'
                    if first == 'foot' and second == 'yard':
                        answer = f'{input} foot = {int(input) / 3} yard'
                context = {
                    'form': form,
                    'm_form': measurement_form,
                    'input': True,
                    'answer': answer
                }

        elif request.POST['measurement'] == 'mass':
            measurement_form = ConversionMassForm()
            context = {
                'form': form,
                'm_form': measurement_form,
                'input': True
            }
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >= 0:
                    if first == 'pound' and second == 'kilogram':
                        answer = f'{input} pound = {int(input) * 0.453592} kilogram'
                    if first == 'kilogram' and second == 'pound':
                        answer = f'{input} kilogram = {int(input) * 2.20462} pound'
                context = {
                    'form': form,
                    'm_form': measurement_form,
                    'input': True,
                    'answer': answer
                }
    else:
        form = ConversionForm()
        context = {
            'form': form,
            'input': False
        }
    return render(request, "dashboard/conversion.html", context)

def register(request):
    if request.method =='POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request,f"Account Created for {username}!!")
            return redirect("login")

    else:
        form = UserRegistrationForm()
    context = {
        'form':form
    }
    return render(request,"dashboard/register.html",context)

@login_required
def profile(request):
    homeworks = Homework.objects.filter(is_finished=False,user=request.user)
    todos = Todo.objects.filter(is_finished=False,user=request.user)
    if len(homeworks) == 0:
        homework_done = True
    else:
        homework_done = False
    if len(todos) == 0:
        todos_done = True
    else:
        todos_done = False
    context = {
        'homeworks':homeworks,
        'todos':todos,
        'homework_done' :homework_done,
        'todos_done' :todos_done
    }
    return render(request,"dashboard/profile.html",context)


@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('logged_out') 