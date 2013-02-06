/* Copyright (c) 2012, National Survey and Cadastre, Denmark
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
#include "ogr_api.h"
#include "ogr_srs_api.h"
#include "trlib_api.h"

int TransformGeometry(TR *trf, OGRGeometryH hGeometry, int is_geo_in, int is_geo_out, int *n_ok, int *n_bad);
int TransformOGRDatasource(TR *trf, OGRDataSourceH hDSin, OGRDataSourceH hDSout, OGRSpatialReferenceH srs_out, char **layer_names, char **lcos, char **extra_lcos);
int TransformOGR(char *inname,  char *outname, TR *trf, char *drv_out, char **layer_names, int set_projection, char **dscos, char **lcos);
OGRSpatialReferenceH TranslateMiniLabel(char *mlb);
int TranslateSrs( OGRSpatialReferenceH srs, char *mlb);
int FlattenMLB(char *mlb_in, char *mlb_flat);
const char *GetOGRDrivers(int reset, int is_output);
OGRLayerH GetLayer(OGRDataSourceH hDSin, int layer_num);
OGRGeometryH GetNextGeometry(OGRLayerH hLayer, int *point_count);
const char *GetLayerName(OGRLayerH hLayer);
int GetLayerCount(OGRDataSourceH hDSin);
void Close(OGRDataSourceH hDSin);
OGRDataSourceH Open(char *inname);
void GetCoords(OGRGeometryH hGeom,double *x_out, double *y_out, int np);
void RedirectOGRErrors();
const char* GetGDALVersion();






