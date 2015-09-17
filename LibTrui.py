"""/*
* Copyright (c) 2015, Danish Geodata Agency, Denmark
* (Geodatastyrelsen), gst@gst.dk
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 */
 """
import sys, os
from TrLib_constants import LIBTRUI
import ctypes
from OGR_drivers import *
DEBUG = False
C_CHAR_P = ctypes.c_char_p
C_INT = ctypes.c_int
LP_c_double = ctypes.POINTER(ctypes.c_double)
LP_c_int = ctypes.POINTER(ctypes.c_int)
libtrui = None
CALL_BACK = None
MESSAGE_HANDLER = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_char_p)
AFFINE_MATRIX = ctypes.c_double * 9
AFFINE_TRANSLATION = ctypes.c_double * 3

class SettingsStruct(ctypes.Structure):
    _fields_ = [('is_kms_format', C_INT),
     ('col_x', C_INT),
     ('col_y,', C_INT),
     ('col_z', C_INT),
     ('flip_xy', C_INT),
     ('flip_xy_in', C_INT),
     ('crt_xyz', C_INT),
     ('zlazy', C_INT),
     ('set_output_projection', C_INT),
     ('copy_bad', C_INT),
     ('n_decimals', C_INT),
     ('units_in_output', C_INT),
     ('kms_no_units', C_INT),
     ('sep_char', C_CHAR_P),
     ('output_geo_unit', C_CHAR_P),
     ('input_geo_unit', C_CHAR_P),
     ('comments', C_CHAR_P)]


def setMessageHandler(fct):
    global libtrui
    global CALL_BACK
    CALL_BACK = MESSAGE_HANDLER(fct)
    libtrui.RedirectOGRErrors()
    libtrui.SetCallBack(CALL_BACK)


def initLibrary(prefix, lib_name = LIBTRUI):
    global libtrui
    path = os.path.join(prefix, lib_name)
    try:
        libtrui = ctypes.cdll.LoadLibrary(path)
        libtrui.GetOGRDrivers.argtypes = [C_INT, C_INT]
        libtrui.GetOGRDrivers.restype = C_CHAR_P
        libtrui.GetLayer.restype = ctypes.c_void_p
        libtrui.GetLayer.argtypes = [ctypes.c_void_p, C_INT]
        libtrui.GetLayerCount.restype = C_INT
        libtrui.GetLayerCount.argtypes = [ctypes.c_void_p]
        libtrui.GetLayerName.restype = C_CHAR_P
        libtrui.GetLayerName.argtypes = [ctypes.c_void_p]
        libtrui.GetNextGeometry.restype = ctypes.c_void_p
        libtrui.GetNextGeometry.argtypes = [ctypes.c_void_p, LP_c_int]
        libtrui.Close.restype = None
        libtrui.Close.argtypes = [ctypes.c_void_p]
        libtrui.Open.restype = ctypes.c_void_p
        libtrui.Open.argtypes = [C_CHAR_P]
        libtrui.GetCoords.argtypes = [ctypes.c_void_p,
         LP_c_double,
         LP_c_double,
         C_INT]
        libtrui.GetCoords.restype = None
        libtrui.RedirectOGRErrors.restype = None
        libtrui.SetCallBack.restype = None
        libtrui.SetCallBack.argtypes = [MESSAGE_HANDLER]
        libtrui.affine_transformation.argtypes = [ctypes.c_void_p,
         LP_c_double,
         LP_c_double,
         LP_c_double]
        libtrui.affine_transformation.restype = None
        libtrui.affine_from_string.argtpes = [ctypes.c_char_p]
        libtrui.affine_from_string.restype = ctypes.c_void_p
        libtrui.affine_destroy.argtypes = [ctypes.c_void_p]
        libtrui.affine_destroy.restype = None
    except Exception as e:
        return (False, repr(e))

    return (True, '')


def getOGRFormats(is_output = True):
    libtrui.GetOGRDrivers(1, 0)
    drivers = []
    drv = libtrui.GetOGRDrivers(0, 1)
    while drv is not None:
        if drv in OGR_SHORT_TO_LONG:
            drivers.extend(OGR_SHORT_TO_LONG[drv])
        else:
            drivers.append(drv)
        drv = libtrui.GetOGRDrivers(0, int(is_output))

    return drivers


def getLayer(ds, layer_num = 0):
    return libtrui.GetLayer(ds, layer_num)


def getNextGeometry(hLayer):
    nump = ctypes.c_int(0)
    geom = libtrui.GetNextGeometry(hLayer, ctypes.byref(nump))
    return (geom, nump.value)


def close(ds):
    libtrui.Close(ds)


def open(inname):
    return libtrui.Open(inname)


def getCoords(geom, n):
    arr = ctypes.c_double * n
    x = arr()
    y = arr()
    libtrui.GetCoords(geom, ctypes.cast(x, LP_c_double), ctypes.cast(y, LP_c_double), n)
    return zip(x, y)


def getLines(inname):
    ds = open(inname)
    lines = []
    if ds is None:
        return []
    else:
        layer = getLayer(ds, 0)
        if layer is None:
            close(ds)
            return []
        geom, n = getNextGeometry(layer)
        i = 0
        while geom != 0 and geom is not None:
            i += 1
            if n == 0:
                if DEBUG:
                    print 'No points, feature %d' % i
            else:
                lines.append(getCoords(geom, n))
            geom, n = getNextGeometry(layer)

        if DEBUG:
            print geom, geom == 0, geom == None
        close(ds)
        return lines


def getLayerNames(ds):
    layers = []
    if ds is not None:
        n = libtrui.GetLayerCount(ds)
        for i in range(n):
            layers.append(libtrui.GetLayerName(libtrui.GetLayer(ds, i)))

    return layers


class AffineTransformation(object):

    def __init__(self):
        self.R = {}
        self.T = {}
        self.apply = False
        self.paffine = None
        
    def tostring(self):
        val = ''
        for ij in self.R:
            val += 'r{0:d}{1:d}={2:s},'.format(ij[0], ij[1], str(self.R[ij]))

        for i in self.T:
            val += 't{0:d}={1:s},'.format(i, str(self.T[i]))

        if len(val) > 0:
            val = val[:-1]
        return val

    def setup(self):
        if self.paffine is not None:
            libtrui.affine_destroy(self.paffine)
            self.paffine = None
        val = self.tostring()
        if len(val) > 0:
            self.paffine = libtrui.affine_from_string(val)
        return

    def transform(self, x, y, z):
        if self.paffine is None:
            return (x, y, z)
        else:
            x = ctypes.c_double(x)
            y = ctypes.c_double(y)
            z = ctypes.c_double(z)
            libtrui.affine_transformation(self.paffine, ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
            return (x.value, y.value, z.value)

    def get_nvals(self):
        return len(self.R) + len(self.T)

    def __del__(self):
        """Destructor"""
        if self.paffine is not None:
            libtrui.affine_destroy(self.paffine)
        return
