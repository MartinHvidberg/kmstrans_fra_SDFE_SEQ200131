/* Header for the reporting module for trogr */
#include <stdio.h>
#include <stdarg.h>
void Report(int class_code, int err_no, int verbosity,  const char *frmt, ...);
void SetCallBack( int (*func)(int, int , const char*) );
void ResetReport();
int SetLogName(char *fname);
void SetLogFile(FILE *fp);
int GetErrors();

void SetIgnoreMessages(int ignore); /*temporarily ignore errors*/
void ReportDebugMessages(int onoff);
#define VERB_LOW  (0)
#define VERB_HIGH (1)
enum REPORT_TYPE { REP_DEBUG=0, REP_INFO=1, REP_WARNING=2 , REP_ERROR=3, REP_CRITICAL=4};

