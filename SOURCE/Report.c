#include <string.h>
#include "Report.h"

#define MAX_MESSAGES (1000)
#define LEN_GEOID_LIST (1024)
#define MAX_GEOIDS     (18)

static int (*CALL_BACK)(int, int, const char*) =NULL ;
static  int N_LOGGED=0;
static  int N_ERRS=0;
static int N_CHARS_GEOID_LIST=0;
static  char GEOID_LIST[LEN_GEOID_LIST];
static int N_GEOIDS=0;
static  unsigned long GEOID_HASH[MAX_GEOIDS];
static  char LAST_GEOID[64];
static FILE *log_file=NULL;


static unsigned long hash(const char *str)
{
    unsigned long hash =0;
    int c;

    while ((c = *str++))
        hash+=c;

    return hash;
}


/* There are different scenarios for reporting:
0: report progress to call_back AND save to log file
1: very verbose stuff only to log file
This is controlled via the verbosity parameter...
*/

void Report(int class_code, int err_no, int verbosity, const char *frmt, ...){
	char msg[512];
	int written_now=0;
	va_list ap;
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
	/* if call back set - handle messages yourself */
	if (CALL_BACK!=NULL && (verbosity==VERB_LOW || log_file==NULL))
		CALL_BACK(class_code, err_no, msg);
	/* else - write to standard file pointers */
	if (log_file!=NULL)
		fputs(msg,log_file);
	
}

void SetCallBack( int (*func)(int, int , const char*) ){
	CALL_BACK=func;
}

void InitialiseReport(){
	N_GEOIDS=0;
	GEOID_LIST[0]='\0';
	N_CHARS_GEOID_LIST=0;
	LAST_GEOID[0]='\0';
	N_LOGGED=0;
	N_ERRS=0;
}

void TerminateReport(){
	if (log_file!=NULL){
		fclose(log_file);
		log_file=NULL;
	}
}

void SetLogFile(FILE *fp){
	log_file=fp;
}

int GetErrors(){
	return N_ERRS;
}

void AppendGeoid(const char *geoid_name){
	int i,n;
	unsigned long h;
	if (N_GEOIDS==MAX_GEOIDS)
		return;
	/*possibly overflow*/
	if (N_CHARS_GEOID_LIST>LEN_GEOID_LIST-128){
		strcat(GEOID_LIST,"\n... no more space ....");
		N_GEOIDS=MAX_GEOIDS;
		return;
	}
	/*if its the last logged geoid - escape */
	if (!strcmp(LAST_GEOID,geoid_name)) 
		return;
	/*else check if its already logged*/
	h=hash(geoid_name);
	for (i=0; i<N_GEOIDS && h!=GEOID_HASH[i]; i++);
	if (i!=N_GEOIDS)
		return;
	n=strlen(geoid_name);
	if (n>128){
		strcat(GEOID_LIST,"\n...overflow...");
		N_GEOIDS=MAX_GEOIDS;
	}
	GEOID_HASH[N_GEOIDS]=h;
	N_GEOIDS+=1;
	strcat(GEOID_LIST,geoid_name);
	strcat(GEOID_LIST,"\n");
	N_CHARS_GEOID_LIST+=n+1;
	strncpy(LAST_GEOID,geoid_name,64);
	LAST_GEOID[63]='\0';
	return;
}

void LogGeoids(){
	if (N_GEOIDS>0){
		Report(REP_INFO,0,VERB_LOW,"\nGeoids used:");
		Report(REP_INFO,0,VERB_LOW,GEOID_LIST);
	}
}


		
	