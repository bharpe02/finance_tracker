from django.shortcuts import render
from dotenv import load_dotenv
from os.path import join, dirname
import os
import plaid
from plaid.api import plaid_api
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import PlaidCredential
import datetime
import calendar
import json
from plaid.exceptions import ApiException
from django.contrib.auth.decorators import login_required


# Create your views here.
dotenv_path = '.env'
load_dotenv(dotenv_path)

PLAID_CLIENT_ID = "66c68e763871db001a2d278f"
PLAID_CLIENT_SECRET = "2f518173b2e00a260eeb74d46c718b"

configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_CLIENT_SECRET,
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

PLAID_COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES", "US").split(",")
PLAID_PRODUCTS = os.getenv("PLAID_PRODUCTS", "transactions").split(",")
PLAID_REDIRECT_URI = "http://localhost:8000"

access_token = None
item_id = None

def index(request):
    return render(request, "plaid_api/index.html")

@csrf_exempt
def create_link_token(request):
    try:
        response = client.link_token_create(
            {
                'user': {
                    'client_user_id': str(request.user.id)
                },
                'client_name': 'Finance Tracker',
                'products': PLAID_PRODUCTS,
                'language': 'en',
                'country_codes': PLAID_COUNTRY_CODES,
                'redirect_uri': PLAID_REDIRECT_URI
            }
        )
        response_data = response.to_dict()
        return JsonResponse(response_data, safe=False)
    except plaid.ApiException as e:
        response = json.loads(e.body)
        return JsonResponse(response, safe=False)


@csrf_exempt
@login_required(login_url='/auth/login/')
def get_access_token(request):
    #Make sure user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated."}, status=401)
    
    # Ensure the request is a POST request
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        # Parse the JSON body of the request
        data = json.loads(request.body)
        public_token = data.get("public_token")

        # Validate that a public token was provided
        if not public_token:
            return JsonResponse({"error": "Public token is required."}, status=400)

    except json.JSONDecodeError:
        # Handle JSON parsing errors
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    try:
        # Try to find existing Plaid credentials for the user
        p = PlaidCredential.objects.get(user=request.user)
        request.session["access_token"] = p.access_token
        return JsonResponse({"error": None, "access_token": p.access_token})
    except PlaidCredential.DoesNotExist:
        # If the credentials don't exist, proceed to exchange the public token
        pass

    try:
        # Exchange the public token for an access token using Plaid's client
        exchange_response = client.item_public_token_exchange(public_token).to_dict()

        # Save the access token in the session
        request.session["access_token"] = exchange_response["access_token"]

        # Create a new PlaidCredential instance for the user
        PlaidCredential.objects.create(
            user=request.user,
            access_token=exchange_response["access_token"]
        )

        return JsonResponse(exchange_response, safe=False)

    except ApiException as e:
        # Handle exceptions raised by the Plaid API
        response = json.loads(e.body)
        return JsonResponse(response, safe=False, status=e.status)

@csrf_exempt
def info(request):
    if request.session["access_token"]:
        access_token = request.session["access_token"]
    else:
        access_token = None

    return JsonResponse({
        "item_id": item_id,
        "access_token": access_token,
        "products": PLAID_PRODUCTS,
    })

def _get_transactions(access_token, month=None, year=None):
    if not month and not year:
        given_date = datetime.datetime.today().date()
        start_date = str(given_date.replace(day=1)) #gives us the start of the month
        end_date = '{:%Y-%m-%d}'.format(datetime.datetime.now()) #end date is today
    else:
        if month >= 10:
            start_date = f"{str(year)}-{str(month)}-01"
            end_date = f"{str(year)}-{str(month)}-{calendar.monthrange(year, month)[1]}"
        else:
            start_date = f"{str(year)}-0{str(month)}-01"
            end_date = f"{str(year)}-0{str(month)}-{calendar.monthrange(year, month)[1]}"
        
    try:
        transaction_response = client.Transactions.get(access_token, start_date, end_date)
    except plaid.ApiException as e:
        return e
    
    return transaction_response

def get_transactions(request):
    return JsonResponse(_get_transactions(request.session["access_token"]))