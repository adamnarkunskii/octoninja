from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from gpsweb.models import *
from gpsweb.forms import RegistrationForm, LoginForm
import datetime
from gpsweb.utils import utils


def UserRegistration(request):
    if request.user.is_authenticated():
            return HttpResponseRedirect('/main_map')
    if request.method == 'POST':
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = User.objects.create_user(username=form.cleaned_data['username'],
                                                password=form.cleaned_data['password'],
                                                email=form.cleaned_data['email'])
                user.save()
                user.first_name=form.cleaned_data['first_name']
                user.last_name=form.cleaned_data['last_name']
                user.save()
                return HttpResponseRedirect('/main_map')
            else:
                return render_to_response('register.html', {'form':form}, context_instance=RequestContext(request))
    else:
            ''' user is not submitting the form, show them a blank registration form '''
            form = RegistrationForm()
            context = {'form': form}
            return render_to_response('register.html', context, context_instance=RequestContext(request))

def UserLogin(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/main')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/main')
            else:
                return render_to_response('login.html', {'form':form}, context_instance=RequestContext(request))
        else:
            return render_to_response('login.html', {'form':form}, context_instance=RequestContext(request))
    else:
        ''' user is not submitting the form, show them the login form '''
        form = LoginForm()
        context = {'form':form}
        return render_to_response('login.html', context, context_instance=RequestContext(request))

def UserLogout(request):
    logout(request)
    return HttpResponseRedirect('/')
#####################    Main View     ##################### 
@login_required
def mainView(request):
    user = request.user
    user_id = user.id
    cars = Car.objects.filter(owner_id=user_id)
    list_of_locations = []
    for car in cars:
        try:
            last_location = LocationLog.objects.filter(car=car).latest('timestamp')
        except LocationLog.DoesNotExist:
            pass
        else:
            list_of_locations.append(last_location)

    context = {
        'menuParams' : utils.initMenuParameters(user),
        'list_of_locations': list_of_locations,
        'user' : user,
        'map_center_lat': '32.047818',
        'map_center_long': '34.761265',
    }
    return render(request, 'mainView/mainView.html', context)
#####################    Car History     #####################
@login_required 
def carHistory(request, car_id, fromDate=None, toDate=None):
    user = request.user
    user_id = user.id
    car = Car.objects.filter(owner_id=user_id).filter(id__in=car_id)
    if not car:
        return HttpResponseRedirect('/')

    fromDateStr = utils.formatDateStr(fromDate)
    toDateStr = utils.formatDateStr(toDate, zeroHour=False)
        
    list_of_locations = LocationLog.objects.filter(car=car).filter(timestamp__range=[fromDateStr,toDateStr]).order_by('-timestamp')
    

    context = {
        'menuParams' : utils.initMenuParameters(user),
        'fromDateStr' : fromDateStr[:-9], # [:-9] truncates the hour
        'toDateStr' : toDateStr[:-9],
        'route_details':utils.RouteDetails(list_of_locations),
        'user' : user,
        'car': car[0],
        'primary_driver' : car[0].getPrimaryDriversByDateRange(fromDateStr,toDateStr),
        'temporary_drivers' : car[0].getTemporaryDriversByDateRange(fromDateStr,toDateStr),
        'map_center_lat' : '32.047818',
        'map_center_long' : '34.761265',
    }

    return render(request, 'carHistory/carHistory.html', context)         
    
#####################    Driver History     #####################   
@login_required 
def driverHistory(request, driver_id, fromDate=None, toDate=None):
    user = request.user
    user_id = user.id
    driver = Driver.objects.filter(owner_id=user_id).filter(id__in=driver_id)
    if not driver:
        return HttpResponseRedirect('/')
    fromDateStr = utils.formatDateStr(fromDate)
    toDateStr = utils.formatDateStr(toDate, zeroHour=False)
    #Need to get all primary\temporary of the driver in this dates

    temporary = TemporaryDriver.objects.filter(driver = driver).filter(Q(end__gte = fromDateStr) | Q(start__lte = toDateStr))
    temporaryPeriodsLocations = utils.getLocationsOfPeriod(fromDateStr, toDateStr, temporary)
    primary = PrimaryDriver.objects.filter(driver = driver).filter(Q(end__gte = fromDateStr) | Q(end = None) )
    primaryPeriodsLocations = utils.getLocationsOfPeriod(fromDateStr, toDateStr, primary)

    
 
    context = {
        'menuParams' : utils.initMenuParameters(user),
        'fromDateStr' : fromDateStr[:-9], # [:-9] truncates the hour
        'toDateStr' : toDateStr[:-9],
        'temporaryPeriodsLocations' : temporaryPeriodsLocations,
        'primaryPeriodsLocations' : primaryPeriodsLocations,
        'user' : user,
        'driver' : driver[0],
        'map_center_lat' : '32.047818',
        'map_center_long' : '34.761265',
    }
    return render(request, 'driverHistory/driverHistory.html', context)        

#####################   Alerts    #####################
@login_required 
def alerts(request):
    user = request.user
    alerts_log = AlertLog.objects.filter(alert__car__owner = user).filter(marked_as_read = False).order_by('location_log__timestamp')
    
    first_loop = True
    alert_group = []
    alerts_group_array = []
    for cur_alert in alerts_log:
        if cur_alert.notification_sent and not first_loop: #close old group and start new group
            alerts_group_array.append(alert_group)
            alert_group = []
            first_loop = False
        alert_group.append(cur_alert)
        first_loop = False
    if alert_group:
        alerts_group_array.append(alert_group)
  
    context = {
        'menuParams' : utils.initMenuParameters(user),
        'user' : user,
        'map_center_lat' : '32.047818',
        'map_center_long' : '34.761265',
        'alertsArrays':alerts_group_array,
    }
    return render(request, 'alert/alerts.html', context)              
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    