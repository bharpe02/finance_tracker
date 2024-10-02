from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, JsonResponse
from plaid_api.models import PlaidCredential
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
import json


def register(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")
            first_name = data.get("firstName")
            last_name = data.get("lastName")

            print(email)
            print(password)
            print(first_name)
            print(last_name)
            if not all([email, password, first_name, last_name]):
                return JsonResponse({"success": False, "error": "All fields are required."}, status=400)

            # Check if the user already exists
            if User.objects.filter(username=email).exists():
                return JsonResponse({"success": False, "error": "A user with this email already exists."}, status=400)

            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            login(request, user)
            if request.GET.get("next"):
                return JsonResponse({"success": True, "redirect": request.GET.get("next")})
            return JsonResponse({"success": True, "redirect": "/"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON."}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@ensure_csrf_cookie
def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({"csrfToken": csrf_token})

def login_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        #email = request.POST.get("email")
        #password = request.POST.get("password")
        email = data.get("email")
        password = data.get("password")
        print(f"Attempting login with email: {email} and password: {password}")
        user = authenticate(username=email, password=password)
        if user is not None:
            login(request, user)
            try:
                p = PlaidCredential.objects.get(user=user)
                request.session["access_token"] = p.access_token
            except PlaidCredential.DoesNotExist:
                pass

            if request.GET.get("next"):
                return JsonResponse({"success": True, "redirect": request.GET.get("next")})
            return JsonResponse({"success": True, "redirect": "/"})
        
        else:
            return JsonResponse({"success": False, "error": "Invalid login credentials."}, status=403)
    else:
        #return render(request, "authentication/login.html")
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@login_required(login_url="/auth/login/")
def logout_view(request):
    logout(request)
    return JsonResponse({"success": True, "redirect": "/"})

# New view to check if the user is authenticated
@require_GET
@login_required(login_url="/auth/login/")
def check_auth(request):
    return JsonResponse({"authenticated": True})