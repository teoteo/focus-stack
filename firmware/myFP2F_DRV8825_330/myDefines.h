//-----------------------------------------------------------------------
// myFocuserPro2 Definitions
// (c) R Brown, 2014-2023, All rights reserved.
//-----------------------------------------------------------------------
#ifndef myDefines_h
#define myDefines_h

#include <Arduino.h>
#include "focuserconfig.h"

//-----------------------------------------------------------------------
// GLOBAL DEFINES - DO NOT CHANGE
//-----------------------------------------------------------------------

// Machine states
enum StateMachineStates { State_Idle,
                          State_InitMove,
                          State_ApplyBacklash,
                          State_Moving,
                          State_SetHomePosition,
                          State_FindHomePosition,
                          State_MoveEnded,
                          State_DelayAfterMove,
                          State_FinishedMove };

// myfocuser struct for holding all controller values
struct config_t {
  int validdata;              // if this is 99 then data is valid
  long fposition;             // last focuser position
  long maxstep;               // max steps
  double stepsize;            // the step size in microns, ie 7.2, minimum value is 0.001 microns
  int tempcoefficient;        // steps per degree temperature coefficient value
  int stepmode;               // stepping mode, full, half, 1/4, 1/8. 1/16. 1/32 [1.2.4.8.16.32.64.128.256]
  byte reversedirection;      // reverse direction
  byte coilpower;             // coil pwr
  byte tempmode;              // temperature display mode, Celcius=1, Fahrenheit=0
  byte lcdpagetime;           // refresh rate of display - time each page is displayed for
  byte stepsizeenabled;       // if 1, controller returns step size
  byte lcdupdateonmove;       // update position on lcd when moving
  byte tempresolution;        // resolution of DS18B20 temperature probe
  byte tempcompenabled;       // indicates if temperature compensation is enabled
  byte delayaftermove;        // delay after movement is finished
  byte backlashsteps_in;      // number of backlash steps to apply for IN moves
  byte backlashsteps_out;     // number of backlash steps to apply for OUT moves
  byte focuserdirection;      // keeps track of last focuser move direction
  byte backlash_in_enabled;   // enable or disable backlash compensation for IN
  byte backlash_out_enabled;  // enable or disable backlash compensation for OUT
  byte tcdirection;           // temperature compensation in or out
  byte motorspeed;            // speed of stepper motor
  byte displayenabled;        // status of display, enabled or disabled
  byte pbsteps;               // for 1 push button press, move this amount of motor steps
  byte displayoption;         // which display pages to show. pg0-pg6 [7 pages]
  unsigned long stepdelay;
};

extern struct config_t myfocuser;

#define PBSWITCHESPIN A0  // push button switches
#define INLED A1          // in and out leds
#define OUTLED A2
#define BUZZERPIN A3  // buzzer
#define BTRX 11       // bluetooth adapter HC05
#define BTTX 10
#define TEMPPIN 2   // temperature probe on pin 2, use 4.7k pullup
#define HPSWPIN 12  // home position switch is on D12
#define STEPPERDETECTPIN A7
#define ENCODERSWPIN 11  // rotary encoder push sw on pin 11
#define ROTENCPIN9 9     // rotary encoder is connected to pins 9 and 10
#define ROTENCPIN10 10
#define RECV_PIN 9  // infrared controller signal must be connected to pin 9

#define FOCUSERUPPERLIMIT 2000000000L  // arbitary focuser limit up to 2000000000
#define FOCUSERLOWERLIMIT 1024L        // lowest value that maxsteps can be
#define DEFAULTMAXSTEP 50000L
#define DEFAULTPOSITION 5000L
#define ENDMOVEDELAY 5000L  // Time to wait after a move before disabling coil power

#define HOMESTEPS 200          // Prevent searching for home position switch never returning, this should be > than # of steps between closed and open
#define DEFAULTSTEPSIZE 50.0   // This is the default setting for the step size in microns
#define MAXIMUMSTEPSIZE 100.0  // This is the maximum for stepsize, 100 microns

#define MOVINGIN 0   // direction of focuser moving inwards towards 0
#define MOVINGOUT 1  // direction of focuser moving outwards towards maxstep

#define EEPROMSIZE 1024             // ATMEGA328P 1024 EEPROM
#define EEPROMWRITEINTERVAL 10000L  // interval in milliseconds to wait after a move before writing settings to EEPROM, 10s
#define VALIDDATAFLAG 99            // valid eeprom data flag

#define DISPLAYPAGETIMEMAX 10  // 10s
#define DISPLAYPAGETIMEMIN 4   // 2s
#define LCDUPDATESTEPCOUNT 15  // the number of steps moved which triggers an lcd update when moving, do not make too small
#define LCDADDRESS 0x27        // some LCD displays maybe at 0x3F, use I2Cscanner to find the correct address
#define OLED_ADDR 0x3C         // some OLED displays maybe at 0x3F, use I2Cscanner to find the correct address
#define OLEDREFRESHTIME 1000L  // ogni quanti ms controllare se i valori sul display OLED sono cambiati

#define TEMPREFRESHRATE 1000L  // refresh rate between temperature conversions unless an update is requested via serial command
#define TEMPRESOLUTION 10      // Set the default DS18B20 resolution to 0.25 of a degree 9=0.5, 10=0.25, 11=0.125, 12=0.0625

#define DISPLAYUPDATEWAIT 5000L  // do not update display when moving - update display after move has stopped

#define BTPORTSPEED 9600      // define bluetooth speed, DO NOT CHANGE
#define SERIALPORTSPEED 9600  // 9600, 14400, 19200, 28800, 38400, 57600
#define QUEUELENGTH 20        // number of commands that can be saved in the serial queue
#define EOFSTR '#'
#define SLOWSPEEDJOGDELAY 250  // milliseconds delay for slow speed jogging


//-----------------------------------------------------------------------
// DEBUGGING
//-----------------------------------------------------------------------
// do not change - leave this commented out
//#define DEBUG 1

#if defined(DEBUG)                                     //Macros are usually in all capital letters.
#define DebugPrint(...) Serial.print(__VA_ARGS__)      //DPRINT is a macro, debug print
#define DebugPrintln(...) Serial.println(__VA_ARGS__)  //DPRINTLN is a macro, debug print with new line
#else
#define DebugPrint(...)  //now defines a blank line
#define DebugPrintln(...)
#endif

// do not change - leave this commented out
//#define HPSWDEBUG 1

#if defined(HPSWDEBUG)
#define HPSWDebugPrint(...) Serial.print(__VA_ARGS__)
#define HPSWDebugPrintln(...) Serial.println(__VA_ARGS__)
#else
#define HPSWDebugPrint(...)
#define HPSWDebugPrintln(...)
#endif


#endif
