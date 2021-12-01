# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import unittest

from edo_client.api import SessionStore


class SessionStoreTestCase(unittest.TestCase):

    def setUp(self):
        self.workspace = tempfile.mkdtemp()
        self.store = SessionStore(self.workspace)

    def tearDown(self):
        shutil.rmtree(self.workspace)

    def test_session_store_init(self):
        temp_dir = os.path.join(self.workspace, 'does_no_exist')
        self.assertFalse(os.path.isdir(temp_dir), 'root does not exist yet')
        self.store = SessionStore(temp_dir)
        self.assertTrue(
            os.path.isdir(temp_dir),
            'SessionStore should create its `root` if not exist'
        )

    def test_session_store_save_load_remove(self):
        test_key = 'test_key might be a file path or other text'
        test_data = {
            'key_1': 'some random string',
            'key_2': 'well, not that random',
            'some other type': 911,
        }
        self.store.save(test_key, **test_data)
        self.assertEqual(
            1, len(os.listdir(self.workspace)),
            'Data should be saved to a file on disk'
        )
        self.assertEqual(
            self.store.load(test_key),
            test_data,
            'Should be able to load data back the same as we saved them'
        )
        self.store.remove(test_key)
        self.assertEqual(
            0, len(os.listdir(self.workspace)),
            'File should be removed from disk once we remove this session'
        )
        self.assertIsNone(
            self.store.load(test_key),
            'Should return default value if no session found'
        )
