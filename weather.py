import requests, json, time, sys
from datetime import datetime
from pytz import timezone
from subprocess import call
from omega_gpio import OmegaGPIO
from some_functions import connected_to_internet, are_you_subscribed, clear_pins

#Making sure we're connected to the internet, otherwise we just loop and keep checking
online = connected_to_internet()

while online is False:
    print('not online')
    call(["logger", "-t", "weather", "Not online"])
    time.sleep(60)
    online = connected_to_internet()

print('We are online')
call(["logger", "-t", "weather", "we are online"])

#Are you subscribed
subscribed = are_you_subscribed()

while subscribed == 'unsubscribed':
    print('unsubscribed')
    call(["logger", "-t", "weather", "unsubscribed"])
    time.sleep(1800)
    subscribed = are_you_subscribed()

#handling creds
config = '/root/.config.txt'
creds = open(config,'r').read().split('\n')

max1 = creds[0]
max2 = creds[1]
api = creds[2]


#Setting up Omega's pins
try:
    omega = OmegaGPIO()
    clear_pins()
    print('GPIO enabled')
    call(["logger", "-t", "weather", "GPIO enabled"])
           
except:
    print('failed to set up pins')
    call(["logger", "-t", "weather", "failed to set up pins"])
           
#getting maxmind info for own IP address
try:
    
    r = requests.get('https://geoip.maxmind.com/geoip/v2.1/city/me', auth=(max1, max2))
    maxmind_info = r.json()
    location_info = maxmind_info['location']

    location_info['latitude']
    location_info['longitude']

    coords = str(location_info['latitude']), str(location_info['longitude'])

    lat = coords[0]
    long = coords[1]

    coordinates = lat + ',' + long

except:
    print('ip info error')
    call(["logger", "-t", "weather", "ip info error"])

#getting local time, now we have max mind info
def get_time():
    TZ = location_info['time_zone']
    #using timezone ID to get local time
    local = timezone(TZ)
    full_local_time = datetime.now(local)
    h_local_time = full_local_time.strftime('%H')
    m_local_time = full_local_time.strftime('%M')
    m_local_time = 1.66666*int(m_local_time)
    local_time = int(h_local_time) + 0.01*(int(m_local_time))
    return local_time

try:
    local_time = get_time()
    print(local_time)
    call(["logger", "-t", "weather", "local_time"])
except:
    print('couldnt get time')
    call(["logger", "-t", "weather", "couldnt get time"])

#getting weather info
try:

    #Api locations finder
    URL = 'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search.json?q='+ coordinates +'&apikey='+ api

    #Requesting location data, then converting to a library
    res = requests.get(URL)
    locationdata = res.json()
    #Below is location key of Google coordinates
    geokey = locationdata['Key']

    ######

    #Create dictionary
    forecast = {'test':'0'}

    #Creating entries for every hour of the day
    for i in range(25):
            forecast[i] = '0'
            
    #Adding :00 to each key
    forecast = {f'{k}:00': v for k, v in forecast.items()}

except:
    print('fail getting weather data')
    call(["logger", "-t", "weather", "fail getting weather data"])

#Setup is complete, now we go into the main loop
while 1 == 1:
    print('enter loop')
    call(["logger", "-t", "weather", "enter loop"])
    #Loops between 4am and 11pm
    while local_time >= 4 and local_time <= 23:
        print('in second loop')
        call(["logger", "-t", "weather", "in second loop"])
        
        #Saving 9am and 12pm weather so can add it back in after old weather addition
        if local_time >= 21 and local_time <= 25:
            nine_saved_weather = forecast['9:00']
            twelve_saved_weather = forecast['12:00']

            
        #Get weather data for specified location request, then parse to list
        weatherURL= 'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/' + geokey + '?apikey=' + api

        try:
                res1 = requests.get(weatherURL)
                weatherdata = res1.json()

                #Function creates dictionary with hour:weather cond
                def build_dict(x):
                    p = weatherdata[x]   
                    H = p['DateTime']
                    h = (H[11:16])
                    F = p['IconPhrase']
                    forecast[h] = F

        except:
                print('accuweather error')
                call(["logger", "-t", "weather", "accuweather error"])

        #create list of numbers to use in creating forecast w/ build_dict
        numbers = [0,1,2,3,4,5,6,7,8,9,10,11]
        
        try:
            for item in numbers:
                    build_dict(item)
        except:
            print('failed to build dict')

                
        #accounting for weird AccuWeather format change to 08:00 from 8:00 in early morning.
        try:
            forecast['8:00'] = forecast['08:00']

        except:
                print('didnt update 8am')
                call(["logger", "-t", "weather", "didnt update 8am"])

        ##################### Getting historical weather data ###########
        try:
            #Create dictionary
            old_forecast = {'test':'0'}
                    
            #Adding :00 to each key
            old_forecast = {f'{k}:00': v for k, v in old_forecast.items()}

            #Get historical weather data for specified location request, then parse to list
            old_weatherURL= 'http://dataservice.accuweather.com/currentconditions/v1/' + geokey + '/historical/24?apikey=' + api
            old_res = requests.get(old_weatherURL)
            old_weatherdata = old_res.json()

            #Function creates dictionary with hour:weather cond
            def old_build_dict(x):
                p = old_weatherdata[x]   
                H = p['LocalObservationDateTime']
                h = (H[11:14])
                F = p['WeatherText']
                old_forecast[h] = F

            #create list of numbers to use in creating forecast w/ build_dict
            old_numbers = [0,1,2,3,4,5,6, 7, 8, 9, 10, 11, 12]

            for item in old_numbers:
                    old_build_dict(item)

            #how many hours in the past are you going to add to dictionary? don't want to overwrite this evening with yday
            prev = local_time - 5
            ext_prev = local_time - 12
            #temporarily make int, instead of float
            prev = int(prev)
            ext_prev = int(ext_prev)
            
        except:
            print('getting historical weather data error')
        
        #Just 5 hours in the past
        if local_time >= 5 and local_time <= 12:
            for i in range(prev, int(local_time)):

                if int(i) <= 9 and int(i) >= 1:
                    j = (str(i)).zfill(2)
                else:
                    j = i
                try:
                    forecast[(str(i) + ':00')] = str(old_forecast[str(j) + ':'])
                except:
                    print('')

        #12 hours in the past        
        if local_time >= 12 and local_time <= 23:

            for i in range(ext_prev, int(local_time)):
            
                if int(i) <= 9 and int(i) >= 1:
                    j = (str(i)).zfill(2)
                else:
                    j = i
                try:
                    forecast[(str(i) + ':00')] = str(old_forecast[str(j) + ':'])
                except:
                    print('')

                    
        ##################### End of old weather data section ###########        


        #putting saved weather back in for 9am and 12pm (so it's todays not tomorrows)
        if local_time >= 21 and local_time <= 25:
            forecast['9:00'] = nine_saved_weather
            forecast['12:00'] = twelve_saved_weather          

        print(forecast)
        call(["logger", "-t", "weather", str(forecast)])

        #####getting temperature of this hour#####
        try:
                temp_dict = weatherdata[1]
                temp_details = temp_dict['Temperature']

                #temp in fahrenheit
                temp = temp_details['Value']
                temp = int(temp)
                print(temp)
                
        except:
                time.sleep(o)

        #######GPIO_Allocation#######

        #Turning on correct pins/icons
        pin_timer = 0
        try:
            clear_pins()
        except:
            print('fail clear_pins')
            
        #Class conversions
        Rain = ['Rain', 'Drizzle', 'Showers', 'A shower', 'Light rain shower', 'Flurries', 'T-storms', 'Snow', 'Mostly cloudy w/ showers', 'Partly sunny w/ showers', 'Mostly cloudy w/ T-Storms', 'Partly sunny w/ T-Storms', 'Mostly cloudy w/ flurries', 'Partly sunny w/ flurries', 'Mostly cloudy w/ snow', 'Ice', 'Sleet', 'Freezing rain', 'Rain and snow', 'Partly cloudy w/ showers', 'Mostly cloudy w/ showers', 'Partly cloudy w/ T-Storms', 'Mostly cloudy w/ T-Storms', 'Mostly cloudy w/ flurries', 'Mostly cloudy w/ snow']
        Cloud = ['Mostly cloudy', 'Fog', 'Partly cloudy', 'Cloudy', 'Dreary (Overcast)', 'Fog', 'Some clouds', 'Some clouds', 'Intermittent clouds']
        Sun = ['Clear', 'Partly sunny', 'Mostly sunny', 'Sunny', 'Hazy', 'Hazy sunshine', 'Intermittent Clouds', 'Mostly clear', 'Clouds and sun']
        #Cycle lasts 60mins
        while pin_timer <= 3599:
                print(pin_timer)
                call(["logger", "-t", "weather", str(pin_timer)])
                try:
                    
                    #8am
                    if forecast['8:00'] in Rain:                        
                        omega.pin_on(2)
                        print('8R')
                        call(["logger", "-t", "weather", "8R"])

                    if forecast['8:00'] in Cloud:
                        omega.pin_on(17)
                        print('8C')
                        call(["logger", "-t", "weather", "8C"])

                    if forecast['8:00'] in Sun:
                        omega.pin_on(16)
                        print('8S')
                        call(["logger", "-t", "weather", "8S"])

                    #12pm
                    if forecast['12:00'] in Rain: 
                        omega.pin_on(15)
                        print('12R')
                        call(["logger", "-t", "weather", "12R"])

                    if forecast['12:00'] in Cloud: 
                        omega.pin_on(46)
                        print('12C')
                        call(["logger", "-t", "weather", "12C"])

                    if forecast['12:00'] in Sun:
                        omega.pin_on(13)
                        print('12S')
                        call(["logger", "-t", "weather", "12S"])

                    #4pm
                    if forecast['16:00'] in Rain:
                        omega.pin_on(19)
                        print('16R')
                        call(["logger", "-t", "weather", "16R"])

                    if forecast['16:00'] in Cloud:
                        omega.pin_on(4)
                        print('16C')
                        call(["logger", "-t", "weather", "16C"])

                    if forecast['16:00'] in Sun:
                        omega.pin_on(5)
                        print('16S')
                        call(["logger", "-t", "weather", "16S"])

                    #8pm
                    if forecast['20:00'] in Rain:
                        omega.pin_on(18)
                        print('20R')
                        call(["logger", "-t", "weather", "20R"])

                    if forecast['20:00'] in Cloud:
                        omega.pin_on(3)
                        print('20C')
                        call(["logger", "-t", "weather", "20C"])

                    if forecast['20:00'] in Sun:
                        omega.pin_on(0)
                        print('20S')
                        call(["logger", "-t", "weather", "20S"])

                    if pin_timer <= 299:
                        #less sleep while pins are on
                        time.sleep(300)
                        pin_timer = pin_timer + 300
                    else:
                        #Pulse - 3mins on
                        time.sleep(180)
                        pin_timer = pin_timer + 180
                        call(["logger", "-t", "weather", "just 3 mins on before 1 min off"])
                        print("just 3 mins on before 1 min off")

                    #Pulse - 1min off
                    #If temp 18c or lower, then pulse for less
                    if temp <= 64:
                        clear_pins()
                        time.sleep(20)
                        pin_timer = pin_timer + 20
                        print('cold, so small pulse')
                    else:
                        clear_pins()
                        time.sleep(120)
                        pin_timer = pin_timer + 120
                        call(["logger", "-t", "weather", "just pulsed for 1min, outside temp above 12c"])
                    
                # If there's problems turning on pins, we wait before re-trying.    
                except:
                    pin_timer = pin_timer + 120
                    time.sleep(120)

                
        else:
            print('pins turning off and resetting pin_timer')
            call(["logger", "-t", "weather", "pins turning off and resetting pin_timer"])
            pin_timer = 0
            try:
                local_time = get_time()
            except:
                print('failed to get time')

            #turning off pins for break, how long dictated by outside temp (v.rough proxy to room temp)
            try:
                #If temp 18c or lower then sleep for shorter
                if temp <= 64:
                    call(["logger", "-t", "weather", "60mins up, cold, so only 1min break"])
                    time.sleep(120)
                    clear_pins()
                    time.sleep(60)
                else:
                    call(["logger", "-t", "weather", "60mins up, warm, time for a 3min break"])
                    clear_pins()
                    time.sleep(180)
                    
            except:
                    print('60mins up, time for a 3min break')
                    time.sleep(180)



        #Updates local_time
        try:
            local_time = get_time()
            print("time is "+(str(local_time)))
            call(["logger", "-t", "weather", str(local_time)])
        except:
            print('fail')

    else:
        try:
            #sleeps and updates local_time
            print('sleep_mode')
            call(["logger", "-t", "weather", "sleep_mode"])
            print("time is "+(str(local_time)))
            call(["logger", "-t", "weather", str(local_time)])
        except:
            print('fail 1')
            
        time.sleep(1800)
        
        #turning pins off for sleep mode
        try:
            clear_pins()
        except:
            print('')       

        local_time = get_time()
        
