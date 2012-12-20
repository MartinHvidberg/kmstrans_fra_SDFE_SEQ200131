#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "geo_lab.h"
#include "fgetln_kms.h"
#include "sgetg.h"
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
static int split_tokens(char *line, char *delimiter, char **items, int max_items){
	char *item;
	int n_items=0;
	item=strtok(line,delimiter);
	if (item==NULL){
		return 0;
	}
	while (item && n_items<max_items){
		*(items+n_items++)=item;
		item=strtok(NULL,delimiter);
	}
	return n_items;
}
/* skip single spaces and comments - gives a more machine readable kms-format*/
static int extract_kms(char *buf, char *buf_out, int *in_comment){
	char *pos=buf;
	int n_read=0, was_space=0;
	while (*pos){
		if (*in_comment){
			/*if (f_out!=NULL)
				fputc(*pos,f_out);*/
			if (*pos==';')
				*in_comment=0;
		}
		else if (*pos=='*')
			*in_comment=1;
		else if (!(*pos==' ' && *(pos+1)!=' ' && !was_space) || *(pos+1)=='*'){
			*(buf_out++)=*pos;
			n_read++;
		}
		was_space=(*pos==' ');
		pos++;
	}
	return n_read;
}
		

/* Transform simple text. Or KMS-format
* TODO: consider using col numbers for KMS-format.
* Implement a general flip_xy arg 
*/
int TransformText(char *inname, char *outname,TR *trf, char *sep_char, int col_x, int col_y, int col_z, int set_output_projection, int is_kms_format)
{  
    double r2d=R2D;
    double d2r=D2R;
    FILE *f_in, *f_out;
    int ERR = 0,i=0,is_geo_in=0,is_geo_out=0;
    int n_trans_ok=0, n_trans_bad=0, n_warnings=0;
    int look_for_label;
    int lines_read=0, mlbs_found=0, n_items=0, max_col,min_col, coords_to_find,is_stdout,is_stdin;
    int coord_order[3]={0,1,2};
    enum {BUFSIZE = 4096};
    char buf[BUFSIZE],buf_out[BUFSIZE];
    char mlb_in_file[128],geoid_name[128],*tmp1,*tmp2;
    char unit_out[3];
    char *coord_positions[6]={NULL,NULL,NULL,NULL,NULL,NULL};
    int in_comment=0, flip_xy=0; /*special flags for kms_format*/
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
    if (!sep_char) /*defaults to all whitespace*/
	    sep_char=" \t\r\n";
   
    if (!trf || !trf->proj_out){
	    Report(REP_ERROR,TR_LABEL_ERROR,VERB_LOW,"Output projection not set!");
	    return TR_LABEL_ERROR;
    }
    
    look_for_label=(trf->proj_in==NULL);
    is_geo_out=IS_GEOGRAPHIC(trf->proj_out);
    if (is_geo_out)
	    strcpy(unit_out,"dg");
    else
	    strcpy(unit_out,"m");
    if (trf->proj_in){
	is_geo_in=IS_GEOGRAPHIC(trf->proj_in);
    }
     if (is_kms_format){
	     if (trf->proj_in){
	          coords_to_find=(IS_3D(trf->proj_in))? 3 : 2;
		  if (COORD_ORDER(trf->proj_in)==0){
		     /* N,E, (Z) */
		      coord_order[0]=1;
		      coord_order[1]=0;
		  }
		  else{
		      coord_order[0]=0;
		      coord_order[1]=1;
		  }
		  coord_order[2]=2;
	    } /*else coords to find set when minilabel is found*/
	    /*format is always: station XY/YX (Z)*/
	    col_x=coord_order[0]+1;
	    col_y=coord_order[1]+1;
	    col_z=3;
	    sep_char=" \t\r\n";
	    /*printf("%d %d %d\n",coord_order[0],coord_order[1],coord_order[2]);*/
     }    /*end kms_format*/
	     
     
     else{
	    /* set the minimum number of columns and order of coordinates
	    TODO: test order of z-column
	    */
	    max_col=(col_x>col_y)?(col_x):(col_y);
	    max_col=(col_z>max_col)?(col_z):(max_col);
	    min_col= (col_x<col_y)?(col_x):(col_y);
	    min_col= (col_z<min_col && col_z>=0) ? (col_z) : (min_col);
	    if (IS_3D(trf->proj_out) && col_z<0){
		   Report(REP_WARNING,0,VERB_LOW,"Warning: output projection is 3 dimensional- but z column is not specified.");
		   Report(REP_WARNING,0,VERB_LOW,"Will attempt to read z-values from the column after the last planar coord.");
		    col_z=max_col+1;
		   /*perhaps add : use_z_hack=1;*/
	    }
	    coords_to_find=(col_z>=0)?(3):(2);
	    if (col_y<col_x){
		    coord_order[0]=1;
		    coord_order[1]=0;
	    }
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
   
    
    
    if (set_output_projection) 
	    fprintf(f_out,"#%s\n",GET_MLB(trf->proj_out));
    tmp1=buf_out; /*used to buffer extracted kms output*/
    *tmp1='\0';
    while (0!= fgets(buf, BUFSIZE, f_in)) {
        int    argc, err;
        double coords[3]={NAN,NAN,NAN},store,x,y,z;
	char *current_pos,*end_pointer,*current_pos_out,*current_test_char,sep_char_found,n_read;
	
	int current_col=0, coords_found=0, found_z=0,found_next_col;
	/*struct typ_dec type_out;*/
	lines_read++;
	/*slightly complicated because of that stupid format....*/
	
	/*look for input system label*/
	if (look_for_label){
		argc=sscanf(buf,"#%s",mlb_in_file);
		if (argc==1){
			err=TR_Insert(trf,mlb_in_file,0);
			if (err==TR_OK){
				is_geo_in=IS_GEOGRAPHIC(trf->proj_in);
				mlbs_found++;
				/*special handling of kms-formats*/
				if (is_kms_format){
					coords_to_find=(IS_3D(trf->proj_in))? 3 : 2;
					if (COORD_ORDER(trf->proj_in)==0){
						/* N,E, (Z) */
						coord_order[0]=1;
						coord_order[1]=0;
					}
					else{
						coord_order[0]=0;
						coord_order[1]=1;
					}
					coord_order[2]=2;
					col_x=coord_order[0]+1;
					col_y=coord_order[1]+1;
					col_z=3;
				} /*end kms-format*/
						
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
	
	if (is_kms_format){
		n_read=extract_kms(buf,tmp1,&in_comment);
		/*if not in comment - proceed as normal*/
		if (!in_comment){
			//printf("read: %d\n",n_read);
			*(tmp1+n_read)='\0';
			strcpy(buf,buf_out);
			tmp1=buf_out;
			*tmp1='\0';
		} /*else keep on reading*/
		else {
			if ((tmp1-buf_out)<BUFSIZE-256){
				tmp1+=n_read;
				continue;
			}
			else{
				Report(REP_ERROR,TR_ALLOCATION_ERROR,VERB_LOW,"Couldn't escape comment - aborting!");
				TerminateReport();
				return TR_ALLOCATION_ERROR;
			}
		}
	} /*end KMS-format*/
	/*scan the line for tokens*/
	current_pos=buf;
	/*spool to first column - left whitespace means nothing*/ 
	while (*current_pos && isspace(*current_pos))
		current_pos++;
	/*test if its a whitespace line*/
	if (!(*current_pos)){
		fputs(buf,f_out);
		continue;
	}
	while (coords_found<coords_to_find && *current_pos){
		if (current_col==col_x || current_col==col_y || current_col==col_z){
			if (is_kms_format){ /* or just if we have units at coords - implement this as an option*/
				struct typ_dec type;
				int used;
				char udt[2];
				udt[0]='\0';
				store=sgetg(current_pos,&type,&used,udt);
				/*some test to see if we found a number - check with KE*/
				if (used>0 && udt[0]=='\0'){
					coord_positions[coords_found*2]=current_pos;
					current_pos+=used;
					coord_positions[coords_found*2+1]=current_pos;
					coords[coords_found]=store;
					//Report(REP_DEBUG,0,VERB_HIGH,"%s\n%s\n%.4f",coord_positions[coords_found*2],coord_positions[coords_found*2+1],store);
					coords_found++;
					
					if (current_col==col_z)
						found_z=1;
				}
			} /*end kms-format*/
			else{
				store=strtod(current_pos,&end_pointer);
				/*check if we found a valid number, which could be zero*/
				if (store!=0 || (end_pointer-current_pos)>0){
					coord_positions[coords_found*2]=current_pos;
					current_pos=end_pointer;
					coord_positions[coords_found*2+1]=current_pos;
					coords[coords_found]=store;
					//printf("Current col: %d, coords_found: %d, coord: %.5f\n",current_col,coords_found,store);
					coords_found++;
					if (current_col==col_z)
						found_z=1;
				}
			}
		}
		
		if (coords_found==coords_to_find)
			break;
		
		/*spool to next col*/
		sep_char_found='\0';
		while (*current_pos && (!sep_char_found || !found_next_col)){
			found_next_col=1; /*lets assume that and see if its really true*/
			for(current_test_char=sep_char; *current_test_char; current_test_char++){
				if (*current_pos==*current_test_char){
					if (!sep_char_found)
						sep_char_found=*current_test_char;
					found_next_col=0;
				}
			}
			/*dont go to far - all this could be simplified I guess - but premature optimization....*/
			if (!(sep_char_found && found_next_col))
				current_pos++;
		}/*end spool to next col*/
		current_col++;
		
	} /*end scan line (while)*/
	
	
	if (!found_z)/*insert default*/
		coords[coord_order[2]]=0;
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
		if (lines_read==CHECK_WARNING_RATIO==0 && n_warnings>MAX_WARNINGS && n_warnings*0.25>n_trans_ok)
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
        if (is_geo_in && !is_kms_format){
		coords[coord_order[0]]*=d2r;
		coords[coord_order[1]]*=d2r;
	}
	/*TODO: fixup what is to be writen to log */
	err = TR_Transform(trf,coords+coord_order[0],coords+coord_order[1],coords+coord_order[2],1);
	if (err==TR_OK){
		n_trans_ok++;
		/*perhaps do this in all cases?*/
		if (HAS_HEIGHTS(trf->proj_in) ||  HAS_HEIGHTS(trf->proj_out)){
			TR_GetGeoidName(trf,geoid_name);
			AppendGeoid(geoid_name);
		}
	}
	else{
		n_trans_bad++;
		ERR = err;
		/*write to err log here because \n is in front of err msg - will look bad if output==stdout */
		Report(REP_ERROR,err,VERB_HIGH,"Error: %d, In: %.5f %.5f %.5f ",TR_GetLastError(),x,y,z);
		if (is_stdout) puts("\n");
	}
	/*continue even after an error?*/
	
	/*If geo - multiply to get degrees*/
        if (is_geo_out){
		coords[coord_order[0]]*=r2d;
		coords[coord_order[1]]*=r2d;
		
	}
	
	/*flip xy?*/
	flip_xy=(is_kms_format && COORD_ORDER(trf->proj_in)!=COORD_ORDER(trf->proj_out));
	if (flip_xy){
		int old_order=coord_order[0];
		coord_order[0]=coord_order[1];
		coord_order[1]=old_order;
	}
        /*  Now compose the output string */
	current_pos=buf;
	current_pos_out=buf_out;
	coords_found=0;
	while(*current_pos){
		if (coords_found<coords_to_find && current_pos==coord_positions[2*coords_found]){
			current_pos_out+=sprintf(current_pos_out,"%.8lg",coords[coords_found]);
			current_pos=coord_positions[2*coords_found+1];
			coords_found++;
			//printf("%s, %s\n",buf_out,current_pos);
		}
		else{
			*(current_pos_out++)=*(current_pos++); /*copy char*/
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
	