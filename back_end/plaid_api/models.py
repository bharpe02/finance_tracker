from django.db import models

# Create your models here.
class PlaidCredential(models.Model):
    user = models.ForeignKey("auth.User", 
    related_name="plaid_credentials",
    on_delete=models.CASCADE)

    access_token = models.CharField(max_length=255)

class Transaction(models.Model):
    transaction_id = models.CharField(max_length=255, unique=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=255)
    description = models.TextField()