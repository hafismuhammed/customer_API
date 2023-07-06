from django.db import models
from django.contrib.auth.models import User



class Product(models.Model):
    user = models.ForeignKey(User, null=False, blank=False,  on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255, null=False, blank=False)
    product_price = models.FloatField(null=False, blank=False)
    product_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name