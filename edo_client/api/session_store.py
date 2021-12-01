# -*- coding: utf-8 -*-
import json
import logging
import os

log = logging.getLogger(__name__)


class SessionStore(object):
    def __init__(self, root=None):
        super(SessionStore, self).__init__()
        if not root:
            root = os.path.expanduser(os.path.join('~', '.edo'))
        if not os.path.exists(root):
            os.makedirs(root)
        self.root = root

    def __repr__(self):
        return '<SessionStore @ "{}">'.format(self.root)

    def save(self, _key, **data):
        '''
        Save some data into a JSON file.
        Args:
            _key: the key you want to use.
            data: JSON-serilizable dict you want to save.
        Returns: None
        Notice: session file name is md5 value of `_key`.
        '''
        session_fpath = os.path.join(self.root, _key)
        with open(session_fpath, 'w') as wf:
            json.dump(data, wf)

    def load(self, _key, default=None):
        '''
        Load saved data of given key, return `default` if not found or invalid.
        '''
        session = default
        session_fpath = os.path.join(self.root, _key)
        if not os.path.isfile(session_fpath):
            return default
        try:
            with open(session_fpath) as rf:
                session = json.load(rf)
        except IOError:
            log.warn(
                u'Error reading session file "%s"',
                session_fpath, exc_info=True
            )
        except ValueError:
            # TODO dump original data from session file if less than 4kb
            log.warn(
                u'Malformed session data in file "%s"',
                session_fpath, exc_info=True
            )
            # delete session file (since it's invalid)
            self.remove(_key)
        finally:
            return session

    def remove(self, _key):
        '''
        Remove a session file by key.
        Notice: will never raise any Exception. (or shall we?)
        '''
        session_fpath = os.path.join(self.root, _key)
        if not os.path.isfile(session_fpath):
            return
        retry = 3
        while 1:
            if retry < 0:
                break
            try:
                os.remove(session_fpath)
                break
            except:
                retry -= 1
                log.warn(
                    u'Error removing session file "%s" (%d retries remaining)',
                    session_fpath, retry, exc_info=True
                )
