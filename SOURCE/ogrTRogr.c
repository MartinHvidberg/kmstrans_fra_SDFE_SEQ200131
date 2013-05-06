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
#include "gdal.h"
#include "geo_constants.h"
#include "geo_lab.h"
#include "trlib_intern.h"
#include "get_mlb.h"
#include "cpl_error.h"
#include "ogrTRogr.h"
#include "Report.h"
#define MAX_LAYERS (1000)
#ifndef S_ISDIR
# define S_ISDIR(ST_MODE) (((ST_MODE) & _S_IFMT) == _S_IFDIR)
#endif

static void ParseFileGDBLayerPath(OGRDataSourceH hDS, const char *layer_name, char *path);

void CPL_STDCALL TR_OGR_ErrorHandler(CPLErr err, int err_no, const char *msg){
	char buf[512]="gdal: ";
	strncat(buf,msg,504);
	Report( (int) err, err_no, VERB_HIGH, buf);
}

 void RedirectOGRErrors(){
	CPLSetErrorHandler((CPLErrorHandler) TR_OGR_ErrorHandler);
}



 const char* GetGDALVersion(){
	return GDALVersionInfo("RELEASE_NAME");
}



/*Call with reset=TRUE first - then call consequentially until NULL is returned*/
 const char *GetOGRDrivers(int reset, int is_output){
	static int current_driver=0;
	static int ndrivers=0;
	OGRSFDriverH poDriver;
	if (reset){
	    OGRRegisterAll();
	    ndrivers=OGRGetDriverCount();
	    current_driver=0;
	    return NULL;
	}
	while (current_driver<ndrivers)
	{
	    poDriver=OGRGetDriver (current_driver);
	    current_driver++;
	    if(is_output && !OGR_Dr_TestCapability( poDriver,ODrCCreateDataSource ) )
		    continue;
	    return OGR_Dr_GetName(poDriver);
	}
	return NULL;
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
     char buf[2048];
     OGRSpatialReferenceH srs_out=OSRNewSpatialReference(NULL);
     int err=TR_ERROR;
     OGRErr err2=OGRERR_NONE;
     /*Temporarliy ignore errors*/
     SetIgnoreMessages(1);
     err=TR_ExportLabel(mlb,buf,TR_FRMT_EPSG,2048);
     if (err==TR_OK){
	     char *tmp=strstr(buf,":");
	     int code;
	     err=TR_ERROR;
	     if ((tmp-buf)==4){
		     code=atoi(tmp+1);
		     Report(REP_DEBUG,0,VERB_LOW,"code: %d, tmp: %s", code,tmp);
		     err2=OSRImportFromEPSG(srs_out,code);
	             if (err2==OGRERR_NONE){
			     err=TR_OK;
			     //Report(REP_INFO,0,VERB_HIGH,"Succesful translation of minilabel via EPSG code: %d",code);
		     }
	     }
     }
     if (err!=TR_OK){
	     err=TR_ExportLabel(mlb,buf,TR_FRMT_PROJ4,2048);
	     if (err==TR_OK){
		     err=TR_ERROR;
		     err2=OSRImportFromProj4(srs_out,buf);
		      if (err2==OGRERR_NONE){
			     err=TR_OK;
			     //Report(REP_INFO,0,VERB_HIGH,"Succesful translation of minilabel via proj4-string: %s",buf);
		     }
	     }
     }
      if (err!=TR_OK){
	     err=TR_ExportLabel(mlb,buf,TR_FRMT_ESRI_WKT,2048);
	     if (err==TR_OK){
		     char *tmp[2]={buf,NULL};
		     err=TR_ERROR;
		     err2=OSRImportFromESRI(srs_out,tmp);
		      if (err2==OGRERR_NONE){
			     err=TR_OK;
			     //Report(REP_INFO,0,VERB_HIGH,"Succesful translation of minilabel via ESRI-wkt");
		     }
	     }
	    
     }
     SetIgnoreMessages(0);
     if (err!=TR_OK){     
	OSRRelease(srs_out);
	return NULL;
     }
     return srs_out;
}


int TranslateSrs( OGRSpatialReferenceH srs, char *mlb, int buf_len){
	 char *p;
	 char buf[128];
	 int ok=TR_ERROR;
	 OGRErr err;
	 if (srs==NULL)
		 return TR_LABEL_ERROR;
	 SetIgnoreMessages(1); /*temporarily ignore errors from trlib and gdal*/
	 p=(char*) OSRGetAuthorityName(srs,NULL);
	 if (p && !strcmp(p,"EPSG")){
		 
		 p=(char*) OSRGetAuthorityCode(srs,NULL);
		 if (p!=NULL){
			sprintf(buf,"EPSG:%s",p);
			ok=TR_ImportLabel(buf,mlb,buf_len);
			
		}
	 }
	 if (ok!=TR_OK){
		 err=OSRExportToProj4(srs,&p);
		 if (err==OGRERR_NONE){
			 Report(REP_INFO,0,VERB_LOW,p);
			 ok=TR_ImportLabel(p,mlb,buf_len);
		}
	}
	if (ok!=TR_OK){
		 OSRMorphToESRI(srs);
		 err=OSRExportToWkt(srs,&p);
		 if (err==OGRERR_NONE){
			 ok=TR_ImportLabel(p,mlb,buf_len);
		}
	}
	SetIgnoreMessages(0);
	return ok;
 }
	
  OGRLayerH GetLayer(OGRDataSourceH hDSin, int layer_num){
	 OGRLayerH hLayer=NULL;
	 if (layer_num<0)
		 layer_num=0;
	hLayer=OGR_DS_GetLayer( hDSin,layer_num);
	if (hLayer!=NULL)
		OGR_L_ResetReading(hLayer);
	return hLayer;
}


  const char *GetLayerName(OGRLayerH hLayer){
	return OGR_L_GetName(hLayer);
}

  int GetLayerCount(OGRDataSourceH hDSin){
	return OGR_DS_GetLayerCount(hDSin);
}



 OGRDataSourceH Open(char *inname){
	 OGRDataSourceH hDSin;
	 OGRRegisterAll();
	 hDSin = OGROpen(inname, FALSE, NULL );
	 return hDSin;
 }
	 
 void GetCoords(OGRGeometryH hGeom,double *x_out, double *y_out, int np){
	int i;
	double x,y,z;
	for (i=0;i<np;i++){
		OGR_G_GetPoint(hGeom,i,&x,&y,&z);
		x_out[i]=x;
		y_out[i]=y;
	}
	return;
}
		
		
	

  OGRGeometryH GetNextGeometry(OGRLayerH hLayer, int *point_count){
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

 void Close(OGRDataSourceH hDSin){
	OGR_DS_Destroy( hDSin );
}
	
	

static void ParseFileGDBLayerPath(OGRDataSourceH hDS,const char *layer_name, char *path){
	OGRFeatureH feat;
	OGRLayerH sqlLayer;
	const char *layer_def; 
	char *pos1,*pos2;
	int l=0,slashes_found=0;
	char sql_request[128]="GetLayerDefinition ";
	strcat(sql_request,layer_name);
	sqlLayer=OGR_DS_ExecuteSQL(hDS,sql_request,NULL,NULL);
	if (sqlLayer){
		OGR_L_ResetReading(sqlLayer);
		feat=OGR_L_GetNextFeature(sqlLayer);
		layer_def=OGR_F_GetFieldAsString(feat,0);
		pos1=strstr(layer_def,"<CatalogPath>");
		if (pos1){
			pos1+=14; /*do not include the first slash*/
			pos2=strstr(pos1,"</");
			if (pos2){
				l=(pos2-pos1);
				memcpy(path,pos1,l);
				pos1=path;
				while (pos1-path<l){
					slashes_found+=(*pos1=='\\' || *pos1=='/');
					if (slashes_found==1)
						break;
					pos1++;
				}
				if (slashes_found>0)
					*pos1='\0';
				else
					path[0]='\0';
				*pos1='\0'; /*mark as nothing found*/		
			}
		}
	OGR_DS_ReleaseResultSet(hDS,sqlLayer);
	}
}

 int TransformOGR(char *inname, char *outname, TR *trf, char *drv_out, char **layer_names, int set_output_projection, char **dscos, char **lcos){
	OGRSpatialReferenceH srs_out=NULL;
	OGRDataSourceH hDSin,hDSout;
	OGRSFDriverH hDriver_in, hDriver_out;
	int n_layers=0,is_fgdb_transf=0, i, is_update=0;
	OGRLayerH hLayer=NULL;
	char **extra_lcos=NULL;
	struct stat buf;
	OGRErr err;
	int tr_err;
	OGRRegisterAll();
	InitialiseReport();
	if (trf==NULL || trf->proj_out==NULL){
		Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"Output projection not set!");
		return TR_LABEL_ERROR;
	}
	
	 /*open input file */
	hDSin = OGROpen(inname, FALSE, & hDriver_in);
	if( hDSin == NULL ){
		return TR_ALLOCATION_ERROR;
	}
	Report(REP_INFO,0,VERB_LOW,"Opened input with driver: %s",OGR_Dr_GetName(hDriver_in));
	
	/* Create output driver */
	hDriver_out = OGRGetDriverByName( drv_out);
	if( hDriver_out == NULL )
       {
	       Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Driver %s not available!",drv_out);
	       return TR_ALLOCATION_ERROR;
	}
	
	/* create output ds - fixup logic here for things like databases - I guess a CreateDatasource should work also for a db layer??*/
	/* The logic is now: if output datasource exists- if is a directory update else delete/overwrite,*/ 
	if (!stat(outname, &buf)){
		if (S_ISDIR(buf.st_mode))
		{
			/*err=OGR_Dr_DeleteDataSource(hDriver,outname);*/
			is_update=1;
			hDSout=OGR_Dr_Open(hDriver_out,outname,TRUE);
		}
		else{
		      err= OGR_Dr_DeleteDataSource(hDriver_out, outname);
		      hDSout=OGR_Dr_CreateDataSource( hDriver_out, outname, dscos);
		      if (err!=OGRERR_NONE && hDSout==NULL)
			      Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Failed to overwrite output datasource!");
		}
		
	}
	else
		hDSout = OGR_Dr_CreateDataSource( hDriver_out, outname, dscos);
        
	if( hDSout == NULL )
	{
		OGR_DS_Destroy( hDSin );
		if (srs_out!=NULL)
			OSRRelease(srs_out);
		if (is_update)
			Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Failed to open output datasource!");
		else
			Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Failed to create output datasource!");
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
			Report(REP_INFO,0,VERB_LOW,"Translating output mini label to osr-srs.\nProj4 translation of osr-srs is: %s",proj4_text);
		}
		if (srs_out!=NULL && (!strcmp(drv_out,"FileGDB") || !strcmp(drv_out,"ESRI Shapefile")))
			OSRMorphToESRI(srs_out);
	}
	if (srs_out==NULL){
		Report(REP_WARNING,0,VERB_LOW,"Spatial reference NOT set for output file!");
	}
	/*special filegdb logic here*/
	is_fgdb_transf=(!strcmp(OGR_Dr_GetName(hDriver_in),"FileGDB") && !strcmp(OGR_Dr_GetName(hDriver_out),"FileGDB"));
	if (is_fgdb_transf){
		
		char *lco_here;
		char path[FILENAME_MAX]="";
		Report(REP_INFO,0,VERB_LOW,"FileGDB to FileGDB transformation - will try to preserve feature datasets.");
		if (layer_names!=NULL){
			char **layer_name=layer_names;
			while (*(layer_name++)) n_layers++;
		}
		else
			n_layers=OGR_DS_GetLayerCount(hDSin);
		extra_lcos=malloc(sizeof(char*)*n_layers);
		if (!extra_lcos)
			Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Failed to allocate space for layer creation options.");
		else{
			for(i=0;i<n_layers;i++){
				if (layer_names!=NULL)
					hLayer=OGR_DS_GetLayerByName(hDSin,layer_names[i]);
				else
					hLayer=OGR_DS_GetLayer(hDSin,i);
				if (!hLayer){
					Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Setting layer definition - failed to fetch layer!");
					continue;
				}
				/*TODO: test if malloc ok */
				lco_here=extra_lcos[i]=malloc(sizeof(char)*128);
				ParseFileGDBLayerPath(hDSin,OGR_L_GetName(hLayer),path);
				if (*path){
					sprintf(lco_here,"FEATURE_DATASET=%s",path);
				}
				else{
					free(lco_here);
					extra_lcos[i]=NULL;
				}
					
				
			}/*end loop over layers...*/
					
		}/*end malloc ok*/
	} /*end set extra lcos*/
		
	tr_err=TransformOGRDatasource(trf,hDSin,hDSout,srs_out,layer_names,lcos,extra_lcos);
	OGR_DS_Destroy( hDSin );
	OGR_DS_Destroy( hDSout);
	if (srs_out!=NULL)
		OSRRelease(srs_out);
	if (extra_lcos!=NULL){
		for(i=0;i<n_layers;i++){
			if (extra_lcos[i]!=NULL)
				free(extra_lcos[i]);
		}
		free(extra_lcos[i]);
	}
	LogGeoids();
	TerminateReport();
	return tr_err;
}

int TransformGeometry(TR *trf, OGRGeometryH hGeometry, int is_geo_in, int is_geo_out, int *n_ok, int *n_bad){
	double x,y,z,xo,yo,zo;
	int i,np,tr_err,ERR=TR_OK,log_geoids=0;
	char geoid_name[64];
	/*OGRErr err;*/
	const double d2r=D2R;
	const double r2d=R2D;
	int c_dim=OGR_G_GetCoordinateDimension(hGeometry);
	int g_dim=OGR_G_GetDimension(hGeometry);
	int ngeom=OGR_G_GetGeometryCount(hGeometry);
	int is_poly=(g_dim>1 && ngeom>0);
	OGRGeometryH hGeometry2;
	log_geoids=((HAS_HEIGHTS(trf->proj_in) ||  HAS_HEIGHTS(trf->proj_out)));
	log_geoids=log_geoids && ((GET_HDTM(trf->proj_in)!=GET_HDTM(trf->proj_out)) || (GET_DTM(trf->proj_in)!=GET_DTM(trf->proj_out))) ;
	while (--ngeom>=0 || (!is_poly)){
		if (is_poly)
			hGeometry2=OGR_G_GetGeometryRef(hGeometry,ngeom);
		else
			hGeometry2=hGeometry;
	np=OGR_G_GetPointCount(hGeometry2);
	#ifdef VERY_VERBOSE
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
		if (log_geoids){
			TR_GetGeoidName(trf,geoid_name);
			AppendGeoid(geoid_name);
		}
		if (is_geo_out){
			yo*=r2d;
			xo*=r2d;
		}
		
		if (c_dim<3)
			OGR_G_SetPoint_2D(hGeometry2,i,xo,yo);
		else
			OGR_G_SetPoint(hGeometry2,i,xo,yo,zo);
		#ifdef VERY_VERBOSE
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
    OGRDataSourceH hDSin, 
    OGRDataSourceH hDSout, 
    OGRSpatialReferenceH srs_out,
    char **layer_names,
    char **lcos, /*an array with an extra slot in the end....*/
    char **extra_lcos
)
    {
	
    OGRLayerH hLayer=NULL,hLayer_out;
    OGRFeatureH hFeature,hFeature_out;
    OGRErr err=OGRERR_NONE;
    char mlb_in[128];
    char *all_lcos[32]; /* MAX 32 layer creation options*/
    int is_geo_in=0, is_geo_out=0,look_for_srs,n_lcos=0;
    int nlayers=0,layer_num,field_num,ngeom,feat_num=0,is_multi,tr_err,ERR=TR_OK,ntrans_ok=0,ntrans_bad=0;
    is_geo_out=(IS_GEOGRAPHIC(trf->proj_out));
    look_for_srs=(trf->proj_in==NULL);
    if (!look_for_srs)
	    is_geo_in=(IS_GEOGRAPHIC(trf->proj_in));
    /*copy lcos...*/
    if (lcos!=NULL){
	    while(lcos[n_lcos]!=NULL && n_lcos<30){
		    all_lcos[n_lcos]=lcos[n_lcos];
		    n_lcos++;
	    }
    }
    nlayers=OGR_DS_GetLayerCount(hDSin);
    Report(REP_INFO,0,VERB_LOW,"#Layers in input datasource: %d",nlayers);
    if (layer_names!=NULL){
		nlayers=MAX_LAYERS; /*quick fix - max layers...*/
    }
    for (layer_num=0;layer_num<nlayers; layer_num++)
    {		
		int layer_has_geometry=1;
		int field_count=0;
	        char *lco=NULL;
	        OGRFeatureDefnH hFDefn;
		if (layer_names==NULL){ /*loop over all layers*/
			hLayer=OGR_DS_GetLayer( hDSin,layer_num);
		}
		else{/*loop over layer names only*/
			if (layer_names[layer_num]!=NULL){
				hLayer=OGR_DS_GetLayerByName(hDSin,layer_names[layer_num]);
				if (hLayer==NULL){
					Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Failed to fetch layer: %s",layer_names[layer_num]);
					continue;
				}
			}
			else
				break;
		} 
		if (hLayer==NULL)
			break;
		OGR_L_ResetReading(hLayer);
		Report(REP_INFO,0,VERB_LOW,"Layer: %s, geometry type: %d", OGR_L_GetName(hLayer),OGR_L_GetGeomType(hLayer));
		
		if (extra_lcos!=NULL && extra_lcos[layer_num]){
			/*insert the extra lco*/
			all_lcos[n_lcos]=extra_lcos[layer_num];
			all_lcos[n_lcos+1]=NULL;
			Report(REP_DEBUG,0,VERB_LOW,"Creation option: %s",extra_lcos[layer_num]);
		}
		else
			all_lcos[n_lcos]=NULL;
		
		hLayer_out=OGR_DS_CreateLayer(hDSout,OGR_L_GetName(hLayer),srs_out,OGR_L_GetGeomType(hLayer),all_lcos);
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
			int ok=TranslateSrs(OGR_L_GetSpatialRef(hLayer),mlb_in,128);
			if (ok==TR_OK){
				Report(REP_INFO,0,VERB_LOW,"Translating input srs to mlb: %s",mlb_in);
				ok=TR_Insert(trf,mlb_in,0);
				if (ok!=TR_OK){
					Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"Failed to insert mini label %s",mlb_in);
					continue;
				}
				is_geo_in=(IS_GEOGRAPHIC(trf->proj_in));
			}
			else{
				Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"Failed to translate input srs to mini label- skipping layer.");
				continue;
			}
				
		}
		#ifdef VERY_VERBOSE
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
				#ifdef VERY_VERBOSE
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
				#ifdef VERY_VERBOSE
				Report(REP_DEBUG,0,VERB_HIGH,"Setting geometry and creating feature, tr_err: %d",ERR);
				#endif
				OGR_F_SetGeometryDirectly(hFeature_out,hGeometry);
				//Report(REP_INFO,0,VERB_LOW,"Geom-type out: %d",OGR_G_GetGeometryType(hGeometry));
				
				
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

