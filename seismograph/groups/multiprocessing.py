# -*- coding: utf-8 -*-

from __future__ import absolute_import

from .. import runnable
from ..case import CaseBox
from ..result import State
from ..xunit import XUnitData
from ..utils.common import waiting_for
from ..exceptions import TimeoutException
from ..tools import get_pool_size_of_value


MPQueue = MPProcess = MPValue = MPLock = None


def import_mp():
    global MPQueue, MPProcess, MPValue, MPLock

    from multiprocessing import Process
    from multiprocessing import Manager

    manager = Manager()

    MPProcess = Process
    MPLock = manager.Lock
    MPValue = manager.Value
    MPQueue = manager.Queue


def target(suite, mp_result):
    suite(mp_result)
    mp_result.save_result()


class MPResultState(State):

    def __init__(self, *args, **kwargs):
        super(MPResultState, self).__init__(*args, **kwargs)

        self._lock = MPLock()
        self._should_stop = MPValue(
            'b', self._should_stop,
        )

    @property
    def should_stop(self):
        return self._should_stop.value

    @should_stop.setter
    def should_stop(self, value):
        with self._lock:
            self._should_stop.value = value


class MPResult(object):

    MATCH = {}

    def __init__(self, result):
        self.result = result
        self.queue = MPQueue()

        self.result.current_state = MPResultState(result)

    def __getattr__(self, item):
        return getattr(self.result, item)

    @staticmethod
    def pack_result_storage(storage):
        return [
            (runnable.id, xunit_data.to_marshal())
            for runnable, xunit_data in storage
        ]

    def unpack_result_storage(self, storage):
        for runnable_id, xunit_data in storage:
            yield self.MATCH[runnable_id], XUnitData.from_marshal(xunit_data)

    def match(self, suite):
        self.MATCH[suite.id] = suite
        runnable.stopped_on(
            suite,
            MPValue('s', runnable.method_name(suite)),
        )

        for case in suite:
            if isinstance(case, CaseBox):
                for c in case:
                    self.MATCH[c.id] = c
                    runnable.stopped_on(
                        c,
                        MPValue('s', runnable.method_name(c)),
                    )
            else:
                self.MATCH[case.id] = case
                runnable.stopped_on(
                    case,
                    MPValue('s', runnable.method_name(case)),
                )

    def save_result(self):
        if self.result.proxies:
            self.queue.put(
                (
                    self.result.proxies[0].name,

                    self.pack_result_storage(
                        self.result.successes,
                    ),
                    self.pack_result_storage(
                        self.result.skipped,
                    ),
                    self.pack_result_storage(
                        self.result.failures,
                    ),
                    self.pack_result_storage(
                        self.result.errors,
                    ),
                ),
            )

    def sync(self):
        while not self.queue.empty():
            name, successes, skipped, failures, errors = self.queue.get()

            result_proxy = self.create_proxy(
                name=name,
            )

            result_proxy.errors.extend(
                self.unpack_result_storage(errors),
            )
            result_proxy.successes.extend(
                self.unpack_result_storage(successes),
            )
            result_proxy.skipped.extend(
                self.unpack_result_storage(skipped),
            )
            result_proxy.failures.extend(
                self.unpack_result_storage(failures),
            )

            self.result.extend(result_proxy)
            self.result.proxies.append(result_proxy)


class Multiprocessing(object):

    def __init__(self, result, config, suites=None):
        self.queue = []
        self.stack = []

        self.mp_result = MPResult(result)
        self.release_timeout = config.MULTIPROCESSING_TIMEOUT
        self.max_processes = get_pool_size_of_value(config.ASYNC_SUITES)

        if suites:
            self.add_suites(suites)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.terminate_all()
        self.join_all()
        self.mp_result.sync()

    def add_suite(self, suite):
        self.mp_result.match(suite)

        self.queue.append(
            MPProcess(
                target=target,
                args=(suite, self.mp_result),
            ),
        )

    def add_suites(self, suites):
        for suite in suites:
            self.add_suite(suite)

    def try_release(self):
        for process in self.stack[::-1]:
            if not process.is_alive():
                process.join(timeout=self.release_timeout)
                self.stack.remove(process)

    def is_release(self):
        self.try_release()
        return len(self.stack) < self.max_processes

    def wait_release(self):
        try:
            waiting_for(
                self.is_release,
                sleep=0.001,
                timeout=self.release_timeout,
            )
        except TimeoutException:
            raise TimeoutException(
                'Process list have not been release for "{}" sec.'.format(
                    self.release_timeout,
                ),
            )

    def join_all(self):
        for process in self.stack:
            process.join(timeout=self.release_timeout)

    def terminate_all(self):
        for process in self.stack:
            process.terminate()

    def serve(self):
        while self.queue:
            process = self.queue.pop()
            process.start()
            self.stack.append(process)
            self.wait_release()

        self.join_all()


class MultiprocessingSuiteGroup(runnable.RunnableGroup):

    def run(self, result):
        import_mp()

        with Multiprocessing(result, self.config, suites=self.objects) as mp:
            mp.serve()
