from django.db import models

#Модель с каталогами - группирующими объектами
class Catalog(models.Model):
	name = models.CharField(max_length=100,verbose_name='Наименование')

	def __str__(self):
		return self.name


#Модель с объектами
class Object_list(models.Model):
    JOB_STATUSES = ((True,'Соединение установлено'),(False,'Соединение разорвано'),)
    ip = models.CharField(max_length=100, verbose_name='IP адрес')
    name = models.CharField(max_length=100,verbose_name = 'Наименование')
    description = models.CharField(max_length=100,verbose_name='Обозначение')
    active_status = models.BooleanField(verbose_name='Текущий статус', choices=JOB_STATUSES,null=False,default=True)
    catalog = models.ForeignKey(Catalog,verbose_name='Каталог',on_delete=models.SET_NULL,null=True,blank=True)

    def __str__(self):
        msg = self.name+' '+self.ip
        return msg


#Модель для добавления данных с сервиса-обхода
class Connection_data(models.Model):
    date = models.DateTimeField(auto_now=True,verbose_name='Дата/Время')
    ip = models.CharField(max_length=100, verbose_name='IP адрес')
    active_status = models.BooleanField(verbose_name='Текущий статус',null=False)



#Модель для статистики по количеству поломок сервисов
class IP_rawdata(models.Model):
    date = models.DateTimeField(auto_now_add=True,verbose_name='Дата/Время')
    ip_object = models.ForeignKey(Object_list,verbose_name='Обьект отслеживания',on_delete=models.CASCADE)
    status = models.BooleanField(verbose_name='Текущий статус',null=False)


#Модель для статистики(сайдбаров)
class Sidebar_statistics(models.Model):
    ip_object = models.ForeignKey(Object_list,verbose_name='Обьект отслеживания',on_delete=models.CASCADE)
    start_date = models.DateField(verbose_name='Дата начала периода',blank=True,null=True)
    end_date = models.DateField(verbose_name='Дата конца периода',blank=True,null=True)
    start_time = models.TimeField(verbose_name='Время начала периода',blank=True,null=True)
    end_time = models.TimeField(verbose_name='Время конца периода',blank=True,null=True)
    de_facto = models.DurationField(verbose_name='Время работы с учетом расписания',blank=True,null=True)
    status = models.BooleanField(verbose_name='Текущий статус',null=True,blank=True)
