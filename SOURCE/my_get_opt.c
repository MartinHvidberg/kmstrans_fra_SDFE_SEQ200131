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
#include <string.h>
#include <stdlib.h>
#include "my_get_opt.h"

/* char *opt must be writeable  e.g. char opt[]="flag_only;look_for_key:" will specify an flag option -flag_only and an option -look_for_key with a value <val>
* key will contain the current key under consideration and val its value, optionally (if found and defined).
* argv[1:] will contain no-switch inputs, while unrecognized flags will be put from argv[argc-1] and downwards....
* final return value will be the number of additonal, uncomsumed inputs.
*/
int my_get_opt(char *opt_definition,int argc,char **argv, char **key, char **val){
	static char *pos=NULL;
	char *lkey,*tmp,**items;
	int i,j,k,has_arg,found_key=0;
	if (pos==NULL)
		pos=opt_definition;
	while (!found_key){
		/*if we have processed all keys*/
		if (!*pos){
			j=k=0;
			*key=NULL;
			*val=NULL;
			items=malloc(sizeof(char*)*(argc-1));
			if (!items)
				return -1;
			for(i=1;i<argc;i++){
				if (argv[i]){
					if (argv[i][0]!='-'){
						items[j]=argv[i];
						j++;
					}
					else{
						items[argc-k-2]=argv[i];
						k++;
					}
				}
				else
					items[i-1]=NULL;
			}
			for(i=1;i<argc;i++) 
				argv[i]=items[i-1];
			/*sort argv*/
			free(items);
			return j;
		}
		lkey=pos;
		has_arg=0;
		while (*pos && *pos!=';' && *pos!=':'){
			pos++;
			if (*pos==':'){
				*(pos++)='\0';
				has_arg=1;
				break;
			}
			if (*pos==';'){
				*(pos++)='\0';
				break;
			}
		}
		*val=NULL;
		*key=lkey;
		found_key=0;
		for(i=1; i<argc; i++){
			if (!argv[i])
				continue;
			tmp=strstr(argv[i],lkey);
			if (tmp && tmp-argv[i]==1 && argv[i][0]=='-'){
				if (!strcmp(argv[i]+1,lkey)){
					found_key=1;
					if (has_arg && i<argc-1 && argv[i+1] && argv[i+1][0]!='-'){
						*val=argv[i+1];
						argv[i+1]=NULL;
					}
					
				}
				else if (has_arg){
					found_key=1;
					*val=argv[i]+1+strlen(lkey);
				}
			if (found_key)
				argv[i]=NULL; /*used*/	
			}
		}
	}
	return 0;
}

	