import pytest
import requests_mock
from requests import patch

from main import  qb_request

class TestAPIRequest:
    @requests_mock.Mocker()
    def test_successful_request(self, m):
        m.get("https://sandbox-quickbox.api.intuit.com/test",
              json={"data": "success"})

        with patch("main.get_access_token", return_value="test_token"):
            result = qb_request("GET", "/test")
            assert result == {"data": "success"}

    @requests_mock.Mocker()
    def test_rate_limit_retry(self,m):
        m.get("https://sandbox-quickbooks.api.intuit.com/test",
              [{"status_code" : 401}, {"json" : {"data" : "success"}}])

        with patch("main.get_access_token", return_value = "test_token"):
            with patch("main.refresh_access_token"):
                result = qb_request("GET", "/test")
                assert result == {"data": "success"}

