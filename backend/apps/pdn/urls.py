from django.urls import path

from . import views

urlpatterns = [
    # 【知识点】restful 风格主要将互联网都视为资源，不够灵活和自由，当然可以推荐练习 restful，但是暂时我的想法是将 http 请求视为云函数比较自由。
    path("get_topology_structure/", views.TopologyStructureRetrieveView.as_view()),
    path("get_power_flow_calculation_result/", views.PowerFlowCalculationRetrieveView.as_view()),
]
