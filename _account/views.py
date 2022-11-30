from datetime import datetime

from django.contrib import auth
from django.contrib.auth.hashers import check_password
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import CustomUserChangeForm
from django.core.serializers import serialize
from django.shortcuts import render, redirect
import json
from django.http import HttpResponse, JsonResponse
# Create your views here.
from django.views.decorators.csrf import csrf_exempt

from _account.models import User
from _deal.models import Deal


@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = User.objects.filter(username=data.get("username"))
        if user.exists():
            password = data.get("password")
            user = user[0]
            if user.password == password:
                auth.login(request, user)

                return redirect("barrow:home")
            else:
                context = {
                    "err": "PWD"
                }
                return JsonResponse(context)
        else:
            context = {
                "err": "ID"
            }
            return JsonResponse(context)

    else:
        return render(request, "login.html")


@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            user = User()
            data = json.loads(request.body)
            user.username = data.get("username")
            user.password = data.get("password")
            user.name = data.get("name")
            user.birth = data.get("birth1") + \
                data.get("birth2")+data.get("birth3")
            user.address = data.get("address1")+data.get("address2")
            user.address_detail = data.get("address3")
            user.phoneNum = data.get("phoneNum", "")
            user.save()

            return redirect('login')

        except Exception as e:
            print(e)
            return render(request, 'signup.html')

    return render(request, 'signup.html')


# 마이페이지 개인정보 수정하기 passowrd랑 주소찾기
# def changeUserInfo(request):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         try:
#             user = User.objects.get(id=int(data["user_id"]))
#             user.password = data["password"]
#             user.address = data["address"]
#             user.save()
#             is_changed = True
#         except:
#             is_changed = False
#     context = {
#         "is_changed": is_changed,
#     }
#     return JsonResponse(context)

# 마이페이지 유저정보가져오기
def getUserInfo(request):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            user = User.objects.get(id=int(data["user_id"]))
            password = user.password
            username = user.username
            name = user.name
            birth = user.birth
            address = user.address
            phonenum = user.phoneNum
        except Exception as e:
            print(e)
    context = {
        "username": username,
        "password": password,
        "name": name,
        "birth": birth,
        "address": address,
        "phoneNum": phonenum,
    }
    return JsonResponse(context)


def home(request):
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        id = user.id
        return render(request, "login.html", {"userid": id})
    else:
        return render(request, "login.html")


def findIdPwd(request):
    return render(request, "findIdPwd.html")


@csrf_exempt
def findId(request):
    if request.method == "POST":
        data = json.loads(request.body)

        if User.objects.filter(name=data["name"],  phoneNum=data["phoneNum"]).exists():
            context = {
                "user_id": User.objects.get(name=data["name"], phoneNum=data["phoneNum"]).username
            }
        else:
            context = {
                "user_id": None
            }
        return JsonResponse(context)

@csrf_exempt
def is_id_duplicated(request):
    if request.method == "POST":
        data = json.loads(request.body)

        if User.objects.filter(username = data["id"]).exists():
            context = {
                "is_id_duplicated": True
            }
        else:
            context = {
                "is_id_duplicated": False
            }
        return JsonResponse(context)
#### mypage ####


def mypage_main(request):
    context = {
        "lend": {},
        "barrow": {},
    }
    deals = Deal.objects.filter(user_cons=request.user)
    context["lend"]["total"] = deals.count()
    context["lend"]["products"] = deals.order_by("-created")[0:2]
    deals = Deal.objects.filter(user_cons=request.user, state="WAIT").count()
    context["lend"]["WAIT"] = deals
    deals = Deal.objects.filter(user_cons=request.user, state="LEND").count()
    context["lend"]["LEND"] = deals
    deals = Deal.objects.filter(
        user_cons=request.user, state="TERMINATE").count()
    context["lend"]["TERMINATE"] = deals

    deals = Deal.objects.filter(user_prod=request.user)
    context["barrow"]["total"] = deals.count()
    context["barrow"]["products"] = deals.order_by("-created")[0:2]
    deals = Deal.objects.filter(user_prod=request.user, state="WAIT").count()
    context["barrow"]["WAIT"] = deals
    deals = Deal.objects.filter(user_prod=request.user, state="LEND").count()
    context["barrow"]["LEND"] = deals
    deals = Deal.objects.filter(
        user_prod=request.user, state="TERMINATE").count()
    context["barrow"]["TERMINATE"] = deals

    favorite = request.user.favorite.all().order_by("-id")[0:3]
    context["favorite"] = favorite
    return render(request, "mypage/mypage_main.html", context)


def mypage_notice(request):
    return render(request, "mypage/mypage_notice.html")


def mypage_modify(request):
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.add_message(
                    request,
                    messages.SUCCESS,
                    '수정되었습니다.'
            )
            return redirect('account:mypage_modify')
        else:
            messages.add_message(
                    request,
                    messages.ERROR,
                    '회원정보 수정실패.'
            )
            return redirect('account:mypage_modify')
    else:
        return render(request, "mypage/mypage_modify2.html")


@csrf_exempt
def mypage_modify_confirm(request):
    if request.method == "POST":
        
            if check_password(request.POST["pwd"], request.user.password):
                return redirect("account:mypage_modify")
            else:
                messages.add_message(
                request,
                messages.ERROR,
                '비밀번호가 틀렸습니다.'
                )   
            
    return render(request, "mypage/mypage_modify.html")       


def mypage_favorites(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            target = User.objects.get(id = request.user.id).favorite.get(id = data["id"])
            target.delete()
            context = {
                        "is_deleted": True,
                    }           
        except:
            context = {
                        "is_deleted": False,
                    }
        return JsonResponse(context)
    else:
        products = User.objects.get(id = 10).favorite.all()
        type_queries = list(products.values("type"))
        types = []

        for type in type_queries:
            type = list(type["type"])
            type = list(map(int, type))
            types.append(type)
        products = list(zip(list(products),types))
        context = {
            "products" : products,
        }
        return render(request, "mypage/mypage_heartList.html",context)


def mypage_chatroom(request):
    return render(request, "mypage/room.html")


def mypage_account(request):
    return render(request, "mypage/mypage_account.html")


def mypage_use(request, type):
    standard = {
        "startdate" : "",
        "enddate" :"",
        "keyword" : "",
    }
    if request.method == "POST":
        
        if "startdate" in request.POST:
            standard["startdate"] = request.POST.get("startdate")
            standard["enddate"] = request.POST.get("enddate")
        if "keyword" in request.POST:
            standard["keyword"] = request.POST.get("keyword")
    if type == "barrow_from":
        context = {
            "type": type,
            "barrow": {},
        }
        deals = Deal.objects.filter(user_cons=request.user)
        if standard["startdate"] != "":
            deals = deals.filter(start_date__gte = standard["startdate"], end_date__lte = standard["enddate"])
        if standard["keyword"] != "":
            deals = deals.filter(product__title__contains = standard["keyword"])
        context["barrow"]["total"] = deals.count()
        context["barrow"]["products"] = deals.order_by("-created")
        cnt = deals.filter(user_cons=request.user, state="WAIT").count()
        context["barrow"]["WAIT"] = cnt
        cnt = deals.filter(user_cons=request.user, state="LEND").count()
        context["barrow"]["LEND"] = cnt
        deals = deals.filter(
            user_cons=request.user, state="TERMINATE").count()
        context["barrow"]["TERMINATE"] = deals
        return render(request, "mypage/mypage_useList.html",context)
    elif type == "barrow_to":
        context = {
            "type": type,
            "barrow": {},
        }
        deals = Deal.objects.filter(user_prod=request.user)
        if standard["startdate"] != "":
            deals = deals.filter(start_date__gte = standard["startdate"], end_date__lte = standard["enddate"])
        if standard["keyword"] != "":
            deals = deals.filter(product__title__contains = standard["keyword"])
        context["barrow"]["total"] = deals.count()
        context["barrow"]["products"] = deals.order_by("-created")
        cnt = deals.filter(user_prod=request.user, state="WAIT").count()
        context["barrow"]["WAIT"] = cnt
        cnt = deals.filter(user_prod=request.user, state="LEND").count()
        context["barrow"]["LEND"] = cnt
        deals = deals.filter(
            user_prod=request.user, state="TERMINATE").count()
        context["barrow"]["TERMINATE"] = deals

        return render(request, "mypage/mypage_useList.html",context)


def change_pwd(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    '비밀번호 변경이 완료되었습니다.'
                )
                return redirect('account:mypage_modify')
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    '비밀번호가 일치하지 않습니다.'
                )
        else:
            messages.add_message(
                request,
                messages.ERROR,
                '비밀번호 변경 실패'
            )
        return render(request, "mypage/mypage_modifyPw.html")
    else:
        return render(request, "mypage/mypage_modifyPw.html")

