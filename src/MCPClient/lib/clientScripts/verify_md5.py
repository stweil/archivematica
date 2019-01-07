# -*- coding: utf-8 -*-

"""Module docstring"""

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
from __future__ import unicode_literals

import os
import subprocess
import sys

from custom_handlers import get_script_logger


def concurrent_instances():
    """Function docstring. N.B. Delete me."""
    return 1


logger = get_script_logger("archivematica.mcp.client.compare_hashes")


class NoHashCommandAvailable(Exception):
    """Provide feedback to the user if the chacksum command cannot be found
    for the provided checksum file.
    """


class Hashsum(object):
    """CLASS docstring."""

    COMMANDS = {
        "metadata/checksum.md5": "md5sum",
        "metadata/checksum.sha1": "sha1sum",
        "metadata/checksum.sha256": "sha256sum",
        "metadata/checksum.sha512": "sha512sum",
        "metadata/checksum.b2": "b2sum",
    }

    FAIL_STRING = ": FAILED"
    ZERO_STRING = "no properly formatted"
    IMPROPER_STRING = "improperly formatted"

    def __init__(self, path, job=print):
        """Function docstring."""
        try:
            self.COMMAND = self.COMMANDS[path]
            self.job = job
        except KeyError:
            raise NoHashCommandAvailable()

    def _call(self, *args):
        """Function docstring."""
        return self._decode(
            subprocess.check_output(
                (self.COMMAND,) + args))

    def count_and_compare_lines(self, hashfile, objectsdir):
        """Function docstring."""
        lines = self._count_lines(hashfile)
        objects = self._count_files(objectsdir)
        if lines == objects:
            return True
        self.job.pyprint(
            "{}: Comparison failed with {} checksum lines and {} "
            "transfer files"
            .format(self.get_ext(hashfile), lines, objects), file=sys.stderr)
        return False

    def compare_hashes(self, hashfile, objectsdir):
        """Function docstring."""
        if not self.count_and_compare_lines(hashfile, objectsdir):
            return 1
        try:
            self._call('-c', '--strict', hashfile)
            return 0
        except subprocess.CalledProcessError as err:
            for line in self._decode(err.output):
                if line.endswith(self.FAIL_STRING) or \
                    self.ZERO_STRING in line or \
                        self.IMPROPER_STRING in line:
                    self.job.pyprint(
                        u"{}: {}".format(self.get_ext(hashfile), line),
                        file=sys.stderr
                    )
            return err.returncode

    def version(self):
        """Function docstring."""
        try:
            return self._call('--version')[0]
        except subprocess.CalledProcessError:
            return self.COMMAND

    @staticmethod
    def _decode(out):
        """Function docstring."""
        try:
            return str(out, "utf8").split("\n")
        except TypeError:
            return out.decode("utf8").split("\n")

    @staticmethod
    def get_ext(path):
        """Return the extension of the checksum file provided"""
        ext = os.path.splitext(path)[1]
        if not ext:
            return path
        return ext.replace(".", "")

    @staticmethod
    def _count_lines(path):
        """Function docstring."""
        count = 0
        with open(path) as hashfile:
            for count, _ in enumerate(hashfile):
                pass
        # Negate zero-based count
        return count + 1

    @staticmethod
    def _count_files(path):
        return sum([len(files) for _, _, files in os.walk(path)])


def run_hashsum_commands(job):
    """Run hashsum commands and generate a cumulative return code."""
    transfer_dir = None
    event_id = None
    transfer_uuid = None
    try:
        transfer_dir = job.args[1]
        event_id = job.args[0]
        transfer_uuid = job.args[0]
    except IndexError:
        logger.error("Cannot access expected module arguments: %s", job.args)
        return 1
    ret = 0
    for hashfile in Hashsum.COMMANDS:
        os.chdir(transfer_dir)
        objectsdir = "objects/"
        hashsum = None
        if os.path.exists(hashfile):
            try:
                hashsum = Hashsum(hashfile, job)
            except NoHashCommandAvailable:
                job.pyprint("Nothing to do for {}. No command available."
                            .format(Hashsum.get_ext(hashfile)))
                continue
        if hashsum:
            job.pyprint(
                "Comparing transfer checksums with the supplied {} file"
                .format(Hashsum.get_ext(hashfile)), file=sys.stderr)
            result = hashsum.compare_hashes(
                hashfile=hashfile, objectsdir=objectsdir)
            if result == 0:
                # TODO: Write PREMIS here...
                job.pyprint(
                    "{}: Comparison was OK".format(Hashsum.get_ext(hashfile)))
                continue
            ret += result
    return ret


def call(jobs):
    """Primary entry point for MCP Client script."""
    for job in jobs:
        with job.JobContext(logger=logger):
            job.set_status(run_hashsum_commands(job))
