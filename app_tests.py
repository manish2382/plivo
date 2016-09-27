import unittest
import time
from multiprocessing import Process
from app import app, db
from app.utils import *


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config['TESTING'] = True

        # do db related configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://manish:kumar@localhost/test"
        db.create_all()

        # add test data
        acc = Account(username='test123', auth_id='20S0KPNOIM')
        db.session.add(acc)
        db.session.commit()

        phone = phone_number(number=4924195509192, account_id=acc.id)
        db.session.add(phone)
        db.session.commit()

        # do redis related configuration
        app.config["REDIS_HOST"] = "localhost"
        app.config["6379"] = 6379

    def tearDown(self):
        """Rip out the database tables to have a 'clean slate' for the next test case."""
        db.session.remove()
        db.drop_all()

        r = get_redis_connection()
        r.flushall()

    def test_inbound(self):

        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "inbound sms ok" in rv.data

    def test_inbound_auth(self):

        # invalid credentials
        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "Test messages",
            "username": "plivo",
            "password": "20S0KPNOIM"
        })
        assert "403 Forbidden" in rv.data

        # missing user name
        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "Test messages",
            "password": "20S0KPNOIM"
        })
        assert "403 Forbidden" in rv.data

        # missing password
        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "Test messages",
            "username": "test123",
        })
        assert "403 Forbidden" in rv.data

        # invalid to number
        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256",
            "to": "492419509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "to parameter not found" in rv.data

    def test_inbound_negative(self):

        # text is missing in input
        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'text' is missing" in rv.data

        # from is missing
        rv = self.app.post('/inbound/sms/', data={
            "from": "",
            "text": "Test messages",
            "to": "4924195509192",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'from' is missing" in rv.data

        # to is missing
        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'to' is missing" in rv.data

        # invalid from => max_length exceeded
        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256333333333333333333333333333",
            "to": "4924195509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'from' is invalid" in rv.data

        # invalid from => less than min_length
        rv = self.app.post('/inbound/sms/', data={
            "from": "1",
            "to": "4924195509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'from' is invalid" in rv.data

        # invalid to => max_length exceeded
        rv = self.app.post('/inbound/sms/', data={
            "to": "+919916425256333333333333333333333333333",
            "from": "4924195509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'to' is invalid" in rv.data

        # invalid from => less than min_length
        rv = self.app.post('/inbound/sms/', data={
            "to": "1",
            "from": "4924195509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'to' is invalid" in rv.data

        # invalid from => max_length exceeded
        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "Test messages eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
                    "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'text' is invalid" in rv.data

    def test_outbound(self):
        rv = self.app.post('/outbound/sms/', data={
            "from": "4924195509192",
            "to": "1234567643434",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "outbound sms ok" in rv.data

    def test_outbound_auth(self):
        # invalid credentials
        rv = self.app.post('/outbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "Test messages",
            "username": "plivo",
            "password": "20S0KPNOIM"
        })
        assert "403 Forbidden" in rv.data

        # missing user name
        rv = self.app.post('/outbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "Test messages",
            "password": "20S0KPNOIM"
        })
        assert "403 Forbidden" in rv.data

        # missing password
        rv = self.app.post('/outbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "Test messages",
            "username": "test123",
        })
        assert "403 Forbidden" in rv.data

        # invalid from number
        rv = self.app.post('/outbound/sms/', data={
            "from": "+919916425256",
            "to": "492419509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "from parameter not found" in rv.data

    def test_outbound_negative(self):
        # text is missing in input
        rv = self.app.post('/outbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'text' is missing" in rv.data

        # from is missing
        rv = self.app.post('/outbound/sms/', data={
            "from": "",
            "text": "Test messages",
            "to": "4924195509192",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'from' is missing" in rv.data

        # to is missing
        rv = self.app.post('/outbound/sms/', data={
            "from": "+919916425256",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'to' is missing" in rv.data

        # invalid from => max_length exceeded
        rv = self.app.post('/outbound/sms/', data={
            "from": "+919916425256333333333333333333333333333",
            "to": "4924195509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'from' is invalid" in rv.data

        # invalid from => less than min_length
        rv = self.app.post('/outbound/sms/', data={
            "from": "1",
            "to": "4924195509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'from' is invalid" in rv.data

        # invalid to => max_length exceeded
        rv = self.app.post('/outbound/sms/', data={
            "to": "+919916425256333333333333333333333333333",
            "from": "4924195509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'to' is invalid" in rv.data

        # invalid from => less than min_length
        rv = self.app.post('/outbound/sms/', data={
            "to": "1",
            "from": "4924195509192",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'to' is invalid" in rv.data

        # invalid from => max_length exceeded
        rv = self.app.post('/outbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "Test messages eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
                    "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "username": "test123",
            "password": "20S0KPNOIM"
        })
        assert "parameter 'text' is invalid" in rv.data

    def test_stop_request(self):

        # register stop request
        rv = self.app.post('/inbound/sms/', data={
            "from": "+919916425256",
            "to": "4924195509192",
            "text": "STOP",
            "username": "test123",
            "password": "20S0KPNOIM"
        }
        )

        # send sms to same number which is registered for stop request
        rv = self.app.post('/outbound/sms/', data={
            "from": "4924195509192",
            "to": "+919916425256",
            "text": "Test messages",
            "username": "test123",
            "password": "20S0KPNOIM"
        })

        assert "sms from 4924195509192 to +919916425256 blocked by STOP request" in rv.data

    def test_register_and_stop_request(self):

        # register and check if registration is successful
        register_stop_request("STOP", "test_3344556677", "12345678", 3)
        r = check_stop_request("test_3344556677", "12345678")
        assert "sms from %s to %s blocked by STOP request" == r

        # after expiry of stop request
        time.sleep(4)
        r = check_stop_request("test_3344556677", "12345678")
        assert r is None

        # stop with newline character
        # register and check if registration is successful
        register_stop_request("STOP\n", "test_3344556677", "12345678", 3)
        r = check_stop_request("test_3344556677", "12345678")
        assert "sms from %s to %s blocked by STOP request" == r

        # stop with newline character
        # register and check if registration is successful
        register_stop_request("STOP\r\n", "test_123344556677", "1212345678", 3)
        r = check_stop_request("test_123344556677", "1212345678")
        assert "sms from %s to %s blocked by STOP request" == r

    def test_check_and_update_usage(self):

        # check if limit is getting updated properly and getting proper error message after limit exhaustion
        r = check_and_update_usage("1234567", 2, 10)
        assert r is None
        r = check_and_update_usage("1234567", 2, 10)
        assert r is None

        # as it has reached its limit error will be returned
        r = check_and_update_usage("1234567", 2, 10)
        assert r == "limit reached for from %s"

        # after expiration of key it should work again
        time.sleep(10)
        r = check_and_update_usage("1234567", 2, 10)
        assert r is None

    def test_concurrent_check_and_update_usage(self):

        # create 3 processes each will update usage count
        for num in range(3):
            p = Process(target=check_and_update_usage, args=("12345678", 3, 6))
            p.start()
            p.join()

        # Limit must be exhausted. Error will be returned in case of further use
        r = check_and_update_usage("12345678", 3, 6)
        assert r == "limit reached for from %s"

        # after counter has expired no error should be thrown
        time.sleep(6)
        r = check_and_update_usage("12345678", 3, 6)
        assert r is None

if __name__ == '__main__':
    unittest.main()


