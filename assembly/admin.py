from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Order)
admin.site.register(Subdivision)
admin.site.register(Task)

admin.site.register(Brigade)


admin.site.register(Report)