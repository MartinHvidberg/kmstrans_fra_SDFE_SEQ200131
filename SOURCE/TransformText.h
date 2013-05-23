#include "trlib_api.h"
struct format_options{
int is_kms_format;
int col_x,col_y,col_z,flip_xy;
int set_output_projection;
char *sep_char;
int units_in_output;
char *output_geo_unit; 
char *comments;
};

int TransformText(char *inname, char *outname, TR *trf, struct format_options frmt);
