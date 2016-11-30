import os
import types
import unittest

from mock import Mock

import seismograph
from tests import fake_package
from seismograph import loader, Suite, Case, Context, Script, Program
from seismograph.exceptions import LoaderError
from seismograph.loader import check_path_is_exist, is_package
from tests.lib.factories import case_factory
from tests.lib.factories import config_factory
from tests.lib.factories import suite_factory


class TestLoaderCheckers(unittest.TestCase):
    def setUp(self):
        self.not_existed_path = ' '
        self.package_path = os.getcwd()
        self.not_python_package = os.path.join(os.getcwd(), "not_python_package")
        os.mkdir(self.not_python_package, 644)

    def tearDown(self):
        self.not_existed_path = None
        self.package_path = None
        os.rmdir(self.not_python_package)
        self.not_python_package = None

    def test_check_path_is_exist(self):
        self.assertIsNone(loader.check_path_is_exist(self.package_path))
        with self.assertRaises(LoaderError):
            check_path_is_exist(self.not_existed_path)

    def test_is_package(self):
        self.assertTrue(is_package(os.path.dirname(os.path.realpath(__file__))))
        self.assertFalse(is_package(self.not_python_package))

    def test_is_py_module(self):
        self.assertTrue(loader.is_py_module('test.py'))
        self.assertFalse(loader.is_py_module('__init__.py'))
        self.assertFalse(loader.is_py_module('test.c'))


class TestLoadModule(unittest.TestCase):
    def setUp(self):
        self.module_name = "test_module"
        self.module_file_name = ''.join([self.module_name, '.py'])
        open(self.module_file_name, mode='a').close()

    def tearDown(self):
        os.remove(self.module_file_name)
        self.module_name = None
        self.module_file_name = None

    def test_with_existed_module(self):
        self.assertIsNotNone(loader.load_module(self.module_name))

    def test_with_already_imported_module(self):
        with self.assertRaises(LoaderError):
            loader.load_module('sys')


class TestLoadTestNamesFromCase(unittest.TestCase):
    def setUp(self):
        self.test_class = case_factory.create()
        self.test_class.__name__ = self.test_class.__class_name__()

    def tearDown(self):
        self.test_class = None

    def test_with_test_cls(self):
        test_names = loader.load_test_names_from_case(self.test_class)
        self.assertIsInstance(test_names, types.GeneratorType)
        self.assertEqual(test_names.send(None), "test")

    def test_with_not_test_class(self):
        with self.assertRaises(StopIteration):
            loader.load_test_names_from_case(unittest.TestCase).send(None)


class TestLoadTestsFromCase(unittest.TestCase):
    def test_loading_with_test_class(self):
        fake_config = config_factory.create()
        fake_case = case_factory.create()
        fake_case.__name__ = fake_case.__class_name__()

        tests_gen = loader.load_tests_from_case(case_factory.FakeCase, fake_config, method_name='test')
        self.assertIsInstance(tests_gen, types.GeneratorType)
        self.assertIsInstance(tests_gen.send(None), case_factory.FakeCase)

        tests_gen_v2 = loader.load_tests_from_case(case_factory.FakeCase, fake_config)
        self.assertIsInstance(tests_gen_v2, types.GeneratorType)
        self.assertIsInstance(tests_gen_v2.send(None), case_factory.FakeCase)

        with self.assertRaises(StopIteration):
            tests_gen_v2.send(None)

    def test_loading_with_not_test_class(self):
        with self.assertRaises(LoaderError):
            loader.load_tests_from_case(unittest.TestCase, method_name="test").send(None)


class TestLoadSuiteByName(unittest.TestCase):
    def setUp(self):
        self.suite_list = [suite_factory.FakeSuite('Suite' + str(i)) for i in range(5)]

    def tearDown(self):
        self.suite_list = None

    def test_loading_suite_by_name(self):
        suite = loader.load_suite_by_name('Suite1', suites=self.suite_list)
        self.assertIsInstance(suite, suite_factory.FakeSuite)
        self.assertEqual(suite.name, 'Suite1')

    def test_loading_not_existed_suite_by_name(self):
        with self.assertRaises(LoaderError):
            loader.load_suite_by_name('NotExistedSuite', self.suite_list)


class TestLoadCaseFromSuite(unittest.TestCase):
    def setUp(self):
        self.fake_suite = suite_factory.create()
        self.fake_suite.cases.append(case_factory.FakeCase)

    def tearDown(self):
        self.fake_suite = None

    def test_load_existed_case(self):
        case_cls = loader.load_case_from_suite('FakeCase', self.fake_suite)
        self.assertEqual(case_cls, case_factory.FakeCase)

    def test_load_not_existed_case(self):
        with self.assertRaises(LoaderError):
            loader.load_case_from_suite('AnotherClass', self.fake_suite)


class TestLoadSuitesFromModule(unittest.TestCase):
    def test_load_existed_suite(self):
        suite_gen = loader.load_suites_from_module(suite_factory, suite_factory.FakeSuite)
        self.assertIsInstance(suite_gen, types.GeneratorType)


class TestLoadSuitesFromPath(unittest.TestCase):
    def setUp(self):
        self.not_existed_path = ' '
        self.existed_path = os.path.dirname(fake_package.__file__)
        self.no_recursive_suites_count = 2
        self.recursive_suites_count = 5
        self.fake_package = "tests.fake_package"

    def test_load_not_existed_path(self):
        with self.assertRaises(LoaderError):
            next(loader.load_suites_from_path(self.not_existed_path, suite_factory.FakeSuite))

    def test_load_with_no_package(self):
        with self.assertRaises(ImportError):
            next(loader.load_suites_from_path(os.path.dirname(suite_factory.__file__), suite_factory.FakeSuite))

    def test_existed_path_no_recursive(self):
        suites = loader.load_suites_from_path(self.existed_path, suite_class=Suite, package=self.fake_package,
                                              recursive=False)
        self.assertEqual(sum(1 for _ in suites), self.no_recursive_suites_count)

    def test_existed_path_recursive(self):
        suites = loader.load_suites_from_path(self.existed_path, suite_class=Suite, package=self.fake_package,
                                              recursive=True)
        self.assertEqual(sum(1 for _ in suites), self.recursive_suites_count)


class TestLoadSeparatedClassesForFlows(unittest.TestCase):
    class NoFlowsCase(Case):
        __flows__ = (
        )

    class FlowsCase(Case):
        __flows__ = (
            Context(num=1),
            Context(num=2),
            Context(num=3)
        )

    def setUp(self):
        self.flows_count = 3

    def test_load_no_flows_class(self):
        classes = loader.load_separated_classes_for_flows(self.NoFlowsCase)
        self.assertIn(self.NoFlowsCase, classes)
        self.assertEqual(1, len(classes))

    def test_load_flows_class(self):
        classes = loader.load_separated_classes_for_flows(self.FlowsCase)
        self.assertEqual(self.flows_count, len(classes))
        for index, clazz in enumerate(classes):
            self.assertEqual(self.FlowsCase.__name__ + str(index + 1), clazz.__name__)


class TestLoadTasksFromScript(unittest.TestCase):
    class Script(Script):
        def task_1(self):
            pass

        def task_2(self):
            pass

        def customtsk_1(self):
            pass

        def customtsk_2(self):
            pass

        def customtsk_3(self):
            pass

    def setUp(self):
        self.default_tasks_count = 2
        self.custom_tasks_count = 3
        self.program = Program(),
        self.custom_task_prefix = "customtsk"
        self.default_tasks_names = (
            self.Script.task_1.__name__,
            self.Script.task_2.__name__
        )
        self.custom_task_names = (
            self.Script.customtsk_1.__name__,
            self.Script.customtsk_2.__name__,
            self.Script.customtsk_3.__name__
        )

    def test_load_default_tasks(self):
        scripts = list(loader.load_tasks_from_script(self.program, self.Script))
        task_names = map(lambda script: script._method_name, scripts)
        for default_task_name in self.default_tasks_names:
            self.assertIn(default_task_name, task_names)

    def test_load_custom_tasks(self):
        scripts = list(loader.load_tasks_from_script(self.program, self.Script, task_name_prefix=self.custom_task_prefix))
        task_names = map(lambda script: script._method_name, scripts)
        for custom_task_name in self.custom_task_names:
            self.assertIn(custom_task_name, task_names)
