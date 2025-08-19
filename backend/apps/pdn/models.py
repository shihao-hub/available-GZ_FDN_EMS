from django.db import models


# ====== 拓扑结构 ====== #

class BusData(models.Model):
    bus_i = models.IntegerField(verbose_name="母线编号", primary_key=True)
    type = models.CharField(verbose_name="母线类型", max_length=20)  # todo: 改为筛选下拉框，比如 3 代表发电机
    Pd = models.FloatField(verbose_name="总功率")  # 后续用多元数据覆盖
    Qd = models.FloatField(verbose_name="总无功")  # 后续用多元数据覆盖
    Gs = models.FloatField(verbose_name="总导纳")  # 后续用多元数据覆盖
    Bs = models.FloatField(verbose_name="总 susceptance")
    area = models.IntegerField(verbose_name="区域编号")
    Vm = models.FloatField(verbose_name="总电压幅值")
    Va = models.FloatField(verbose_name="总电压角度")
    baseKV = models.FloatField(verbose_name="母线基础电压")
    zone = models.IntegerField(verbose_name="区域编号")
    Vmax = models.FloatField(verbose_name="总电压最大值")
    Vmin = models.FloatField(verbose_name="总电压最小值")

    class Meta:
        verbose_name = verbose_name_plural = "母线数据"

    def __str__(self):
        return self.bus_i


class GeneratorData(models.Model):
    bus = models.OneToOneField(BusData, on_delete=models.CASCADE)
    Pg = models.FloatField(verbose_name="总功率")
    Qg = models.FloatField(verbose_name="总无功")
    Qmax = models.FloatField(verbose_name="总无功最大值")
    Qmin = models.FloatField(verbose_name="总无功最小值")
    Vg = models.FloatField(verbose_name="总电压幅值")
    mBase = models.FloatField(verbose_name="母线基础电压")
    status = models.IntegerField(verbose_name="状态")
    Pmax = models.FloatField(verbose_name="总功率最大值")
    Pmin = models.FloatField(verbose_name="总功率最小值")
    Pc1 = models.FloatField(verbose_name="总功率最大值")
    Pc2 = models.FloatField(verbose_name="总功率最大值")
    Qc1min = models.FloatField(verbose_name="总无功最小值")
    Qc1max = models.FloatField(verbose_name="总无功最大值")
    Qc2min = models.FloatField(verbose_name="总无功最小值")
    Qc2max = models.FloatField(verbose_name="总无功最大值")

    class Meta:
        verbose_name = verbose_name_plural = "发电机数据"

    def __str__(self):
        return f"{self.bus}"


class BranchData(models.Model):
    fbus = models.OneToOneField(BusData, on_delete=models.CASCADE, related_name="fbus")
    tbus = models.OneToOneField(BusData, on_delete=models.CASCADE, related_name="tbus")
    r = models.FloatField(verbose_name="resistance")
    x = models.FloatField(verbose_name="reactance")
    b = models.FloatField(verbose_name="susceptance")
    rateA = models.FloatField(verbose_name="A相最大电流")
    rateB = models.FloatField(verbose_name="B相最大电流")
    ratio = models.FloatField(verbose_name="导纳比")
    angle = models.FloatField(verbose_name="角度")
    status = models.IntegerField(verbose_name="状态")
    angmin = models.FloatField(verbose_name="角度最小值")
    angmax = models.FloatField(verbose_name="角度最大值")

    class Meta:
        verbose_name = verbose_name_plural = "分支数据"

    def __str__(self):
        return f"{self.fbus} - {self.tbus}"
