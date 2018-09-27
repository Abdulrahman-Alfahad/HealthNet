from django.contrib import admin
from .models import ProfileInformation, Patient, Doctor, Nurse, Administrator

admin.site.register(ProfileInformation)
admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Nurse)
admin.site.register(Administrator)
