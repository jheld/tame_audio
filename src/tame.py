import time
import threading
import os
import ujson
import traceback
import argparse

import bottle
import alsaaudio
# has issue on the pi
# import soundmeter
# from soundmeter.monitor import Meter

from math import log10

driver_shared_data = {'cycle_time': 3}

def audio_meter(driver_shared_data):
    while True:
        try:
            m = Meter(collect=True, seconds=2)
            m.start()
            m.stop()
            driver_shared_data['db'] = 20 * log10(m._data['avg']/(32678.0 - 32677.0))
            print('metered db: {}'.format(driver_shared_data['db']))
        except Exception:
            pass

def tame_driver(driver_shared_data=None):
    """

    :param driver_shared_data: python shared object for runtime data
    :return:
    """
    if driver_shared_data is None:
        driver_shared_data = {}
    while True:
        stopped = driver_shared_data.get('stop', False)
        if not stopped:
            default_mixer = alsaaudio.Mixer()
            # print('have data: {}'.format(driver_shared_data))
            adjustment_mode = driver_shared_data.get('mode', 'linear')
            preferred_audio_range = driver_shared_data.get('range', (20, 50, ))
            min_db, max_db = preferred_audio_range
            current_decibel_level = driver_shared_data.get('db', 35)
            current_volume = int(default_mixer.getvolume()[0])
            sweet_spot = driver_shared_data.get('sweet_spot', float(sum(preferred_audio_range)) / len(preferred_audio_range))
            print('current_volume: {}'.format(current_volume))
            print('preferred range: {}'.format(preferred_audio_range))
            try:
                # TODO: reinstitute sweet_spot when ready.
                # if current_decibel_level < sweet_spot and (current_decibel_level >= sweet_spot - 15 and current_decibel_level < preferred_audio_range[1] and preferred_audio_range[1] < preferred_audio_range[0]):
                #     default_mixer.setvolume(current_volume + 3)
                # if current_decibel_level == sweet_spot or current_decibel_level== sweet_spot - 2 or current_decibel_level == sweet_spot + 2:
                #     time.sleep(2)
                #     continue
                if current_decibel_level > max_db:
                    print('lowering')
                    default_mixer.setvolume(current_volume - 3)
                elif current_volume < min_db:
                    print('raising')
                    default_mixer.setvolume(current_volume + 3)
                elif (int(current_decibel_level) < int(sweet_spot) - 8) and sweet_spot - 8 > min_db:
                    default_mixer.setvolume(current_volume + 3)
                elif (int(current_decibel_level) > int(sweet_spot) + 8) and sweet_spot + 8 < max_db:
                    default_mixer.setvolume(current_volume - 3)

            except alsaaudio.ALSAAudioError as e:
                print(e)
            time.sleep(driver_shared_data.get('cycle_time', 3))
        else:
            time.sleep(1)

@bottle.route('/adjust', method='POST')
@bottle.route('/adjust/', method='POST')
def index():
    audio_data = ujson.loads(list(bottle.request.POST.keys())[0])
    global driver_shared_data
    print('Full request: {}'.format(audio_data))
    print('Received REST db: {}'.format(int(audio_data['value'])))
    driver_shared_data['db'] = int(audio_data['value'])

@bottle.route('/adjust/')
@bottle.route('/adjust')
def index_get():
    global driver_shared_data
    cycle_time = int(ujson.loads(bottle.request.GET.get('cycle_time', '-1')))
    if cycle_time > -1:
        driver_shared_data['cycle_time'] = cycle_time
    can_raise = ujson.loads(bottle.request.GET.get('raise', 'false'))
    if can_raise:
        driver_shared_data['db'] = driver_shared_data.get('db', 35) + 5
    can_lower = ujson.loads(bottle.request.GET.get('lower', 'false'))
    if can_lower:
        driver_shared_data['db'] = driver_shared_data.get('db', 35) - 5
    can_raise_max = ujson.loads(bottle.request.GET.get('raise_max', 'false'))
    if can_raise_max:
        min_db, max_db = driver_shared_data.get('range', (20, 50, ))
        driver_shared_data['range' ] = min_db, max_db + 5
    can_lower_min = ujson.loads(bottle.request.GET.get('lower_min', 'false'))
    if can_lower_min:
        min_db, max_db = driver_shared_data.get('range', (20, 50, ))
        driver_shared_data['range' ] = min_db - 5, max_db
    
    stop = ujson.loads(bottle.request.GET.get('stop', 'false'))
    if stop:
        driver_shared_data['stop'] = True
        driver_shared_data['start'] = False
    start = ujson.loads(bottle.request.GET.get('start', 'false'))
    if start:
        driver_shared_data['stop'] = False
        driver_shared_data['start'] = True

    reset = ujson.loads(bottle.request.GET.get('reset', 'false'))
    if reset:
        driver_shared_data['stop'] = False
        driver_shared_data['start'] = False
        driver_shared_data['range' ] = (20, 50)
        
    upper_range = ujson.loads(bottle.request.GET.get('too_high', 'false'))
    if upper_range:
        new_range = driver_shared_data.get('range', (20, 50, ))
        min_db, max_db = new_range
        new_value = (max_db - 5) or driver_shared_data.get('db', 35)
        max_db = new_value
        # if min_db < max_db:
        #     max_db = new_value - 5
        #     min_db = min_db if max_db >= min_db else max_db - 5
        # elif min_db > max_db:
        #     max_db = new_value + 5
        if max_db < min_db:
            min_db = max_db - 5
        new_range = min_db, max_db
        driver_shared_data['range'] = new_range
    lower_range = ujson.loads(bottle.request.GET.get('too_low', 'false'))
    if lower_range:
        new_range = driver_shared_data.get('range', (20, 50, ))
        min_db, max_db = new_range
        new_value = (min_db + 5) or driver_shared_data.get('db', 35)
        min_db = new_value
        # if max_db < min_db:
        #     min_db = new_value - 5
        #     max_db = max_db if min_db >= max_db else min_db - 5
        # elif max_db > min_db:
        #     min_db = new_value + 5
        if min_db > max_db:
            max_db = min_db + 5
        new_range = min_db, max_db
        driver_shared_data['range'] = new_range
    just_right = ujson.loads(bottle.request.GET.get('just_right', 'true'))
    if just_right:
        driver_shared_data['sweet_spot'] = driver_shared_data.get('db', 35)
    return ujson.dumps([['cur_db', driver_shared_data.get('db', 'NA')], ['range', driver_shared_data.get('range', (20, 50, ))]])


@bottle.route('/static/<filename>')
def server_static(filename):
    return bottle.static_file(filename, root='./')

@bottle.route('/hello')
def hello():
    if not os.path.exists('./audio_file.json'):
        open('./audio_file.json', 'wb').write('{}')
    audio_data = ujson.load(open('./audio_file.json', 'rbU'))
    mor_max = int(audio_data.get('MorMax', 50))
    mor_min = int(audio_data.get('MorMin', 20))
    eve_max = int(audio_data.get('EveMax', 50))
    eve_min = int(audio_data.get('EveMin', 20))
    nig_max = int(audio_data.get('NigMax', 50))
    nig_min = int(audio_data.get('NigMin', 20))

    return bottle.template('./firstpg.tpl', MorMin=mor_min, MorMax=mor_max, EveMin=eve_min, EveMax=eve_max, NigMin=nig_min, NigMax=nig_max)

@bottle.route('/settings', method ='Get')
def hello1():
        if not os.path.exists('./audio_file.json'):
            open('./audio_file.json', 'wb').write('{}')
        audio_data = ujson.load(open('./audio_file.json', 'rbU'))

    	MorMax = audio_data.get('MorMax', 50) 
	MorMin = audio_data.get('MorMin', 20)
	EveMax= audio_data.get('EveMax', 50) 
	EveMin = audio_data.get('EveMin', 20) 
	NigMax= audio_data.get('NigMax', 50) 
	NigMin = audio_data.get('NigMin', 20)

	return bottle.template('./secpg.tpl', MorMin=MorMin, MorMax=MorMax, EveMin=EveMin, EveMax=EveMax, NigMin=NigMin, NigMax=NigMax)


@bottle.route('/updatepg')
def hello2():
    mor_max = bottle.request.query.get('MorMax')
    mor_min = bottle.request.query.get('MorMin')
    eve_max = bottle.request.query.get('EveMax')
    eve_min = bottle.request.query.get('EveMin')
    nig_max = bottle.request.query.get('NigMax')
    nig_min = bottle.request.query.get('NigMin')

    if not os.path.exists('./audio_file.json'):
        open('./audio_file.json', 'wb').write('{}')
    audio_data = ujson.load(open('./audio_file.json', 'rbU'))
    audio_data['MorMax'] = int(mor_max)
    audio_data['MorMin'] = int(mor_min)
    audio_data['EveMax'] = int(eve_max)
    audio_data['EveMin'] = int(eve_min)
    audio_data['NigMax'] = int(nig_max)
    audio_data['NigMin'] = int(nig_min)

    ujson.dump(audio_data, open('./audio_file.json', 'wb'))
    bottle.redirect('/hello')
   



tame_thread = threading.Thread(target=tame_driver, kwargs=dict(driver_shared_data=driver_shared_data))
tame_thread.daemon = True

audio_thread = threading.Thread(target=audio_meter, args=(driver_shared_data, ))
audio_thread.daemon = True
# audio_thread.start()
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--only-meter', type=bool, help='Whether or not we only want to meter the sound -- not provide control',
                    default=False)
    args = ap.parse_args()
    if not args.only_meter:
        tame_thread.start()
    bottle.run(host='0.0.0.0', port=8000)
    # while True:
    #     time.sleep(2)

