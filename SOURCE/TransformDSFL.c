#include <stdio.h>
#include <stdlib.h>
#include "trlib_intern.h"
#include "tr_DSFL.h"
#include "TransformDSFL.h"
#include "Report.h"
int TransformDSFL(char *inname, char *outname, TR *trf)
{	
	int err;
	char msg_str[1024];
	msg_str[0]='\0';
	err=tr_DSFL(inname,outname,trf->proj_out->plab, msg_str);
	if (*msg_str)
		Report(REP_INFO,0,VERB_HIGH,msg_str);
	return err;
} 