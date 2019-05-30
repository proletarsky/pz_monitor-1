# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .models import Participant, Reason, Equipment, TimetableDetail, Timetable, TimetableContent

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


# Register your models here.
admin.site.register(Participant)
admin.site.register(Reason)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(TimetableDetail)
admin.site.register(Timetable, TimetableAdmin)
