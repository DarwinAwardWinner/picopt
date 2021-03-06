"""Timestamp writer for keeping track of bulk optimizations."""

import os
from datetime import datetime

from . import PROGRAM_NAME
from .settings import Settings

RECORD_FILENAME = '.%s_timestamp' % PROGRAM_NAME
TIMESTAMP_CACHE = {}


def _get_timestamp(dirname_full, remove):
    """
    Get the timestamp from the timestamp file.

    Optionally remove it if we're going to write another one.
    """
    record_filename = os.path.join(dirname_full, RECORD_FILENAME)

    if os.path.exists(record_filename):
        mtime = os.stat(record_filename).st_mtime
        mtime_str = datetime.fromtimestamp(mtime)
        print('Found timestamp %s:%s' % (dirname_full, mtime_str))
        if Settings.record_timestamp and remove:
            os.remove(record_filename)
        return mtime

    return None


def _get_parent_timestamp(dirname, mtime):
    """
    Get the timestamps up the directory tree.

    Because they affect every subdirectory.
    """
    parent_pathname = os.path.dirname(dirname)

    mtime = max(_get_timestamp(parent_pathname, False), mtime)

    if parent_pathname == os.path.dirname(parent_pathname):
        return mtime

    return _get_parent_timestamp(parent_pathname, mtime)


def get_walk_after(filename, optimize_after=None):
    """
    Figure out the which mtime to check against.

    If we look up return that we've looked up too
    """
    if Settings.optimize_after is None:
        dirname = os.path.dirname(filename)
        if dirname in TIMESTAMP_CACHE:
            return TIMESTAMP_CACHE[dirname]
        if optimize_after is None:
            optimize_after = _get_parent_timestamp(dirname,
                                                   optimize_after)
        optimize_after = max(_get_timestamp(dirname, True),
                             optimize_after)
        TIMESTAMP_CACHE[dirname] = optimize_after
    else:
        optimize_after = Settings.optimize_after
    return optimize_after


def record_timestamp(pathname_full):
    """Record the timestamp of running in a dotfile."""
    if Settings.test or Settings.list_only or not Settings.record_timestamp:
        return
    elif not Settings.follow_symlinks and os.path.islink(pathname_full):
        if Settings.verbose:
            print('Not setting timestamp because not following symlinks')
        return
    elif not os.path.isdir(pathname_full):
        if Settings.verbose:
            print('Not setting timestamp for a non-directory')
        return

    record_filename_full = os.path.join(pathname_full, RECORD_FILENAME)
    try:
        with open(record_filename_full, 'w'):
            os.utime(record_filename_full, None)
        if Settings.verbose:
            print("Set timestamp: %s" % record_filename_full)
    except IOError:
        print("Could not set timestamp in %s" % pathname_full)
