# Copyright (c) 2013, National Geodata Agency, Denmark
# (Geodatastyrelsen), gst@gst.dk
# 
# Permission to use, copy, modify, and/or distribute this software for any
#purpose with or without fee is hereby granted, provided that the above
#copyright notice and this permission notice appear in all copies.
#  
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN 
#ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#######################################################
## Some minilabel utility methods
## TODO: fixup dependencies as much functionality has been moved to TrLib.py - DONE
## simlk, oct 2012.
## 
#######################################################
import sys
from TrLib import SplitMLB,GetParameters,DescribeProjection,LabelException

#DEFAULT FIELD LABELING MECHANISM - moved from TrLib_constants to correct a regression...#
GEO_LABELS=["Longitude:","Latitude:","H:"]
PROJ_LABELS=["Easting:","Northing:","H:"]
S34_LABELS=["X (Westing):","Y (Northing):","H:"]
CRT_LABELS=["X:","Y:","Z:"]
def getSystemLabels(mlb): 
    try:
        region,proj,datum,hdatum,htype=SplitMLB(mlb)
    except:
        return None
    if proj=="geo":
        return GEO_LABELS
    if proj=="crt":
        return CRT_LABELS
    if proj in ["s34j","s34s","s34b","s45b","os","kk","gs","gsb"]:
        return S34_LABELS
    return PROJ_LABELS


def isProjWeaklyDefined(mlb):
    try:
        region,proj,datum,hdatum,htype=SplitMLB(mlb)
    except:
        return True
    if proj in ["s34j","s34s","s34b","s45b","os","kk"]:
        return True
    return False

def getPlanarSystems(mlbs):
    systems=[]
    for mlb in mlbs:
        try:
            region,proj,datum,hdatum,htype=SplitMLB(mlb)
        except:
            continue
        if proj=="crt":
            continue
        out=proj
        if len(datum)>0:
            out+="_"+datum
        for param in GetParameters(mlb):
            out+="  "+param
        systems.append(out)
    return systems

def getImplicitDatum(mlb_prj):
    descr_prj,impl_dtm=DescribeProjection(mlb_prj)
    if descr_prj is None or len(impl_dtm)==0:
        raise LabelException("Label not OK!")
    return impl_dtm

def changeHeightSystem(mlb,default_systems, allowed_systems=None,allow_no_heights=True):
    try:
        region,proj,datum,hdatum,htype=SplitMLB(mlb)
    except:
        return mlb
    
    if proj=="crt":
        return mlb
    if len(datum)==0:
        sdtm=getImplicitDatum(proj)
    else:
        sdtm=datum
    if allowed_systems is not None and sdtm in allowed_systems:
        systems=allowed_systems[sdtm]
    else:
        systems=default_systems
    i=0
    if not hdatum in systems:
        default=systems[i]
    else:
        i=(systems.index(hdatum)+1) % len(systems)
        default=systems[i]
    if (not allow_no_heights) and default=="_": #go to next system
        default=systems[(i+1)% len(systems)]
    out=""
    if region!="":
        out=region+"_"
    out+=proj
    if default in ["E","N"]:
        out+=default+datum
    elif default=="_":
        if len(datum)>0:
            out+="_"+datum
    else:
        out+="H"+datum+"_h_"+default
    for param in GetParameters(mlb):
        out+="  "+param
    return out


