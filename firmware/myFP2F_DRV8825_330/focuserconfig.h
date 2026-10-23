//-----------------------------------------------------------------------
// myFocuserPro2 Focuser Config File DRV8825
// (c) R Brown, 2014-2023, All rights reserved.
//-----------------------------------------------------------------------
#ifndef focuserconfig_h
#define focuserconfig_h

#include <Arduino.h>
#include "myBoardDefs.h"


//-----------------------------------------------------------------------
// SPECIFY FOCUS CONTROLLER OPTIONS HERE
//-----------------------------------------------------------------------
// Caution: Do not enable a feature if the associated hardware circuits are
// not fitted on the board. Enable or disable the specific hardware below


// -----------------------------------------------------------------------------
// SPECIFY DRIVER BOARD HERE
// -----------------------------------------------------------------------------
// DRIVER BOARDS - Please specify your driver board here, only 1 can be defined, see #define DRVBRD lines
// Set DRVBRD to the correct driver board, ONLY ONE!!!! - uncomment the correct line for your controller
#define DRVBRD DRV8825
//#define DRVBRD   DRV8825RE
//#define DRVBRD   DRV8825TFT22        // Wiring details in myBoards.h

// Scheda Ardufocus (circuito stampato ufficiale rev1 con driver DRV8825) invece della scheda
// myFocuserPro2. Motore: D4 DIR, D5 STEP, D6 SLEEP (alto = motore alimentato), microstep fissato
// sulla scheda. Pulsanti verso massa su D2 (OUT) e D3 (IN). Sonda DS18B20, OLED, LED e buzzer
// vengono disattivati perché quei piedini sull'Ardufocus hanno altri usi.
// Per compilare per l'Ardufocus togliere il commento alla riga seguente, oppure passare
// -DARDUFOCUSPCB al compilatore (lo fa build_release.sh per firmware-ardufocus.hex).
//#define ARDUFOCUSPCB 1


//-----------------------------------------------------------------------
// INPUT DEVICES
// HOME POSITION SWITCH, STEPPER POWER DETECT, TEMPERATURE PROBE, PUSH BUTTONS
//-----------------------------------------------------------------------
// do NOT uncomment HOMEPOSITIONSWITCH if you do not have the switch fitted
// To enable the HOMEPOSITION SWITCH, uncomment the nextline
//#define HOMEPOSITIONSWITCH 1

// This prevents the stepper motor moving when 12V to the stepper is OFF
// and needs special circuitry or has no effect. To enable the 12V power
// detect to the stepper motor, uncomment the next line (only available on some boards)
//#define STEPPERPWRDETECT 1

// To enable the temperature probe, uncomment next line
#define TEMPERATUREPROBE 1

// To enable a Rotary encoder. uncomment the next line (only available on some boards)
//#define ROTARYENCODER 1

// To enable the Push Buttons for manual focusing, uncomment the next line
#define PUSHBUTTONS 1

// To specify the number of motor steps to move for 1 push button press
// change the 1 value for PB_STEPS below. The max value should be 1/2 the
// focuser step size, [1-255 is the range]. If you set PB_STEPS to 0
// then the push buttons will not move the focuser.
#define PB_STEPS 1

// Pulsante tenuto premuto: il motore si muove senza pause e si ferma appena si rilascia.
// La velocità sale a gradini (periodo = microsecondi fra due passi):
//   da 0 a PB_SPEED2TIME ms        velocità normale del motore (~20 passi/s)
//   fino a PB_SPEED3TIME ms        PB_SPEED2PERIOD (13333 us = 75 passi/s)
//   fino a PB_SPEED4TIME ms        PB_SPEED3PERIOD (4000 us = 250 passi/s)
//   oltre                          PB_SPEED4PERIOD (2500 us = 400 passi/s)
// Se il motore a velocità alta perde passi o fischia senza muoversi, aumentare il periodo.
#if defined(ARDUFOCUSPCB)
// Ardufocus con NEMA 17 da 1,8° e riduttore 26,85:1 (17HS13-0404S-PG27): per un giro d'uscita
// servono ~5370 passi, quindi si parte subito a 200 passi/s, poi 600 dopo 2 s e 1200 dopo 5 s.
#define PB_SPEED2TIME     0L
#define PB_SPEED3TIME     2000L
#define PB_SPEED4TIME     5000L
#define PB_SPEED2PERIOD   5000L
#define PB_SPEED3PERIOD   1667L
#define PB_SPEED4PERIOD   833L
#else
#define PB_SPEED2TIME     5000L
#define PB_SPEED3TIME     10000L
#define PB_SPEED4TIME     20000L
#define PB_SPEED2PERIOD   13333L
#define PB_SPEED3PERIOD   4000L
#define PB_SPEED4PERIOD   2500L
#endif

// Movimenti comandati (app, ASCOM/INDI): rampa di accelerazione e decelerazione.
// Il motore parte a MOVE_STARTSPEED, accelera di MOVE_ACCEL passi/s al secondo fino a
// MOVE_MAXSPEED e rallenta allo stesso modo prima dell'arrivo. Anche lo stop (comando :27#)
// decelera. Con velocità motore "media" o "lenta" la massima è ridotta come nel firmware
// originale (/2 e /2,5). I pulsanti fisici usano invece i gradini PB_SPEED*.
// Se il motore perde passi in partenza o in arrivo, ridurre MOVE_STARTSPEED o MOVE_ACCEL.
#if defined(ARDUFOCUSPCB)
// NEMA 17 con riduttore: la coppia all'uscita abbonda anche dove quella del motore cala.
// Velocità motore "media" e "lenta" nell'app portano la massima a 1000 e 800 passi/s.
#define MOVE_STARTSPEED   200.0   // passi/s
#define MOVE_MAXSPEED     2000.0  // passi/s
#define MOVE_ACCEL        4000.0  // passi/s al secondo
#else
#define MOVE_STARTSPEED   100.0   // passi/s
#define MOVE_MAXSPEED     400.0   // passi/s (motore 14HM11-0404S, 25 ohm: a 12 V oltre perde coppia)
#define MOVE_ACCEL        2000.0  // passi/s al secondo
#endif


//-----------------------------------------------------------------------
// OUTPUT DEVICES
// BUZZER AND LEDS
//-----------------------------------------------------------------------
// Buzzer is used as a power on boot test, and with push-buttons as a
// feedback for push button operation
// To enable the buzzer, uncomment the next line
#define BUZZER 1

// To enable the IN-OUT LEDS, uncomment the next line
#define INOUTLEDS 1


//-----------------------------------------------------------------------
// CONTROLLER CONNECTION OPTIONS: BLUETOOTH, CONTROLLERISAMICRO
//-----------------------------------------------------------------------
// To enable bluetooth, uncomment the next line  (only available on some boards)
// #define BLUETOOTH 1

// provided by IL, enables the serialEventRun function for a Micro
// To enable support when usng a Micro instead of a Nano, uncomment the next line
//#define CONTROLLERISAMICRO 1


//-----------------------------------------------------------------------
// SOFTWARE OPTIONS
//-----------------------------------------------------------------------
// To enable the super slow jogging, uncomment the next line
//#define SUPERSLOWJOG 1

// To enable the start boot screen showing startup messages, uncomment the next line
//#define SHOWBOOTMSGS 1


//-----------------------------------------------------------------------
// LCD DISPLAY
//-----------------------------------------------------------------------
// only uncomment one of the following LCDxxxx lines depending upon your lcd type
//#define LCD1602             1             // 16 character, 2 lines
//#define LCD1604           2             // 16 character, 4 lines
//#define LCD2004           3             // 20 character, 4 lines


//-----------------------------------------------------------------------
// OLED DISPLAY
//-----------------------------------------------------------------------
// To enable the OLED DISPLAY uncomment the next line
#define OLEDDISPLAY 1

// only uncomment one of the following USE_SSxxxx lines depending upon your lcd type
// For the OLED 128x64 0.96" display using the SSD1306 driver, uncomment the following line
#define USE_SSD1306 1

// For the OLED 128x64 1.3" display using the SSH1106 driver, uncomment the following line
//#define USE_SSH1106   2


//-----------------------------------------------------------------------
// TFT22 DISPLAY
//-----------------------------------------------------------------------
// To enable a TFT22 display on the TFT22 stripboard, uncomment the next line
//#define TFTDISPLAY 3


//-----------------------------------------------------------------------
// USER CONFIGURATION END: DO NOT EDIT BELOW THIS LINE
//-----------------------------------------------------------------------

#if defined(ARDUFOCUSPCB)
#undef TEMPERATUREPROBE  // D2 è il pulsante OUT
#undef OLEDDISPLAY
#undef INOUTLEDS         // A1 è il potenziometro, A2 un pulsante
#undef BUZZER
#define FSBOARD 1        // risposta al comando :98#
#else
#define FSBOARD 0        // scheda myFocuserPro2 DRV8825
#endif


//-----------------------------------------------------------------------
// HARDWARE OPTIONS CHECKS: DO NOT CHANGE
//-----------------------------------------------------------------------
// DO NOT CHANGE

#if !defined(PB_STEPS)
#define PB_STEPS 1
#endif

// check DRVBRD
#if !defined(DRVBRD)
#error "DRVBRD is not defined in focuserconfig.h"
#endif

//-----------------------------------------------------------------------
// check display
//-----------------------------------------------------------------------
#if defined(LCD1602)
#if defined(LCD1604)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD2004)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(OLEDDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(TFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(UTFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(NOKIADISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#endif  // LCD1602

// LCD1604
#if defined(LCD1604)
#if defined(LCD1602)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD2004)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(OLEDDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(TFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(UTFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(NOKIADISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#endif  // LCD1604

// LCD2004
#if defined(LCD2004)
#if defined(LCD1602)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD1604)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(OLEDDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(TFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(UTFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(NOKIADISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#endif  // LCD2004

// OLEDDISPLAY
#if defined(OLEDDISPLAY)
#if defined(LCD1602)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD1604)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD2004)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(TFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(UTFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(NOKIADISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#endif  // OLEDDISPLAY

// TFTDISPLAY
#if defined(TFTDISPLAY)
#if defined(LCD1602)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD1604)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD2004)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(OLEDDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(UTFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(NOKIADISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#endif  // TFTDISPLAY

// UTFTDISPLAY
#if defined(UTFTDISPLAY)
#if defined(LCD1602)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD1604)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD2004)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(OLEDDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(TFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(NOKIADISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#endif  // UTFTDISPLAY

// NOKIADISPLAY
#if defined(NOKIADISPLAY)
#if defined(LCD1602)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD1604)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(LCD2004)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(OLEDDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(UTFTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#if defined(TDTDISPLAY)
#error "More than 1 display type is enabled focuserconfig.h"
#endif
#endif  // NOKIADISPLAY

// check OLED display
#if defined(OLEDDISPLAY)
#if defined(USE_SSD1306) && defined(USE_SSH1106)
#error "Both USE_SSD1306 and USE_SSH1106 is defined, only enable one if using an OLEDDISPLAY"
#endif
#if !defined(USE_SSD1306) && !defined(USE_SSH1106)
#error "You must enable either USE_SSD1306 and USE_SSH1106 for an OLEDDISPLAY"
#endif
#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
#error "You cannot enable both LCDxxxx and OLEDDISPLAY at the same time"
#endif
#if defined(TFTDISPLAY)
#error "You cannot have OLEDDISPLAY AND TFTDISPLAY enabled at the same time"
#endif
#endif


#endif
