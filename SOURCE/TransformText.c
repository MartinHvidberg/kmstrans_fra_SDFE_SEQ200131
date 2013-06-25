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
#define LOGR   (7)       /*base number of decimals - precision is added*/
#define LOGM  (3)
#define LOGS  (2)
#define LOGD  (5)
#define GET_COORD_POSITION(a,b,c) ((a==c) ? 2 : ((a==b) ? 0 : 1))
#undef MAX
#define MAX(a,b) ((a>b)?a:b)

static int next_column(char **current_pos, char **end, char *sep_char, char **buf_out, int is_kms_format);
static char *next_sep(char *current_pos, char *sep_char, char **buf_out, int is_kms_format);
static char *next_non_sep(char *current_pos, char *sep_char, char **buf_out, int is_kms_format, int *end_reached);
static int set_coordinate_order(TR *trf, int *output_order, struct format_options *frmt);

static struct typ_dec type_metric= {4,1,6,4};  /*metric output with 4 decimals */
static struct typ_dec type_height= {4,1,2,3}; /* default height output format with 3 decimals - will be updated if input heights are read*/
static struct typ_dec type_dg      ={2,1,2,8};
static struct typ_dec type_nt       ={1,8,4,5};
static struct typ_dec type_sx       ={1,1,6,4};
static struct typ_dec type_rad      ={2,3,1,10};


static char *next_sep(char *current_pos, char *sep_char, char **buf_out, int is_kms_format){
	/*keep on going until we reach a separator or a newline*/
	char sep_found='\0',*current_test_char;
	while (*current_pos && (!sep_found)){
		/* tab or two spaces*/
		if (is_kms_format){
			if (*current_pos=='\t' || (*current_pos==' ' && *(current_pos+1)==' '))
				sep_found='\t'; /*dummy value*/
			
		}
		else{
			if (current_test_char=strchr(sep_char,*current_pos))
				sep_found=*current_test_char;
		}
		if (*current_pos=='\r' || *current_pos=='\n'){
			sep_found='\n';
		}
		if (buf_out && !sep_found){
			**buf_out=*current_pos;
			(*buf_out)++;
		}
		/*dont go too far - just point to the first sep_char_found*/
		if (!sep_found)
			current_pos++;
		
	}/*end spool to next col*/
	
	return current_pos;
}

static char *next_non_sep(char *current_pos, char *sep_char, char **buf_out, int is_kms_format, int *end_reached){
	int found=0;
	*end_reached=0;
	while (*current_pos && !found){
		if ((is_kms_format && !isspace(*current_pos)) || (!is_kms_format && !strchr(sep_char,*current_pos)))
			found=1;
		if (*current_pos=='\r' || *current_pos=='\n'){
			found=1;
			*end_reached=1;
		}
		if (buf_out && !found){
			**buf_out=*current_pos;
			(*buf_out)++;
		}
		if (!found)
			current_pos++;
	}
	return current_pos;
}

static int next_column(char **current_pos, char **end, char *sep_char, char **buf_out, int is_kms_format){
	int end_reached=0;
	*current_pos=next_sep(*current_pos,sep_char, buf_out, is_kms_format);
	if (!**current_pos || **current_pos=='\r' || **current_pos=='\n'){
		*end=*current_pos;
		return 0;
	}
	*current_pos=next_non_sep(*current_pos,sep_char,buf_out,is_kms_format, &end_reached);
	if (!**current_pos || end_reached){ /*emtpty last field*/
		*end=*current_pos;
		return 0;
	}
	*end=next_sep(*current_pos,sep_char, buf_out, is_kms_format);
	return 1;
}

static int set_coordinate_order(TR *trf, int *output_order, struct format_options *frmt){
	if (!trf->proj_out || !trf->proj_in)
		return -1; /*well - should alwyas be set when this is called...*/
	if (frmt->is_kms_format){
		frmt->col_z=3;
		output_order[2]=2;
		if (COORD_ORDER(trf->proj_in)!=0 || IS_CARTESIC(trf->proj_in)){
				/* N,E, (Z) */
				frmt->col_x=1;
				frmt->col_y=2;
			}
			else{
				frmt->col_x=2;
				frmt->col_y=1;
			}
		
		
		if (COORD_ORDER(trf->proj_out)!=0 || IS_CARTESIC(trf->proj_out)){
			output_order[0]=0;
			output_order[1]=1;
		}
		else{
			output_order[0]=1;
			output_order[1]=0;
		}
		
		return IS_3D(trf->proj_in)?3:2;
		
	}
	else{ /*if TEXT */
		int max_col,min_col;
		if (frmt->col_z<0){
			if (IS_3D(trf->proj_in)){
				Report(REP_WARNING,0,VERB_LOW,"Warning: input system is 3 dimensional- but input z column is not specified.");
				Report(REP_INFO,0,VERB_LOW,"Will attempt to read z-values from the column after the last planar coord.");
			}
			frmt->col_z=(frmt->col_x>frmt->col_y)?(frmt->col_x+1):(frmt->col_y+1);
		}
		/*what to do if input is 3D and output is 2D??*/
		/*well - that's ok - in that case we just don't write the output z-coord*/ 
		max_col=MAX(frmt->col_x,frmt->col_y);
		min_col=-MAX(-frmt->col_x,-frmt->col_y);
		max_col=MAX(max_col,frmt->col_z);
		min_col=-MAX(-min_col,-frmt->col_z);
		if (IS_CARTESIC(trf->proj_out) && frmt->crt_xyz){
			output_order[0]=0;
			output_order[1]=1;
			output_order[2]=2;
			
		}
		else{ /*TODO:  hmm - what if col_z is given but input is 2D? for now consider it an error on the user side*/
			output_order[0]=GET_COORD_POSITION(frmt->col_x,min_col,max_col);
			output_order[1]=GET_COORD_POSITION(frmt->col_y,min_col,max_col);
			output_order[2]=GET_COORD_POSITION(frmt->col_z,min_col,max_col);
			if (frmt->flip_xy){
				int store=output_order[0];
				output_order[0]=output_order[1];
				output_order[1]=store;
			}
		}
		Report(REP_DEBUG,0,VERB_LOW,"Ouput order: xyz: %d%d%d, min_col: %d, max_col: %d",output_order[0],output_order[1],output_order[2],min_col,max_col);
		if (IS_CARTESIC(trf->proj_out) && (output_order[0]!=0 || output_order[1]!=1))
			Report(REP_WARNING,0,VERB_LOW,"Warning: Output projection is cartesian, but output coordinate order is not x,y,z. ");
		return IS_3D(trf->proj_in) ? (max_col) : MAX(frmt->col_x,frmt->col_y);
	}
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
    int  output_order[3]={0,1,2};
    enum {BUFSIZE = 4096};
    char buf[BUFSIZE],buf_out[BUFSIZE];
    char mlb_in_file[128],geoid_name[128],*tmp1,*tmp2;
    char *unit_out;
    struct typ_dec type_out, type_h, *p_type_h;
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
    /* set output units and precision*/
    p_type_h=&type_height; /*only for writing of heights - not cartesic z*/
    if (is_geo_out){
	    type_out=type_dg;
	    type_out.df=LOGD+frmt.n_decimals;
	    unit_out="dg";
	    if (frmt.output_geo_unit){
		    unit_out=frmt.output_geo_unit;
		    if (!strcmp(unit_out,"sx")){
			    type_out=type_sx;
			    type_out.df=LOGS+frmt.n_decimals;
		    }
		    else if (!strcmp(unit_out,"nt")){
			    type_out=type_nt;
			    type_out.df=LOGM+frmt.n_decimals;
		    }
		    else if (!strcmp(unit_out,"rad")){
			    type_out=type_rad;
			    type_out.df=LOGR+frmt.n_decimals;
		    }
		    else if (strcmp(unit_out,"dg"))
			    Report(REP_WARNING,0,VERB_LOW,"Unrecognized output unit: %s - using degrees.",unit_out);
		}
	  
    }
    else{
	    unit_out="m";
	    type_out=type_metric;
	    type_out.df=frmt.n_decimals;
    }
   
     if (frmt.is_kms_format){
		append_unit=!frmt.kms_no_unit; 
		space_in_sep=0;
		frmt.sep_char="\t";
	    
     }    /*end kms_format*/
     else{
		append_unit=frmt.units_in_output;
	   
		/*test whether we have space in sep*/
		if (strchr(frmt.sep_char,' '))
			space_in_sep=1;
	  
     }
     /* 2D->3D is disabled from main in this case...*/
     if (trf->proj_in){
	max_col=set_coordinate_order(trf,output_order,&frmt);
	is_geo_in=IS_GEOGRAPHIC(trf->proj_in);
	coords_to_find=(IS_3D(trf->proj_in))? 3 : 2;
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
	char *current_pos,*current_pos_out,*col_end;
	char *coord_positions[6]={NULL,NULL,NULL,NULL,NULL,NULL};
	int current_col=0, coords_found=0, found_z=0,found_next_col=0,write_z=0,keep_going=1,end_reached=0;
	/*struct typ_dec type_out;*/
	lines_read++;
	
	
	/*look for input system label*/
	if (look_for_label){
		argc=sscanf(buf,"#%s",mlb_in_file);
		if (argc==1){
			err=TR_Insert(trf,mlb_in_file,0);
			if (err==TR_OK){
				if (IS_3D(trf->proj_out) && !IS_3D(trf->proj_in)){
					Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"2D -> 3D transformation not allowed. Will continue to look for valid input label.");
					TR_Insert(trf,NULL,0); /*invalidate proj_in*/
					continue;
				}
				Report(REP_INFO,0,VERB_LOW,"Tranformation: %s->%s",GET_MLB(trf->proj_in),GET_MLB(trf->proj_out));
				mlbs_found++;
				max_col=set_coordinate_order(trf,output_order,&frmt);
				is_geo_in=IS_GEOGRAPHIC(trf->proj_in);
				log_geoids=((HAS_HEIGHTS(trf->proj_in) ||  HAS_HEIGHTS(trf->proj_out)));
				log_geoids=log_geoids && ((GET_HDTM(trf->proj_in)!=GET_HDTM(trf->proj_out)) || (GET_DTM(trf->proj_in)!=GET_DTM(trf->proj_out))) ;
				coords_to_find=(IS_3D(trf->proj_in))? 3 : 2;
				
			}
			else
				Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"Failed to convert minilabel: %s",mlb_in_file);
			continue;
			}
			
		if (!trf->proj_in && lines_read>MAX_LINES_SEARCH){
			Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"No proper minilabel found!");
			return TR_LABEL_ERROR;
		}
		
	} /* end look for label */
	/*perhaps write output - like a header - to f_out */
	if (!trf->proj_in){
		if (frmt.copy_bad)
			fputs(buf,f_out);
		if (is_stdin)
			fprintf(stdout,"Set minilabel first: #minilabel\n");
		continue;
	}
	/*scan the line for tokens*/
	current_pos=buf;
	/*spool to first column - left whitespace means nothing*/ 
	while (*current_pos && isspace(*current_pos))
		current_pos++;
	
	/*test if its a whitespace or a commentary line*/
	is_comment=frmt.is_kms_format ? (*current_pos==';' || *current_pos=='*' || strstr(current_pos,"-1")==current_pos) : (*current_pos && frmt.comments && strstr(current_pos,frmt.comments)==current_pos);
	if (!(*current_pos) || is_comment){
		fputs(buf,f_out);
		continue;
	}
	
	col_end=next_sep(current_pos,frmt.sep_char,NULL,frmt.is_kms_format);
	
	while (coords_found<coords_to_find && *current_pos && current_col<=max_col && keep_going){
		Report(REP_DEBUG,0,VERB_LOW,"We are now at:%s, col: %d",current_pos,current_col);
		Report(REP_DEBUG,0,VERB_LOW,"Col end is:%s",col_end);
		if (current_col==frmt.col_x || current_col==frmt.col_y || (current_col==frmt.col_z && coords_to_find==3)){
			int is_number=0;
			int used=0; /* wont read more than an int can hold!*/
			struct typ_dec type_in;
			char *udt,*tmp,tmp_sep;
			if (is_geo_in && current_col!=frmt.col_z)
				udt=frmt.input_geo_unit;
			else
				udt="m";
			while(isspace(*current_pos) && current_pos<col_end)
				current_pos++;
			/*sgetg will skip non-numeric chars - we dont want that. Right now we should be pointing to the beginning of a number!*/
			if (!isdigit(*current_pos) && *current_pos!='+' && *current_pos!='-'){
				Report(REP_ERROR,1,VERB_HIGH,"Line: %d, non numeric input in column: %d",lines_read,current_col+1);
				if (!(current_col==frmt.col_z && frmt.zlazy))
					break; /*no need to continue then*/
			}
			else{
				/* it is always safe to use sgetg - IF we insert a stop where it's not allowed to go further!*/
				tmp_sep=*col_end;
				*col_end='\0';
				store=sgetg(current_pos,&type_in,&used,udt);
				is_number=(type_in.gf>0);
				*col_end=tmp_sep; /*restore*/	
				if (is_number){
					current_pos+=used;
					coords_found++;
					if (current_col==frmt.col_z){
						coords[2]=store;
						found_z=1;
						if (!IS_CARTESIC(trf->proj_in)){ /*if it's a real height (including E) */
							type_h=type_in;
							type_h.tf=1; /*always m in ouput -TODO: transform number of decimals if input is not in m*/
							p_type_h=&type_h;
						}
						else
							p_type_h=&type_height;
						
					}
					else if (current_col==frmt.col_x)
						coords[0]=store;
					else
						coords[1]=store;
				}
				else{/*so we failed - no need to scan any further unless we are in lazy-h mode!*/
					Report(REP_ERROR,1,VERB_HIGH,"Line: %d, sgetg failed to interpret input in column: %d as a number.",lines_read,current_col+1);
					if (!(current_col==frmt.col_z && frmt.zlazy))
						break; /*no need to continue then*/
					
				}
			}
			
		}
		
		if (coords_found==coords_to_find)
			break;
		/*spool to next col */
		keep_going=next_column(&current_pos,&col_end,frmt.sep_char,NULL,frmt.is_kms_format);
		current_col++;
		
	} /*end scan line (while)*/
	/* We will no more never, no more never forceably insert a z-column!*/ 
	if (!found_z){/*insert default*/
		coords[2]=0;
		if (IS_3D(trf->proj_in)){
			if (frmt.zlazy && !IS_CARTESIC(trf->proj_in)) /*be forgiving.....*/
				coords_found+=1;
			else if (n_warnings<MAX_WARNINGS){
				Report(REP_WARNING,0,VERB_HIGH,"Line: %d, did not find z-coordinate.",lines_read);
				n_warnings++;
			}
		}
	}
	
	x=coords[0];
	y=coords[1];
	z=coords[2];
	
	/*uninterpretable line*/
	if (coords_found!=coords_to_find){
		if (frmt.copy_bad)
			fputs(buf,f_out);
		if (n_warnings<MAX_WARNINGS){
			Report(REP_WARNING,0,VERB_HIGH,"Line: %d, not all coords found.",lines_read);
		}
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
	err = TR_Transform(trf,coords,coords+1,coords+2,1);
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
	/*  Now compose the output string */
	current_pos=buf;
	current_pos_out=buf_out;
	current_col=0;
	coords_found=0;
	write_z=(IS_3D(trf->proj_out) && found_z) || IS_CARTESIC(trf->proj_out);
	end_reached=0;
	col_end=NULL;
	/*spool to first column - left whitespace means nothing*/ 
	while (*current_pos && isspace(*current_pos))
		*(current_pos_out++)=*(current_pos++);
	while(*current_pos && current_col<=max_col && !end_reached){
		if (current_col==frmt.col_x || current_col==frmt.col_y || (current_col==frmt.col_z && coords_to_find==3)){
			int coord_index;
			if (output_order[0]==coords_found)
				coord_index=0;
			else if (output_order[1]==coords_found)
				coord_index=1;
			else
				coord_index=2;
			Report(REP_DEBUG,0,VERB_LOW,"current_col: %d, c-index: %d\n",current_col,coord_index);
			if (coord_index!=2 || write_z){ /* some test to determine if we should write output z, i.e. whether it was 'lazily' not included even when ouput is 3d...*/
				char coord_buf[256];
				tmp1=coord_buf;
				if (coord_index!=2 || IS_CARTESIC(trf->proj_out)) /*if x,y or cartesic z*/
					sputg(coord_buf,coords[coord_index],&type_out,"");
				else
					sputg(coord_buf,coords[coord_index],p_type_h,"");
				/* if not kms format - trim the output*/
				if (!frmt.is_kms_format){
					while(isspace(*tmp1))
						tmp1++;
					/*perhaps only rtrim if space_in_sep?? */
					tmp2=tmp1;
					while(*tmp2 && !isspace(*tmp2))
						tmp2++;
					*tmp2='\0';
				}
				current_pos_out+=sprintf(current_pos_out,tmp1);
				if (append_unit){
					if (coord_index!=2) /*if not z*/
						current_pos_out+=sprintf(current_pos_out,"%s",unit_out);
					else
						current_pos_out+=sprintf(current_pos_out,"m");
				}
				current_pos=next_sep(current_pos,frmt.sep_char,NULL,frmt.is_kms_format);
				col_end=current_pos_out;
				/*write sep*/
				current_pos=next_non_sep(current_pos,frmt.sep_char,&current_pos_out,frmt.is_kms_format,&end_reached);
				
			}
			else{
				current_pos=next_sep(current_pos,frmt.sep_char,NULL,frmt.is_kms_format);
				/*never write the sep*/
				current_pos=next_non_sep(current_pos,frmt.sep_char,NULL,frmt.is_kms_format,&end_reached);
				if (end_reached && col_end) /*end reached?*/
					current_pos_out=col_end; /*eat last sep*/
			}
			current_col++;
			coords_found++;
			Report(REP_DEBUG,0,VERB_LOW,"Current pos: %s",current_pos);
		}
		else{ /*copy columns*/
			current_pos=next_sep(current_pos,frmt.sep_char,&current_pos_out,frmt.is_kms_format);
			col_end=current_pos_out;
			current_pos=next_non_sep(current_pos,frmt.sep_char,&current_pos_out,frmt.is_kms_format,&end_reached);
			current_col++;
			Report(REP_DEBUG,0,VERB_LOW,"Current pos: %s",current_pos);
		}
	} /*end compose output */
	/*finally copy any remaining stuff - better performance*/
	while (*current_pos)
		*(current_pos_out++)=*(current_pos++);
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
    if (n_trans_ok==0)
	    Report(REP_WARNING,0,VERB_LOW,"No transformations performed - did you set a proper column separator?");
    LogGeoids();
    TerminateReport();
    return ERR? TR_ERROR: TR_OK;
}
	