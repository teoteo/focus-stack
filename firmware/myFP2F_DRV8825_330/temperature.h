//-----------------------------------------------------------------------
// myFocuserPro2 Temperature Routines
// (c) R Brown, 2014-2023, All rights reserved.
//-----------------------------------------------------------------------

#ifndef temperature_h
#define temperature_h

//-----------------------------------------------------------------------
// INCLUDES
//-----------------------------------------------------------------------
#include <Arduino.h>
#include "focuserconfig.h"
#if defined(TEMPERATUREPROBE)
#include <OneWire.h>              // see https://github.com/PaulStoffregen/OneWire
#include <myDallasTemperature.h>  // needed for DS18B20 temperature probe
#endif

//-----------------------------------------------------------------------
// LOCAL DATA
//-----------------------------------------------------------------------

unsigned long lasttempconversion;
byte tprobe1;           // indicate if there is a probe found
float lasttemp = 20.0;  // start temp value
char tprobenotfound[] = "Probe not found";
char checktprobe[] = "Check for Tprobe";

#if defined(TEMPERATUREPROBE)
OneWire oneWirech1(TEMPPIN);  // setup temperature probe
DallasTemperature sensor1(&oneWirech1);
DeviceAddress tpAddress;  // holds address of the temperature probe
#endif                    // #if defined(TEMPERATUREPROBE)

//-----------------------------------------------------------------------
// TEMPERATURE PROBE ROUTINES
//-----------------------------------------------------------------------
void init_temp(void) {
  lasttempconversion = millis();
#if defined(TEMPERATUREPROBE)
  pinMode(TEMPPIN, INPUT);  // Configure GPIO pin for temperature probe
#if defined(SHOWBOOTMSGS)
#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
  lcd->clear();
  lcd->print(checktprobe);
#endif
#if defined(OLEDDISPLAY)
  myoled->clear();
  myoled->println(checktprobe);
#endif
#endif
  DebugPrintln("TMP002");
  sensor1.begin();           // start the temperature sensor1
  sensor1.getDeviceCount();  // should return 1 if probe connected
  if (sensor1.getAddress(tpAddress, 0) == true) {
    tprobe1 = 1;
    DebugPrint("TMP003 ");
    DebugPrintln(tprobe1);
    sensor1.setResolution(tpAddress, myfocuser.tempresolution);  // set probe resolution
    sensor1.requestTemperatures();
  } else {
    DebugPrintln("TMP004");
#if defined(SHOWBOOTMSGS)
#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
    lcd->setCursor(0, 1);
    lcd->print(tprobenotfound);
#endif
#if defined(OLEDDISPLAY)
    myoled->println(tprobenotfound);
#endif
#endif
  }
#endif  // #if defined(TEMPERATUREPROBE)
}

float read_temp() {
  float result = lasttemp;
#if defined(TEMPERATUREPROBE)
  result = sensor1.getTempCByIndex(0);  // get channel 1 temperature, always in celsius
  DebugPrint("TMP005 ");
  DebugPrintln(result);
  if ((result > -40.0) && (result < 80.0))  // check if reading is valid
  {
    lasttemp = result;
  } else {
    result = lasttemp;
  }
#endif  // #if defined(TEMPERATUREPROBE)
  return result;
}

void update_temp(void) {
#if defined(TEMPERATUREPROBE)
  static byte tcchanged = myfocuser.tempcompenabled;  // keeps track if tempcompenabled changes

  if (tprobe1 == 1) {
    static byte requesttempflag = 0;  // start with request
    unsigned long timenow = millis();

    if (((timenow - lasttempconversion) > TEMPREFRESHRATE) || (timenow < lasttempconversion)) {
      static float tempval;
      static float starttemp;  // start temperature to use when temperature compensation is enabled

      lasttempconversion = timenow;  // update time stamp

      if (tcchanged != myfocuser.tempcompenabled) {
        tcchanged = myfocuser.tempcompenabled;
        if (tcchanged == 1) {
          starttemp = read_temp();
        }
      }

      if (requesttempflag) {
        tempval = read_temp();
      } else {
        sensor1.requestTemperatures();
      }

      requesttempflag ^= 1;  // toggle flag

      if (myfocuser.tempcompenabled == 1)  // check for temperature compensation
      {
        if ((abs)(starttemp - tempval) >= 1)  // calculate if temp has moved by more than 1 degree
        {
          long newPos;
          byte temperaturedirection;  // did temperature fall (1) or rise (0)?
          temperaturedirection = (tempval < starttemp) ? 1 : 0;
          if (myfocuser.tcdirection == 0)  // check if tc direction for compensation is inwards
          {
            // temperature compensation direction is in, if a fall then move in else move out
            if (temperaturedirection == 1)  // check if temperature is falling
            {
              // then move inwards
              newPos = ftargetposition - myfocuser.tempcoefficient;
            } else {
              // else move outwards
              newPos = ftargetposition + myfocuser.tempcoefficient;
            }
          } else {
            // temperature compensation direction is out, if a fall then move out else move in
            if (temperaturedirection == 1) {
              newPos = ftargetposition + myfocuser.tempcoefficient;
            } else {
              newPos = ftargetposition - myfocuser.tempcoefficient;
            }
          }
          newPos = (newPos > myfocuser.maxstep) ? myfocuser.maxstep : newPos;
          newPos = (newPos < 0) ? 0 : newPos;
          ftargetposition = newPos;
          starttemp = tempval;  // save this current temp point for future reference
        }                       // end of check for tempchange >= 1
      }                         // end of check for tempcomp enabled
    }                           // end of check for temperature needs updating
  }                             // end of if tprobe
#endif                          // #if defined(TEMPERATUREPROBE)
}

#endif
