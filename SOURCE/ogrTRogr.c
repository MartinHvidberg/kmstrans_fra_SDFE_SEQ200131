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
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <stdarg.h>
#include "geo_constants.h"
#include "geo_lab.h"
#include "trlib_intern.h"
#include "get_mlb.h"
#include "cpl_error.h"
#include "ogrTRogr.h"
#include "Report.h"
#define MAX_LAYERS (1000)

#ifdef DLL_EXPORT
#undef DLL_EXPORT
#ifdef _WIN32
#define DLL_EXPORT __declspec( dllexport )
#else
#define DLL_EXPORT
#endif
#else
#define DLL_EXPORT
#endif

void CPL_STDCALL TR_OGR_ErrorHandler(CPLErr err, int err_no, const char *msg){
	Report( (int) err, err_no, VERB_HIGH, msg);
}

DLL_EXPORT void RedirectOGRErrors(){
	CPLSetErrorHandler((CPLErrorHandler) TR_OGR_ErrorHandler);
}





DLL_EXPORT void GetOGRDrivers(char *text){
	int iDriver,ndrivers;
	OGRSFDriverH poDriver;
	*text='\0';
	OGRRegisterAll();
	ndrivers=OGRGetDriverCount();
	for(iDriver = 0; iDriver < ndrivers; iDriver++ )
	{
	poDriver=OGRGetDriver (iDriver);
	if( OGR_Dr_TestCapability( poDriver,ODrCCreateDataSource ) ){
		strcat(text,OGR_Dr_GetName (poDriver));
		strcat(text,"\n");
		}
	}
	return;
}

int FlattenMLB(char *mlb_in, char *mlb_flat){
	char mlb1[128], mlb2[128], *h_datum;
	short sepch,region;
	get_mlb(mlb_in,&region,mlb1,&sepch,mlb2,&h_datum);
	strcpy(mlb_flat,mlb1);
	strcat(mlb_flat,"_");
	strcat(mlb_flat,mlb2);
	return TR_OK;
}

OGRSpatialReferenceH TranslateMiniLabel(char *mlb){
     /*try to translate minilabel to osr spatial reference*/
     char wkt[1024];
     OGRSpatialReferenceH srs_out;
     int err=TR_GetEsriText(mlb,wkt);
     if (err!=TR_OK)
	     return NULL;
     srs_out=OSRNewSpatialReference(wkt);
     return srs_out;
}

int TranslateSrs( OGRSpatialReferenceH srs, char *mlb){
	 char *p;
	 char buf[128];
	 int ok=TR_ERROR;
	 OGRErr err;
	 if (srs==NULL)
		 return TR_LABEL_ERROR;
	p=(char*) OSRGetAuthorityName(srs,NULL);
	 if (p && !strcmp(p,"EPSG")){
		 
		 p=(char*) OSRGetAuthorityCode(srs,NULL);
		 if (p!=NULL){
			sprintf(buf,"EPSG:%s",p);
			ok=TR_ImportLabel(buf,mlb);
			if (ok==TR_OK){
				/*Report(REP_INFO,0,VERB_LOW,"EPSG");*/
				return TR_OK;
			}
		}
	 }
	 err=OSRExportToProj4(srs,&p);
	 if (err==OGRERR_NONE){
		 Report(REP_INFO,0,VERB_LOW,p);
		 ok=TR_ImportLabel(p,mlb);
		 if (ok==TR_OK){
			 /*Report(REP_INFO,0,VERB_LOW,"Proj4");*/
			 return TR_OK;
		 }
	 }
	 OSRMorphToESRI(srs);
	 err=OSRExportToWkt(srs,&p);
	 if (err==OGRERR_NONE){
		 ok=TR_ImportLabel(p,mlb);
		 if (ok==TR_OK){
			 /*Report(REP_INFO,0,VERB_LOW,"WKT");*/
			 return TR_OK;
		 }
	 }
	 return TR_LABEL_ERROR;
 }
	
 DLL_EXPORT OGRLayerH GetLayer(OGRDataSourceH hDSin, int layer_num){
	 OGRLayerH hLayer=NULL;
	 if (layer_num<0)
		 layer_num=0;
	hLayer=OGR_DS_GetLayer( hDSin,layer_num);
	if (hLayer!=NULL)
		OGR_L_ResetReading(hLayer);
	return hLayer;
}


 DLL_EXPORT const char *GetLayerName(OGRLayerH hLayer){
	return OGR_L_GetName(hLayer);
}

 DLL_EXPORT int GetLayerCount(OGRDataSourceH hDSin){
	return OGR_DS_GetLayerCount(hDSin);
}



DLL_EXPORT OGRDataSourceH Open(char *inname){
	 OGRDataSourceH hDSin;
	 OGRRegisterAll();
	 hDSin = OGROpen(inname, FALSE, NULL );
	 return hDSin;
 }
	 
DLL_EXPORT void GetCoords(OGRGeometryH hGeom,double *x_out, double *y_out, int np){
	int i;
	double x,y,z;
	for (i=0;i<np;i++){
		OGR_G_GetPoint(hGeom,i,&x,&y,&z);
		x_out[i]=x;
		y_out[i]=y;
	}
	return;
}
		
		
	

 DLL_EXPORT OGRGeometryH GetNextGeometry(OGRLayerH hLayer, int *point_count){
	OGRGeometryH hGeometry;
	OGRFeatureH hFeature;
	hFeature = OGR_L_GetNextFeature(hLayer);
	if (hFeature==NULL)
		return NULL;
	hGeometry = OGR_G_Clone(OGR_F_GetGeometryRef(hFeature));
	OGR_F_Destroy( hFeature );
	*point_count=OGR_G_GetPointCount(hGeometry);
	return hGeometry;
}

DLL_EXPORT void Close(OGRDataSourceH hDSin){
	OGR_DS_Destroy( hDSin );
}
	
	

	

DLL_EXPORT int TransformOGR(char *inname, char *outname, TR *trf, char *drv_out, char **layer_names, int set_output_projection){
	OGRSpatialReferenceH srs_out=NULL;
	OGRDataSourceH hDSin,hDSout;
	OGRSFDriverH hDriver;
	struct stat buf;
	OGRErr err;
	int tr_err;
	OGRRegisterAll();
	InitialiseReport();
	if (trf==NULL || trf->proj_out==NULL){
		Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"Output projection not set!");
		return TR_LABEL_ERROR;
	}
	/* Create output driver */
	hDriver = OGRGetDriverByName( drv_out);
	if( hDriver == NULL )
       {
	       return TR_ALLOCATION_ERROR;
	}
	 /*open input file */
	hDSin = OGROpen(inname, FALSE, NULL );
	if( hDSin == NULL ){
		return TR_ALLOCATION_ERROR;
	}
	/* create output ds - fixup logic here for things like databases */
	if (!stat(outname, &buf))
		{
			/*err=OGR_Dr_DeleteDataSource(hDriver,outname);*/
			hDSout=OGR_Dr_Open(hDriver,outname,1);
		}
	else
		hDSout = OGR_Dr_CreateDataSource( hDriver, outname, NULL);
	
	if( hDSout == NULL )
	{
		OGR_DS_Destroy( hDSin );
		if (srs_out!=NULL)
			OSRRelease(srs_out);
		return TR_ALLOCATION_ERROR;
	}
	
	if (set_output_projection){
		
		srs_out=TranslateMiniLabel(GET_MLB(trf->proj_out));
		if (srs_out==NULL){
			char mlb_flat[512];
			Report(REP_WARNING,TR_LABEL_ERROR,VERB_LOW,"Unable to translate %s to osr spatial reference",GET_MLB(trf->proj_out));
			tr_err=FlattenMLB(GET_MLB(trf->proj_out),mlb_flat);
			srs_out=TranslateMiniLabel(mlb_flat);
			if (srs_out!=NULL)
				Report(REP_INFO,0,VERB_LOW,"Succeded in translating 2d-part of %s.",GET_MLB(trf->proj_out));
		}
		
		
		if (srs_out!=NULL){
			char *proj4_text; 
			err=OSRExportToProj4(srs_out,&proj4_text);
			Report(REP_INFO,0,VERB_LOW,"Translating output projection to: %s",proj4_text);
		}
		if (srs_out!=NULL && (!strcmp(drv_out,"FileGDB") || !strcmp(drv_out,"ESRI Shapefile")))
			OSRMorphToESRI(srs_out);
	}
	if (srs_out==NULL){
		Report(REP_WARNING,0,VERB_LOW,"Spatial reference NOT set for output file!");
	}
	tr_err=TransformOGRDatasource(trf,hDSin,hDSout,srs_out,hDriver,layer_names);
	OGR_DS_Destroy( hDSin );
	OGR_DS_Destroy( hDSout);
	if (srs_out!=NULL)
		OSRRelease(srs_out);
	LogGeoids();
	TerminateReport();
	return tr_err;
}

int TransformGeometry(TR *trf, OGRGeometryH hGeometry, int is_geo_in, int is_geo_out, int *n_ok, int *n_bad){
	double x,y,z,xo,yo,zo;
	int i,np,tr_err,ERR=TR_OK;
	char geoid_name[64];
	OGRErr err;
	const double d2r=D2R;
	const double r2d=R2D;
	int c_dim=OGR_G_GetCoordinateDimension(hGeometry);
	int g_dim=OGR_G_GetDimension(hGeometry);
	int ngeom=OGR_G_GetGeometryCount(hGeometry);
	int is_poly=(g_dim>1 && ngeom>0);
	OGRGeometryH hGeometry2;
	while (--ngeom>=0 || (!is_poly)){
		if (is_poly)
			hGeometry2=OGR_G_GetGeometryRef(hGeometry,ngeom);
		else
			hGeometry2=hGeometry;
	np=OGR_G_GetPointCount(hGeometry2);
	#ifdef DEBUG
	Report(REP_DEBUG,0,VERB_HIGH,"ngeom: %d, cdim: %d, gdim: %d, np: %d",ngeom,c_dim,g_dim,np);
	#endif
	for (i=0;i<np;i++){
		OGR_G_GetPoint(hGeometry2,i,&x,&y,&z);
		if (is_geo_in){
			x*=d2r;
			y*=d2r;
		}
		tr_err=TR_TransformPoint(trf,x,y,z,&xo,&yo,&zo);
		if (tr_err!=TR_OK){
			ERR=tr_err;
			(*n_bad)++;
			
		}
		else{
			(*n_ok)++;
		}
		if (HAS_HEIGHTS(trf->proj_in) ||  HAS_HEIGHTS(trf->proj_out)){
			TR_GetGeoidName(trf,geoid_name);
			AppendGeoid(geoid_name);
		}
		if (is_geo_out){
			yo*=r2d;
			xo*=r2d;
		}
		OGR_G_SetPoint(hGeometry2,i,xo,yo,zo);
		#ifdef DEBUG
		Report(REP_DEBUG,0,VERB_HIGH,"%g %g %g -> %g %g %g", x,y,z,xo,yo,zo);
		#endif
		}
	if (!is_poly)
		break;
	}
       return ERR;
}

 

/*Main workhorse which loops over input layers*/

int TransformOGRDatasource(
    TR *trf, 
    OGRDataSourceH 
    hDSin, 
    OGRDataSourceH hDSout, 
    OGRSpatialReferenceH srs_out,
    OGRSFDriverH hDriver,
    char **layer_names)
    {
	
    OGRLayerH hLayer=NULL,hLayer_out;
    OGRFeatureH hFeature,hFeature_out;
    OGRErr err=OGRERR_NONE;
    char mlb_in[128];
    int is_geo_in=0, is_geo_out=0,look_for_srs;
    int nlayers=0,layer_num,field_num,ngeom,feat_num=0,is_multi,tr_err,ERR=TR_OK,ntrans_ok=0,ntrans_bad=0;
    is_geo_out=(IS_GEOGRAPHIC(trf->proj_out));
    look_for_srs=(trf->proj_in==NULL);
    if (!look_for_srs)
	    is_geo_in=(IS_GEOGRAPHIC(trf->proj_in));
   
    nlayers=OGR_DS_GetLayerCount(hDSin);
    Report(REP_INFO,0,VERB_LOW,"#Layers: %d",nlayers);
    if (layer_names!=NULL){
		nlayers=MAX_LAYERS; /*quick fix - max layers...*/
    }
    for (layer_num=0;layer_num<nlayers; layer_num++)
    {		
		int layer_has_geometry=1;
		int field_count=0;
	        OGRFeatureDefnH hFDefn;
		if (layer_names==NULL){ /*loop over all layers*/
			hLayer=OGR_DS_GetLayer( hDSin,layer_num);
		}
		else{/*loop over layer names only*/
			if (layer_names[layer_num]!=NULL)
				hLayer=OGR_DS_GetLayerByName(hDSin,layer_names[layer_num]);
			else
				break;
		} 
		if (hLayer==NULL)
			break;
		OGR_L_ResetReading(hLayer);
		Report(REP_INFO,0,VERB_LOW,"Layer: %s", OGR_L_GetName(hLayer));
		hLayer_out=OGR_DS_CreateLayer(hDSout,OGR_L_GetName(hLayer),srs_out,OGR_L_GetGeomType(hLayer),NULL);
		if (hLayer_out==NULL){
			Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Could not CREATE layer in output datasource!");
			continue;
		}
		hFDefn=OGR_L_GetLayerDefn(hLayer);
		if (hFDefn==NULL)
		{
			Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Could not fetch layer definition!");
			continue;
		}
		layer_has_geometry=(OGR_FD_GetGeomType(hFDefn)!=wkbNone);
		field_count=OGR_FD_GetFieldCount(hFDefn);
		if (layer_has_geometry && look_for_srs){
			int ok=TranslateSrs(OGR_L_GetSpatialRef(hLayer),mlb_in);
			if (ok==TR_OK)
				Report(REP_INFO,0,VERB_LOW,"Translating input srs to mlb: %s",mlb_in);
			if (ok==TR_OK){
				ok=TR_Insert(trf,mlb_in,0);
				if (ok!=TR_OK){
					Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"Failed to translate input srs - skipping layer.");
					continue;
				}
				is_geo_in=(IS_GEOGRAPHIC(trf->proj_in));
			}
				
		}
		#ifdef DEBUG
		Report(REP_DEBUG,0,VERB_HIGH,"Field count: %d",field_count);
		#endif
		for (field_num=0; field_num<field_count; field_num++)
			err=OGR_L_CreateField(hLayer_out,OGR_FD_GetFieldDefn(hFDefn,field_num),TRUE);
		while( (hFeature = OGR_L_GetNextFeature(hLayer)) != NULL )
		{
			OGRGeometryH hGeometry=NULL,hGeometry2=NULL;
			feat_num++;
			hFeature_out=OGR_F_Clone(hFeature);
			
			if (layer_has_geometry)
				hGeometry = OGR_G_Clone(OGR_F_GetGeometryRef(hFeature_out));
			if( hGeometry != NULL)
			{
				OGRwkbGeometryType geom_type;
				ngeom=OGR_G_GetGeometryCount(hGeometry);
				geom_type=wkbFlatten(OGR_G_GetGeometryType(hGeometry));
				is_multi=(geom_type== wkbGeometryCollection || geom_type==wkbMultiPoint || geom_type== wkbMultiLineString || geom_type== wkbMultiPolygon);
				#ifdef DEBUG
				Report(REP_DEBUG,0,VERB_HIGH,"Feature: %d Ngeom: %d, is_multi: %d",feat_num,ngeom,is_multi);
				#endif
				while ((--ngeom>=0)||(!is_multi))
				{
					if (is_multi)
						hGeometry2=OGR_G_GetGeometryRef(hGeometry,ngeom);
					else 
						hGeometry2=hGeometry;
						
				
				tr_err=TransformGeometry(trf,hGeometry2,is_geo_in,is_geo_out, &ntrans_ok, &ntrans_bad);
				if (tr_err!=TR_OK){
					Report(REP_ERROR,tr_err,VERB_HIGH,"Error: %d, transforming geometry of feature: %d",TR_GetLastError(),feat_num);
					ERR=err;
				}
				if (!is_multi)
					break;
				}
				#ifdef DEBUG
				Report(REP_DEBUG,0,VERB_HIGH,"Setting geometry and creating feature, tr_err: %d",ERR);
				#endif
				OGR_F_SetGeometryDirectly(hFeature_out,hGeometry);
				
			} /*end if geom!=NULL*/
			else if (layer_has_geometry){
				Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_HIGH,"Unable to get geometry! Feature: %d",feat_num);
			}
			err=OGR_L_CreateFeature(hLayer_out,hFeature_out);
			if (err!=OGRERR_NONE){
				Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_HIGH,"Unable to create feature! Feature: %d",feat_num);
			}
			OGR_F_Destroy( hFeature ); //only if not null?
			OGR_F_Destroy(hFeature_out);
	    
		} /*end feature loop */
    } /* end layer loop */

Report(REP_INFO,0,VERB_LOW,"%-23s: %d","#Transformations OK",ntrans_ok);
if (ntrans_bad>0)
	Report(REP_INFO,0,VERB_LOW,"%-23s: %d","#Transformation errors",ntrans_bad);
return ERR;
}