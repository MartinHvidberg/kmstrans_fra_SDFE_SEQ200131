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

// C_SPACE og C_DIGIT udskiftet med henh. isspace og isdigit   20120529 stl

#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>

#include "conv_lab.h"
#include "gd_trans.h"
#include "geoid_d.h"
#include "geoid_c.h"
#include "geo_lab.h"
#include "get_mlb.h"



int tr_DSFL(char *MainFilePath, char *SlaveFilePath,
            union geo_lab *g_lab_slave, char* MsgStr)
{

  enum CDSFLcommand {CMD_H1, CMD_H2, CMD_H3, CMD_H4, CMD_H5, CMD_H6,
    CMD_H9, CMD_T, CMD_P1K, CMD_LK, CMD_FK, CMD_STOP, CMD_DEFAULT};

  struct ccc {
    char               txt[6];
    enum CDSFLcommand  Cmd;
  };

  enum CDSFLLabel {LAB_S34S, LAB_S34J, LAB_S45B, LAB_S34B, LAB_U32,
    LAB_U33, LAB_U32W, LAB_U33W, LAB_KP2000J, LAB_KP2000S, LAB_KP2000B,
    LAB_DKTM1, LAB_DKTM2, LAB_DKTM3, LAB_DKTM4, LAB_LOK, LAB_STOP,
    LAB_DVR90, LAB_DNN, LAB_DNNI, LAB_DNNM, HAB_STOP};

  struct cccLab {
    enum CDSFLLabel  Lab;
    char             mlb[MLBLNG];
    char             DSFLmlb[10];
    short            lng;
  };

  struct ccc DSFLcommands[] = {
    {"H1 ", CMD_H1},
    {"H2 ", CMD_H2},
    {"H3 ", CMD_H3},
    {"H4 ", CMD_H4},
    {"H5 ", CMD_H5},
    {"H6 ", CMD_H6},
    {"H9 ", CMD_H9},
    {"T",   CMD_T},
    {"P1K", CMD_P1K},
    {"L*K", CMD_LK},
    {"F*K", CMD_FK},
    {"S",   CMD_STOP},
    {"",    CMD_DEFAULT}
  };

  struct cccLab DSFLlabels[] = {
    {LAB_U32W,    "utm32_euref89", "U32E",    13},
    {LAB_U32W,    "utm32_etrf89",  "U32E",    13},
    {LAB_U32W,    "utm32_etrs89",  "U32E",    12},
    {LAB_U33W,    "utm33_euref89", "U33E",    13},
    {LAB_U33W,    "utm33_etrf89",  "U33E",    13},
    {LAB_U32W,    "utm33_etrs89",  "U32E",    12},
    {LAB_U32W,    "utm32_wgs84",   "U32W",    11},
    {LAB_U33W,    "utm33_wgs84",   "U33W",    11},
    {LAB_DKTM1,   "dktm1",         "DKTM1",    5},
    {LAB_DKTM2,   "dktm2",         "DKTM2",    5},
    {LAB_DKTM3,   "dktm3",         "DKTM3",    5},
    {LAB_DKTM4,   "dktm4",         "DKTM4",    5},
    {LAB_S34S,    "s34s" ,         "S34S",     4},
    {LAB_S34J,    "s34j" ,         "S34J",     4},
    {LAB_S45B,    "s34b" ,         "S34B",     4},
    {LAB_S34B,    "s45b" ,         "S45B",     4},
    {LAB_KP2000J, "kp2000j",       "KP2000J",  7},
    {LAB_KP2000S, "kp2000s",       "KP2000S",  7},
    {LAB_KP2000B, "kp2000b",       "KP2000B",  7},
    {LAB_U32,     "utm32_ed50",    "U32",     10},
    {LAB_U33,     "utm33_ed50",    "U33",     10},
    {LAB_LOK,     "local",         "LOK",      5},
    {LAB_STOP,    "",              "",         0}
  };

  struct cccLab DSFLlabelH[] = {
    {LAB_DVR90,  "h_dvr90", "DVR90", 7},
    {LAB_DNN,    "h_dnn",   "DNNGI", 5},
    {LAB_DNNI,   "h_gi50",  "DNNGI", 6},
    {LAB_DNNM,   "h_gm91",  "DNNGM", 6},
    {HAB_STOP,   "",        "",      0}
  };
  struct cccLab *DSFLlabPtrMain  = NULL;
  struct cccLab *DSFLlabPtrMaHgt = NULL;
  struct cccLab *DSFLlabPtrSlave = NULL;
  struct cccLab *DSFLlabPtrSlHgt = NULL;

  enum CDSFLcommand   DSFLcommand;
  struct ccc         *CmdPtr;
  struct cccLab      *DSFLlabPtr;

  short      g_lab_main_ok = 0;

  short      H1Ok = 0, H2Ok = 0, H3Ok = 0, H4Ok = 0, H5Ok = 0, H6Ok = 1;
  short      bInputHeights = 0;
  short      bSwopInputCoo = 0, bSwopOutputCoo = 0;
  FILE      *fh_in, *fh_out;
  char       c, *p, *cp, *cp1, *cp2, *TxtPtr;
  char       CmdTxt[20], DSFLmlb[20], mlbOut[MLBLNG];
  short      DSFLStop = 0, CmdStop = 0;
  short      cStop = 0, LabFound = 0, HLabFound = 0;
  int        PctCount = 0, NlCount = 0, Lineno = 0, lv = 0;
  int        qCmd = 0, res = 0, lng;

  union  geo_lab    g_lab_main_a;
  union  geo_lab   *g_lab_main = &g_lab_main_a;
  struct coord_lab *c_lab_main = &g_lab_main->u_c_lab;
  struct mgde_str   geoid_table;

  char           CmdTerm = '_', CX[20], buffer[100], ParamIdTxt[80];

  double         H4C1 = 0.0, H4C2 = 0.0, H4Z = 0.0;
  double         H5C1 = 0.0, H5C2 = 0.0, H5Z = 0.0;
  double         C1Min, C1Max, C2Min, C2Max, ght;
  double         RefC1 = 0.0, RefC2 = 0.0, RefC3 = 0.0;
  double         C1In = 0.0, C2In = 0.0, C3In = 0.0;
  double         C1Out, C2Out, C3Out, tmp;
  double         Val[3], ParamValue, DummyH= 0.0;

  int            cmdlng, Dec = 3, s, n;
  int            qXerror = 0, qBufChars = 0;
  int            qCoordsPrSet = 0, qValues = 0;

  long           qTransCommands = 0;
  long           qSyntaxError = 0, qFrameError = 0, qTransError = 0;

  short          bMinMaxOk = 0;
  short          CmdFound, HeaderOk = 0;
  short          First = 1, CooOk, GoOn = 1, cError;
  short          bDigitsRecorded =0, bSignRecorded =0, bPktRecorded =0;
  short          bAfterParams = 0, bLineParamStarted = 0;
  short          DummyH9 = 0 , DummyHout = 0;

  geoid_table.init = 0;
  *MsgStr          = '\0';

  if ((fh_in=fopen(MainFilePath, "r"))==NULL) {
    (void) sprintf(MsgStr,
           "\nCannot open infile: %s\n  ", MainFilePath);
    return(-50);
  }
  else {
    /* Is FileFormat Possible DSFL?  Look for '%' chars */

    (void) fseek(fh_in, 0L, SEEK_SET);
    while (!cStop) {
      c = (char)getc(fh_in);
      if (c=='\n') NlCount++;
      else if (c=='%') PctCount++;
      if (feof(fh_in) || NlCount>5) cStop = 1;
    }
    (void) fseek(fh_in, 0L, SEEK_SET);

    if (NlCount>5 && PctCount<2) {
      (void) strcpy(MsgStr, "FileFormat is probably NOT DSFL !");
      (void) fclose(fh_in);
      return(-52);
    }


    /* Test Syntax and set Label */
    H1Ok = 0;
    H2Ok = 0;
    H3Ok = 0;

    do     c = (char) getc(fh_in);
    while (c!='%' && !feof(fh_in));

    if (c == '%')  {
      do {
        cStop = 0;
        for (cp1=mlbOut, lng=0; !cStop; ) {
          c = (char) getc(fh_in);
          if (c=='%' || feof(fh_in)) cStop = 1;
          else {
            if (c=='\n') ++ Lineno;
            if (lng<100)
              *(cp1++) = c;
            lng++;
          }
        }
        *cp1   = '\0';
        TxtPtr = NULL;
        cStop  = 0;
        lng    = 0;
        for (cp1 = mlbOut, cp2 = CmdTxt;
             *cp1 && !cStop && lng<10; cp1++) {
          if (!isspace(*cp1)) {
            *(cp2++) = *cp1;
            lng++;
          }
          else {
            cStop = 1;
            TxtPtr = cp1;
          }
        }
        *cp2 = '\0';
        for (cp1 = TxtPtr, cp2 = DSFLmlb; *cp1; cp1++)
            if (!isspace(*cp1)) *(cp2++) = *cp1;
        *cp2 = '\0';

        if (!strcmp(CmdTxt, "H1")) {
          if (H1Ok) {
            (void) strcpy(MsgStr, "DSFL command %H1 twice\n");
            res = -53;
          }
          else {
            H1Ok = 1;
            for (DSFLlabPtr=DSFLlabels;
                 !LabFound && *DSFLlabPtr->mlb != '\0'; DSFLlabPtr++) {
              if (!strcmp(DSFLlabPtr->DSFLmlb, DSFLmlb)) {
                LabFound       = 1;
                DSFLlabPtrMain = DSFLlabPtr;
              }
            }
          }

          if (!LabFound) {
            (void) sprintf(MsgStr,
                    "H1 command in line %d : no DSFLlabel : %s",
                    Lineno, DSFLmlb);
            res = -58;
          }
        } else
        if (!strcmp(CmdTxt, "H2")) {  /* Height system */
          if (H2Ok) {
            (void) strcpy(MsgStr, "DSFL command %H2 twice\n");
            res = -54;
          }
          else {
            H2Ok = 1;
            for (DSFLlabPtr=DSFLlabelH;
                !HLabFound && *DSFLlabPtr->mlb != '\0'; DSFLlabPtr++) {
              if (!strcmp(DSFLlabPtr->DSFLmlb, DSFLmlb)) {
                HLabFound       = 1;
                DSFLlabPtrMaHgt = DSFLlabPtr;
              }
            }
          }

          if (!HLabFound) {
            (void) sprintf(MsgStr,
                    "H2 command in line %d : no DSFL_Hlabel : %s",
                    Lineno, DSFLmlb);
            res = -59;
          }

        } else
        if (!strcmp(CmdTxt, "H3")) {  /* TEST Height system */
          if (H3Ok) {
            (void) strcpy(MsgStr, "DSFL command %H3 twice\n");
            (void) fclose(fh_in);
            return(-55);
          }
          else if (!H1Ok) {
            (void) strcpy(MsgStr, "DSFL command %H3 before %H1\n");
            res = -61;
          }
          else {
            bInputHeights = (short) (strlen(DSFLmlb) == 3);
            bSwopInputCoo = 0;
            if (DSFLlabPtrMain->Lab <= LAB_S34B) {
              if (!strncmp(DSFLmlb, "YX", 2)) H3Ok = 1;
              else if (!strncmp(DSFLmlb, "XY", 2)) {
                bSwopInputCoo = 1;
                H3Ok          = 1;
              }
              else {
                (void) sprintf(MsgStr,
                " lineno %d : S34 layout should be YX or XY\n", Lineno);
                res = -62;
              }
            } else
            if (DSFLlabPtrMain->Lab <= LAB_STOP) {
              if (!strncmp(DSFLmlb, "NE", 2)) {
                bSwopInputCoo = 0;
                H3Ok = 1;
              } else
              if (!strncmp(DSFLmlb, "EN", 2)) {
                bSwopInputCoo = 1;
                H3Ok          = 1;
              }
              else {
                (void) sprintf(MsgStr,
                 "Line %-5d : UTM layout should be NE or EN\n", Lineno);
                res = -63;
              }
            }
            else {
              (void) sprintf(MsgStr,
                             "Line %-5d : layout error\n", Lineno);
              res = -64;
            }
          }
          CmdStop = 1;
        }
        if (feof(fh_in) || qCmd>10) CmdStop = 1;
      } while ((!CmdStop) && !res);
    }

    /* SET main_label */
    if (DSFLlabPtrMain->Lab < LAB_LOK) {
      lv = conv_lab(DSFLlabPtrMain->mlb, g_lab_main, "");
      if (DSFLlabPtrMaHgt != 0) {
        (void) strcpy(mlbOut, c_lab_main->mlb);
        if (mlbOut[g_lab_main->u_c_lab.sepix] == '\0')
            (void) strcat(mlbOut, "H_");
        else {
          *(mlbOut + g_lab_main->u_c_lab.sepix) = 'H';
          (void) strcat(mlbOut, "_");
        }
        (void) strcat(mlbOut, DSFLlabPtrMaHgt->mlb);
        lv = conv_lab(mlbOut, g_lab_main, "");
      }
      if (lv != CRD_LAB) {
        (void) sprintf(MsgStr, "NO CRD label: %s\n", mlbOut);
        res = -60;
      }
    }

    if (res < 0) {
      (void) fclose(fh_in);
      return(res);
    }

    if (HLabFound != bInputHeights) {
      g_lab_main_ok          = 0;
    } else {
      g_lab_main_ok         = 1;
    }

  }

  /* ProcessSlaveFile  */
  if ((fh_out=fopen(SlaveFilePath, "w"))==NULL) {
    (void) sprintf(MsgStr,
                   "Cannot open output file: %s\n", SlaveFilePath);
    res = -51;
  }

  if (!g_lab_main_ok) {
    (void) strcat(MsgStr, "Main system NOT ok\n");
    res = -65;
  }
  if (g_lab_slave->u_c_lab.lab_type != CRD_LAB) {
    (void) strcat(MsgStr, "Slave system NOT CRD_lab\n");
    res = -66;
  }

  if (res) {
    (void) fclose(fh_out);
    (void) fclose(fh_in);
    return(res);
  }

  *MsgStr = '\0';

  /* ExecuteDSFL */
  /* ----------- */
  qCoordsPrSet   = bInputHeights ? 3 : 2;
  qValues        = 0;
  qTransCommands = 0;
  qSyntaxError   = 0;
  qFrameError    = 0;
  qTransError    = 0;

  DSFLStop = 0;
  cStop    = 0;

  /* H2Ok is only claimed in 3D */
  if (!(H1Ok && H3Ok)) {
    (void) strcpy(MsgStr, "Error in H1/H2/H3 in DSFL-Format");
    (void) fprintf(fh_out,"\n\n");
    (void) fclose(fh_out);
    (void) fclose(fh_in);
    return(-69);
  }

  if (bInputHeights != (g_lab_slave->u_c_lab.h_ix > 0)) {
    if (bInputHeights) {
      (void) strcpy(MsgStr, "\n***input 3DIM and output 2DIM");
    } else {
      (void) strcpy(MsgStr, "\n***input 2DIM and output 3DIM");
    }
    (void) fprintf(fh_out,"\n\n");
    (void) fclose(fh_out);
    (void) fclose(fh_in);
    return(-67);
  }


  (void) strcpy(mlbOut, g_lab_slave->u_c_lab.mlb);
  *(mlbOut + g_lab_slave->u_c_lab.sepix) = '_';
  for (DSFLlabPtr = DSFLlabels, LabFound = 0;
       !LabFound && *DSFLlabPtr->mlb != '\0'; DSFLlabPtr++) {
    if (!strncmp(DSFLlabPtr->mlb, mlbOut, DSFLlabPtr->lng)) {
      LabFound = 1;
      DSFLlabPtrSlave = DSFLlabPtr;
    }
  }

  if (!LabFound) {
    (void) sprintf(MsgStr,
                   "The system <%s> cannot be used in DSFL-Format",
                   g_lab_slave->u_c_lab.mlb);
    (void) fprintf(fh_out,"\n\n");
    (void) fclose(fh_out);
    (void) fclose(fh_in);
    return(-66);
  }

  bSwopOutputCoo = g_lab_slave->u_c_lab.p_seq;
  if (g_lab_slave->u_c_lab.h_ix > 0) {
    LabFound = 0;
    cp1 = mlbOut + g_lab_slave->u_c_lab.h_ix;
    for (DSFLlabPtr=DSFLlabelH;
         !LabFound && *DSFLlabPtr->mlb != '\0';DSFLlabPtr++) {
      if (!strcmp(DSFLlabPtr->mlb, cp1)) {
        LabFound        = 1;
        DSFLlabPtrSlHgt = DSFLlabPtr;
      }
    }

    if (!LabFound) {
      (void) sprintf(MsgStr,
                     "The system <%s> cannot be used in DSFL-Format",
                     g_lab_slave->u_c_lab.mlb);
      (void) fprintf(fh_out,"\n\n");
      (void) fclose(fh_out);
      (void) fclose(fh_in);
      return(-66);
    }
  }

  H1Ok = 0;
  H2Ok = 0;
  H3Ok = 0;

  (void) fseek(fh_in, 0, SEEK_SET);

  do {
    c = (char) getc(fh_in);
    if (c=='\n') Lineno++;
  } while (c!='%' && !feof(fh_in));

  if (c=='%')
    do {
      cp1    = CmdTxt;
      cmdlng = 0;
      cStop  = 0;
      while (!cStop && !feof(fh_in)) {
        c = (char) getc(fh_in);
        if (c == 'Y')  Lineno--; else
        if (c == '\n') Lineno++;
        if (c == '%')  cStop = 1;
        else if (isspace(c)) {
          if (cmdlng>0) {
            CmdTerm = c;
            cStop   = 1;
          }
        }
        else {
          if (cmdlng>=20) {
            (void) strcpy(MsgStr,  "Command too long");
            cStop = 1;
            ++ qSyntaxError;
          }
          else {
            *(cp1++) = c;
            ++ cmdlng;
          }
        }
      }
      *(cp1) = '\0';

      if (cmdlng > 0) {
        DSFLcommand = CMD_DEFAULT;
        (void) strcpy(CX, CmdTxt);
        lng = (int) strlen(CX);
        CX[lng]   = ' ';
        CX[lng+1] = '\0';
        if ((CX[0]=='L' || CX[0]=='F') && CX[2]=='K') CX[1] = '*';
        if (CX[0]=='T' && CX[1]=='T') CX[0] = 'Z';

        CmdFound = 0;
        for (CmdPtr=DSFLcommands;
             !CmdFound && strcmp(CmdPtr->txt, ""); CmdPtr++) {
          if (strstr(CX, CmdPtr->txt)==CX) {
            CmdFound = 1;
            DSFLcommand = CmdPtr->Cmd;
          }
        }

        switch (DSFLcommand) {
        case CMD_H1 :
          if (H1Ok) {
            (void) strcpy(MsgStr, "DSFL command %H1 twice\n");
            (void) fprintf(fh_out,"\n\n");
            (void) fclose(fh_out);
            (void) fclose(fh_in);
            return(-53);
          }
          else {
            /* g_lab_main is set in: ProcessMainFilePath */
            (void) fprintf(fh_out, "%c%-5s%c", '%', CmdTxt, CmdTerm);
            (void) fprintf(fh_out, "%s\n", DSFLlabPtrSlave->DSFLmlb);
            cStop = 0;
            while (!cStop && !feof(fh_in)) {
              c = (char) getc(fh_in);
              if (c == '\n') Lineno++; else
              if (c == '%')  cStop = 1;
              else *(cp1 ++) = c;
            }
            H1Ok = 1;
          }
          break;
        case CMD_H2 :
          if (H2Ok) {
            (void) strcpy(MsgStr, "DSFL command %H2 twice\n");
            (void) fprintf(fh_out,"\n\n");
            (void) fclose(fh_out);
            (void) fclose(fh_in);
            return(-54);
          }
          else {
            /* g_lab_main is set in: ProcessMainFilePath */
            (void) fprintf(fh_out, "%c%-5s%c", '%', CmdTxt, CmdTerm);
            (void) fprintf(fh_out, "%s\n", DSFLlabPtrSlHgt->DSFLmlb);
            cStop = 0;
            while (!cStop && !feof(fh_in)) {
              c = (char) getc(fh_in);
              if (c == '\n') Lineno++; else
              if (c == '%')  cStop = 1;
              else
                *(cp1 ++) = c;
            }
            H2Ok = 1;
          }
          break;
        case CMD_H3 :
          if (H3Ok) {
            (void) strcpy(MsgStr, "DSFL command %H3 twice\n");
            (void) fprintf(fh_out,"\n\n");
            (void) fclose(fh_out);
            (void) fclose(fh_in);
            return(-55);
          }
          else if (!H1Ok) {
            (void) strcpy(MsgStr, "DSFL command %H3 before H1\n");
            ++ qSyntaxError;
            break;
          }
          else {
            /* g_lab_main is set in: ProcessMainFilePath */
            lng   = 0;
            cp1   = CX;
            cStop = 0;
            while (!cStop && !feof(fh_in)) {
              c = (char) getc(fh_in);
              if (c == '\n') Lineno++; else
              if (c == '%')  cStop = 1; else
              if (!isdigit(c) && !isspace(c)) {
                *(cp1++) = (char) toupper(c);
                ++ lng;
              }
            }

            CX[0] = '\0';
            if (DSFLlabPtrSlave->Lab<=LAB_S34B) {
              (void) strcpy(CX, "YX");
              if (bInputHeights) (void) strcat(CX, "Z");
            }
            else if (DSFLlabPtrSlave->Lab<=LAB_STOP) {
              (void) strcpy(CX,
                   (g_lab_slave->u_c_lab.p_seq) ? "EN" : "NE");
              if (bInputHeights) (void) strcat(CX, "H");
            }

            (void) fprintf(fh_out,"%-6s %s\n", "%H3", CX);
            H3Ok = 1;
          }
          break;
        case CMD_H4 :
        case CMD_H5 :
          if (!H1Ok || !H3Ok) {
            (void) strcpy(MsgStr, "DSFL command H4/H5 before H1, H3\n");
            ++ qSyntaxError;
            break;
          }

          if (DSFLcommand == CMD_H4) {
            if (H4Ok) {
              (void) strcpy(MsgStr, "DSFL command %H4 twice\n");
              (void) fprintf(fh_out,"\n\n");
              (void) fclose(fh_out);
              (void) fclose(fh_in);
              return(-56);
            }

            res = fscanf(fh_in, "%lf %lf", &H4C1, &H4C2);
            if (bInputHeights) res += fscanf(fh_in, "%lf", &H4Z);

            c = ' ';
            while (!feof(fh_in) && c != '%') {
              c = (char) getc(fh_in);
              if (c == '\n') Lineno++;
            }

            if (res != (bInputHeights ? 3 :2)) {
              (void) strcpy(MsgStr, "Height missing/requested\n");
              qSyntaxError++;
              break;
            }

            if (bSwopInputCoo) {
              tmp  = H4C1;
              H4C1 = H4C2;
              H4C2 = tmp;
            }
            H4Ok = 1;
          } else {
            if (H5Ok) {
              (void) strcpy(MsgStr, "DSFL command %H5 twice\n");
              (void) fprintf(fh_out,"\n\n");
              (void) fclose(fh_out);
              (void) fclose(fh_in);
              return(-57);
            }

            res = fscanf(fh_in, "%lf %lf", &H5C1, &H5C2);
            if (bInputHeights)
              res += fscanf(fh_in, "%lf", &H5Z);

            c = ' ';
            while (!feof(fh_in) && c != '%') {
              c = (char) getc(fh_in);
              if (c == '\n') ++ Lineno;
            }

            if (res != (bInputHeights ? 3 :2)) {
              (void) strcpy(MsgStr, "Height missing/requested\n");
              ++ qSyntaxError;
              break;
            }

            if (bSwopInputCoo) {
              tmp  = H5C1;
              H5C1 = H5C2;
              H5C2 = tmp;
            }
            H5Ok = 1;
          }

          if (H4Ok && H5Ok) {
            if (H4C1<H5C1) {
              tmp  = H4C1;
              H4C1 = H5C1;
              H5C1 = tmp;
            }
            if (H4C2<H5C2) {
              tmp  = H4C2;
              H4C2 = H5C2;
              H5C2 = tmp;
            }
            if (H4Z<H5Z) {
              tmp  = H4Z;
              H4Z  = H5Z;
              H5Z  = tmp;
            }

            C1Min = C1Max = C2Min = C2Max = 0.0;
            for (s = 0; s<4; s++) {
              switch (s) {
              case 0 :
                C1In = H4C1;
                C2In = H4C2;
                break;
              case 1 :
                C2In = H5C2;
                break;
              case 2 :
                C1In = H5C1;
                break;
              case 3 :
                C2In = H4C2;
                break;
              }

              res = gd_trans(g_lab_main, g_lab_slave,
                C1In, C2In, 0.0, &C1Out, &C2Out, &C3Out,
                &ght, 0, &geoid_table, "", NULL);
              if (res != 0) {
                if (res != TAB_C_ARE_ && res != TRF_INACC_) ++ qXerror;
                if (res == TRF_ILLEG_) {
                  (void) strcpy(MsgStr,
                   "\nIllegal Transformation\nTransformation stopped");
                  break;
                }
              } else {
                if (bSwopOutputCoo) {
                  tmp   = C1Out;
                  C1Out = C2Out;
                  C2Out = tmp;
                }

                if (First) {
                  C1Max = C1Min = C1Out;
                  C2Max = C2Min = C2Out;
                  First = 0;
                } else {
                  if (C1Max < C1Out) C1Max = C1Out;
                  else
                  if (C1Min > C1Out) C1Min = C1Out;
                  if (C2Max < C2Out) C2Max = C2Out;
                  else
                  if (C2Min > C2Out) C2Min = C2Out;
                }
              }
            } /* end s loop */
            if (qXerror == 0) {
              bMinMaxOk = 1;
              (void) fprintf(fh_out,
                             "%-6s %.0f %.0f","%H4", C1Max, C2Max);
              if (bInputHeights) (void) fprintf(fh_out, " %.0f", H4Z);
              (void) fprintf(fh_out,"\n");

              (void) fprintf(fh_out,
                             "%-6s %.0f %.0f","%H5", C1Min, C2Min);
              if (bInputHeights) (void) fprintf(fh_out, " %.0f", H5Z);
              (void) fprintf(fh_out,"\n");
            }
            else {
              qTransError += qXerror;
            }

          }
          break;

        case CMD_H6 :
          res   = fscanf(fh_in, "%lf %lf", &RefC1, &RefC2);
          if (bInputHeights)
              res += fscanf(fh_in, "%lf", &RefC3);

          CooOk = ((short) res) == ((bInputHeights) ? 3 : 2);

          c = ' ';
          while (!feof(fh_in) && c != '%') {
            c = (char) getc(fh_in);
            if (c == '\n') ++ Lineno;
          }

          if (CooOk) {
            (void) fprintf(fh_out, "%-6s %.*f %.*f",
                           "%H6", Dec, 0.0, Dec, 0.0);
            if (bInputHeights) {
              (void) fprintf(fh_out, " %.*f", Dec, 0.0);
            }
            (void) fprintf(fh_out, "\n");
          }
          else {
            (void) strcpy(MsgStr, "Command H6 Height missing/req\n");
            ++ qSyntaxError;
            H6Ok = 0;
          }
          break;

        case CMD_H9 :
          DummyH9 = 1;
          res     = fscanf(fh_in, "%lf", &DummyH);
          (void) fprintf(fh_out, "%-6s %.*f\n","%H9", Dec, DummyH);
          break;

        case CMD_T :
        case CMD_P1K :
          if (!HeaderOk) {
            HeaderOk = H1Ok && H3Ok && H6Ok;
            if (!HeaderOk) {
              DSFLStop = 1;
              break;
            }
          }

          if (bInputHeights) {
            res   = fscanf(fh_in, "%lf %lf %lf", &C1In, &C2In, &C3In);
            C1In += RefC1;
            C2In += RefC2;
            if (!DummyH9 || C3In != DummyH) C3In += RefC3;
            else {
              C3In      = 30.0;
              DummyHout = 1;
            }
            CooOk = ((short) res) == 3;
          }
          else {
            res   = fscanf(fh_in, "%lf %lf", &C1In, &C2In);
            C1In += RefC1;
            C2In += RefC2;
            C3In  = 30.0;
            CooOk = ((short) res) == 2;
          }

          c = ' ';
          while (!feof(fh_in) && c != '%') {
            c = (char) getc(fh_in);
            if (c == '\n') ++ Lineno;
          }

          if (!CooOk) {
            (void) strcpy(MsgStr, "Height missing/requested\n");
            ++ qSyntaxError;
          }
          else {
            if (bMinMaxOk &&
               (C1In<H5C1 || H4C1<C1In || C2In<H5C2 || H4C2<C2In)) {
              (void) strcpy(MsgStr, "Min/Max error\n");
              ++ qFrameError;
            }
            if (bSwopInputCoo) {
              tmp  = C1In;
              C1In = C2In;
              C2In = tmp;
            }

            res = gd_trans(g_lab_main, g_lab_slave,
              C1In, C2In, C3In, &C1Out, &C2Out, &C3Out,
              &ght, 0, &geoid_table, "", NULL);

            if (res != 0) {
              if (res == TRF_ILLEG_) {
                (void) strcpy(MsgStr,
                 "\nIllegal Transformation\nTransformation stopped");
                break;
              }

              ++ qTransError;
            }
            else {
              if (bSwopOutputCoo) {
                tmp   = C1Out;
                C1Out = C2Out;
                C2Out = tmp;
              }
              (void) fprintf(fh_out, "%c%-5s %.*f %.*f",
                      '%', CmdTxt, Dec, C1Out, Dec, C2Out);
              if (bInputHeights) {
                if (DummyHout) {
                  C3Out     = DummyH;
                  DummyHout = 0;
                }
                (void) fprintf(fh_out, " %.*f", Dec, C3Out);
              }
              (void) fprintf(fh_out, "\n");
            }
          }
          break;

        case CMD_LK :
        case CMD_FK :
          if (!HeaderOk) {
            HeaderOk = H1Ok && H3Ok && H6Ok;
            if (!HeaderOk) {
              DSFLStop = 1;
              break;
            }
          }

          (void) fprintf(fh_out, "%c%-5s%c", '%', CmdTxt, CmdTerm);
          n                 = 0;
          p                 = buffer;
          GoOn              = 1;
          cError            = 0;
          bDigitsRecorded   = 0;
          bLineParamStarted = 0;
          while (GoOn && !feof(fh_in)) {
            c = (char) getc(fh_in);
            switch (c) {
            case '0':
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
            case '9':
              *(p++) = c;
              ++ qBufChars;
              bDigitsRecorded = 1;
              break;
            case '-':
            case '+':
              if (bDigitsRecorded || bSignRecorded) {
                cError = 1;
                GoOn   = 0;
              } else  {
                *(p++)        = c;
                bSignRecorded = 1;
                ++ qBufChars;
              }
              break;
            case '.' :
              if (bPktRecorded) {
                cError = 1;
                GoOn   = 0;
              } else  {
                *(p++)       = c;
                bPktRecorded = 1;
                ++ qBufChars;
              }
              break;
            case 'R' :
            case 'H' :
            case 'A' :
              if (bDigitsRecorded) {
                DSFLStop = 1;
                (void) strcpy(MsgStr, "Digits recorded before R/H/A\n");
                ++ qSyntaxError;
              }
              bLineParamStarted = 1;
              bDigitsRecorded   = 0;
              p                 = buffer;
              *p                = '\0';

              ParamIdTxt[0]     = c;
              cp                = ParamIdTxt + 1;
              c                 = (char) getc(fh_in);
              while (!isspace(c) && !feof(fh_in)) {
                *(cp++) = c;
                c       = (char) getc(fh_in);
              }
              *cp = '\0';
              cp  = ParamIdTxt;
              break;
            case '\n':
            case ' ' :
            case '\t':
            case '%' :
              if (c == '\n') {
                ++ Lineno;
                if (!bDigitsRecorded) {
                  if (bAfterParams) (void) fprintf(fh_out, "\n");
                }
              }
              if (bDigitsRecorded) {
                if (bLineParamStarted) {
                  *p                = '\0';
                  bLineParamStarted = 0;
                  ParamValue        = atof(buffer);
                  if (bAfterParams) (void) fprintf(fh_out, ",");
                  (void) fprintf(fh_out,
                                 " %s %3.3f", ParamIdTxt, ParamValue);
                  bAfterParams      = 1;
                  n                 = 0;
                } else {
                  *(p++)         = '\0';
                  *(Val + (n++)) = atof(buffer);
                  p              = buffer;
                  qBufChars      = 0;
                  ++ qValues;
                  if (n % qCoordsPrSet == 0) {
                    C1In = Val[0] + RefC1;
                    C2In = Val[1] + RefC2;
                    if (!DummyH9 || Val[2] != DummyH)
                      C3In = (bInputHeights) ? Val[2] + RefC3 : 30.0;
                      else {
                      C3In      = 30.0;
                      DummyHout = 1;
                    }

                    if (bMinMaxOk && (C1In<H5C1
                        || H4C1<C1In || C2In<H5C2 || H4C2<C2In)) {
                      (void) strcpy(MsgStr, "Min/Max error\n");
                      ++ qFrameError;
                    }

                    if (bSwopInputCoo) {
                      tmp  = C1In;
                      C1In = C2In;
                      C2In = tmp;
                    }

                    res = gd_trans(g_lab_main, g_lab_slave,
                      C1In, C2In, C3In, &C1Out, &C2Out, &C3Out,
                      &ght, 0, &geoid_table, "", NULL);

                    if (res!=0) {
                      if (res == TRF_ILLEG_) {
                        (void) strcpy(MsgStr,
                   "\nIllegal Transformation\nTransformation stopped");
                        break;
                      }
                      ++ qTransError;
                    } else {
                      if (bSwopOutputCoo) {
                        tmp   = C1Out;
                        C1Out = C2Out;
                        C2Out = tmp;
                      }
                      if (bAfterParams) (void) fprintf(fh_out, "\n");
                      bAfterParams = 0;
                      if (bInputHeights) {
                        if (DummyHout) {
                          C3Out     = DummyH;
                          DummyHout = 0;
                        }
                        (void) fprintf(fh_out, " %.*f %.*f %.*f",
                                Dec, C1Out, Dec, C2Out, Dec, C3Out);
                      } else
                        (void) fprintf(fh_out, "% .*f% .*f",
                                        Dec, C1Out, Dec, C2Out);
                      (void) fprintf(fh_out, "\n");
                    }
                  }
                }
              }
              if (n >= qCoordsPrSet) n = 0;
              p               = buffer;
              *p              = '\0';
              bDigitsRecorded = 0;
              bSignRecorded   = 0;
              bPktRecorded    = 0;
              if (c == (char) '%') GoOn = 0;
              break;

            default :
              cError = 1;
            }
          } /* end while */
          if (cError) {
            qSyntaxError++;
          }
          break;

        case CMD_STOP :
          (void) fprintf(fh_out, "%c%-5s\n",'%', CmdTxt);
          DSFLStop = 1;
          break;
        case CMD_DEFAULT :
        default          :
          (void) fprintf(fh_out, "%c%-5s%c", '%', CmdTxt, CmdTerm);
          c = (char) getc(fh_in);
          while (!feof(fh_in) && c != '%') {
            (void) fputc(c, fh_out);
            c = (char) getc(fh_in);
          }
          break;
      }  /* end switch */
      if (DSFLcommand<=CMD_STOP) qTransCommands++;

    } /* end if cmdlng>0 */


  } while (!feof(fh_in) && !DSFLStop);

  (void) fprintf(fh_out,"\n\n");
  (void) fclose(fh_out);
  (void) fclose(fh_in);
  (void) geoid_c(&geoid_table, 0, NULL);
  if (res == TRF_ILLEG_) return(res);

  if (qTransError>0 || qSyntaxError>0) {
    (void) strcat(MsgStr, "Errors detected:\n");
    if (qSyntaxError>0) {
      (void) sprintf(buffer, "Syntax Errors : %ld", qSyntaxError);
      (void) strcat(MsgStr, buffer);
    }
    if (qFrameError>0) {
      (void) sprintf(buffer, "Frame Errors : %ld", qFrameError);
      (void) strcat(MsgStr, buffer);
    }
    if (qTransError>0) {
      (void) sprintf(buffer, "Transf Errors : %ld", qTransError);
      (void) strcat(MsgStr, buffer);
    }
    return(-68);
  }

  return(0);

}

