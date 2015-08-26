#include <string.h>
#include "Report.h"

#define MAX_MESSAGES (1100)




static int (*CALL_BACK)(int, int, const char*) =NULL ;
static  int N_LOGGED=0;
static  int N_ERRS=0;
static FILE *log_file=NULL;
static int IGNORE_MESSAGES=0; /* flag to temporarily disable error messages */
static int DEBUG=0;



/* There are different scenarios for reporting:
0: report progress to call_back AND save to log file
1: very verbose stuff only to log file
This is controlled via the verbosity parameter...
*/

 void Report(int class_code, int err_no, int verbosity, const char *frmt, ...){
	char msg[512];
	int written_now=0;
	va_list ap;
	if (IGNORE_MESSAGES || ((class_code)<=REP_DEBUG && !DEBUG))
		return;
	N_ERRS+=(class_code>=REP_ERROR);
	if (verbosity>VERB_LOW && N_LOGGED>MAX_MESSAGES)
		return;
	if (verbosity>VERB_LOW && N_LOGGED==MAX_MESSAGES)
		strcpy(msg,"No more warnings or errors will be reported!\n");
	else{
		va_start(ap, frmt);
		written_now=vsnprintf(msg,512,frmt,ap);
		va_end(ap);
		strcat(msg,"\n");
	}
	N_LOGGED++;
	/* if call back set - handle messages */
	if (CALL_BACK!=NULL && (verbosity==VERB_LOW || log_file==NULL))
		CALL_BACK(class_code, err_no, msg);
	if (log_file!=NULL)
		fprintf(log_file,"%s",msg);
	
	
}

void ResetReport(){
    N_LOGGED=0;
}

void SetIgnoreMessages(int ignore){
	IGNORE_MESSAGES=ignore;
}

void ReportDebugMessages(int on){
	DEBUG=on;
}

 void SetCallBack( int (*func)(int, int , const char*) ){
	CALL_BACK=func;
}

 void SetLogFile(FILE *fp){
	log_file=fp;
}

 int  GetErrors(){
	return N_ERRS;
}


		
	