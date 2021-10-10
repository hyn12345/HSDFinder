from django.contrib import admin
from . import models
from embed_video.admin import AdminVideoMixin

admin.site.register(models.KO)
admin.site.register(models.QandA)


class MyModelAdmin(AdminVideoMixin, admin.ModelAdmin):
    pass


admin.site.register(models.Item, MyModelAdmin)
# Register your models here.
