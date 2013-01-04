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
#include <stdlib.h>
#include <unistd.h> 
#include <sys/stat.h>
#include <time.h>
#include "gdal.h"
#include "geo_lab.h"
#include "ogrTRogr.h"
#include "TransformText.h"
#include "TransformDSFL.h"
#include "trlib_api.h"
#include "Report.h"
#include "lord.h"
#define PROG_NAME ("trogr")
#define VERSION  ("1.01 - 2013-01-05")
void Usage(int help);
void ListFormats(void);
void PrintVersion(void);
static char *INPUT_DRIVERS[]={"DSFL","TEXT","KMS","OGR",0};

void Usage(int help){
	printf("To run:\n");
	printf("%s ..options.. <mlb_out> <fname_out> <fname_in> <layer_name1> <layer_name2> ...\n",PROG_NAME);
	printf("Layer names are optional - if not given the program will loop over all layers.\n");
	printf("Available options:\n");
	printf("-p <mlb_in> If not included input metadata should be extracted from input file.\n");
	if (help)
		printf("For the DSFL driver the -p switch can *not* be used.\n");
	printf("-d <input_driver> Optional. Will default to 'OGR'. Output driver will be the same as the input driver.\n");
	printf("-f <output_ogr_driver> Optional. defaults to 'ESRI Shapefile'.\n");
	printf("-l <log_file> Specify log file.\n");
	if (help)
		printf("Will append output if the file already exists.\n");
	printf("-n Do NOT try to set the projection metadata on the output datasource/layer.\n");
	if (help)
		printf("Useful for some drivers which fail to create layers unless projection metadata satisfy striqt requirements.\n");
	printf("-v Be verbose - i.e. enable info and debug messages.\n");
	printf("\nOptions specific for the 'TEXT' driver:\n");
	printf("-s <sep_char> is used to specify separation char for 'TEXT' format. **Defaults to whitespace.**\n");
	printf("-x <int> Specify x-column for 'TEXT' driver (default: first column).\n");
	printf("-y <int> Specify y-column for 'TEXT' driver (default: second column).\n");
	printf("-z <int> Specify z-column for 'TEXT' driver (default: third column).\n");
	printf("Use %s --formats to list available drivers.\n",PROG_NAME);
	printf("Use %s --version to print version info.\n",PROG_NAME);
	if (!help)
		printf("Use %s --help to print extra info.\n",PROG_NAME);
	else{
		printf("For the 'TEXT' driver special filenames 'stdin' and 'stdout' are available.\n");
		printf("For OGR-datasources:\nIf destination datasource <fname_out> exists, the datasource will be opened for update -\n");
		printf("and the program will try to CREATE new layers corresponding to layers in input.\n");
	}
	return;
}


void ListFormats(void){
	char stars[]="********************************************";
	char *drv_in;
	int i=0;
	fprintf(stdout,"%s\nInput drivers:\n%s\n",stars,stars);
	while ((drv_in=INPUT_DRIVERS[i++]))
		fprintf(stdout,"%s\n",drv_in);
	char formats[16438];
	fprintf(stdout,"%s\nOutput drivers provided by OGR (option -f <driver>):\n%s\n",stars,stars);
	GetOGRDrivers(formats);
	fprintf(stdout,formats);
	return;
}

void PrintVersion(void){
	const char *gdal_version;
	char trlib_version[512];
	TR_GetVersion(trlib_version,512);
	gdal_version=GDALVersionInfo("RELEASE_NAME");
	fprintf(stdout,"%s %s\n",PROG_NAME,VERSION);
	fprintf(stdout,"TrLib-version: %s\n",trlib_version);
	fprintf(stdout,"GDAL/OGR-version: %s\n",gdal_version);
	return;
}

int message_handler(int err_class, int err_code, const char *msg){
	if (err_class>=REP_ERROR){
		fputs(msg,stderr);
		fflush(stderr);
	}
	else{
		fputs(msg,stdout);
		fflush(stdout);
	}
	return 0;
}

int main(int argc, char *argv[])
{  int c;
    int digit_optind = 0;
    char *inname=NULL,*outname=NULL,*mlb_in=NULL,*mlb_out=NULL,*drv_in=NULL, *drv_out=NULL,*sep_char=NULL, **layer_names=NULL;
    char *log_name=NULL;
    int set_output_projection=1, n_layers=0,col_x=0, col_y=1, col_z=-1,err=0,is_init=0,be_verbose=0;
    time_t rawtime;
    struct tm * timeinfo;
    TR *trf=NULL;
    FILE *fp_log=NULL;
    /*set reporting callback fct.*/
    SetCallBack(message_handler);
    RedirectOGRErrors();
    if (argc>1) {
	    if (!strcmp(argv[1],"--formats")){
		    ListFormats();
		    exit(0);
	    }
	    if (!strcmp(argv[1],"--version")){
		    PrintVersion();
		    exit(0);
	    }
	    if (!strcmp(argv[1],"--help")){
		    Usage(1);
		    exit(0);
	    }
    }
    /*parse options*/
    while ( (c = getopt(argc, argv, "p:d:f:s:x:y:z:l:nv")) != -1) {
        int this_option_optind = optind ? optind : 1;
        switch (c) {
       
		case 'p':
			mlb_in=optarg;
			break;
		case 'f':
			drv_out = optarg;
			break;
		case 'd':
			drv_in=optarg;
			break;
		case 's':
			sep_char=optarg;
			break;
		case 'n':
			set_output_projection=0;
			break;
		case 'x':
			col_x=atoi(optarg)-1; /*zero based index used - user should input 1 based indexing...*/
			break;
		case 'y':
			col_y=atoi(optarg)-1;
			break;
		case 'z':
			col_z=atoi(optarg)-1;
			break;
		case 'l':
			log_name=optarg;
			break;
		case 'v':
			be_verbose=1;
			break;
		case '?':
			break;
		default:
			printf ("?? getopt returned character code 0%o ??\n", c);
        }
    }
    /*if not enough args*/
   if (argc<optind+3){
        Usage(0);
	exit(0);
    }
    
    
    mlb_out=argv[optind];
    inname=argv[optind+2];
    outname=argv[optind+1];
    /* check if layers specified*/
    if (argc>optind+3){
	    int i;
	    n_layers=argc-optind-3;
	    layer_names=malloc(sizeof( char*)*(n_layers+1));
	    for (i=0; i<n_layers; i++){
		    layer_names[i]=argv[optind+3+i];
	    }
	    layer_names[n_layers]=NULL; /*terminator*/
    }
    if (!strcmp(inname,outname)){
	    fprintf(stderr,"Outname and inname must differ (for now!)\n");
	    exit(TR_ALLOCATION_ERROR);
    }
    if (!drv_in)
	    drv_in="OGR"; /*default driver */
    else{
	    char *pt=drv_in;
	    int i=0;
	    /*convert driver to upper case*/
	    for (;*pt;pt++) *pt=toupper(*pt);
	    while (INPUT_DRIVERS[i] && strcmp(INPUT_DRIVERS[i],drv_in))
		    i++;
	    if (!INPUT_DRIVERS[i]){
		    fprintf(stderr,"Unavailable input driver: %s\nUse option --formats to list available drivers.\n",drv_in);
		    exit(TR_ALLOCATION_ERROR);
	    }
    }
    if (strcmp(drv_in,"OGR"))
	    drv_out=drv_in;
    
    if (!drv_out)
	    drv_out="ESRI Shapefile";
    
    is_init=TR_InitLibrary("");
    if (is_init!=TR_OK){
	    fprintf(stderr,"Failed to initialise KMS-transformation library! Did you set TR_TABDIR to a proper geoid folder?\n");
	    exit(TR_ALLOCATION_ERROR);
    }
    TR_AllowUnsafeTransformations();
    trf=TR_Open(mlb_in,mlb_out,"");
    if (!trf){
	    fprintf(stderr,"Failed to open transformation/projection.\n");
	    exit(TR_LABEL_ERROR);
    }
   
    /*init logging*/
    if (log_name!=NULL){
	    fp_log=fopen(log_name,"a");
	    if (fp_log==NULL)
		    fprintf(stderr,"Failed to open log file %s - will not use log.\n",log_name);
    }
    if (fp_log!=NULL){
	    SetLogFile(fp_log);
	    set_lord_outputs(fp_log,fp_log,fp_log,fp_log,fp_log);
	    
    }
    else
	    set_lord_outputs(stdout,stdout,stderr,stderr,stderr);
    /*TODO: control this via options*/
    set_lord_modes(be_verbose,be_verbose,1,1,1);
    set_lord_verbosity_levels(3,3,3,3,3);
    time ( &rawtime );
    timeinfo = localtime ( &rawtime );
    Report(REP_INFO,0,VERB_LOW,"Running %s at %s", PROG_NAME,asctime (timeinfo) );
    Report(REP_INFO,0,VERB_LOW,"Using input driver %s and output driver %s.",drv_in,drv_out);
    Report(REP_INFO,0,VERB_LOW,"%-25s: %s","Input datasource",inname);
    Report(REP_INFO,0,VERB_LOW,"%-25s: %s","Output datasource",outname);
    if (fp_log!=NULL)
	    Report(REP_INFO,0,VERB_LOW,"%-25s: %s","Log file",log_name);
    if (mlb_in)
	    Report(REP_INFO,0,VERB_LOW,"Projection: %s->%s",mlb_in,mlb_out);
    else
	    Report(REP_INFO,0,VERB_LOW,"Using output projection: %s. Looking for projection metadata in input datasource.",mlb_out);
    if (n_layers>0)
	    Report(REP_INFO,0,VERB_LOW,"%d layer(s) specified.",n_layers);
    else
	    Report(REP_INFO,0,VERB_LOW,"Reading all layers in input datasource.");
    {/*test if output exists*/
    struct stat buf;
    int f_err=stat(outname, &buf);
    if (!f_err && strcmp(outname,"stdout"))
	    Report(REP_INFO,0,VERB_LOW,"%s exists and will be updated!",outname);
    }
    /* disptach according to driver */
    
    if (!strcmp(drv_in,"DSFL") || !strcmp(drv_in,"dsfl")){ /*begin DSFL */
	     if (mlb_in)
		     Report(REP_INFO,0,VERB_LOW,"Input MiniLabel should not be set for the DSFL-driver."); 
	    err=TransformDSFL(inname,outname,trf);
    }
    /* end DSFL */
    
   else if (!strcmp(drv_in,"KMS")){ /*begin simple text */
	   err=TransformText(inname,outname,trf,NULL,-1,-1,-1,1,1);
    } /*end KMS*/
    else if (!strcmp(drv_in,"TEXT")){ /*begin simple text */
	    if (sep_char)
	        Report(REP_INFO,0,VERB_LOW,"Using column separator(s): %s",sep_char);
	    else
		Report(REP_INFO,0,VERB_LOW,"Using (all) whitespace as default column separator.");
	    err=TransformText(inname,outname,trf,sep_char,col_x,col_y,col_z,set_output_projection,0);
    } /* end simple text */
    else if (!strcmp(drv_in,"OGR")){ /*begin OGR */
	   err=TransformOGR(inname, outname, trf, drv_out,layer_names, set_output_projection);
    }/* end OGR */	     
    
    else {
	    Report(REP_INFO,0,VERB_LOW,"Input driver %s not available!",drv_in);
	    exit(TR_ALLOCATION_ERROR);
    } 
   
    if (err!=TR_OK)
	    Report(REP_WARNING,err,VERB_LOW,"Abnormal return code from transformation: %d",err);
    
    if (GetErrors()>0){
	    Report(REP_WARNING,0,VERB_LOW,"Errors occured...");
	    if (fp_log!=NULL)
		    fprintf(stdout,"See log file for details..\n");
    }
    
    TR_Close(trf);
     /* Clean Up */
    TR_TerminateLibrary();
    /*if (fp_log!=NULL)
	fclose(fp_log);*/
    if (layer_names!=NULL)
		free(layer_names);
    return err;
   }