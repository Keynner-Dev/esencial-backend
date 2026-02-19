from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    businesses = models.ManyToManyField("core.Business", related_name="users", blank=True)
