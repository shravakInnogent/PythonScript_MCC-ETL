import pytest
from unittest.mock import patch, mock_open

import main
from main import load_tokens, save_tokens, refresh_access_token

class TestAuthentication:
    @patch("builtins.open", new_callable=mock_open, read_data = '{"access_token" : "test_token", "expires_at" : 99999999}')
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_tokens_success(self ,mock_exists, mock_file):
        tokens  = load_tokens()
        assert tokens["access_token"] == "test_token"

    @patch("pathlib.path.exists", return_value=False)
    def test_load_tokens_file_not_found(self, mock_exists):
        with pytest.raises(FileNotFoundError):
            load_tokens()

    @patch("requests.post")
    def test_refresh_token_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600
        }
        with patch("main.save_tokens"):
            result = refresh_access_token("refresh_token")
            assert result["access_token"] == "new_token"
