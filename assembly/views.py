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
		context['check']=0
		if self.request.user.id and self.request.user.groups.filter(id=4):
			context['check']=1
		return context





class Create_task(CreateView):
	model=Task
	template_name='assembly/pdo_create.html'
	fields = ['description','name','order','date','laboriousness','subdivision','creator']

	def get_context_data(self,**kwargs):
		context = super().get_context_data(**kwargs)
		context['check']=0
		if self.request.user.id and self.request.user.groups.filter(id=4):
			context['check']=1
		return context






class Update_task(UpdateView):
	model = Task
	template_name = 'assembly/pdo_update.html'
	fields = ['description','name','order','date','laboriousness','subdivision']


	def get_context_data(self,**kwargs):
		context = super().get_context_data(**kwargs)
		context['check']=0
		if self.request.user.id and self.request.user.groups.filter(id=4):
			context['check']=1
		return context




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
	'quality',
	'nothing'
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
			reports = Report.objects.filter(subdivision=subdivision).order_by('-creating')
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
	'quality',
	'nothing'
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



def assembly_statistics(request):
	end = datetime.datetime.now().date()
	start = end-datetime.timedelta(days=7)

	subdivisions = Subdivision.objects.all()
	subdivision_id = tuple(x.id for x in  subdivisions)
	return_subdivision = 0
	all_works_time = sum([x.quantity*8 for x in Brigade.objects.all()])

	if request.GET.get('subdivision_id'):
		subdivision_id = int(request.GET.get('subdivision_id')),
		return_subdivision = subdivision_id[0]
		all_works_time = sum([x.quantity*8 for x in Brigade.objects.filter(subdivision_id=subdivision_id)])

	if request.GET.get('start_date'):
		start_get = request.GET.get('start_date')
		start = datetime.date(year=int(start_get[0:4:1]),month=int(start_get[5:7:1]),day=int(start_get[8:10:1]))
	if request.GET.get('end_date'):
		end_get = request.GET.get('end_date')
		end = datetime.date(year=int(end_get[0:4:1]),month=int(end_get[5:7:1]),day=int(end_get[8:10:1]))

	delta_days = (end-start).days
	working_date = []
	working_out = []

	for x in range(0,delta_days+1):
		working_date.append(start+datetime.timedelta(days=x))


	for x in working_date:
		current_date=x.strftime('%Y-%m-%d')
		sql_query = Task_Report.objects.raw('''select 1 as id,coalesce(sum(b.working_out),0) as result
												from assembly_report a
												join assembly_task_report b on a.id=b.report_id
												where a.subdivision_id  in %(subdivision_id)s
												and date(creating) = %(current_date)s''',params = {'subdivision_id':subdivision_id,'current_date':current_date})
		working_out.append([current_date,sql_query[0].result,(sql_query[0].result/all_works_time)*100])

	context={}
	context['working_out'] = working_out


	end = end.strftime('%Y-%m-%d')
	start = start.strftime('%Y-%m-%d')



	# work = Task_Report.objects.raw('''select 1 as id,
	# 									coalesce(sum(b.working_out),0) as work
	# 									from assembly_report a
	# 									join assembly_task_report b on a.id=b.report_id
	# 									where a.subdivision_id  in %(subdivision_id)s
	# 									and date(creating) >= %(start)s
	# 									and date(creating)<=%(end)s''', params = {'subdivision_id':subdivision_id,'start':start,'end':end})

	# context['work'] = work[0]
	# context['all_works_time'] = all_works_time

	losses_query = Task_Report.objects.raw('''
			select 1 as id,
		coalesce(sum(change),0) as change,
		coalesce(sum(drawing),0) as drawing,
		coalesce(sum(deviations),0) as deviations,
		coalesce(sum(personal),0) as personal,
		coalesce(sum(otk),0) as otk,
		coalesce(sum(vp),0) as vp,
		coalesce(sum(proektant),0) as proektant,
		coalesce(sum(ogt),0) as ogt,
		coalesce(sum(other_order),0) as other_order,
		coalesce(sum(ssz),0) as ssz,
		coalesce(sum(complect_zavod),0) as complect_zavod,
		coalesce(sum(complect_workshop),0) as complect_workshop,
		coalesce(sum(pki),0) as pki,
		coalesce(sum(materials),0) as materials,
		coalesce(sum(osn),0) as osn,
		coalesce(sum(instr),0) as instr,
		coalesce(sum(prisp),0) as prisp,
		coalesce(sum(card_valid),0) as card_valid,
		coalesce(sum(quality),0) as quality,
		coalesce(sum(nothing),0) as nothing
	from assembly_report a
	where subdivision_id in %(subdivision_id)s
	and date(creating) >= %(start)s
	and date(creating)<=%(end)s''', params = {'subdivision_id':subdivision_id,'start':start,'end':end})

	context['losses'] = losses_query
	filter = calendar_repair(0,queryset=Report.objects.all())
	context['filter'] = filter
	context['subdivisions'] = Subdivision.objects.all()
	context['start'] = start
	context['end'] = end
	context['subdivision'] = return_subdivision
	return render(request,'assembly/assembly_statistics.html',context)






