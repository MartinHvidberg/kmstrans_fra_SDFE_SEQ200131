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
#include <sys/stat.h>
#include <ctype.h>
#include <time.h>

#include "geo_lab.h"
#include "ogrTRogr.h"
#include "TransformText.h"
#include "TransformDSFL.h"
#include "trlib_intern.h"
#include "trlib_api.h"
#include "Report.h"
#include "lord.h"
#include "my_get_opt.h"
#define PROG_NAME ("trogr")
#define VERSION  ("1.07 (" __DATE__ "," __TIME__ ")")
void Usage(int help);
void ListFormats(void);
void PrintVersion(void);
static void unescape(char*);
static int validate_geo_unit(char*);
static char *INPUT_DRIVERS[]={"DSFL","TEXT","KMS","OGR",0};

/* quick and dirty unescaper - can be hard to enter literal tabs,newlines etc in some shells*/
static void unescape(char *text){
	char *out=text;
	while(*text){
		if (*text=='\\'){ /* if a literal escape character */
			switch(*(text+1)){
				case 'r':
					*(out++)='\r';
					text+=2;
					break;
				case 'n':
					*(out++)='\n';
					text+=2;
					break;
				case 't':
					*(out++)='\t';
					text+=2;
					break;
				default:
					*(out++)=*(text++); /*simply copy*/
			}
		}
		else
			*(out++)=*(text++);
	}
	*out='\0';
}

int validate_geo_unit(char *unit){
	if (!strcmp(unit,"dg") || !strcmp(unit,"sx") || !strcmp(unit,"nt") || !strcmp(unit,"rad"))
		return 1;
	else
		return 0;
}
	

void Usage(int help){
	printf("To run:\n");
	printf("%s ..options.. <mlb_out> <fname_out> <fname_in> <layer_name1> <layer_name2> ...\n",PROG_NAME);
	printf("Layer names (OGR only) are optional - if not given the program will loop over all layers.\n");
	if (help<1)
		return;
	printf("Available options:\n");
	printf("-pin <mlb_in> If not included input metadata should be extracted from input file.\n");
	if (help>1)
		printf("For the DSFL driver the -pin switch can *not* be used.\n");
	printf("-drv <input_driver> Optional. Will default to 'OGR'. Output driver will be the same as the input driver.\n");
	printf("-of <output_ogr_driver> Optional. defaults to 'ESRI Shapefile'.\n");
	printf("-dco <datasource_creation_options> OGR driver specific datasource creation options (comma separated list of key=value pairs).\n");
	printf("-lco <layer_creation_options> OGR driver specific layer creation options (comma separated list of key=value pairs).\n");
	printf("-log <log_file> Specify log file.\n");
	printf("-alog Append to log file if it exists (and -log <log_file> is used)");
	if (help>1)
		printf("Will append output if the file already exists.\n");
	printf("-nop Do NOT try to set the projection metadata on the output datasource/layer.\n");
	if (help>1)
		printf("Useful for some drivers which fail to create layers unless projection metadata satisfy striqt requirements.\n");
	printf("-verb Be verbose - i.e. enable info and debug messages.\n");
	printf("-debug  Turn on debug info (mainly relevant for developers)\n");
	printf("\nOptions specific for the 'TEXT' driver:\n");
	printf("-sep <sep_char> is used to specify separation char for 'TEXT' format. **Defaults to whitespace.**\n");
	printf("-x <int> Specify x-column for 'TEXT' driver (default: first column).\n");
	printf("-y <int> Specify y-column for 'TEXT' driver (default: second column).\n");
	printf("-z <int> Specify z-column for 'TEXT' driver (default: third column).\n");
	printf("-naxyz Do NOT automatically set output coordinate order x,y,z for cartesian output systems.\n");
	printf("-ounits Append units to output coordinates (default 'm' and 'dg').\n");
	printf("-comments <comment_marker>  Skip, but copy, lines starting with <comment_marker>\n");
	printf("\nOptions which apply to both 'TEXT' and 'KMS' formats\n");
	printf("-flipxy Invert order of x and y columns in output (for KMS format relative to DEFAULT order).\n");
	printf("-geoout <unit> (sx, nt or rad) to use a special output format for geographic coordinates (default dg)\n");
	printf("-geoin <unit> (sx, nt or rad) to use a special interpretation of input geographic coordinates (default dg)\n");
	printf("-cpbad Copy uninterpretable lines to output file.\n");
	printf("-lazyh Silently set height=0 and do not emit an error if input system is 3D and height is NOT found.\n"); 
	printf("-prc <n_decimals> Specify (metric) precision of coordinate output.\n");
	printf("\nOptions specific to the 'KMS' format:\n");
	printf("-nounits To turn off units in output for 'KMS' format.\n"); 
	printf("-flipxyin Input x/y column order is inverted relative to the default order.\n");
	printf("Use %s --formats to list available drivers.\n",PROG_NAME);
	printf("Use %s --version to print version info.\n",PROG_NAME);
	if (help<2)
		printf("Use %s --help to print extra info.\n",PROG_NAME);
	else{
		printf("For the 'TEXT' driver special filenames 'stdin' and 'stdout' are available.\n");
		printf("For OGR-datasources:\nIf destination datasource <fname_out> exists AND is a directory, the datasource will be opened for update -\n");
		printf("and the program will try to CREATE new layers corresponding to layers in input.\n");
		printf("In all other cases the default is to overwrite existing output files.\n");
	}
	return;
}


void ListFormats(void){
	char stars[]="********************************************";
	char *drv_in;
	const char *frmt;
	int i=0;
	fprintf(stdout,"%s\nInput drivers:\n%s\n",stars,stars);
	while ((drv_in=INPUT_DRIVERS[i++]))
		fprintf(stdout,"%s\n",drv_in);
	fprintf(stdout,"%s\nOutput drivers provided by OGR (option -of <driver>):\n%s\n",stars,stars);
	GetOGRDrivers(1,0); /*reset reading*/
	while ((frmt=GetOGRDrivers(0,1))!=NULL)
		fprintf(stdout,"%s\n",frmt);
	GetOGRDrivers(1,0); /*reset reading*/
	fprintf(stdout,"%s\nInput drivers provided by OGR:\n%s\n",stars,stars);
	while ((frmt=GetOGRDrivers(0,0))!=NULL)
		fprintf(stdout,"%s\n",frmt);
	return;
}

void PrintVersion(void){
	const char *gdal_version;
	char trlib_version[512];
	TR_GetVersion(trlib_version,512);
	gdal_version=GetGDALVersion();
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

/*callback to a callback to a callback....
* Will enable us to temporarily disable output from trlib via SetIgnoreErrors
*/
void trlib_callback(LORD_CLASS errc,int err, const char *msg){
	Report(errc, err, VERB_HIGH, msg);
}

char **ParseCreationOptions(char *text){
	char **pairs,*pos1,*pos2;
	int n_pairs=0;
	/*puts(text);*/
	pairs=malloc(sizeof(char*)*24);
	/*remove whitespace - could of course be done in one go*/
	for (pos1=pos2=text; *pos1; pos1++){
		if (!isspace(*pos1))
			*(pos2++)=*pos1;
	}
	*pos2='\0';
	/*puts(text);*/
	pos1=text; /*save this pos - when we find a '=' we store the key=value pair*/
	while (*text && n_pairs<23){
		/*start looking for a new pair*/
		if (*text==','){
			*text='\0';
			pos1=text+1;
		}
		/*save the pair*/
		else if (*text=='='){
			pairs[n_pairs]=pos1;
			n_pairs++;
		}
		text++;
	}
	/*printf("npairs: %d\n",n_pairs);*/
	pairs[n_pairs]=NULL;
	pairs=realloc(pairs,sizeof(char*)*(n_pairs+2)); /*leave some room for appending an item*/
	return pairs;
}
	

int main(int argc, char *argv[])
{  
    char *inname=NULL,*outname=NULL,*mlb_in=NULL,*mlb_out=NULL,*drv_in=NULL, *drv_out=NULL,*sep_char=NULL, **layer_names=NULL;
    char *log_name=NULL,*dsco=NULL,*lco=NULL,**dscos=NULL,**lcos=NULL;
    char *key,*val,opts[]="pin:drv:of:sep:x:y:z:log:dco:lco:comments:prc:geoin:geoout:nop;verb;debug;alog;ounits;flipxy;flipxyin;naxyz;lazyh;cpbad;nounits;"; /*for processing command line options*/
    char *output_geo_unit="dg",*input_geo_unit="dg",*comments=NULL;
    /* defaults here */
    int set_output_projection=1, n_layers=0,col_x=0, col_y=1, col_z=-1,err=0,is_init=0,be_verbose=0,n_opts, append_to_log=0,units_in_output=0,flip_xy=0;
    int flip_xy_in=0,copy_bad=0, n_decimals=4, kms_no_unit=0,crt_xyz=1,zlazy=0,debug=0;
    struct format_options frmt;
    time_t rawtime;
    struct tm * timeinfo;
    TR *trf=NULL;
    FILE *fp_log=NULL;
    /*set reporting callback fct.*/
    SetCallBack(message_handler);
    RedirectOGRErrors();
    TR_SetLordCallBack(trlib_callback);
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
		    Usage(2);
		    exit(0);
	    }
    }
    else{
	    Usage(1);
	    exit(0);
    }
    /*parse options*/
    do{
	n_opts=my_get_opt(opts,argc,argv,&key,&val);
	if (key){
		/*printf("key: %s\n",key);*/
		if (!strcmp(key,"pin")){
			if (val)
				mlb_in=val;
		else
			goto usage;
		}
		else if (!strcmp(key,"of")){
			if (val)
				drv_out=val;
			else
				goto usage;
		}
		else if (!strcmp(key, "drv")){
			if (val)
				drv_in=val;
			else
				goto usage;
		}
		else if (!strcmp(key,"sep")){
			if (val)
			     sep_char=val;
			else
				goto usage;
		}
		else if (!strcmp(key,"dco")){
			if (val)
				dsco=val;
			else
				goto usage;
		}
		else if (!strcmp(key,"lco")){
			if (val)
				lco=val;
			else
				goto usage;
		}
		else if (!strcmp(key,"x")){
			if (val)
				col_x=atoi(val)-1; /*zero based index used - user should input 1 based indexing...*/
			else
				goto usage;
		}
		else if (!strcmp(key,"y")){
			if (val)
				col_y=atoi(val)-1;
			else
				goto usage;
		}
		else if (!strcmp(key, "z")){
			if (val)
				col_z=atoi(val)-1;
			else
				goto usage;
		}
		else if (!strcmp(key,"log")){
			if (val)
				log_name=val;
			else
				goto usage;
		}
		else if (!strcmp(key,"comments")){
			if (val)
				comments=val;
			else
				goto usage;
		}
		else if (!strcmp(key,"prc")){
			if (val)
				n_decimals=atoi(val);
			else
				goto usage;
		}
		else if (!strcmp(key,"geoin")){
			if (val)
				input_geo_unit=val;
			else
				goto usage;
		}
		else if (!strcmp(key,"geoout")){
			if (val)
				output_geo_unit=val;
			else
				goto usage;
		}
		else if (!strcmp(key,"verb"))
			be_verbose=1;
		else if (!strcmp(key,"debug"))
			debug=1;
		else if (!strcmp(key,"nop"))
			set_output_projection=0;
		else if (!strcmp(key,"alog"))
			append_to_log=1;
		else if (!strcmp(key,"ounits"))
			units_in_output=1;
		else if (!strcmp(key,"nounits"))
			kms_no_unit=1;
		else if (!strcmp(key,"flipxy"))
			flip_xy=1;
		else if (!strcmp(key,"flipxyin"))
			flip_xy_in=1;
		else if (!strcmp(key,"naxyz"))
			crt_xyz=0;
		else if (!strcmp(key,"cpbad"))
			copy_bad=1;
		else if (!strcmp(key,"lazyh"))
			zlazy=1;
		else{
			printf ("?? my_getopt returned unknown option %s\n", key);
			goto usage;
		}
        }
   } /*end do*/
    while (n_opts == 0 && key); 
   /*validate some choices...*/
   if (drv_in && (!strcmp(drv_in,"KMS") || !strcmp(drv_in,"TEXT"))){
	   if (!validate_geo_unit(input_geo_unit) || !validate_geo_unit(output_geo_unit)){
		fprintf(stderr,"Geographic unit not supported. Only 'dg','sx','nt' or 'rad' allowed.\n");
		goto usage;
	   }
	   if (!strcmp(drv_in,"TEXT") && (col_x==col_y || col_z==col_y || col_x==col_z || col_x<0 || col_y<0 || (col_z<0 && col_z!=-1))){
		fprintf(stderr,"Invalid geometry column specification - column numbers must differ and be at least 1.\n");
		goto usage;
	   }
			
   }
   /*if not enough args*/
   if (n_opts<3){
	fprintf(stderr,"At least three no-switch arguments needed: <mlb_out> <ds_out> <ds_in>\n");
        goto usage;
    }
    /* check unconsumed args - safe to modify argc here as it's not used below*/
    while( argc-1>3){
	    if (argv[argc-1] && *argv[argc-1]=='-'){
		    fprintf(stderr,"Unrecognized option key: %s\n",argv[argc-1]);
		    /*fprintf(stderr,"len: %d argc: %d mem: %d\n",strlen(argv[argc-1]),argc,argv[argc-1]);*/
		    goto usage;
	    }
	    argc--;
    }
    mlb_out=argv[1];
    outname=argv[2];
    inname=argv[3];
    if (debug)
	    ReportDebugMessages(1);
    /* check if layers specified*/
    if (n_opts>3){
	    int i;
	    n_layers=n_opts-3;
	    layer_names=malloc(sizeof( char*)*(n_layers+1));
	    for (i=0; i<n_layers; i++){
		    layer_names[i]=argv[4+i];
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
    
    if (strcmp(drv_in,"OGR")){
	    drv_out=drv_in;
	    if (lco || dsco) /*these options only available for OGR-input*/
		    goto usage;
    }
    else{/*TODO: remove debug output from here....*/
	    if (lco){
		char **pos;
		lcos=ParseCreationOptions(lco);
		pos=lcos;
		while (*pos){
			puts(*pos);
			pos++;
		}
		
	    }
	    if (dsco){
		char **pos;
		dscos=ParseCreationOptions(dsco);
		pos=dscos;
		while (*pos){
			puts(*pos);
			pos++;
		}
		
	    }
		    
    }
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
	    TR_TerminateLibrary();
	    exit(TR_LABEL_ERROR);
    }
    if (trf->proj_in  && IS_3D(trf->proj_out) && !IS_3D(trf->proj_in)){
	    fprintf(stderr,"2D -> 3D transformation not allowed.\n");
	    TR_Close(trf);
	    TR_TerminateLibrary();
	    exit(TR_LABEL_ERROR);
    }
    /*init logging*/
    if (log_name!=NULL){
	    if (append_to_log)
		fp_log=fopen(log_name,"a");
	    else
		fp_log=fopen(log_name,"w");
	    if (fp_log==NULL)
		    fprintf(stderr,"Failed to open log file %s - will not use log.\n",log_name);
    }
    if (fp_log!=NULL){
	    SetLogFile(fp_log);
	    /*set_lord_outputs(fp_log,fp_log,fp_log,fp_log,fp_log); now uses callback*/
	    
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
    /*TODO: report lcos and dscos */
    
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
	    Report(REP_INFO,0,VERB_LOW,"%s exists and will be updated / overwritten!",outname);
    }
    /* disptach according to driver */
    
    if (!strcmp(drv_in,"DSFL") || !strcmp(drv_in,"dsfl")){ /*begin DSFL */
	     if (mlb_in)
		     Report(REP_INFO,0,VERB_LOW,"Input MiniLabel should not be set for the DSFL-driver."); 
	    err=TransformDSFL(inname,outname,trf);
    }
    /* end DSFL */
    
   else if (!strcmp(drv_in,"KMS") || !strcmp(drv_in,"TEXT")){ /*begin simple text or KMS*/
	frmt.is_kms_format=!strcmp(drv_in,"KMS");
	if (!frmt.is_kms_format){
	    if (sep_char)
	        Report(REP_INFO,0,VERB_LOW,"Using column separator(s): %s",sep_char);
	    else
		Report(REP_INFO,0,VERB_LOW,"Using (all) whitespace as default column separator.");
        }
	else if (flip_xy_in)
		Report(REP_INFO,0,VERB_LOW,"Assuming that input x/y columns are inverted reletive to DEFAULT KMS format.");
	if (flip_xy)
		Report(REP_INFO,0,VERB_LOW,"Flipping output x/y columns.");
	if (zlazy)
		Report(REP_INFO,0,VERB_LOW,"'Lazy h' mode - will silently set h=0 if input height is not found.");
	Report(REP_INFO,0,VERB_LOW,"Precision of output coordinates: 1e-%d m",n_decimals); 
	if (comments)
		unescape(comments);
	if (sep_char){
		unescape(sep_char);
		#ifdef _DEBUG
		{
			char *tmp=sep_char;
			while (*tmp){
				printf("\nsep:%c\n",*tmp);
				tmp++;
			}
		}
		#endif
	}
	frmt.col_x=col_x;
	frmt.col_y=col_y;
	frmt.col_z=col_z;
	frmt.flip_xy=flip_xy;
	frmt.flip_xy_in=flip_xy_in;
	frmt.crt_xyz=crt_xyz;
	frmt.zlazy=zlazy;
	frmt.set_output_projection=set_output_projection;
	frmt.sep_char=sep_char;
	frmt.units_in_output=units_in_output;
	frmt.n_decimals=n_decimals;
	frmt.output_geo_unit=output_geo_unit;
	frmt.input_geo_unit=input_geo_unit;
	frmt.kms_no_unit=kms_no_unit;
	frmt.comments=comments;
	frmt.copy_bad=copy_bad;
	frmt.units_in_output=units_in_output;
	frmt.comments=comments;
        err=TransformText(inname,outname,trf,frmt);
    } /* end simple text /KMS */
    else if (!strcmp(drv_in,"OGR")){ /*begin OGR */
	   err=TransformOGR(inname, outname, trf, drv_out,layer_names, set_output_projection,dscos,lcos);
    }/* end OGR */	     
    
    else {
	    Report(REP_INFO,0,VERB_LOW,"Input driver %s not available!",drv_in);
	    exit(TR_ALLOCATION_ERROR);
    } 
   
    if (err!=TR_OK)
	    Report(REP_WARNING,err,VERB_LOW,"Abnormal return code from transformation: %d",err);
    
    if (GetErrors()>0){
	    err=(err==TR_OK)? (GetErrors()) : err;
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
    if (lcos!=NULL)
	free(lcos);
    if (dscos!=NULL)
	free(dscos);
    return err;
    usage:
	fprintf(stderr,"Invalid specification of options...\n");
	Usage(0);
	exit(1);
}
