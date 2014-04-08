# coding: utf-8

import datetime
import json

from flask_peewee.utils import dict_to_obj
from peewee import Model


strptime = datetime.datetime.strptime
DATE_FMT = '%Y-%m-%d'
TIME_FMT = '%H:%M:%S'
DATETIME_FMT = ' '.join([DATE_FMT, TIME_FMT])
CONVERSION = {
        datetime.datetime: DATETIME_FMT,
        datetime.date: DATE_FMT,
        datetime.time: TIME_FMT,}

def serialize_value(data):
    '''Given `data`, serializes it recursively to an object JSON can encode'''
    data_type = type(data)

    if data_type is dict:
        return {key: serialize_value(value) for key, value in data.items()}
    elif data_type in (list, tuple):
        return map(serialize_value, data)
    elif data_type in CONVERSION:
        return data.strftime(CONVERSION[data_type])
    elif issubclass(data_type, Model):
        return data.get_id()
    else:
        return data

def deserialize_value(value):
    '''Deserialize `str` to native Python `datetime` (when detected)'''
    if type(value) not in (str, unicode):
        return value

    new_value = None
    for fmt in CONVERSION.values():
        try:
            new_value = strptime(value, fmt)
        except ValueError:
            pass
    if new_value is None:
        new_value = value
    return new_value

class JSONSerializerDeserializer(object):
    '''Basic Serializer/Deserializer - uses JSON for the job'''

    def serialize_message(self, message):
        return json.dumps(serialize_value(message))

    def serialize_object(self, obj, obj_type, fields, expand=0, jsonify=True):
        '''Serialize an object (instance of `peewee.Model`) to JSON'''

        field_names = fields[obj_type]
        data = {}
        for field_name in field_names:
            value = getattr(obj, field_name)
            if isinstance(value, Model) and expand > 0:
                value = self.serialize_object(value, type(value), fields,
                        expand=expand - 1, jsonify=False)
            else:
                value = serialize_value(value)
            data[field_name] = value

        data = serialize_value(data)
        if jsonify:
            data = json.dumps(data)
        return data

    def deserialize_object(self, data, obj):
        '''Deserialize JSON data to an object (instance of `peewee.Model`)'''

        data = json.loads(data)
        data_type = type(data)
        if data_type is not dict:
            raise ValueError("Couldn't deserialize type '%s'" % data_type)

        data = {key: deserialize_value(value) for key, value in data.items()}
        return dict_to_obj(data, obj)
