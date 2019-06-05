from rest_framework.parsers import BaseParser
from urllib.parse import unquote
import re, datetime
from django.utils import timezone
import pytz


class CoordinatorDataParser(BaseParser):
    media_type = 'application/x-www-form-urlencoded'

    def parse(self, stream, media_type=None, parser_context=None):
        bytes = stream.read()
        strbytes = str(bytes)
        data = unquote(strbytes)
        elements = None
        try:
            rawstrings = data.split('\n')[1:]
            elements = [self.parse_string(s) for s in rawstrings if self.parse_string(s) is not None]
            max_tick_count = max([x['tick_count'] for x in elements])
            for e in elements:
                e['time'] = timezone.now() - datetime.timedelta(
                    seconds=(max_tick_count - e['tick_count']) // 1000)  # 1 tick is 1 ms
        except Exception:
            pass
        return elements

    def parse_string(self, string_of_data):
        values = string_of_data.split(',')
        if len(values) == 4:
            try:
                tick_count = int(values[0])
                val_float = float(values[1])
                xbee_data = values[3].split('/')
                assert xbee_data[0] == 'xbee.analog'
                mac_address = re.findall(r'\[(.+)\]', xbee_data[1])[0]
                channel = xbee_data[2]
            except Exception:
                return
            return {'tick_count': tick_count, 'value': val_float,
                    'mac_address': mac_address, 'channel': channel, 'time': datetime.datetime.now()}
        else:
            return
