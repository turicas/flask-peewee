import datetime
import json

from flask_peewee.serdes import JSONSerializerDeserializer
from flask_peewee.tests.base import FlaskPeeweeTestCase
from flask_peewee.tests.test_app import Message, User
from flask_peewee.utils import obj_to_dict


DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

class SerializerDeserializerTestCase(FlaskPeeweeTestCase):
    def setUp(self):
        super(SerializerDeserializerTestCase, self).setUp()
        self.serdes = JSONSerializerDeserializer()

        self.users = self.create_users()
        self.model = type(self.admin)
        self.user_fields = ['id', 'username', 'password', 'join_date',
                            'active', 'admin', 'email']

    def test_serializer_without_expanding(self):
        serialized = self.serdes.serialize_object(self.admin, self.model,
                {User: self.user_fields})
        self.assertEqual(json.loads(serialized), {
            'id': self.admin.id,
            'username': 'admin',
            'password': self.admin.password,
            'join_date': self.admin.join_date.strftime(DATETIME_FMT),
            'active': True,
            'admin': True,
            'email': '',
        })

        serialized = self.serdes.serialize_object(self.admin, self.model,
                {User: ['id', 'username']})
        self.assertEqual(json.loads(serialized), {
            'id': self.admin.id,
            'username': 'admin',
        })

        some_fields = set(self.user_fields) - set(['password', 'join_date'])
        serialized = self.serdes.serialize_object(self.admin, self.model,
                {User: list(some_fields)})
        self.assertEqual(json.loads(serialized), {
            'id': self.admin.id,
            'username': 'admin',
            'active': True,
            'admin': True,
            'email': '',
        })

        message = Message.create(content='answer 42', user=self.admin)
        fields = {Message: ['user', 'content', 'pub_date']}
        serialized = self.serdes.serialize_object(message, Message, fields)
        result = json.loads(serialized)
        self.assertEqual(result.keys(), ['content', 'pub_date', 'user'])
        self.assertEqual(result['content'], 'answer 42')
        self.assertEqual(result['user'], self.admin.id)

    def test_serializer_expanding_one_level(self):
        message = Message.create(content='answer 42', user=self.admin)
        fields = {Message: ['user', 'content', 'pub_date'],
                  User: ['username', 'email']}
        serialized = self.serdes.serialize_object(message, Message, fields,
                expand=1)
        result = json.loads(serialized)
        self.assertEqual(result.keys(), ['content', 'pub_date', 'user'])
        self.assertEqual(result['content'], 'answer 42')
        self.assertEqual(result['user'], {'username': self.admin.username,
                                          'email': self.admin.email})

    def test_deserializer(self):
        serialized = json.dumps({
            'id': self.admin.id,
            'username': 'admin',
            'password': self.admin.password,
            'join_date': self.admin.join_date.strftime(DATETIME_FMT),
            'active': True,
            'admin': True,
        })
        deserialized = self.serdes.deserialize_object(serialized, User)
        self.assertEqual(deserialized, self.admin)

        serialized = json.dumps({
            'username': 'edited',
            'active': False,
            'admin': False,
        })
        deserialized = self.serdes.deserialize_object(serialized, self.admin)

        admin_id = self.admin.get_id()
        self.assertEqual(deserialized.id, admin_id)
        self.assertEqual(deserialized.username, 'edited')
        self.assertEqual(deserialized.admin, False)
        self.assertEqual(deserialized.active, False)

        deserialized.save()
        self.assertEqual(User.select().count(), 3)
        edited = User.get(username='edited')
        self.assertEqual(edited.id, admin_id)

    def test_serialize_and_deserialize(self):
        serialized = self.serdes.serialize_object(self.admin, self.model,
                {User: self.user_fields})
        deserialized = self.serdes.deserialize_object(serialized, User)
        self.assertEqual(deserialized, self.admin)
