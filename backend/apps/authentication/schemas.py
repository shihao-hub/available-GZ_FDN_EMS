from rest_framework import serializers

from . import models


# 【知识点】输入/处理/输出三层序列化器，这个分层设计特别适合中大型项目。对于小型项目或简单模型，可以适当简化，使用单个 ModelSerializer 配合 read_only 和 write_only 字段。
# 参考链接：

class Success(serializers.Serializer):
    message = serializers.CharField(default="success")


class Error(serializers.Serializer):
    message = serializers.CharField(default="error")
    reason = serializers.JSONField(default=None)


"""
方案2：继承方式（适合简单场景）

class UserBase(serializers.ModelSerializer):
    # 公共字段和验证
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email']

class UserIn(UserBase):
    # 输入特定字段和验证
    password = serializers.CharField(write_only=True)
    age = serializers.IntegerField(min_value=0, max_value=150)
    
    class Meta(UserBase.Meta):
        fields = UserBase.Meta.fields + ['password', 'age']

class UserOut(UserBase):
    # 输出特定字段
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    
    class Meta(UserBase.Meta):
        fields = UserBase.Meta.fields + ['created_at']

疑问：class Meta 的 fields 与 Serializer 中，一定要对齐吗？Meta 是不是就是方便复用，等于自动创建了字段？

待定：输入/处理/输出三层序列化器的实际使用尚未体验过，假如对 fastapi 足够熟悉，才方便在其他框架中模仿。
"""


class UserRegisterIn(serializers.Serializer):
    # todo: 进行复杂校验，比如：用户名格式/用户名是否存在/密码格式/密码长度 等
    username = serializers.CharField(max_length=10)
    password = serializers.CharField(max_length=20)


class UserLoginIn(UserRegisterIn):
    username = serializers.CharField(max_length=10) # 无意义，单纯练习一下覆盖操作


class UserLogoutIn(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=1000)


class UserRegisterOut(serializers.ModelSerializer):
    # 无异于，单纯联系一下 Meta（用户注册返回值只需要一个 username 而已）
    class Meta:
        model = models.User
        fields = ("username",)


class UserChangePasswordIn(UserRegisterIn):
    new_password = serializers.CharField(max_length=20)
    confirm_password = serializers.CharField(max_length=20)