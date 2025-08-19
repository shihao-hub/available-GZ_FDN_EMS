from django.contrib import admin

from . import models

# 【知识点】可以使用 @admin.register({model}) 装饰 admin.ModelAdmin 的子类

# 【知识点】admin.site.register 第一个参数是 model，第二个参数可选 admin.ModelAdmin
admin.site.register(models.BusData)
admin.site.register(models.GeneratorData)
admin.site.register(models.BranchData)

# 【知识点】再搭配 apps.py#label 和 models.py#model#class Meta#verbose_name&verbose_name_plural，即可让 admin 后台汉化