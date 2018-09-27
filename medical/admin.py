from django.contrib import admin
from . import models

admin.site.register(models.Diagnosis)
admin.site.register(models.Test)
admin.site.register(models.Prescription)
admin.site.register(models.Drug)
