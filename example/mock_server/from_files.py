# -*- coding: utf-8 -*-

from seismograph import Case, Suite


suite = Suite(__name__, require=['mock_server'])


@suite.register
class TestMocksFromFiles(Case):

    server = None

    def setup(self):
        self.server = self.ext('mock_server')
        self.server.start()

    def teardown(self):
        self.server.stop()

    def test_hello_get(self):
        response = self.server.client.get('/hello')
        self.assertion.equal(response.status_code, 200)
        self.assertion.equal(response.headers['Server'], 'nginx/1.2.1')

        data = response.json()
        self.assertion.is_instance(data['data'], list)
        self.assertion.equal(data['test']['test'], 3.5)
        self.assertion.equal(data['hello'], 'hello world!')

    def test_hello_put(self):
        response = self.server.client.put('/hello')
        self.assertion.equal(response.status_code, 200)
        self.assertion.equal(response.headers['Server'], 'nginx/1.2.1')

        data = response.json()
        self.assertion.equal(data['result'], 'changed')

    def test_hello_post(self):
        response = self.server.client.post('/hello')
        self.assertion.equal(response.status_code, 201)
        self.assertion.equal(response.headers['Server'], 'nginx/1.2.1')

        data = response.json()
        self.assertion.equal(data['result'], 'created')


if __name__ == '__main__':
    import seismograph
    seismograph.main()
