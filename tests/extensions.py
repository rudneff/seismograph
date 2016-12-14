import inspect

from seismograph import extensions
from seismograph import program
from seismograph import exceptions
from copy import deepcopy

from .lib.case import (
    BaseTestCase,
)


class TestExtension(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


args = (1, 2, 3, 4, 5)
kwargs = dict(a=1, b=2, c=3, d=4, e=5)


class TestSharedExtension(BaseTestCase):
    ex_tmp = extensions._TMP

    def setUp(self):
        program.Program.shared_extension(
            'test_extension',
            TestExtension,
            args=args,
            kwargs=kwargs,
        )

    def test_se_creation(self):
        self.assertIn('test_extension', self.ex_tmp)

    def test_se_type(self):
        container = self.ex_tmp['test_extension']
        self.assertIsInstance(container, extensions.ExtensionContainer)
        self.assertFalse(isinstance(container, extensions.SingletonExtensionContainer))

    def test_se_params(self):
        container = self.ex_tmp['test_extension']
        self.assertEqual(container.args, args)
        self.assertEqual(container.kwargs, kwargs)
        self.assertEqual(container.ext, TestExtension)

    def test_se_call_function(self):
        container = self.ex_tmp['test_extension']
        self.assertEqual(container.__call__().args, args)
        self.assertEqual(container.__call__().kwargs, kwargs)

    def test_se_get_function(self):
        container = self.ex_tmp['test_extension']
        self.assertEqual(container.args, extensions.get('test_extension').args)
        self.assertEqual(container.kwargs, extensions.get('test_extension').kwargs)

        extensions._WAS_CLEAR = True
        self.assertRaises(RuntimeError, extensions.get, 'sss')

        extensions._WAS_CLEAR = False
        self.assertRaises(extensions.ExtensionNotFound, extensions.get, '')

        extensions._TMP.update({'test': '_test_'})
        self.assertEqual(deepcopy('_test_'), extensions.get('test'))

    def tearDown(self):
        extensions._TMP.pop('test_extension', None)


class TestSharedSingletonExtension(BaseTestCase):
    ex_tmp = extensions._TMP

    def setUp(self):
        program.Program.shared_extension(
            'test_extension',
            TestExtension,
            args=args,
            kwargs=kwargs,
            singleton=True,
        )

    def test_sse_creation(self):
        self.assertIn('test_extension', self.ex_tmp)

    def test_sse_type(self):
        container = self.ex_tmp['test_extension']
        self.assertIsInstance(container, extensions.SingletonExtensionContainer)
        self.assertTrue(isinstance(container, extensions.SingletonExtensionContainer))

    def test_sse_params(self):
        container = self.ex_tmp['test_extension']
        self.assertEqual(container.args, args)
        self.assertEqual(container.kwargs, kwargs)
        self.assertEqual(container.ext, TestExtension)

    def test_sse_call_function(self):
        container = self.ex_tmp['test_extension']
        self.assertEqual(container.__call__().args, args)
        self.assertEqual(container.__call__().kwargs, kwargs)

    def tearDown(self):
        extensions._TMP.pop('test_extension', None)
