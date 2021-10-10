from django.contrib import admin
from . import models
admin.site.register(models.Files)
admin.site.register(models.Hsds)
admin.site.register(models.Genes)
admin.site.register(models.KEGG)
admin.site.register(models.Faq)
# Register your models here.
