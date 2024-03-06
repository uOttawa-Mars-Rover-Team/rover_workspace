
//Helper functions used across

//A more understandable way to use strcmp
boolean equalsStr(char* str1, char* str2) {
  return !strcmp(str1, str2);
}//end of equalsStr

//Floats equal up to decimal places
bool floatsEqual(float a, float b, int decimal) {
  return abs(a-b) < 1/pow(10,(decimal));
}//end of floatsEqual
