/*
 * Copyright (c) 2011, National Survey and Cadastre, Denmark
 * (Kort- og Matrikelstyrelsen), kms@kms.dk
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
 


#include "geo_lab.h"

extern int tr_DSFL(char *MainFilePath, char *SlaveFilePath, 
                   union geo_lab *g_lab_slave, char* MsgStr);

/* 
MainFilePath contain the name of the input DSFL file 

SlaveFilePath contain the name of the output DSFL file 

g_lab_slave the pointer to the output coordinate system (incl. Height)

MsgStr      contain error messages if any

tr_DSFL return value int:
          0:  transformation ok.
     TRF_XX:  an error from Transformation system see geo_lab.h
        -50:  inputfile not opened: STOP
        -51:  outputfile not opened: STOP
        -52:  FileFormat is probably NOT DSFL !
        -53:  DSFL command %H1 twice
        -54:  DSFL command %H2 twice
        -55:  DSFL command %H3 twice
        -56:  DSFL command %H4 twice
        -57:  DSFL command %H5 twice
        -58:  H1 command : unknown DSFLlabel
        -59:  H2 command : unknown DSFL_Hlabel
        -60:  NO CRD label in input file
        -61:  DSFL command %H3 before %H1
        -62:  %H3: S34 layout should be YX or XY
        -63:  %H3: UTM layout should be NE or EN
        -64:  %H3: layout error
        -65:  Main system NOT ok
        -66:  Slave system NOT ok
        -67:  Height label found in one system only
        -68:  Syntax error or Transfor,ation error
        -69:  Error in H1/H2/H3 in DSFL-Format

example of call:
  conv_lab("utm32Heuref89_h_dvr90", &i_lab_a);
  res = tr_DSFL("ind", "ud", &i_lab_a, err_txt);
  if (res) fprintf(stdout, err_txt);

*/
