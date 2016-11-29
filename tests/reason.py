# -*- coding: utf-8 -*-

import unittest
from mock import Mock

from seismograph import reason


class SeismographReasonTestCase(unittest.TestCase):
    def setUp(self):
        self.runnable_object_mock = Mock()
        self.runnable_object_mock.__create_reason__ = True

        def __reason__():
            return 'mock'
        self.runnable_object_mock.__reason__ = __reason__

        self.runnable_object_dummy = {}
        self.config_object_dummy = {}
        self.reason_name = 'test'

    # Ради 100% покрытия #1
    # По-хорошему, надо переопределять методы __eq__  и __ne__
    def test_create(self):
        test_create_value = reason.Reason(self.runnable_object_dummy, self.reason_name, self.config_object_dummy)
        self.assertEqual(reason.create(self.runnable_object_dummy, self.reason_name, self.config_object_dummy).__dict__,
                         test_create_value.__dict__)

    def test_format_reason_to_output(self):
        self.reason = reason.create(self.runnable_object_dummy, self.reason_name)
        test_format_reason_value = u'==\n{}\n==\ntest'
        self.assertEqual(reason.format_reason_to_output(self.reason), test_format_reason_value)

    def test_format_reason_with_true_create__reason_in_runnable_object(self):
        self.reason = reason.create(self.runnable_object_mock, self.reason_name)
        test_format_reason_value = u'mocktest'
        self.assertEqual(reason.format_reason(self.reason), test_format_reason_value)

    def test_format_reason_with_false_create__reason_in_runnable_object(self):
        self.runnable_object_mock.__create_reason__ = False
        self.reason = reason.create(self.runnable_object_mock, self.reason_name)
        test_format_reason_value = u'test'
        self.assertEqual(reason.format_reason(self.reason), test_format_reason_value)

    def test_item(self):
        test_item_value = u'test1 (test2): \n  test3.1\n  test3.2\n\n'
        self.assertEqual(reason.item('test1', 'test2', 'test3.1', 'test3.2'), test_item_value)

    def test_join(self):
        test_join_value = u'test1test2test3'
        self.assertEqual(reason.join('test1', 'test2', 'test3'), test_join_value)

    # Ради 100% покрытия #2
    def test_prop_runnable_obj(self):
        self.reason = reason.create(self.runnable_object_dummy, self.reason_name)
        self.assertEqual(self.reason.runnable_object, self.runnable_object_dummy)

    # Ради 100% покрытия #3
    def test_prop_reason(self):
        self.reason = reason.create(self.runnable_object_dummy, self.reason_name)
        self.assertEqual(self.reason.reason, self.reason_name)

    # Ради 100% покрытия #4
    def test_prop_config(self):
        self.reason = reason.create(self.runnable_object_dummy, self.reason_name, self.config_object_dummy)
        self.assertEqual(self.reason.config, self.config_object_dummy)

    # Ради 100% покрытия #5
    def test_prop_config_none(self):
        self.reason = reason.create(self.runnable_object_dummy, self.reason_name)
        self.assertIsNone(self.reason.config)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
