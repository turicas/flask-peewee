# coding: utf-8

import datetime
try:
    import simplejson as json
except ImportError:
    import json

from flask import request
from werkzeug.exceptions import NotFound

from flask_peewee.tests.base import FlaskPeeweeTestCase
from flask_peewee.tests.test_app import app as flask_app, Message, User
from flask_peewee.utils import (check_password, get_object_or_404,
                                make_password, obj_to_dict)


class UtilsTestCase(FlaskPeeweeTestCase):
    def setUp(self):
        super(UtilsTestCase, self).setUp()

    def test_get_object_or_404(self):
        user = self.create_user('test', 'test')

        # test with model as first arg
        self.assertRaises(NotFound, get_object_or_404, User, User.username=='not-here')
        self.assertEqual(user, get_object_or_404(User, User.username=='test'))

        # test with query as first arg
        active = User.select().where(User.active==True)
        inactive = User.select().where(User.active==False)
        self.assertRaises(NotFound, get_object_or_404, active, User.username=='not-here')
        self.assertRaises(NotFound, get_object_or_404, inactive, User.username=='test')
        self.assertEqual(user, get_object_or_404(active, User.username=='test'))

    def test_passwords(self):
        p = make_password('testing')
        self.assertTrue(check_password('testing', p))
        self.assertFalse(check_password('testing ', p))
        self.assertFalse(check_password('Testing', p))
        self.assertFalse(check_password('', p))

        p2 = make_password('Testing')
        self.assertFalse(p == p2)

    def test_obj_to_dict_not_expanded(self):
        username, password, email = 'admin', 'admin', 'admin@example.com'
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()

        user_dict = obj_to_dict(user)

        self.assertIn('join_date', user_dict)
        self.assertEqual(type(user_dict['join_date']), datetime.datetime)
        del user_dict['join_date']

        self.assertIn('password', user_dict)
        del user_dict['password']

        expected_dict = {'username': 'admin', 'admin': False,
                         'email': 'admin@example.com',
                         'active': True,
                         'id': 1,}
        self.assertEqual(user_dict, expected_dict)

    def test_obj_to_dict_expanded_level_1(self):
        username, password, email = 'admin', 'admin', 'admin@example.com'
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()
        user_dict = obj_to_dict(user)

        message = Message.create(user=user, content='answer: 42')
        not_expanded = obj_to_dict(message, expand_level=0)
        expanded = obj_to_dict(message, expand_level=1)

        self.assertEqual(not_expanded['user'], user.id)
        self.assertEqual(expanded['user'], user_dict)
        del expanded['user']
        del not_expanded['user']

        self.assertEqual(expanded['id'], 1)
        self.assertEqual(not_expanded['id'], 1)
        del expanded['id']
        del not_expanded['id']

        self.assertEqual(type(expanded['pub_date']), datetime.datetime)
        self.assertEqual(type(not_expanded['pub_date']), datetime.datetime)
        del expanded['pub_date']
        del not_expanded['pub_date']

        self.assertEqual(expanded['content'], 'answer: 42')
        self.assertEqual(not_expanded['content'], 'answer: 42')
        del expanded['content']
        del not_expanded['content']

        self.assertEqual(expanded, {})
        self.assertEqual(not_expanded, {})
