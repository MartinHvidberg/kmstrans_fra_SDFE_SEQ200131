# Copyright (c) 2015, Simon Kokkendorff, <silyko at gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

# Some tests for KMSTrans2 -
# can be run from the python console or from a command line.
# This setup will test the Trui (Qt4Widget) interface -
# not suitable for unit tests.
# simlk, sept. 2015

import os
# import unittest
import tempfile
import threading
import File2File
from TrLib_constants import TROGRNAME
TROGR = os.path.join(os.path.dirname(__file__), "bin", TROGRNAME)
File2File.setCommand(TROGR)
EVENT = threading.Event()  # used to wait for a thread to finish.

# Some tests to run to test interactive interface:
# each element is mlbin,mlbout,coords_in,coords_out,tolerance
TEST_INTERACTIVE = {
    "setRegionDK": (
        ("utm32Eetrs89", "geoHetrs89_h_dvr90", (512200.1, 6143200.1, 0.0),
            (9.192811341, 55.434853270, -40.5311), (1e-4, 1e-4, 1e-2)),
        ("utm32Eetrs89", "dktm1H_h_dvr90", (512200.1, 6143200.1, 0),
            (212204.7379, 1145535.4502, -40.5311), (1e-3, 1e-3, 1e-2))
    ),
    "setRegionFO": (
        ("fotmH_h_fvr09", "fk89H_h_foldmsl", (200000.0, 876910.2890, 0),
            (594919.9029, 701535.2571, 0.0030), (1e-3, 1e-3, 1e-2)),
    ),
    "setRegionGR": (
        ("utm22Ngr96", "crt_gr96", (451351.7360, 7114111.3190, 0.0),
            (1716806.0708, -2197411.5650, 5717050.4095), (1e-3, 1e-3, 1e-3)),
    )
}

# Test some files.
# A list of dicts whit attrs corresponding to File2File.F2F_Settings
DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "test_data"))
BATCH_TESTS = (
    {"shall_fail": False,
     "ext_out": ".txt",
     "settings":
        {"ds_in": os.path.join(DATA_DIR, "3d_with_spaces.txt"),
         "mlb_out": "geoHwgs84_h_dvr90",
         "driver": "TEXT",
         "sep_char": None,
         "output_geo_unit": "dg"}
     },
    {"shall_fail": False,
     "ext_out": ".txt",
     "settings":
        {"ds_in": os.path.join(DATA_DIR, "3d_with_commas_indent_mlb.txt"),
         "mlb_out": "geoHwgs84_h_dvr90",
         "driver": "TEXT",
         "sep_char": ",",
         "output_geo_unit": "dg"}
     },
    {"shall_fail": True,
     "ext_out": ".txt",
     "settings":
        {"ds_in": os.path.join(DATA_DIR, "3d_with_spaces_no_mlb.txt"),
         "mlb_out": "geoHwgs84_h_dvr90",
         "driver": "TEXT",
         "sep_char": None,
         "output_geo_unit": "dg"}
     },
    {"shall_fail": False,
     "ext_out": ".txt",
     "settings":
        {"ds_in": os.path.join(DATA_DIR, "3d_kms.txt"),
         "mlb_out": "crt_wgs84",
         "driver": "KMS"}
     }
)


def test_interactive(trui):
    """Run some tests for the interactive tab in Trui"""
    nerr = 0
    trui.handleStdOut("\m***** Testing interactive tab *****\n")
    for region_setter in TEST_INTERACTIVE:
        trui.handleStdOut("    Calling: "+region_setter)
        getattr(trui, region_setter)()
        for itest in TEST_INTERACTIVE[region_setter]:
            trui.handleStdOut("        Trying: %s->%s" % (itest[0], itest[1]))
            trui.cb_input_system.lineEdit().setText(itest[0])
            trui.cb_output_system.lineEdit().setText(itest[1])
            trui.setInteractiveInput(itest[2], itest[0])
            trui.transformInput()
            output = trui.output_cache.coords
            should_be = itest[3]
            tolerance = itest[4]
            try:
                assert trui.output_cache.is_valid
                for i in range(3):
                    assert abs(output[i] - should_be[i]) < tolerance[i]
            except Exception as e:
                trui.handleStdErr("        Failed..." + str(e))
                nerr += 1
    return nerr


class TestBatch(object):
    """
    Test transformation of a few datasources.
    We want to have everything (trlib etc.) setup as in the Trui interface
    - so use that (no unittest, no commandline - yet!).
    """

    def __init__(self, trui):
        self.trui = trui
        trui.setForeignHook(self)
        self.n_err = 0
        self.tests = iter(BATCH_TESTS)
        self.test = None
        trui.handleStdOut(
            "\n***** Testing some transformations of datasources *****\n")

    def proceed(self, result=None):
        """Go to next test"""
        if self.test is not None:
            if (not result) and (not self.test["shall_fail"]):
                self.n_err += 1
                self.trui.handleStdErr("    ...fail...")
            else:
                self.trui.handleStdOut("    ...succes...")
            if os.path.isfile(self.test["settings"]["ds_out"]):
                os.remove(self.test["settings"]["ds_out"])
                # TODO: compare output to expected
        try:
            self.test = self.tests.next()
        except StopIteration:
            self.finish()
            return
        started = False
        while not started:
            settings = File2File.F2F_Settings()
            # Create a temp filename
            f = tempfile.NamedTemporaryFile(
                suffix=self.test["ext_out"], delete=False)
            f.close()
            os.unlink(f.name)  # now we have a unique name, nice :-)
            self.test["settings"]["ds_out"] = f.name  # store outname
            settings.__dict__.update(self.test["settings"])
            self.trui.handleStdOut(
                "    Trying: %s, shall_fail: %s" %
                (settings.ds_in, self.test["shall_fail"]))
            self.trui.transformFile2File(settings)
            if not settings.is_started:
                self.trui.handleStdErr("    Transformation unable to  start!")
                self.n_err += 1
                # go to next test!
                try:
                    self.test = self.tests.next()
                except StopIteration:
                    self.finish()
                    return
                continue
            started = True

    def finish(self):
        self.trui.handleStdOut(
            "Batch test finished with %d errors" % self.n_err)


def test(trui, full=True):
    """Run tests for trui, if full is True run also batch tests"""
    nerr = test_interactive(trui)
    if full:
        batch_tester = TestBatch(trui)
        batch_tester.proceed()
    return nerr
