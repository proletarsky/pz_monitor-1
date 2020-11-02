import  datetime
import json

#Создаем список нерабочих дней
chill_days=[]

calendar_import=open('machines/chill20202021.csv',mode='r')
chill_days=[]
for x in calendar_import:
    chill_days.append(datetime.date(day=int(x[0:2]),month=int(x[3:5]),year=int(x[6:10])))

