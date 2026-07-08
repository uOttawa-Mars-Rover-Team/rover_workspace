#include <Arduino.h>

#if defined(APP_RA)
    #include "AppRA.h"
#elif defined(APP_GNC)
    #include "AppGNC.h"
#else
    #error "No APP_RA or APP_GNC build flag defined. Build with -e AppRA or -e AppGNC."
#endif

void setup() {
#if defined(APP_RA)
    appRA_setup();
#elif defined(APP_GNC)
    appGNC_setup();
#endif
}

void loop() {
#if defined(APP_RA)
    appRA_loop();
#elif defined(APP_GNC)
    appGNC_loop();
#endif
}
