__all__ = [
    "User",  # todo: 像这种，User 虽然是 django 的，但是我想当前 app 中都通过 models.py 取怎么办？
]

from django.db import models
from django.contrib.auth.models import User

# todo: 详细了解 django 的 User 实现
