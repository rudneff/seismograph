import os
import unittest
from seismograph import loader
from seismograph.exceptions import LoaderError
from seismograph.loader import check_path_is_exist, is_package


class TestLoaderCheckers(unittest.TestCase):

    def setUp(self):
        self.not_existed_path = ' '
        self.package_path = os.getcwd()
        self.init_py_file_path = os.path.join(self.package_path, '__init__.py')
        self.init_py_file = None
        if not os.path.exists(self.init_py_file_path):
            self.init_py_file = open(self.init_py_file_path, 'a')
        self.not_python_package = os.path.join(os.getcwd(), "not_python_package")
        os.mkdir(self.not_python_package, mode=644)

    def tearDown(self):
        self.not_existed_path = None
        self.package_path = None
        if self.init_py_file:
            self.init_py_file.close()
            os.remove(self.init_py_file_path)
        self.init_py_file_path = None

        os.rmdir(self.not_python_package)
        self.not_python_package = None

    def test_check_path_is_exist(self):
        self.assertIsNone(loader.check_path_is_exist(self.package_path))
        with self.assertRaises(LoaderError):
            check_path_is_exist(self.not_existed_path)

    def test_is_package(self):
        self.assertTrue(is_package(self.package_path))
        self.assertFalse(is_package(self.not_python_package))

    def test_is_py_module(self):
        self.assertTrue(loader.is_py_module('test.py'))
        self.assertFalse(loader.is_py_module('__init__.py'))
        self.assertFalse(loader.is_py_module('test.c'))








