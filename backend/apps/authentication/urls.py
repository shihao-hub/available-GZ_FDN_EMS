from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from . import views

router = routers.DefaultRouter()  # todo: 有无入参需要设置？
# 【知识点】routers.DefaultRouter 可以被 drf 自带的文档识别到，但是在代码中实在不够清晰，暂且少用吧
router.register("", views.LoginViewSet, "login-view-set")  # todo: basename 字段是干什么用的？

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("login/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("login/verify/", TokenVerifyView.as_view(), name="token_verify"), # 用来验证 token 的，根据需要进行配置
]

urlpatterns += router.urls
