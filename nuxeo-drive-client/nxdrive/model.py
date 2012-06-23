

import os
import datetime
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Sequence
from sqlalchemy import String
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from nxdrive.client import NuxeoClient
from nxdrive.client import LocalClient
from nxdrive.client import NotFound

# make the declarative base class for the ORM mapping
Base = declarative_base()


__model_version__ = 1

# Summary status from last known pair of states

PAIR_STATES = {
    # regular cases
    ('unknown', 'unknown'): 'unknown',
    ('synchronized', 'synchronized'): 'synchronized',
    ('created', 'unknown'): 'locally_created',
    ('unknown', 'created'): 'remotely_created',
    ('modified', 'synchronized'): 'locally_modified',
    ('synchronized', 'modified'): 'remotely_modified',
    ('deleted', 'synchronized'): 'locally_deleted',
    ('synchronized', 'deleted'): 'remotely_deleted',
    ('deleted', 'deleted'): 'deleted',  # should probably never happen

    # conflict cases
    ('modified', 'deleted'): 'conflicted',
    ('deleted', 'modified'): 'conflicted',
    ('modified', 'modified'): 'conflicted',
}


class ServerBinding(Base):
    __tablename__ = 'server_bindings'

    local_folder = Column(String, primary_key=True)
    server_url = Column(String)
    remote_user = Column(String)
    remote_password = Column(String)

    def __init__(self, local_folder, server_url, remote_user,
                 remote_password):
        self.local_folder = local_folder
        self.server_url = server_url
        self.remote_user = remote_user
        self.remote_password = remote_password


class RootBinding(Base):
    __tablename__ = 'root_bindings'

    local_root = Column(String, primary_key=True)
    remote_repo = Column(String)
    remote_root = Column(String)
    local_folder = Column(String, ForeignKey('server_bindings.local_folder'))

    server_binding = relationship(
        'ServerBinding',
        backref=backref("roots", cascade="all, delete-orphan"))

    def __init__(self, local_root, remote_repo, remote_root):
        local_root = os.path.abspath(local_root)
        self.local_root = local_root
        self.remote_repo = remote_repo
        self.remote_root = remote_root

        # expected local folder should be the direct parent of the
        local_folder = os.path.abspath(os.path.join(local_root, '..'))
        self.local_folder = local_folder

    def __repr__(self):
        return ("RootBinding<local_root=%r, local_folder=%r, remote_repo=%r,"
                "remote_root=%r>" % (self.local_root, self.local_folder,
                                     self.remote_repo, self.remote_root))


class LastKnownState(Base):
    """Aggregate state aggregated from last collected events."""
    __tablename__ = 'last_known_states'

    local_root = Column(String, ForeignKey('root_bindings.local_root'),
                        primary_key=True)
    root_binding = relationship(
        'RootBinding',
        backref=backref("states", cascade="all, delete-orphan"))

    # Timestamps to detect modifications
    last_local_updated = Column(DateTime)
    last_remote_updated = Column(DateTime)

    # Save the digest too for better updates / moves detection
    local_digest = Column(String)
    remote_digest = Column(String)

    # Parent path from root for fast children queries,
    # can be None for the root it-self.
    parent_path = Column(String, index=True)

    # Path from root using unix separator, '/' for the root it-self.
    path = Column(String, primary_key=True)

    folderish = Column(Integer)

    # Remote reference (instead of path based lookup)
    remote_repo = Column(String)
    remote_ref = Column(String, index=True)

    # Last known state based on event log
    local_state = Column(String)
    remote_state = Column(String)
    pair_state = Column(String, index=True)

    # Track move operations to avoid loosing history
    locally_moved_from = Column(String)
    locally_moved_to = Column(String)
    remotely_moved_from = Column(String)
    remotely_moved_to = Column(String)

    def __init__(self, local_root, path, remote_repo, remote_ref,
                 last_local_updated, last_remote_updated, folderish=True,
                 local_digest=None, remote_digest=None,
                 local_state='unknown', remote_state='unknown'):
        self.local_root = local_root
        self.path = path
        if path == '/':
            self.parent_path = None
        else:
            parent_path, _ = path.rsplit('/', 1)
            self.parent_path = '/' if parent_path == '' else parent_path
        self.remote_repo = remote_repo
        self.remote_ref = remote_ref
        self.last_local_updated = last_local_updated
        self.last_remote_updated = last_remote_updated
        self.folderish = int(folderish)
        self.local_digest = local_digest
        self.remote_digest = remote_digest
        self.update_state(local_state=local_state, remote_state=remote_state)

    def update_state(self, local_state=None, remote_state=None):
        if local_state is not None:
            self.local_state = local_state
        if remote_state is not None:
            self.remote_state = remote_state
        pair = (self.local_state, self.remote_state)
        self.pair_state = PAIR_STATES.get(pair, 'unknown')

    def __repr__(self):
        return ("LastKnownState<local_root=%r, path=%r, "
                "local_state=%r, remote_state=%r>") % (
                self.local_root, self.path, self.local_state,
                    self.remote_state)

    def get_local_client(self):
        return LocalClient(self.local_root)

    def get_remote_client(self, factory=None):
        if factory is None:
            factory = NuxeoClient
        rb = self.root_binding
        sb = rb.server_binding
        return factory(
            sb.server_url, sb.remote_user, sb.remote_password,
            base_folder=rb.remote_root, repository=rb.remote_repo)

    def refresh_local(self, client=None):
        """Update the state from the local filesystem info."""
        client = client if client is not None else self.get_local_client()
        try:
            local_info = client.get_info(self.path)
        except NotFound:
            if self.local_state in ('created', 'updated', 'synchronized'):
                # the file use to exist, it has been deleted
                self.update_state(local_state='deleted')
                self.local_digest = None
            return None

        if self.last_local_updated is None:
            self.last_local_updated = local_info.last_modification_time
            self.local_digest = local_info.get_digest()
            # shall we update the state here? if so how?
            self.folderish = local_info.folderish

        elif local_info.last_modification_time > self.last_local_updated:
            self.last_local_updated = local_info.last_modification_time
            self.local_digest = local_info.get_digest()
            # XXX: shall we store local_folderish and remote_folderish to
            # detect such kind of conflicts instead?
            self.folderish = local_info.folderish
            self.update_state(local_state='modified')

        return local_info

    def refresh_remote(self, client=None):
        """Update the state from the remote server info.

        Can reuse an existing client to spare some redundant client init HTTP
        request.
        """
        client = client if client is not None else self.get_remote_client()
        try:
            remote_info = client.get_info(self.remote_ref)
        except NotFound:
            if self.remote_state in ('created', 'updated', 'synchronized'):
                self.update_state(remote_state='deleted')
                self.remote_digest = None
            return None

        if self.last_remote_updated is None:
            self.last_remote_updated = remote_info.last_modification_time
            self.remote_digest = remote_info.get_digest()
            # shall we update the state here? if so how?
            self.folderish = remote_info.folderish

        elif remote_info.last_modification_time > self.last_remote_updated:
            self.last_remote_updated = remote_info.last_modification_time
            self.remote_digest = remote_info.get_digest()
            # XXX: shall we store local_folderish and remote_folderish to
            # detect such kind of conflicts instead?
            self.folderish = remote_info.folderish
            self.update_state(local_state='modified')

        return remote_info


class FileEvent(Base):
    __tablename__ = 'fileevents'

    id = Column(Integer, Sequence('fileevent_id_seq'), primary_key=True)
    local_root = Column(String, ForeignKey('root_bindings.local_root'))
    utc_time = Column(DateTime)
    path = Column(String)

    root_binding = relationship("RootBinding")

    def __init__(self, local_root, path, utc_time=None):
        self.local_root = local_root
        if utc_time is None:
            utc_time = datetime.utcnow()


def get_session_maker(nxdrive_home, echo=False):
    """Return a session maker configured for using nxdrive_home

    The database is created in nxdrive_home if missing and the tables
    are intialized based on the model classes from this module (they
    all inherit the same abstract base class.
    """
    # We store the DB as SQLite files in the nxdrive_home folder
    dbfile = os.path.join(os.path.abspath(nxdrive_home), 'nxdrive.db')
    engine = create_engine('sqlite:///' + dbfile, echo=echo)

    # Ensure that the tables are properly initialized
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def get_scoped_session_maker(nxdrive_home, echo=False):
    """Return a session maker configured for using nxdrive_home

    The database is created in nxdrive_home if missing and the tables
    are intialized based on the model classes from this module (they
    all inherit the same abstract base class.

    Sessions built with this maker are reusable thread local
    singletons.
    """
    return scoped_session(get_session_maker(nxdrive_home, echo=echo))
