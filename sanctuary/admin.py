from django.contrib import admin

from .models import Catalog,Object_list,Connection_data,IP_rawdata,Sidebar_statistics
# Register your models here.
admin.site.register(Catalog)
admin.site.register(Object_list)
admin.site.register(Connection_data)
admin.site.register(IP_rawdata)
admin.site.register(Sidebar_statistics)
