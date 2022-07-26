from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.forms.models import model_to_dict

from .forms import *
from .models import *
from user.models import User

import json, difflib, sys, datetime

# Create your views here.
def main(request):
    alphabet = [
        '#',
        'a', 'b', 'c', 'd',
        'e', 'f', 'g', 'h',
        'i', 'j', 'k', 'l',
        'm', 'n', 'o', 'p',
        'q', 'r', 's', 't',
        'u', 'v', 'w', 'x',
        'y', 'z'
    ]
    jaum = [
        'ㄱ', 'ㄴ', 'ㄷ', 'ㄹ',
        'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ',
        'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ',
        'ㅍ', 'ㅎ'
    ]
    context = {
        'choices': {
            c[0]: {
                'name': c[1].replace(' ',''),
                'data': {
                    a: Article.objects.filter(title__name__istartswith=a, field=c[0]).order_by('title__name')
                    for a in alphabet
                },
            } for c in ARTICLE_FIELD_CHOICES
        },
        # 'choices': {i:v[1] for i, v in enumerate(HEADWORD_CHOICES)},
        'alphabet': alphabet,
        'jaum': jaum,
    }
    return render(request,'wiki/main.html',context)


def editor(request):
    if request.method == 'POST':
        if request.POST['cuDiv'] == 'create':
            request.session['rq_editor'] = request.POST
            return HttpResponseRedirect('/wiki/editor/create')

    else:
        wf = Headword.objects.filter(is_published=False, is_banned=False)
        rh = History.objects.all().order_by('-id')[:10]# recent history
        context = {
            'wf': wf,
            'rh': rh,
        }
        return render(request,'wiki/editor.html',context)

# create
def create(request):
    if request.method == 'POST':
        # realtime validation on the client side
        # - ['headword','field','fieldname','definition'] : required
        # - ['headword','fieldname'] : unique together

        # Headword
        obj_h, created_h = Headword.objects.get_or_create(name=request.POST['title'])

        # Article
        if request.POST['fieldname'] == '':
            field_nm = ARTICLE_FIELD_CHOICES_DICT[request.POST['field']]
        else:
            field_nm = request.POST['fieldname']

        obj_a = Article(
            id = None,
            title = obj_h,
            field = request.POST['field'],
            fieldname = field_nm,
        )
        obj_a.save()

        # History
        obj_u = User.objects.get(email=request.user)
        history = History(
            id = None,
            is_draft = True,
            editor = obj_u,
            article = obj_a,
            abstract = 'draft',
            definition = request.POST['definition'],
            description = request.POST['description'],
        )
        history.save()

        if request.POST['keywords'] != '':
            kwds = [k.strip(' ') for k in request.POST['keywords'].split(',')]
            for k in kwds:
                obj_k, created_k = Headword.objects.get_or_create(name=k)
                history.keywords.add(obj_k)
            else:
                kwds = None

        obj_h.is_published=True
        obj_h.save()

        messages.success(request, "Success to create an article.")
        return redirect(f'/wiki/{obj_a.id}')

    else:
        rq_editor = request.session.get('rq_editor')
        context = {
            'cuDiv': rq_editor['cuDiv'],
            'cuType': rq_editor['cuType'],
            'data': Headword.objects.get(id=int(rq_editor['hid'])) if rq_editor['cuType'] == 'waitingFor' else None,
            'artclAll': json.dumps([f'{obj.fieldname.lower()}:{obj.title.name.lower()}' for obj in Article.objects.all()]),
            'artclChoices': json.dumps(ARTICLE_FIELD_CHOICES_DICT),
            'form': ArticleForm(),
        }
        return render(request,'wiki/createArticle.html',context)

# # read
# def read(aid):
#     return render()
#
# # update
# def update(aid):
#     return render()


# read / update / delete
def article(request, aid):
    obj_a = Article.objects.get(id=aid)
    # edit
    if request.method == "POST":
        obj_u = User.objects.get(email=request.user)
        history = History(
            id = None,
            editor = obj_u,
            article = obj_a,
            abstract = request.POST['abstract'],
            definition = request.POST['definition'],
            description = request.POST['description'],
        )
        history.save()

        if request.POST['keywords'] != '':
            kwds = [k.strip(' ') for k in request.POST['keywords'].split(',')]
            for k in kwds:
                obj_k, created_k = Headword.objects.get_or_create(name=k)
                history.keywords.add(obj_k)

        messages.success(request,'Success to update the article.')
        return redirect(f'/wiki/{aid}')
    else:
        a_latest = obj_a.history.filter(is_cancelled=False).latest()
        context = {
            'cuDiv': 'update',
            'cuType': None,
            'data_view_on': 'article',
            'data': a_latest,
            'form': ArticleForm(),
            'delform': ArticleDeleteForm(),
            'artclChoices': ARTICLE_FIELD_CHOICES_DICT,
            # 'history': a.history.all().order_by('-updated_at'),
        }
    return render(request,'wiki/article.html',context)


def ord2strord(num):
    if str(num)[-1] == '1':
        return f"{num}st"
    elif str(num)[-1] == '2':
        return f"{num}nd"
    elif str(num)[-1] == '3':
        return f"{num}rd"
    else:
        return f"{num}th"

def diffInputFormat(str):
    str_input = str.replace('\r\n\r\n','\r\n').replace('\r\n','\r\n.').split('.')
    str_input = [x.strip()+'.' if '\r\n' not in x else x for x in str_input]
    return [x for x in str_input if x!= '.']

def historyDetail(request,aid,order):
    obj_a = Article.objects.get(id=aid)
    historyAll = obj_a.history.all()
    curr = historyAll[order-1]
    get_size_kb = lambda data: sys.getsizeof(data.definition+data.description)/1024
    context = {
        'ord': {
            'numord': order,
            'strord': ord2strord(order),
            'prev': order-1,
            'next': order+1,
            'start': order==1,
            'end': order==len(obj_a.history.all()),
        },
        'size': {
            'delta': get_size_kb(curr),
            'curr': get_size_kb(curr)
        },
        'data': curr,
    }
    if order > 1:
        prev = historyAll[order-2]
        context['size']['delta'] = get_size_kb(curr) - get_size_kb(prev)
        context['diff'] = {
            ''
        }
        context['diff'] = {
            'definition': '\n'.join(difflib.unified_diff(
                diffInputFormat(prev.definition),
                diffInputFormat(curr.definition),
                fromfile = 'previous def',
                tofile = 'current def',
            )).replace('\n\n','\n'),
            'description': '\n'.join(difflib.unified_diff(
                diffInputFormat(prev.description),
                diffInputFormat(curr.description),
                fromfile = 'previous desc',
                tofile = 'current desc',
            )).replace('\n\n','\n'),
            'keywords': '\n'.join(difflib.unified_diff(
                [k.name for k in prev.keywords.all()],
                [k.name for k in curr.keywords.all()],
                fromfile = 'previous kwds',
                tofile = 'current kwds',
            )).replace('\n\n','\n'),
        }
    return render(request, 'wiki/articleHistoryDetail.html',context)

# request = {
#     'dfrom': ['headword','history'],
#     'ban': {
#         'headword': [True,False],
#         'user': [True,False],
#     },
#     'abstract': 'asdfasdf'
# }

def delete(request):
    obj_a = Article.objects.get(id=request.POST['aid'])
    obj_u = User.objects.get(email=request.user)

    # delete headword
    if request.POST['deltype'] == '00':
        curr_version = obj_a.history.filter(is_cancelled=False).latest()
        curr_version.is_cancelled = True
        curr_version.cancelled_by = obj_u
        curr_version.cancelled_at = datetime.datetime.now()
        curr_version.cancelled_why = request.POST['delwhy']
        curr_version.cancelled_why_detail = request.POST['delwhydetail']
        curr_version.save()

        messages.success(request, 'Success to cancel the update!')
        return redirect(f"/wiki/{request.POST['aid']}")

    # delete all articles
    elif request.POST['deltype'] == '01':
        obj_h = Headword.objects.get(id=obj_a.title.id)
        obj_h.is_published = False
        obj_h.save()
        obj_a.delete()

        messages.success(request, 'Success to delete all history for the article.')
        return redirect("/wiki/editor")

    # cancel an update
    elif request.POST['deltype'] == '02':
        obj_h = Headword.objects.get(id=obj_a.title.id)
        obj_h.is_published = False
        obj_h.is_banned = True
        obj_h.save()
        obj_a.delete()

        messages.success(request, 'Success to delete the headword.')
        return redirect("/wiki/editor")

'''
delete ['headword','article','history']
- type1) delete from Headword
    - ban the headword
    - ban the user

- type2) keep the word and back to the before-publish
- type3) delete a history and back to recent version
'''
