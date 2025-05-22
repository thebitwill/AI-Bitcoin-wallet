# tests/test_settings.py
import unittest
import json
import os
from unittest import mock

# Adjust import path
from app.wallet_logic.settings import save_inheritance_settings, load_inheritance_settings, _get_settings_filepath, SETTINGS_DIR

class TestSettings(unittest.TestCase):
    """Test suite for inheritance settings functions."""

    def setUp(self):
        """Setup common test variables."""
        self.wallet_id = "test_wallet_123"
        self.sample_settings = {
            'enabled': True,
            'beneficiary_address': '1TestBeneficiaryAddr',
            'inactivity_period': 180,
            'transfer_amount': '1.5' 
        }
        self.expected_filepath = _get_settings_filepath(self.wallet_id)
        self.default_settings = {
            'enabled': False, 
            'beneficiary_address': '', 
            'inactivity_period': 90,
            'transfer_amount': '0.0'
        }

    @mock.patch('app.wallet_logic.settings.os.makedirs')
    @mock.patch('app.wallet_logic.settings.open', new_callable=mock.mock_open)
    @mock.patch('app.wallet_logic.settings.json.dump')
    def test_save_inheritance_settings_success(self, mock_json_dump, mock_open_file, mock_os_makedirs):
        """Test successful saving of inheritance settings."""
        # Ensure SETTINGS_DIR is mocked for makedirs if it's part of the logic path being tested for creation
        # However, settings.py creates it on import, so direct check of makedirs call might be tricky
        # unless we reload the module or mock that specific os.makedirs call in settings.py.
        # For simplicity, we assume SETTINGS_DIR exists or its creation is handled.
        # mock_os_makedirs.return_value = None # Simulate directory exists or created

        result = save_inheritance_settings(self.wallet_id, self.sample_settings)

        self.assertTrue(result, "save_inheritance_settings should return True on success.")
        # Check if _get_settings_filepath was used implicitly to construct the path for open
        mock_open_file.assert_called_once_with(self.expected_filepath, 'w')
        mock_json_dump.assert_called_once_with(self.sample_settings, mock_open_file(), indent=4)
        # Verify os.makedirs was called for SETTINGS_DIR (it's called on module import in settings.py)
        # To test this properly, we might need to mock os.path.exists within settings.py for the initial check
        # or ensure the test environment doesn't have the dir initially.
        # For now, let's assume the settings.py module's os.makedirs works.

    @mock.patch('app.wallet_logic.settings.os.makedirs') # Still mock makedirs for consistency
    @mock.patch('app.wallet_logic.settings.open', new_callable=mock.mock_open)
    @mock.patch('app.wallet_logic.settings.json.dump', side_effect=IOError("Disk full"))
    def test_save_inheritance_settings_io_error(self, mock_json_dump, mock_open_file, mock_os_makedirs):
        """Test saving settings with an IOError during json.dump."""
        result = save_inheritance_settings(self.wallet_id, self.sample_settings)
        self.assertFalse(result, "save_inheritance_settings should return False on IOError.")
        mock_open_file.assert_called_once_with(self.expected_filepath, 'w')
        mock_json_dump.assert_called_once()

    def test_save_inheritance_settings_no_wallet_id(self):
        """Test saving settings with no wallet identifier."""
        result = save_inheritance_settings("", self.sample_settings)
        self.assertFalse(result, "save_inheritance_settings should return False if wallet_identifier is empty.")

    @mock.patch('app.wallet_logic.settings.os.path.exists', return_value=True)
    @mock.patch('app.wallet_logic.settings.open', new_callable=mock.mock_open)
    @mock.patch('app.wallet_logic.settings.json.load')
    def test_load_inheritance_settings_file_exists(self, mock_json_load, mock_open_file, mock_path_exists):
        """Test loading settings when the settings file exists."""
        mock_json_load.return_value = self.sample_settings
        
        result = load_inheritance_settings(self.wallet_id)

        mock_path_exists.assert_called_once_with(self.expected_filepath)
        mock_open_file.assert_called_once_with(self.expected_filepath, 'r')
        mock_json_load.assert_called_once()
        self.assertEqual(result, self.sample_settings, "Should return the loaded settings.")

    @mock.patch('app.wallet_logic.settings.os.path.exists', return_value=False)
    def test_load_inheritance_settings_file_not_exists(self, mock_path_exists):
        """Test loading settings when the settings file does not exist."""
        result = load_inheritance_settings(self.wallet_id)
        
        mock_path_exists.assert_called_once_with(self.expected_filepath)
        self.assertEqual(result, self.default_settings, "Should return default settings if file not found.")

    @mock.patch('app.wallet_logic.settings.os.path.exists', return_value=True)
    @mock.patch('app.wallet_logic.settings.open', new_callable=mock.mock_open)
    @mock.patch('app.wallet_logic.settings.json.load', side_effect=json.JSONDecodeError("Error", "doc", 0))
    def test_load_inheritance_settings_json_decode_error(self, mock_json_load, mock_open_file, mock_path_exists):
        """Test loading settings when there is a JSONDecodeError."""
        result = load_inheritance_settings(self.wallet_id)

        mock_path_exists.assert_called_once_with(self.expected_filepath)
        mock_open_file.assert_called_once_with(self.expected_filepath, 'r')
        mock_json_load.assert_called_once()
        # As per current implementation, it returns None on JSONDecodeError
        self.assertIsNone(result, "Should return None on JSONDecodeError.")


    @mock.patch('app.wallet_logic.settings.os.path.exists', return_value=True)
    @mock.patch('app.wallet_logic.settings.open', side_effect=IOError("Cannot open"))
    def test_load_inheritance_settings_io_error(self, mock_open_file, mock_path_exists):
        """Test loading settings with an IOError during file open."""
        result = load_inheritance_settings(self.wallet_id)
        mock_path_exists.assert_called_once_with(self.expected_filepath)
        mock_open_file.assert_called_once_with(self.expected_filepath, 'r')
        self.assertIsNone(result, "Should return None on IOError during file open.")

    def test_load_inheritance_settings_no_wallet_id(self):
        """Test loading settings with no wallet identifier."""
        result = load_inheritance_settings("")
        self.assertIsNone(result, "load_inheritance_settings should return None if wallet_identifier is empty.")

    def test_get_settings_filepath_generation(self):
        """Test the helper function for settings filepath generation."""
        wallet_id_normal = "testWallet123"
        expected_normal = os.path.join(SETTINGS_DIR, f"inheritance_settings_{wallet_id_normal}.json")
        self.assertEqual(_get_settings_filepath(wallet_id_normal), expected_normal)

        wallet_id_special_chars = "test/Wallet!@#$"
        # Expected: "test_Wallet____" after sanitization by replacing non-alnum with '_'
        sanitized_part = "test_Wallet____" 
        expected_special = os.path.join(SETTINGS_DIR, f"inheritance_settings_{sanitized_part}.json")
        self.assertEqual(_get_settings_filepath(wallet_id_special_chars), expected_special)

if __name__ == '__main__':
    unittest.main()
