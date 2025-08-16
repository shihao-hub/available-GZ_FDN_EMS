from django.apps import AppConfig


class PdnConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pdn'
    label = "配电网络" # todo: 国际化
