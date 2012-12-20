#include "ogr_api.h"
#include "ogr_srs_api.h"
#include "trlib_api.h"

int TransformGeometry(TR *trf, OGRGeometryH hGeometry, int is_geo_in, int is_geo_out, int *n_ok, int *n_bad);
int TransformOGRDatasource(TR *trf, OGRDataSourceH hDSin, OGRDataSourceH hDSout, OGRSpatialReferenceH srs_out,OGRSFDriverH hDriver,char **layer_names);
int TransformOGR(char *inname,  char *outname, TR *trf, char *drv_out, char **layer_names, int set_projection);
OGRSpatialReferenceH TranslateMiniLabel(char *mlb);
int TranslateSrs( OGRSpatialReferenceH srs, char *mlb);
int FlattenMLB(char *mlb_in, char *mlb_flat);
void GetOGRDrivers(char *text);
OGRLayerH GetLayer(OGRDataSourceH hDSin, int layer_num);
OGRGeometryH GetNextGeometry(OGRLayerH hLayer, int *point_count);
void Close(OGRDataSourceH hDSin);
OGRDataSourceH Open(char *inname);
void GetCoords(OGRGeometryH hGeom,double *x_out, double *y_out, int np);
void RedirectOGRErrors();





