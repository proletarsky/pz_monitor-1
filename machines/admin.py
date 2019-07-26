# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .models import Participant, Reason, Equipment, TimetableDetail, Timetable, TimetableContent, ClassifiedInterval
from .models import Code, Profile
from django.contrib import admin


class EquipmentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Equipment._meta.fields]
    list_filter = ['workshop']
    search_fields = ['workshop', 'code', 'model']

    class Meta:
        model = Equipment


class TimetableDetailInLine(admin.TabularInline):
    model = TimetableContent


class TimetableAdmin(admin.ModelAdmin):
    inlines = [
        TimetableDetailInLine,
    ]


class ClassifiedIntervalAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if obj.pk:
            obj.user = request.user
        super().save_model(request, obj, form, change)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone']


class CodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'code']


# Register your models here.
admin.site.register(Participant)
admin.site.register(Reason)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(TimetableDetail)
admin.site.register(Timetable, TimetableAdmin)
admin.site.register(ClassifiedInterval, ClassifiedIntervalAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Code, CodeAdmin)
