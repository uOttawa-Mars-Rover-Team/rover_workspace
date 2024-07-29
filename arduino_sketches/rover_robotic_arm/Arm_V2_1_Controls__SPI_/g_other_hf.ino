
//Helper functions used across

//A more understandable way to use strcmp
boolean equalsStr(char* str1, char* str2) {
  return !strcmp(str1, str2);
}//end of equalsStr

//Floats equal up to a difference;
//eg 0.02 and 0.04 equal for a difference of 0.02
bool floatsEqual(float a, float b, float difference) {
  return abs(a-b) <= difference;
}//end of floatsEqual

void writeLED(int red, int green, int blue) {
  digitalWrite(led.R_PIN, 255-red);
  digitalWrite(led.G_PIN, 255-green);
  digitalWrite(led.B_PIN, 255-blue);
}
