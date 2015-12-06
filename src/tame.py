import time
import threading
import json
import traceback
import argparse

import bottle
import alsaaudio
import soundmeter
from soundmeter.monitor import Meter

from math import log10

driver_shared_data = {}

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
        default_mixer = alsaaudio.Mixer()
        # print('have data: {}'.format(driver_shared_data))
        adjustment_mode = driver_shared_data.get('mode', 'linear')
        preferred_audio_range = driver_shared_data.get('range', (20, 50, ))
        min_db, max_db = preferred_audio_range
        current_decibel_level = driver_shared_data.get('db', 30)
        current_volume = int(default_mixer.getvolume()[0])
        sweet_spot = float(sum(preferred_audio_range)) / len(preferred_audio_range)
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
                print('LOWERING!')
                default_mixer.setvolume(current_volume - 3)
            elif current_volume < min_db:
                print('RAISING!')
                default_mixer.setvolume(current_volume + 3)
            elif int(current_decibel_level) in [_ for _ in xrange(int(sweet_spot) - 20, int(sweet_spot) - 5)]:
                print('SWEET SPOT RAISING!')
                default_mixer.setvolume(current_volume + 3)
            elif int(current_decibel_level) in [_ for _ in xrange(int(sweet_spot) + 5, int(sweet_spot) + 20)]:
                print('SWEET SPOT LOWERING!')
                default_mixer.setvolume(current_volume - 3)

        except alsaaudio.ALSAAudioError as e:
            print(e)
        time.sleep(2)

@bottle.route('/', method='POST')
@bottle.route('', method='POST')
def index():
    audio_data = json.loads(list(bottle.request.POST.keys())[0])
    global driver_shared_data
    driver_shared_data['db'] = float(audio_data['value'])
    print('REST db: {}'.format(driver_shared_data['db']))

@bottle.route('/')
@bottle.route('')
def index_get():
    upper_range = json.loads(bottle.request.GET.get('too_high', 'false'))
    if upper_range:
        new_range = driver_shared_data.get('range', (20, 50, ))
        new_value = driver_shared_data['db']
        min_db, max_db = new_range
        if min_db < max_db:
            max_db = new_value - 5
            min_db = min_db if max_db >= min_db else max_db - 5
        elif min_db > max_db:
            max_db = new_value + 5
        new_range = min_db, max_db
        driver_shared_data['range'] = new_range
        print('\n\n\n\nI said TOO HIGH!\n\n\n\n')
    lower_range = json.loads(bottle.request.GET.get('too_low', 'false'))
    if lower_range:
        new_range = driver_shared_data.get('range', (20, 50, ))
        new_value = driver_shared_data['db']
        min_db, max_db = new_range
        if max_db < min_db:
            min_db = new_value - 5
            max_db = max_db if min_db >= max_db else min_db - 5
        elif max_db > min_db:
            min_db = new_value + 5
        new_range = min_db, max_db
        driver_shared_data['range'] = new_range
    return json.dumps(driver_shared_data['db'])


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
    bottle.run(host='0.0.0.0')
    # while True:
    #     time.sleep(2)

