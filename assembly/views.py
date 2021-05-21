from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import *
from django.views.generic import ListView,CreateView,UpdateView,DetailView
from .filters import *
import json
from django.shortcuts import redirect
import datetime




def main(request):
	return render(request,'assembly/main.html')


class View_pdo_tasks(ListView):
	model = Task
	template_name = 'assembly/pdo_tasks.html'
	context_object_name = 'Tasks'

	def get_context_data(self,**kwargs):
		context = super().get_context_data(**kwargs)
		context['filter'] = TaskFilter(self.request.GET,queryset=self.get_queryset())
		return context





class Create_task(CreateView):
	model=Task
	template_name='assembly/pdo_create.html'
	fields = ['description','name','order','date','laboriousness','subdivision','creator']





class Update_task(UpdateView):
	model = Task
	template_name = 'assembly/pdo_update.html'
	fields = ['description','name','order','date','laboriousness','subdivision']





class Active_tasks(ListView):
	model=Task
	template_name = 'assembly/active_tasks.html'
	context_object_name = 'active_tasks'

	def get_queryset(self):
 		queryset = Task.objects.filter(status__in=[1,2]).order_by('id')
 		return queryset

	def get_context_data(self,**kwargs):
		context = super().get_context_data(**kwargs)
		context['filter'] = TaskFilter(self.request.GET,queryset=self.get_queryset())

		if self.request.GET.get('task_id'):
			task_id = self.request.GET.get('task_id')
			obj = Task.objects.get(id=task_id)
			if obj.status == 2:
				obj.status=3
				obj.save()	
		return context




# class Subdivision_tasks(ListView):
# 	model=Task
# 	template_name = 'assembly/subdivision_tasks.html'

# 	def get_queryset(self):
# 		sub = self.kwargs['subdivision']
# 		queryset = Task.objects.filter(subdivision_id=sub,status__in=[1,2]).order_by('id')
# 		return queryset


# 	def get_context_data(self):
# 		context = super().get_context_data()
# 		sub = self.kwargs['subdivision']
# 		objects = self.get_queryset()
# 		context['objects']=objects
# 		context['current_area'] = sub
# 		if self.request.GET.get('task_id'):
# 			task_id = self.request.GET.get('task_id')
# 			obj = Task.objects.get(id=task_id)
# 			if obj.status == 2:
# 				obj.status=3
# 				obj.save()
# 		return context






class Task_story(ListView):
	model=Task_History
	template_name = 'assembly/task_story.html'
	context_object_name = 'Storys'

	def get_queryset(self):
		queryset = Task_History.objects.filter(closed__isnull=False)
		return queryset






class Create_report(CreateView):
	model=Report
	template_name='assembly/report_create.html'
	fields= (
	'foreman',
	'subdivision', 
	'change', 
	'brigade', 
	'drawing' ,
	'deviations', 
	'personal', 
	'otk',
	'vp',
	'proektant', 
	'ogt', 
	'other_order', 
	'ssz',
	'complect_zavod', 
	'complect_workshop',
	'pki', 
	'materials', 
	'osn', 
	'instr',
	'prisp', 
	'card_valid',
	'quality'
	)

	def form_valid(self, form):
		instance = form.save()
		if self.request.POST.get('tasks_values'):
			tasks_values = self.request.POST.get('tasks_values')
			tasks_values = json.loads(tasks_values)
			for x in tasks_values:
				if float(tasks_values[x])>0:
					Task_Report.objects.create(task_id=x,report_id=instance.id,working_out = float(tasks_values[x]))
				else:
					continue
		return redirect(instance.get_absolute_url())

	def get_context_data(self,**kwargs):
		context = super().get_context_data(**kwargs)
		if self.request.user.id and self.request.user.groups.filter(id=5):
			foreman_id = self.request.user.id
			brigade = Brigade.objects.get(foreman=foreman_id)
			subdivision = Subdivision.objects.get(id=brigade.subdivision.id)
			tasks = Task.objects.filter(subdivision=subdivision,status__in=(1,2)).order_by('id')
			context['brigade'] = brigade
			context['subdivision'] = subdivision
			context['tasks'] = tasks
			now = datetime.datetime.now().date()
			context['now'] = now.strftime('%d.%m.%Y')
		return context



class View_reports(ListView):
	model = Report
	template_name = 'assembly/view_reports.html'
	context_object_name = 'reports'

	def get_queryset(self):
		reports = Report.objects.all()
		print(self.request.user.id)
		if self.request.user.id and self.request.user.groups.filter(id=5):
			foreman_id = self.request.user.id
			brigade = Brigade.objects.get(foreman=foreman_id)
			subdivision = Subdivision.objects.get(id=brigade.subdivision.id)
			reports = Report.objects.filter(subdivision=subdivision).order_by('-id')
		queryset = reports
		return queryset




class Report_view(DetailView):
	model=Report
	template_name = 'assembly/report_view.html'

	def get_context_data(self,**kwargs):
		context = super().get_context_data(**kwargs)
		tasks = Task_Report.objects.filter(report_id=self.object.id)
		context['tasks'] = tasks
		return context




class Update_report(UpdateView):
	model=Report
	template_name = 'assembly/report_update.html'
	fields=(
	'drawing' ,
	'deviations', 
	'personal', 
	'otk',
	'vp',
	'proektant', 
	'ogt', 
	'other_order', 
	'ssz',
	'complect_zavod', 
	'complect_workshop',
	'pki', 
	'materials', 
	'osn', 
	'instr',
	'prisp', 
	'card_valid',
	'quality'
		)

	def form_valid(self, form):
		instance = form.save()
		print(self.request.POST)
		if self.request.POST.get('tasks_values'):
			tasks_values = self.request.POST.get('tasks_values')
			tasks_values = json.loads(tasks_values)

			
			#Обновляем значения у заданий в отчете	
			del_objs = Task_Report.objects.filter(report_id=instance.id)
			#Сначала удаляем объекты
			for y in del_objs: y.delete()
			#А потом записываем новые значения, если необходимо
			for x in tasks_values:
				if float(tasks_values[x])>0:
					Task_Report.objects.create(task_id=x,report_id=instance.id,working_out = float(tasks_values[x]))
		return redirect(instance.get_absolute_url())

	def get_context_data(self,**kwargs):
		
		context = super(Update_report, self).get_context_data(**kwargs)
		if self.request.user.id and self.request.user.groups.filter(id=5):
			foreman_id = self.request.user.id
			brigade = Brigade.objects.get(foreman=foreman_id)
			subdivision = Subdivision.objects.get(id=brigade.subdivision.id)
			active_tasks = Task.objects.filter(subdivision=subdivision,status__in=(1,2)).order_by('id')
			context['active_tasks'] = active_tasks
			context['brigade']=brigade
		tasks = Task_Report.objects.filter(report_id=self.object.id)
		tasks_id = [x.task_id for x in tasks]
		context['tasks'] = tasks
		context['tasks_id'] = tasks_id


		return context





