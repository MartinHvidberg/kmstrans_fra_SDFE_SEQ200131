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
# can be run from the python console in Trui.
# This setup will test the Trui (Qt4Widget) interface -
# simlk, sept. 2015

import os
import unittest
import tempfile
import File2File
import TrLib_constants
from LibTrui import AffineTransformation
TRUI = None

affine_mod = AffineTransformation()
affine_mod.apply = True
affine_mod.R = {(0, 0): 1.5, (1, 1): 0.9, (0, 1): 0.1}
affine_mod.T = {0: 100.0, 1: 200.0, 2: 10.1}

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
     },
    {"shall_fail": False,
     "ext_out": ".txt",
     "settings":
        {"ds_in": os.path.join(DATA_DIR, "3d_kms.txt"),
         "mlb_out": "crt_wgs84",
         "apply_affine": True,
         "affine_mod_out": affine_mod,
         "driver": "KMS"}
     },
    {"shall_fail": False,
     "ext_out": ".sqlite",
     "settings":
        {"ds_in": os.path.join(DATA_DIR, "lines.sqlite"),
         "mlb_in": "webmrc_wgs84",  # this translation seemingly fails!
         "mlb_out": "geo_wgs84",
         "driver": "OGR",
         "format_out": "SQLite"}
     }
)


class TruiTest(unittest.TestCase):

    def setUp(self):
        assert TRUI is not None
        self.trui = TRUI

    def test_set_region_dk(self):
        self.trui.handleStdOut("Setting region DK")
        self.trui.setRegionDK()
        self.assertTrue(self.trui.region == TrLib_constants.REGION_DK)

    def test_set_region_fo(self):
        self.trui.handleStdOut("Setting region FO")
        self.trui.setRegionFO()
        self.assertTrue(self.trui.region == TrLib_constants.REGION_FO)

    def test_set_region_gr(self):
        self.trui.handleStdOut("Setting region GR")
        self.trui.setRegionGR()
        self.assertTrue(self.trui.region == TrLib_constants.REGION_GR)

    def test_set_region_world(self):
        self.trui.handleStdOut("Setting region WORLD")
        self.trui.setRegionWorld()
        self.assertTrue(self.trui.region == TrLib_constants.REGION_WORLD)

    def transform_interactive(self, mlb_in, mlb_out, input_coords, should_be):
        self.trui.handleStdOut("Trying: %s->%s" % (mlb_in, mlb_out))
        self.trui.cb_input_system.lineEdit().setText(mlb_in)
        self.trui.cb_output_system.lineEdit().setText(mlb_out)
        self.trui.setInteractiveInput(input_coords, mlb_in)
        self.trui.transformInput()
        output = self.trui.output_cache.coords
        self.assertTrue(self.trui.output_cache.is_valid)
        for i in range(2):
            self.assertAlmostEqual(output[i], should_be[i], 3)
        self.assertAlmostEqual(output[2], should_be[2], 2)

    def test_interactive_1(self):
        self.transform_interactive("utm32Eetrs89", "geoHetrs89_h_dvr90",
                                   (512200.1, 6143200.1, 0.0), (9.192811341, 55.434853270, -40.5311))

    def test_interactive_2(self):
        self.transform_interactive("utm32Eetrs89", "dktm1H_h_dvr90",
                                   (512200.1, 6143200.1, 0), (212204.7379, 1145535.4502, -40.5311))

    def test_interactive_3(self):
        self.transform_interactive("fotmH_h_fvr09", "fk89H_h_foldmsl",
                                   (200000.0, 876910.2890, 0), (594919.9029, 701535.2571, 0.0030))

    def test_interactive_4(self):
        self.transform_interactive("utm22Ngr96", "crt_gr96",
                                   (451351.7360, 7114111.3190, 0.0), (1716806.0708, -2197411.5650, 5717050.4095))

    def test_angular_units_dg(self):
        self.trui.handleStdOut("Setting geo unit DG")
        self.trui.setAngularUnitsDegrees()
        self.assertEqual(self.trui.geo_unit,
                         TrLib_constants.ANGULAR_UNIT_DEGREES)

    def test_angular_units_nt(self):
        self.trui.handleStdOut("Setting geo unit NT")
        self.trui.setAngularUnitsNt()
        self.assertEqual(self.trui.geo_unit, TrLib_constants.ANGULAR_UNIT_NT)

    def test_angular_units_sx(self):
        self.trui.handleStdOut("Setting geo unit SX")
        self.trui.setAngularUnitsSx()
        self.assertEqual(self.trui.geo_unit, TrLib_constants.ANGULAR_UNIT_SX)
    
    def test_change_h_in_button(self):
        mlb = self.trui.cb_input_system.currentText()
        self.trui.on_bt_change_h_in_clicked()
        self.assertNotEqual(mlb, self.trui.cb_input_system.currentText())
    
    def test_change_h_out_button(self):
        mlb = self.trui.cb_output_system.currentText()
        self.trui.on_bt_change_h_out_clicked()
        self.assertNotEqual(mlb, self.trui.cb_output_system.currentText())


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
            "\n***** Testing some transformations of datasources *****")

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
                "    Trying: %s, shall_fail: %s, affine mods: %s" %
                (settings.ds_in, self.test["shall_fail"], settings.apply_affine))
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


class RedirectTestOutput(object):
    """Class to redirect output from unittest"""

    def __init__(self, trui):
        self.trui = trui

    def write(self, text):
        self.trui.handleStdOut(text.rstrip())

    def flush(self):
        pass

    def close(self):
        pass


def test(trui, full=True):
    """Run tests for trui, if full is True run also batch tests"""
    global TRUI
    TRUI = trui
    suite = unittest.TestLoader().loadTestsFromTestCase(TruiTest)
    runner = unittest.TextTestRunner(stream=RedirectTestOutput(trui))
    runner.run(suite)
    if full:
        batch_tester = TestBatch(trui)
        batch_tester.proceed()
