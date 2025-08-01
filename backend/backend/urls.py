"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# todo: 这个项目将是实际意义上的第一个可用项目，需要精益求精并形成属于自己风格的 django 和 drf 项目结构

urlpatterns = [
    # todo: 为什么 DRF 的用户登录页面的账号和 django admin 互通？
    path('admin/', admin.site.urls),

    # 【知识点】【接口文档配置】 -> drf_spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='swagger-ui'),

    # 【知识点】【DRF 的用户登录页面】
    path('api-auth/', include('rest_framework.urls')),
]

# 【知识点】django-debug-toolbar，但是必须页面有 <body> 标签才能嵌入，这个似乎主要还是与传统 django 搭配使用的？
# See https://juejin.cn/post/6844903720304508935
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [re_path('^__debug__/', include(debug_toolbar.urls)), ] + urlpatterns
