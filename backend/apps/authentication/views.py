import traceback
from typing import Annotated

from loguru import logger

from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework import views, generics, viewsets, filters, decorators, status, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema

from . import schemas, serializers, models


# todo: 构造一个类型，Union[Request, HttpRequest]，因为 drf 使用的不是继承，ide 检测不到，还是说就是不要你用 django Request？

class LoginViewSet(viewsets.ViewSet):
    @extend_schema(request=schemas.UserLogoutIn)
    @decorators.action(detail=False, methods=["POST"], permission_classes=[permissions.AllowAny])
    def logout(self, request: Request):
        # 刷新令牌以提前过期
        user_logout_in = schemas.UserLogoutIn(data=request.data)
        user_logout_in.is_valid(
            raise_exception=True)  # todo: 不推荐使用 raise_exception，因为响应格式太随机？但是加入除非特殊字段（_xxx），其他一律都是错误信息的话，那反倒推荐了。
        refresh_token = user_logout_in.validated_data["refresh_token"]
        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()
            return Response({"detail": "登出成功"}, status=status.HTTP_200_OK)
        except TokenError as e:
            # 目前遇到的情况是：TokenError 令牌类型错误，既然 token 格式都有问题，那自然不需要加入黑名单
            logger.error("{}\n{}", e, traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=schemas.UserRegisterIn, responses=schemas.UserRegisterOut)
    @decorators.action(detail=False, methods=["POST"], permission_classes=[permissions.AllowAny])
    @transaction.atomic
    def register(self, request: Request):
        # todo: 实现一个全局错误响应，前端也需要一个非受检错误的统一处理
        user_register_in = schemas.UserRegisterIn(data=request.data)
        user_register_in.is_valid(raise_exception=True)  # todo: 这个异常抛出后，返回的响应是什么？
        username = user_register_in.validated_data["username"]
        password = user_register_in.validated_data["password"]
        if models.User.objects.filter(username=username).exists():
            return Response(data={"detail": f"注册失败，用户名 `{username}` 已存在"}, status=status.HTTP_400_BAD_REQUEST)
        models.User.objects.create_user(username=username, password=password)
        return Response(data={"detail": f"注册成功，用户名：{username}"}, status=status.HTTP_200_OK)

    @extend_schema(request=schemas.UserChangePasswordIn)
    @decorators.action(detail=False, methods=["POST"], permission_classes=[permissions.AllowAny])
    def change_password(self, request: Request):
        schema_in = schemas.UserChangePasswordIn(data=request.data)
        schema_in.is_valid(raise_exception=True)

        username = schema_in.validated_data["username"]
        password = schema_in.validated_data["password"]
        new_password = schema_in.validated_data["new_password"]
        confirm_password = schema_in.validated_data["confirm_password"]

        if not models.User.objects.filter(username=username).exists():
            return Response(data={"detail": "用户名不存在"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(data={"detail": "旧密码错误"}, status=status.HTTP_400_BAD_REQUEST)
        if password == new_password:
            return Response(data={"detail": "新密码不能和旧密码相同"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return Response(data={"detail": "两次输入的密码不一致"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response(data={"detail": "修改密码成功！"}, status=status.HTTP_200_OK)

    @extend_schema(request=schemas.UserRegisterIn, responses=schemas.UserRegisterOut)
    @decorators.action(detail=False, methods=["POST"])
    @transaction.atomic
    def invalid_register(self, request: Request):
        # 1. 输入验证
        in_schema = schemas.UserRegisterIn(data=request.data)
        in_schema.is_valid(raise_exception=True)

        # 2. 准备数据
        registration_data = {
            "username": in_schema.validated_data["username"],
            "password": in_schema.validated_data["password"]
        }

        # 3. 数据库操作
        db_serializer = serializers.UserSerializer(data=registration_data)
        db_serializer.is_valid(raise_exception=True)
        user = db_serializer.save()

        # 4. 业务逻辑
        # 发送欢迎邮件

        # 5. 输出响应
        # 【知识点】instance 传入，data 不传入，无需 is_valid，但是假如 data 传入，必须 is_valid，奇怪，隐藏的细节实在太多了！
        out_schema = schemas.UserRegisterOut(instance=user)
        return Response(data=out_schema.data, status=status.HTTP_201_CREATED)
