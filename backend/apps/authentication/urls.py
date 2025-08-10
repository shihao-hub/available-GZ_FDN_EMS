from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()  # todo: 有无入参需要设置？
router.register('', views.LoginViewSet, "login-view-set")  # todo: basename 字段是干什么用的？

urlpatterns = [

]

urlpatterns += router.urls
