/* Copyright (c) 2014, Danish Geodata Agency
* (Geodatastyrelsen), gst@gst.dk
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
 #include <string.h>
 #include <ctype.h>
  #include "affine.h"
 
 /*parse a comma-separated list of key,value pairs and return params*/
 affine_params *affine_from_string(char *txt){
	 affine_params *A;
	 int i,j,nr=0,nt=0;
	 char *p1,*p2,*p3;
	 double v;
	 A=calloc(sizeof(affine_params),1);
	 for(i=0;i<3;i++) A->R[3*i+i]=1.0; /*diagonal values*/
	 p1=txt;
	 while(p1 && *p1){
		 /*skip spaces and commas*/
		 while(*p1 && (isspace(*p1) || *p1==','))
			 p1++;
		 if (*p1=='r' || *p1=='t'){
			 p2=strchr(p1,'=');
			 if (p2){
				p2+=1;
				switch (*p1){
					case 'r':
						i=*(p1+1)-'0';
						j=*(p1+2)-'0';
						if (i<3 && i>=0 && j<3 && j>=0){
							v=strtod(p2,&p3);
							if (p3>p2){
								A->R[3*i+j]=v;
								p1=p3;
								printf("Read r%d%d: val: %.4f\n",i,j,v);
							}
							else
								goto ERR;
						}
						else
							goto ERR;
						nr++;
						break;
					case 't':
						i=*(p1+1)-'0';
						if (i<3){
							v=strtod(p2,&p3);
							if (p3>p2){
								A->T[i]=v;
								p1=p3;
								printf("Read t%d, val: %.4f\n",i,v);
							}
						}
						else 
							goto ERR;
				} /*end switch*/
			 }
			 else
				 goto ERR;
		 }
	 }
	 return A;
	 ERR:
		free(A);
		return NULL;
 }
 

 void affine_transformation(affine_params *A, double *x, double *y, double *z){
	 double x0=*x,y0=*y,z0=*z;
	 *x=A->R[0]*x0+A->R[1]*y0+A->R[2]*z0+A->T[0];
	 *y=A->R[3]*x0+A->R[4]*y0+A->R[5]*z0+A->T[1];
	 *z=A->R[6]*x0+A->R[7]*y0+A->R[8]*z0+A->T[2];
}

