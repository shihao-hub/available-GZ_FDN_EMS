from typing import Annotated

from django.db import transaction
from rest_framework import views, generics, viewsets, filters, decorators, status
from rest_framework.request import Request
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from . import schemas, serializers


# todo: 构造一个类型，Union[Request, HttpRequest]，因为 drf 使用的不是继承，ide 检测不到，还是说就是不要你用 django Request？

class LoginViewSet(viewsets.ViewSet):
    @extend_schema(request=schemas.UserLoginIn)
    @decorators.action(detail=False, methods=["POST"])
    def login(self, request: Request):
        pass

    @decorators.action(detail=False, methods=["POST"])
    def logout(self, request: Request):
        pass

    @decorators.action(detail=False, methods=["POST"])
    def refresh(self, request: Request):
        pass

    @extend_schema(request=schemas.UserRegisterIn, responses=schemas.UserRegisterOut)
    @decorators.action(detail=False, methods=["POST"])
    @transaction.atomic
    def register(self, request: Request):
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
