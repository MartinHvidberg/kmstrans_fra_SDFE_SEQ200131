#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#ifdef _MSC_VER
#include <float.h>
#define INFINITY (DBL_MAX+DBL_MAX)
#define NAN (INFINITY-INFINITY)
#endif
#include "geo_lab.h"
#include "fgetln_kms.h"
#include "sgetg.h"
#include "sputg.h"
#include "set_tpd.h"
#include "trlib_intern.h"
#include "geo_constants.h"
#include "TransformText.h"
#include "Report.h"
#define MAX_LINES_SEARCH (512)   /*only read so many lines in order to look for a minilabel*/
#define SKIP_NOW  (1024)   /*skip after so many lines if no transformations done*/
#define MAX_ERRORS  (2000) /*not used YET*/
#define MAX_WARNINGS (50)
#define CHECK_WARNING_RATIO (500) /*check ratio for every 500 lines*/
#define MAX_ITEMS (256)
static char *next_column(char *current_pos, char *sep_char, char *sep_char_found, int is_kms_format);
static struct typ_dec type_metric= {4,1,6,4};  /*metric output with 4 decimals */
static struct typ_dec type_height= {4,1,3,4};
static struct typ_dec type_dg      ={2,1,2,8};
static struct typ_dec type_nt       ={1,8,4,5};
static struct typ_dec type_sx       ={1,1,6,4};
static struct typ_dec type_rad      ={2,3,1,10};


static char *next_column(char *current_pos, char *sep_char, char *sep_char_found, int is_kms_format){
	/*keep on going until we reach a separator - then go one past that*/
	char sep_found='\0',*current_test_char;
	while (*current_pos && (!sep_found)){
		/* tab or two spaces*/
		if (is_kms_format){
			if (*current_pos=='\t' || (*current_pos==' ' && *(current_pos+1)==' '))
				sep_found='\t'; /*dummy value*/
		}
		else{
			for(current_test_char=sep_char; *current_test_char; current_test_char++){
				if (*current_pos==*current_test_char){
					sep_found=*current_test_char;
					break;
				}
			}
		}
		/*dont go to far - just point to the sep_char_found*/
		if (*current_pos && !sep_found)
			current_pos++;
		/*printf("Found sep_char: %d\n",sep_found);*/
	}/*end spool to next col*/
	*sep_char_found=sep_found;
	return current_pos;
}

/* Transform simple text. Or KMS-format
* TODO: consider using col numbers for KMS-format.
* Implement a general flip_xy arg 
*/
int TransformText(char *inname, char *outname,TR *trf,struct format_options frmt)
{  
    double r2d=R2D;
    double d2r=D2R;
    FILE *f_in, *f_out;
    int ERR = 0,is_geo_in=0,is_geo_out=0;
    int n_trans_ok=0, n_trans_bad=0, n_warnings=0;
    int look_for_label,log_geoids=0;
    int lines_read=0, mlbs_found=0, max_col,min_col, coords_to_find=2,is_stdout,is_stdin;
     int coord_order[3]={0,1,2};
    struct typ_dec type_geo;
    enum {BUFSIZE = 4096};
    char buf[BUFSIZE],buf_out[BUFSIZE];
    char mlb_in_file[128],geoid_name[128],*tmp1,*tmp2;
    char *unit_out, default_separator[3];/*default separator used if we need to forcably insert a z-column*/
    struct typ_dec type_out;
    int in_comment=0, is_comment=0, flip_xy=0, append_unit=0, space_in_sep=0; /*flag to determine if we should 'eat' a space before appending unit*/
    /*test if in and out are stdin and stdout*/
    tmp2=buf;
    tmp1=inname;
    /*convert names to lower case for test of stdin stdout*/
    while(*tmp1) *(tmp2++)=tolower(*(tmp1++));
    *tmp2='\0';
    is_stdin=(!strcmp(buf,"stdin"));
    tmp2=buf;
    tmp1=outname;
    while(*tmp1) *(tmp2++)=tolower(*(tmp1++));
    *tmp2='\0';
     is_stdout=(!strcmp(buf,"stdout"));
     
    /*start reporting*/
    InitialiseReport();
    if (!frmt.sep_char) /*defaults to all whitespace*/
	    frmt.sep_char=" \t\r\n";
   
    if (!trf || !trf->proj_out){
	    Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"Output projection not set!");
	    return TR_LABEL_ERROR;
    }
    
    look_for_label=(trf->proj_in==NULL);
    is_geo_out=IS_GEOGRAPHIC(trf->proj_out);
    /* set output units*/
    if (is_geo_out){
	    type_out=type_dg;
	    unit_out="dg";
	    if (frmt.output_geo_unit){
		    unit_out=frmt.output_geo_unit;
		    if (!strcmp(unit_out,"sx"))
			    type_out=type_sx;
		    else if (!strcmp(unit_out,"nt"))
			    type_out=type_nt;
		    else if (!strcmp(unit_out,"rad"))
			    type_out=type_rad;
		    else if (strcmp(unit_out,"dg"))
			    Report(REP_WARNING,0,VERB_LOW,"Unrecognized output unit: %s - using degrees.",unit_out);
		}
	  
    }
    else{
	    unit_out="m";
	    type_out=type_metric;
    }
   
     if (frmt.is_kms_format){
	     if (trf->proj_in){
	          
		  if (COORD_ORDER(trf->proj_in)!=0 || IS_CARTESIC(trf->proj_in)){
		     /* N,E, (Z) */
		      coord_order[0]=0;
		      coord_order[1]=1;
		  }
		  else{
		      coord_order[0]=1;
		      coord_order[1]=0;
		  }
		  coord_order[2]=2;
	    } /*else coords to find set when minilabel is found*/
	    /*format is always: station XY/YX (Z)*/
	    frmt.col_x=coord_order[0]+1;
	    frmt.col_y=coord_order[1]+1;
	    frmt.col_z=3;
	    max_col=2;
	    strcpy(default_separator,"  ");
	    append_unit=1; /* always append units for KMS-format */
	    space_in_sep=0; /*do not eat space after coordinate output from sputg*/
     }    /*end kms_format*/
	     
     
     else{
	   
	   /* set the minimum number of columns and order of coordinates
	    TODO: test order of z-column
	    */
	    max_col=(frmt.col_x>frmt.col_y)?(frmt.col_x):(frmt.col_y);
	    max_col=(frmt.col_z>max_col)?(frmt.col_z):(max_col);
	    min_col= (frmt.col_x<frmt.col_y)?(frmt.col_x):(frmt.col_y);
	    min_col= (frmt.col_z<min_col && frmt.col_z>=0) ? (frmt.col_z) : (min_col);
	    if (frmt.col_y<frmt.col_x){
		    coord_order[0]=1;
		    coord_order[1]=0;
	    }
	    append_unit=frmt.units_in_output;
	    /*test whether we have space in sep*/
	    if (strchr(frmt.sep_char,' '))
		    space_in_sep=1;
	   
    }
    
     if (trf->proj_in){
	is_geo_in=IS_GEOGRAPHIC(trf->proj_in);
	coords_to_find=(IS_3D(trf->proj_in))? 3 : 2;
	if (IS_3D(trf->proj_in) && frmt.col_z<0){
		   Report(REP_WARNING,0,VERB_LOW,"Warning: input projection is 3 dimensional- but z column is not specified.");
		   Report(REP_WARNING,0,VERB_LOW,"Will attempt to read z-values from the column after the last planar coord.");
		   frmt.col_z=max_col+1;
		   
	    }
	log_geoids=((HAS_HEIGHTS(trf->proj_in) ||  HAS_HEIGHTS(trf->proj_out)));
	log_geoids=log_geoids && ((GET_HDTM(trf->proj_in)!=GET_HDTM(trf->proj_out)) || (GET_DTM(trf->proj_in)!=GET_DTM(trf->proj_out))) ;
	
    }
    
    if (!is_stdin)
		f_in=fopen(inname,"rt");
    else
		f_in=stdin;
    if (0==f_in){
	    Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Could not open input file!");
	    return TR_ALLOCATION_ERROR;}
     if (!is_stdout)
	     f_out=fopen(outname,"wt");
     else
	     f_out=stdout;
    if (0==f_out)
    {
	    Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Could not open output file!");
	    fclose(f_in);
	    return TR_ALLOCATION_ERROR;
    }
   
    
    
    if (frmt.set_output_projection) 
	    fprintf(f_out,"#%s\n",GET_MLB(trf->proj_out));
    tmp1=buf_out; /*used to buffer extracted kms output*/
    *tmp1='\0';
    while (0!= fgets(buf, BUFSIZE, f_in)) {
        int    argc, err;
        double coords[3]={NAN,NAN,NAN},store,x,y,z;
	char *current_pos,*end_pointer,*current_pos_out,*current_test_char,sep_char_found='\0',n_read;
	char *coord_positions[6]={NULL,NULL,NULL,NULL,NULL,NULL};
	int current_col=0, coords_found=0, found_z=0, insert_z=0,found_next_col=0;
	/*struct typ_dec type_out;*/
	lines_read++;
	
	
	/*look for input system label*/
	if (look_for_label){
		argc=sscanf(buf,"#%s",mlb_in_file);
		if (argc==1){
			err=TR_Insert(trf,mlb_in_file,0);
			if (err==TR_OK){
				Report(REP_INFO,0,VERB_LOW,"Tranformation: %s->%s",GET_MLB(trf->proj_in),GET_MLB(trf->proj_out));
				is_geo_in=IS_GEOGRAPHIC(trf->proj_in);
				mlbs_found++;
				/*special handling of kms-formats*/
				if (frmt.is_kms_format){
					
					if (COORD_ORDER(trf->proj_in)!=0 || IS_CARTESIC(trf->proj_in)){
						/* N,E, (Z) */
						coord_order[0]=0;
						coord_order[1]=1;
					}
					else{
						coord_order[0]=1;
						coord_order[1]=0;
					}
					coord_order[2]=2;
					frmt.col_x=coord_order[0]+1;
					frmt.col_y=coord_order[1]+1;
					/*
					printf("in: %d, out: %d\n",COORD_ORDER(trf->proj_in),COORD_ORDER(trf->proj_out));
					printf("in: %d, out: %d\n",IS_3D(trf->proj_in),IS_3D(trf->proj_out));
					*/
				} /*end kms-format*/
				log_geoids=((HAS_HEIGHTS(trf->proj_in) ||  HAS_HEIGHTS(trf->proj_out)));
				log_geoids=log_geoids && ((GET_HDTM(trf->proj_in)!=GET_HDTM(trf->proj_out)) || (GET_DTM(trf->proj_in)!=GET_DTM(trf->proj_out))) ;
				coords_to_find=(IS_3D(trf->proj_in))? 3 : 2;
				 if (IS_3D(trf->proj_in) && frmt.col_z<0){
					Report(REP_WARNING,0,VERB_LOW,"Warning: input projection is 3 dimensional- but z column is not specified.");
					Report(REP_WARNING,0,VERB_LOW,"Will attempt to read z-values from the column after the last planar coord.");
					frmt.col_z=max_col+1;					 
				 }
				continue;
			}
			else
				Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"Failed to translate minilabel: %s",mlb_in_file);
			}
		
		if (!trf->proj_in && lines_read>MAX_LINES_SEARCH){
			Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"No proper minilabel found!");
			return TR_LABEL_ERROR;
		}
		
	} /* end look for label */
	/*perhaps write output - like a header - to f_out */
	if (!trf->proj_in){
		if (is_stdin)
			fprintf(stdout,"Set minilabel first: #minilabel\n");
		continue;
	}
	/*Special stuff for KMS-format*/
	/*scan the line for tokens*/
	current_pos=buf;
	/*spool to first column - left whitespace means nothing*/ 
	while (*current_pos && isspace(*current_pos))
		current_pos++;
	
	/*test if its a whitespace or a commentary line*/
	is_comment=frmt.is_kms_format ? (*current_pos==';' || *current_pos=='*') : (*current_pos && frmt.comments && strstr(current_pos,frmt.comments)==current_pos);
	if (!(*current_pos) || is_comment){
		fputs(buf,f_out);
		continue;
	}
	while (coords_found<coords_to_find && *current_pos){
		/*printf("Current_col: %d\n",current_col);*/
		if (current_col==frmt.col_x || current_col==frmt.col_y || current_col==frmt.col_z){
			int is_number=0;
			int used=0; /* wont read more than an int can hold!*/
			struct typ_dec type_in;
			char udt[3];
			if (is_geo_in && current_col!=frmt.col_z)
				strcpy(udt,"dg");
			else
				strcpy(udt,"m");
			/* it is always safe to use sgetg unless column separator is ' ' in which case 
			* well need to check if sgetg stays within the column span - so we might as well do that in all cases*/
			if (frmt.is_kms_format){ 
				store=sgetg(current_pos,&type_in,&used,udt);
				is_number=(type_in.gf>0);
			}
			else{ /*a bit more tricky to see whether there are units which must be consumed*/
				size_t col_span;
				char tmp_sep;
				char *tmp=next_column(current_pos,frmt.sep_char,&tmp_sep,0);
				col_span=tmp-current_pos; /*span until and including the sep_char*/
				store=sgetg(current_pos,&type_in,&used,udt);
				if (!(used<=col_span && type_in.gf>0)){ 
					/*if this fails a unit is not contained in the col span and we will use strtod
					* as sgetg will skip spaces 
					printf("Failed to find unit. col_span: %d, used: %d, pos_after_used: %c\n",col_span,used,*(current_pos+used));*/
					store=strtod(current_pos,&end_pointer);
					used=end_pointer-current_pos;
					is_number=(used>0);
					if (is_number && is_geo_in && current_col!=frmt.col_z) /*since we assumme degrees in this case - convert to radians */
						store*=d2r;
					
				}
				else
					is_number=1;
			}
			/*printf("used: %d, store: %.5f pos: %s current_col: %d\n",used,store,current_pos,current_col);*/
			/*some test to see if we found a number - check with KE*/
			if (is_number){
				coord_positions[coords_found*2]=current_pos;
				current_pos+=used;
				coord_positions[coords_found*2+1]=current_pos;
				coords[coords_found]=store;
				coords_found++;
				default_separator[0]=sep_char_found;
				default_separator[1]='\0';
				/*printf("pos after: %s",current_pos);*/
				if (current_col==frmt.col_z)
					found_z=1;
			}
				
			
		}
		
		if (coords_found==coords_to_find)
			break;
		/*spool to next col */
		current_pos=next_column(current_pos,frmt.sep_char,&sep_char_found,frmt.is_kms_format);
		if (*current_pos) /*if not end reached go one past the sep_char */
			current_pos++;
		current_col++;
		/*at the beginning of a column its safe to skip blanks - this will also leave room in the output 'around' coordinates */
		while (*current_pos && isspace(*current_pos))
			current_pos++;
		
		
	} /*end scan line (while)*/
	
	/*see if we should forceably insert a z column*/
	insert_z=(IS_3D(trf->proj_out) && !found_z);
	
	if (!found_z){/*insert default*/
		coords[coord_order[2]]=0;
	}
	if (!found_z && coords_to_find==3){
		coords_found+=1;
	}
	x=coords[coord_order[0]];
	y=coords[coord_order[1]];
	z=coords[coord_order[2]];
	
	/*uninterpretable line*/
	if (coords_found!=coords_to_find){
		fputs(buf,f_out);
		if (n_warnings<MAX_WARNINGS)
			Report(REP_WARNING,0,VERB_HIGH,"Line: %d, not all coords found.",lines_read);
		else if (n_warnings==MAX_WARNINGS)
			Report(REP_WARNING,0,VERB_LOW,"Line %d, not all coords found - this warning will not be issued anymore.\nDid you set a proper column separator?",lines_read);
		if (lines_read==CHECK_WARNING_RATIO && n_warnings>MAX_WARNINGS && n_warnings*0.25>n_trans_ok)
			Report(REP_ERROR,TR_ERROR,VERB_LOW,"High fraction of lines without coordinates, bad column separator?");
		n_warnings++;
		continue;
	}
	/*Test if we should break - perhaps a bad separator?*/
	if (lines_read>SKIP_NOW && n_trans_ok==0){
		Report(REP_ERROR,TR_ERROR,VERB_LOW,"%d lines read - no transformations done - perhaps a bad separator? Aborting now....",lines_read);
		TerminateReport();
		return TR_ERROR;
	}
       
	/*TODO: fixup what is to be writen to log */
	err = TR_Transform(trf,coords+coord_order[0],coords+coord_order[1],coords+coord_order[2],1);
	if (err==TR_OK){
		n_trans_ok++;
		/*perhaps do this in all cases?*/
		
		if (log_geoids){
			TR_GetGeoidName(trf,geoid_name);
			AppendGeoid(geoid_name);
		}
	}
	else{
		n_trans_bad++;
		ERR = err;
		/*write to err log here because \n is in front of err msg - will look bad if output==stdout */
		Report(REP_ERROR,err,VERB_HIGH,"Error: %d, In: %.5f %.5f %.5f ",TR_GetLastError(),x,y,z);
	}
	/*continue even after an error?*/
	
	/*flip xy?*/
	if (frmt.is_kms_format){
	    flip_xy=(COORD_ORDER(trf->proj_in)!=COORD_ORDER(trf->proj_out));
	    /*stupid exception - seems that cartesic have order 0 */
	    flip_xy=flip_xy || (IS_CARTESIC(trf->proj_out) && (!IS_CARTESIC(trf->proj_in) && COORD_ORDER(trf->proj_in)==0));
	}
	else
		flip_xy=frmt.flip_xy;
	if (flip_xy){
		double old_x=coords[coord_order[0]];
		coords[coord_order[0]]=coords[coord_order[1]];
		coords[coord_order[1]]=old_x;
	}
        /*  Now compose the output string */
	current_pos=buf;
	current_pos_out=buf_out;
	coords_found=0;
	while(*current_pos){
		if (coords_found<coords_to_find && current_pos==coord_positions[2*coords_found]){
			
			if (1==1){/*or coords_found!=coord_order[2] || IS_3D(trf->proj_out)) if we do not want to write z when output is 2d....*/
				if (coords_found!=coord_order[2])
					current_pos_out+=sputg(current_pos_out,coords[coords_found],&type_out,"");
				else
					current_pos_out+=sputg(current_pos_out,coords[coords_found],&type_height,"");
				if (append_unit){
					if (space_in_sep) /*eat space generated by sputg*/
						current_pos_out--;
					if (coords_found!=coord_order[2]) /*if not z*/
						current_pos_out+=sprintf(current_pos_out,"%s",unit_out);
					else
						current_pos_out+=sprintf(current_pos_out,"m");
				}
			}
			
			current_pos=coord_positions[2*coords_found+1];
			coords_found++;
			/*test here if we should insert a z value also*/
			if (insert_z && coords_found==2){
				current_pos_out+=sprintf(current_pos_out,"%s",default_separator);
				current_pos_out+=sputg(current_pos_out,coords[coord_order[2]],&type_height,""); 
				/*sprintf(current_pos_out,frmt_out,coords[coord_order[2]]);*/
				if (append_unit){
					if (space_in_sep)
						current_pos_out--;
					current_pos_out+=sprintf(current_pos_out,"m");
				}
				insert_z=0;
				/*TODO: do we need to append a separator in the end also?*/
			}
		}
		else{ /*copy char*/
			*(current_pos_out++)=*(current_pos++); 
		}
		
		
		
	} /*end compose output */
	*current_pos_out='\0';
	fputs(buf_out,f_out);
	
    } /* end read line from input */
    if (!is_stdin)
	    fclose(f_in);
    if (!is_stdout)
	    fclose(f_out);
   
    if (!trf->proj_in){
	    Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"No proper minilabel found!");
	    return TR_LABEL_ERROR;
    }
    Report(REP_INFO,0,VERB_LOW,"%-23s: %d","#Lines read",lines_read);
    if (look_for_label)
	    Report(REP_INFO,0,VERB_LOW,"%-23s: %d","#Layers found",mlbs_found);
    Report(REP_INFO,0,VERB_LOW,"%-23s: %d","#Transformations OK",n_trans_ok);
    if (n_trans_bad>0)
	Report(REP_INFO,0,VERB_LOW,"%-23s: %d","#Transformation errors",n_trans_bad);
    LogGeoids();
    TerminateReport();
    return ERR? TR_ERROR: TR_OK;
}
	