# tests/test_activity.py
import unittest
import json
import os
from datetime import datetime, timezone
from unittest import mock

# Adjust import path
from app.wallet_logic.activity import (
    update_last_activity_timestamp, 
    get_last_activity_timestamp, 
    _get_activity_filepath,
    ACTIVITY_DIR # For checking directory creation if needed
)

class TestActivity(unittest.TestCase):
    """Test suite for activity timestamp functions."""

    def setUp(self):
        """Setup common test variables."""
        self.wallet_id = "test_activity_wallet_456"
        self.expected_filepath = _get_activity_filepath(self.wallet_id)
        
        # Define a fixed datetime object for mocking datetime.now()
        self.mock_now_dt = datetime(2023, 10, 27, 12, 30, 0, tzinfo=timezone.utc)
        self.mock_now_iso = self.mock_now_dt.isoformat()

    @mock.patch('app.wallet_logic.activity.datetime') # Mock the entire datetime module in activity.py
    @mock.patch('app.wallet_logic.activity.open', new_callable=mock.mock_open)
    @mock.patch('app.wallet_logic.activity.json.dump')
    @mock.patch('app.wallet_logic.activity.os.makedirs') # Mock makedirs as it's called on module import
    def test_update_last_activity_timestamp_success(self, mock_os_makedirs, mock_json_dump, mock_open_file, mock_datetime):
        """Test successful update of the last activity timestamp."""
        # Configure the mock datetime.now() to return our fixed datetime
        mock_datetime.now.return_value = self.mock_now_dt
        
        result = update_last_activity_timestamp(self.wallet_id)

        self.assertTrue(result, "update_last_activity_timestamp should return True on success.")
        mock_datetime.now.assert_called_once_with(timezone.utc) # Verify now() was called with UTC
        mock_open_file.assert_called_once_with(self.expected_filepath, 'w')
        expected_activity_data = {'last_activity_timestamp': self.mock_now_iso}
        mock_json_dump.assert_called_once_with(expected_activity_data, mock_open_file(), indent=4)

    @mock.patch('app.wallet_logic.activity.datetime')
    @mock.patch('app.wallet_logic.activity.open', side_effect=IOError("Failed to write"))
    @mock.patch('app.wallet_logic.activity.os.makedirs')
    def test_update_last_activity_timestamp_io_error(self, mock_os_makedirs, mock_open_file_io_error, mock_datetime):
        """Test timestamp update failure due to IOError."""
        mock_datetime.now.return_value = self.mock_now_dt
        
        result = update_last_activity_timestamp(self.wallet_id)
        
        self.assertFalse(result, "update_last_activity_timestamp should return False on IOError.")
        mock_open_file_io_error.assert_called_once_with(self.expected_filepath, 'w')

    def test_update_last_activity_timestamp_no_wallet_id(self):
        """Test timestamp update with an empty wallet identifier."""
        result = update_last_activity_timestamp("")
        self.assertFalse(result, "Should return False if wallet_identifier is empty.")

    @mock.patch('app.wallet_logic.activity.os.path.exists', return_value=True)
    @mock.patch('app.wallet_logic.activity.open', new_callable=mock.mock_open)
    @mock.patch('app.wallet_logic.activity.json.load')
    def test_get_last_activity_timestamp_file_exists_valid_content(self, mock_json_load, mock_open_file, mock_path_exists):
        """Test getting timestamp when file exists and content is valid."""
        activity_data = {'last_activity_timestamp': self.mock_now_iso}
        mock_json_load.return_value = activity_data
        
        result = get_last_activity_timestamp(self.wallet_id)

        mock_path_exists.assert_called_once_with(self.expected_filepath)
        mock_open_file.assert_called_once_with(self.expected_filepath, 'r')
        mock_json_load.assert_called_once()
        self.assertEqual(result, self.mock_now_iso, "Should return the loaded timestamp string.")

    @mock.patch('app.wallet_logic.activity.os.path.exists', return_value=True)
    @mock.patch('app.wallet_logic.activity.open', new_callable=mock.mock_open)
    @mock.patch('app.wallet_logic.activity.json.load')
    def test_get_last_activity_timestamp_file_exists_invalid_format(self, mock_json_load, mock_open_file, mock_path_exists):
        """Test getting timestamp when file exists but timestamp format is invalid."""
        activity_data = {'last_activity_timestamp': "not-a-valid-iso-timestamp"}
        mock_json_load.return_value = activity_data
        
        result = get_last_activity_timestamp(self.wallet_id)
        self.assertIsNone(result, "Should return None if timestamp format is invalid.")

    @mock.patch('app.wallet_logic.activity.os.path.exists', return_value=True)
    @mock.patch('app.wallet_logic.activity.open', new_callable=mock.mock_open)
    @mock.patch('app.wallet_logic.activity.json.load')
    def test_get_last_activity_timestamp_file_exists_no_timestamp_key(self, mock_json_load, mock_open_file, mock_path_exists):
        """Test getting timestamp when file exists but the key is missing."""
        activity_data = {'other_data': 'some_value'} # Missing 'last_activity_timestamp'
        mock_json_load.return_value = activity_data
        
        result = get_last_activity_timestamp(self.wallet_id)
        self.assertIsNone(result, "Should return None if 'last_activity_timestamp' key is missing.")

    @mock.patch('app.wallet_logic.activity.os.path.exists', return_value=False)
    def test_get_last_activity_timestamp_file_not_exists(self, mock_path_exists):
        """Test getting timestamp when the activity file does not exist."""
        result = get_last_activity_timestamp(self.wallet_id)
        
        mock_path_exists.assert_called_once_with(self.expected_filepath)
        self.assertIsNone(result, "Should return None if activity file does not exist.")

    @mock.patch('app.wallet_logic.activity.os.path.exists', return_value=True)
    @mock.patch('app.wallet_logic.activity.open', new_callable=mock.mock_open)
    @mock.patch('app.wallet_logic.activity.json.load', side_effect=json.JSONDecodeError("Error", "doc", 0))
    def test_get_last_activity_timestamp_json_decode_error(self, mock_json_load, mock_open_file, mock_path_exists):
        """Test getting timestamp when there is a JSONDecodeError."""
        result = get_last_activity_timestamp(self.wallet_id)
        self.assertIsNone(result, "Should return None on JSONDecodeError.")

    @mock.patch('app.wallet_logic.activity.os.path.exists', return_value=True)
    @mock.patch('app.wallet_logic.activity.open', side_effect=IOError("Cannot open"))
    def test_get_last_activity_timestamp_io_error(self, mock_open_file_io_error, mock_path_exists):
        """Test getting timestamp with an IOError during file open."""
        result = get_last_activity_timestamp(self.wallet_id)
        self.assertIsNone(result, "Should return None on IOError during file open.")

    def test_get_last_activity_timestamp_no_wallet_id(self):
        """Test getting timestamp with an empty wallet identifier."""
        result = get_last_activity_timestamp("")
        self.assertIsNone(result, "Should return None if wallet_identifier is empty.")

if __name__ == '__main__':
    unittest.main()
