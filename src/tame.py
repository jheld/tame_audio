import time
import threading
import json
import traceback

import bottle
import alsaaudio
import soundmeter
from soundmeter.monitor import Meter

from math import log10

def audio_meter(driver_shared_data):
    while True:
        m = Meter(collect=True, seconds=2)
        m.start()
        m.stop()
        driver_shared_data['db'] = 20 * log10(m._data['avg']/32678.0)

def tame_driver(driver_shared_data=None):
    """

    :param driver_shared_data: python shared object for runtime data
    :return:
    """
    if driver_shared_data is None:
        driver_shared_data = {}
    while True:
        default_mixer = alsaaudio.Mixer()
        # print('have data: {}'.format(driver_shared_data))
        adjustment_mode = driver_shared_data.get('mode', 'linear')
        preferred_audio_range = driver_shared_data.get('range', (-40, -30, ))
        current_decibel_level = driver_shared_data.get('db', -75)
        print('db from meter: {}'.format(current_decibel_level))
        current_volume = int(default_mixer.getvolume()[0])
        sweet_spot = float(sum(preferred_audio_range)) / len(preferred_audio_range)
        print('current_volume: {}'.format(current_volume))
        try:
            if current_decibel_level < sweet_spot and current_decibel_level >= sweet_spot - 15:
                default_mixer.setvolume(current_volume + 3)
            elif current_decibel_level == sweet_spot or current_decibel_level== sweet_spot - 2 or current_decibel_level == sweet_spot + 2:
                time.sleep(2)
                continue
            elif current_decibel_level < preferred_audio_range[0]:
                default_mixer.setvolume(current_volume + 3)
            elif current_decibel_level > preferred_audio_range[1]:
                default_mixer.setvolume(current_volume - 3)
        except alsaaudio.ALSAAudioError as e:
            print(e)
        time.sleep(2)

@bottle.route('/', method='POST')
@bottle.route('', method='POST')
def index():
    pass
    # audio_data = json.loads(list(bottle.request.POST.keys())[0])
    # print(audio_data)
    # global driver_shared_data
    # driver_shared_data['db'] = float(audio_data['value'])


@bottle.route('/')
@bottle.route('')
def index_get():
    upper_range = json.loads(bottle.request.GET.get('too_high', 'false'))
    if upper_range:
        global driver_shared_data
        driver_shared_data['range'] = driver_shared_data.get('range', (-40, -30, ))[0], driver_shared_data['db'] - 20
    lower_range = json.loads(bottle.request.GET.get('too_low', 'false'))
    if lower_range:
        global driver_shared_data
        driver_shared_data['range'] = driver_shared_data['db'] + 20, driver_shared_data.get('range', (-40, -30, ))[1]
    return json.dumps(driver_shared_data['db'])


driver_shared_data = {}
tame_thread = threading.Thread(target=tame_driver, kwargs=dict(driver_shared_data=driver_shared_data))
tame_thread.daemon = True
tame_thread.start()

audio_thread = threading.Thread(target=audio_meter, args=(driver_shared_data, ))
audio_thread.daemon = True
audio_thread.start()

if __name__ == '__main__':
    bottle.run(host='0.0.0.0')
    # while True:
    #     time.sleep(2)

