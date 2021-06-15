from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
import datetime



class Subdivision(models.Model):
	name = models.CharField(max_length=50,verbose_name='Наименование подразделения')

	def __str__(self):
		return self.name





class Brigade(models.Model):
	name = models.CharField(max_length=50,verbose_name='Наименование бригады')
	quantity = models.IntegerField(verbose_name='Численность человек')
	subdivision = models.ForeignKey(Subdivision,verbose_name='Подразделение',on_delete=models.SET_NULL,null=True)
	foreman = models.ForeignKey(User,verbose_name='Бригадир',on_delete=models.SET_NULL,null=True)


	def __str__(self):
		return self.name





class Order(models.Model):
	number = models.CharField(max_length=50,verbose_name='Номер заказа')
	year = models.DateField(verbose_name='Дата заказа')
	erp = models.CharField(max_length=100,verbose_name='GUID из ERP',null=True,blank=True)

	def __str__(self):
		return self.number+' от '+(self.year.strftime("%m.%d.%Y") if self.year else '')





class Task(models.Model):

	STATUSES = ((1,'Создано'),(2,'В работе'),(3,'Закрыто'))
	name = models.CharField(max_length=150,verbose_name='Наименование работ',null=True,blank=True)
	description = models.CharField(max_length=150,verbose_name='Обозначение')
	order = models.ForeignKey(Order,verbose_name='Заказ на производство',on_delete=models.SET_NULL,null=True)
	date = models.DateField(verbose_name='Срок')
	laboriousness = models.FloatField(verbose_name='Трудоемкость')
	de_facto = models.FloatField(verbose_name='Фактическая трудоемкость',null=True,blank=True,default=0)
	subdivision = models.ForeignKey(Subdivision,verbose_name='Подразделение',on_delete=models.SET_NULL,null=True)
	status = models.IntegerField(verbose_name='Статус',choices=STATUSES,default=1)
	creator = models.ForeignKey(User,verbose_name='Разработчик',on_delete=models.SET_NULL,null=True)
	create = models.DateTimeField(verbose_name='Дата создания',auto_now_add=True,null=True,blank=True)

	def __str__(self):
		check = {1:'Создано',2:'В работе',3:'Закрыто'}
		return self.description+' '+str(self.order) 

	def get_absolute_url(self):
		return reverse('pdo_tasks')

	def get_de_facto(self):
		reports = Task_Report.objects.filter(task_id=self.id)
		if reports:
			sum_working_out = sum([x.working_out for x in reports])
			self.de_facto = sum_working_out
			self.save()
			de_facto = (sum_working_out*100)/self.laboriousness
			return int(de_facto)
		else:
			return 0

	def week_stats(self):
		end = datetime.datetime.now().date()
		start = end - datetime.timedelta(days=7)
		reports = Task_Report.objects.filter(task_id=self.id,report__create__gte=start)
		if reports:
			sum_working_out = sum([x.working_out for x in reports])
			week_stats = (sum_working_out*100)/self.laboriousness
			return_str = '+'+str(int(week_stats))+'%'+' ('+str(int(sum_working_out))+'ч)'
			return return_str
		else:
			return 0

	def month_stats(self):
		end = datetime.datetime.now().date()
		start = end - datetime.timedelta(days=30)
		reports = Task_Report.objects.filter(task_id=self.id,report__create__gte=start)
		if reports:
			sum_working_out = sum([x.working_out for x in reports])
			month_stats = (sum_working_out*100)/self.laboriousness
			return_str = '+'+str(int(month_stats))+'%'+' ('+str(int(sum_working_out))+'ч)'
			return return_str
		else:
			return 0

	def get_remainder(self):
		remainder = 100-self.get_de_facto()
		if remainder>0:
			return remainder
		else:
			return 0 








class Task_History(models.Model):
	task = models.ForeignKey(Task,verbose_name='Задание',on_delete=models.CASCADE)
	create_date = models.DateTimeField(verbose_name='Дата создания',null=True,blank=True)
	on_work = models.DateTimeField(verbose_name='Взято в работу',null=True,blank=True)
	closed = models.DateTimeField(verbose_name='Закрыто',null=True,blank=True)






class Report(models.Model):
	task = models.ManyToManyField(Task,verbose_name='Задание',through='Task_Report',null=True,blank=True)
	foreman = models.ForeignKey(User,verbose_name='Бригадир',on_delete=models.SET_NULL,null=True,blank=True)
	create = models.DateTimeField(verbose_name='Дата создания',auto_now_add=True,null=True,blank=True)
	subdivision = models.ForeignKey(Subdivision,verbose_name='Подразделение',on_delete=models.SET_NULL,null=True,blank=True)
	change = models.IntegerField(verbose_name='Смена',null=True,blank=True)
	brigade = models.ForeignKey(Brigade,verbose_name = 'Бригада',on_delete=models.SET_NULL,null=True,blank=True)

	#Классификация потерь
	drawing = models.FloatField(verbose_name='Отсутствие чертежей',null=True,blank=True)
	deviations = models.FloatField(verbose_name='Отсутствие решения по выявленным отклонениям',null=True,blank=True)
	personal = models.FloatField(verbose_name='Отсутствие персонала',null=True,blank=True)
	otk = models.FloatField(verbose_name='Отсутствие ОТК',null=True,blank=True)
	vp = models.FloatField(verbose_name='Отсутствие ВП и/или представителя заказчика',null=True,blank=True)
	proektant = models.FloatField(verbose_name='Отсутствие представителя проектанта',null=True,blank=True)
	ogt = models.FloatField(verbose_name='Отсутствие представителя ОГТ для решения блокирующих вопросов',null=True,blank=True)
	other_order = models.FloatField(verbose_name='Переход на другой заказ/другие работы',null=True,blank=True)
	ssz = models.FloatField(verbose_name='Отсутствие ССЗ',null=True,blank=True)
	complect_zavod = models.FloatField(verbose_name='Отсутствие комплектующих по межзаводской кооперации',null=True,blank=True)
	complect_workshop = models.FloatField(verbose_name='Отсутствие комплектующих по межцеховой кооперации',null=True,blank=True)
	pki = models.FloatField(verbose_name='Отсутствие ПКИ',null=True,blank=True)
	materials = models.FloatField(verbose_name='Отсутствие расходных/вспомогательных материалов',null=True,blank=True)
	osn = models.FloatField(verbose_name='Отсутствие оснастки',null=True,blank=True)
	instr = models.FloatField(verbose_name='Отсутствие инструмента',null=True,blank=True)
	prisp = models.FloatField(verbose_name='Отсутствие приспособлений',null=True,blank=True)
	card_valid = models.FloatField(verbose_name='Доработка по причине карт разрешений',null=True,blank=True)
	quality = models.FloatField(verbose_name='Добработка по причине исправления качества',null=True,blank=True)
	#-------------------

	def get_absolute_url(self):
		return reverse ('view_reports')
		#return reverse('subdivision_tasks',args=[self.task.subdivision.id])

	def __str__(self):
		string = 'Отчет '+str(self.brigade)+' '+'за '+self.create.strftime('%d-%m-%Y')
		return string





class Task_Report(models.Model):
	task = models.ForeignKey(Task,verbose_name='Задание',on_delete=models.CASCADE,null=True,blank=True)
	working_out = models.FloatField(verbose_name='Значение',null=True,blank=True)
	report = models.ForeignKey(Report,verbose_name='Отчет',on_delete=models.CASCADE,null=True,blank=True)






