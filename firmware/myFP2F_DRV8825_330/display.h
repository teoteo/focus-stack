//-----------------------------------------------------------------------
// myFocuserPro2 Display Routines
// (c) R Brown, 2014-2023, All rights reserved.
//-----------------------------------------------------------------------
#ifndef display_h
#define display_h

#include <Arduino.h>
#include "focuserconfig.h"

#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
#include <Wire.h>  // needed for I2C, installed when installing the Arduino IDE
#include <LCD.h>
#include <LiquidCrystal_I2C.h>  // needed for LCD, see https://bitbucket.org/fmalpartida/new-liquidcrystal/downloads
LiquidCrystal_I2C* lcd;
#endif  // #if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)

#if defined(OLEDDISPLAY)
#include <Wire.h>  // needed for I2C, installed when installing the Arduino IDE
#include <mySSD1306Ascii.h>
#include <mySSD1306AsciiWire.h>
SSD1306AsciiWire* myoled;  // loop variable used in updating lcd when moving
#endif                     // #if defined(OLEDDISPLAY)

#if defined(UTFTDISPLAY)
#include <myUTFT.h>  // Hardware-specific for 2.2" TFT
UTFT* mytft;         // insufficient memory to use more than one font, must be uppercase only
extern uint8_t SmallFont[];
#endif  // #if defined(UTFTDISPLAY)

#if defined(NOKIADISPLAY)
#include <LCD5110_Basic.h>
LCD5110* nokialcd;
extern uint8_t SmallFont[];
#endif  // #if defined(NOKIADISPLAY)

#if defined(TFTDISPLAY)
#include <stdint.h>
#include <myTFTv2.h>
#include <SPI.h>
#endif  // #if defined(TFTDISPLAY)

//-----------------------------------------------------------------------
// extern data and routines
//-----------------------------------------------------------------------
extern byte tprobe1;
extern float lasttemp;
extern float read_temperature(byte);

//-----------------------------------------------------------------------
// Variables
//-----------------------------------------------------------------------

#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
char clearstr[] = "               ";
char postxt[] = "POS=";
char targtxt[] = "TAR=";
#endif

#if defined(OLEDDISPLAY)
char currentpostxt[] = "Position= ";
char targetpostxt[] = "Target  = ";
char coilpwrtxt[] = "Coil.Pwr= ";
char revdirtxt[] = "Rev.Dir = ";
#endif

#if defined(UTFTDISPLAY)
char tempString[12];
char copystr[] = "R.BROWN 2017";
char fstr[] = "F";
char cstr[] = "C";
char slowstr[] = "SLOW  ";
char medstr[] = "MEDIUM";
char faststr[] = "FAST  ";
char cptxt[] = "CURRENT POSITION  = ";
char tptxt[] = "TARGET POSITION   = ";
char cpwrtxt[] = "COIL POWER        = ";
char rdtxt[] = "REVERSE DIRECTION = ";
char smtxt[] = "STEP MODE         = ";
char tetxt[] = "TEMPERATURE       = ";
char mstxt[] = "MOTOR SPEED       = ";
char matxt[] = "MAX STEPS         = ";
char clearstr[] = "               ";
#endif

#if defined(TFTDISPLAY)
// DO NOT CHANGE
// Text Colors for TFT
#define CPositionColor BRIGHT_RED
#define TPositionColor RED
#define CoilPwrColor YELLOW
#define ReverseColor BLUE
#define StepModeColor GREEN
#define TempColor WHITE
#define MotorSpeedColor CYAN
#define MaxStepsColor GRAY1
#define Portrait1 0
#define Landscape1 1
#define Portrait2 2
#define Landscape2 3
#define rotation Portrait2
#define TextSize 2
char tempString[12];
char verstr[] = "Version ";
char copystr[] = "(c) R. BROWN 2017";
char headerstr[] = "myFocuserPro2";
char coilpwrstr[] = "CoilPwr   = ";
char reversestr[] = "Reverse   = ";
char stepmodestr[] = "Stepmode  = ";
char tempstr1[] = "Temp      = ";
char fstr[] = "F";
char cstr[] = "C";
char mspeedstr[] = "MotorSpd  = ";
char slowstr[] = "Slow  ";
char medstr[] = "Medium";
char faststr[] = "Fast";
char maxstepstr[] = "MaxSteps  = ";
char currentpos[] = "CurrentPos= ";
char targetpos[] = "Target Pos= ";
char ontxt[] = "ON  ";
char offtxt[] = "OFF";
#endif

unsigned long lastdisplayupdate;

//-----------------------------------------------------------------------
// Code
//-----------------------------------------------------------------------

#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
void initlcd(void) {
  lastdisplayupdate = millis();
  Wire.begin();
  lcd = new LiquidCrystal_I2C(LCDADDRESS, 2, 1, 0, 4, 5, 6, 7, 3, POSITIVE);
#if defined(LCD1602)
  lcd->begin(16, 2);
#endif  // #if defined(LCD1602)
#if defined(LCD1604)
  lcd->begin(16, 4);
#endif  // #if defined(LCD1604)
#if defined(LCD2004)
  lcd->begin(20, 4);
#endif  // #if defined(LCD2004)
  lcd->setBacklight(HIGH);
  lcd->clear();  // print the title of program and copyright message to lcd
#if defined(SHOWBOOTMSGS)
  lcd->print(programName);
  lcd->setCursor(0, 1);
  lcd->print(programVersion);
  delay(250);
#endif  // #if defined(SHOWBOOTMSGS)
}

#if defined(LCD2004)
void displaylcd2004pg1() {
  lcd->print(postxt);
  lcd->print(fcurrentposition);
  lcd->setCursor(0, 1);
  lcd->print(targtxt);
  lcd->print(ftargetposition);
  lcd->setCursor(0, 2);
  lcd->print("CPwr=");
  lcd->print(myfocuser.coilpower);

  lcd->setCursor(10, 2);
  lcd->print("RDir=");
  lcd->print(myfocuser.reversedirection);
  lcd->setCursor(0, 3);
  lcd->print("Temp=");
  if (tprobe1 == 0) {
    lcd->print("--");
  } else {
    float tempval = lasttemp;
    if (myfocuser.tempmode == 0)  // if fahrenheight
    {
      tempval = (tempval * 1.8) + 32;
    }
    lcd->print(tempval);
  }
}

void displaylcd2004pg2() {
  lcd->setCursor(0, 0);
  lcd->print("MSpd    =");
  lcd->print(myfocuser.motorspeed);

  lcd->setCursor(0, 1);
  lcd->print("TempCoff=");
  lcd->print(myfocuser.tempcoefficient);

  lcd->setCursor(0, 2);
  lcd->print("TComp  =");
  lcd->print(myfocuser.tempcompenabled);

  lcd->setCursor(0, 3);
  lcd->print("Tmode  =");
  if (myfocuser.tempmode == 1) {
    lcd->print("Celsius");
  } else {
    lcd->print("Fahren");
  }
}

void displaylcd2004pg3() {
  lcd->setCursor(0, 0);
  lcd->print("MStep=");
  lcd->print(myfocuser.maxstep);
  lcd->setCursor(0, 1);
  lcd->print("StepM=");
  lcd->print(myfocuser.stepmode);
  lcd->setCursor(0, 2);
  lcd->print("BLIN =");
  lcd->print(myfocuser.backlash_in_enabled);
  lcd->setCursor(9, 2);
  lcd->print(myfocuser.backlashsteps_in);
  lcd->setCursor(0, 3);
  lcd->print("BLOUT=");
  lcd->print(myfocuser.backlash_out_enabled);
  lcd->setCursor(9, 3);
  lcd->print(myfocuser.backlashsteps_out);
}
#endif  // #if defined(LCD2004)

#if defined(LCD1604)
void displaylcd1604pg1() {
  lcd->print(postxt);
  lcd->print(fcurrentposition);
  lcd->setCursor(0, 1);
  lcd->print(targtxt);
  lcd->print(ftargetposition);
  lcd->setCursor(0, 2);
  lcd->print("CPwr=");
  lcd->print(myfocuser.coilpower);

  lcd->setCursor(7, 2);
  lcd->print("RDir=");
  lcd->print(myfocuser.reversedirection);

  lcd->setCursor(0, 3);
  lcd->print("MSpd=");
  lcd->print(myfocuser.motorspeed);

  lcd->setCursor(7, 3);
  lcd->print("StepM=");
  lcd->print(myfocuser.stepmode);
}

void displaylcd1604pg2() {
  lcd->setCursor(0, 0);
  lcd->print("Temp    =");
  if (tprobe1 == 0) {
    lcd->print("--");
  } else {
    float tempval = lasttemp;
    if (myfocuser.tempmode == 0) {
      tempval = (tempval * 1.8) + 32;
    }
    lcd->print(tempval);
  }
  lcd->setCursor(0, 1);
  lcd->print("TempCoff=");
  lcd->print(myfocuser.tempcoefficient);
  lcd->setCursor(0, 2);
  lcd->print("TempComp=");
  lcd->print(myfocuser.tempcompenabled);
  lcd->setCursor(0, 3);
  lcd->print("TempMode=");
  if (myfocuser.tempmode == 1) {
    lcd->print("Celsius");
  } else {
    lcd->print("Fahren");
  }
}

void displaylcd1604pg3() {
  lcd->setCursor(0, 0);
  lcd->print("MaxStep =");
  lcd->print(myfocuser.maxstep);
  lcd->setCursor(0, 1);
  lcd->print("BLIN =");
  lcd->print(myfocuser.backlash_in_enabled);
  lcd->setCursor(9, 1);
  lcd->print(myfocuser.backlashsteps_in);
  lcd->setCursor(0, 2);
  lcd->print("BLOUT=");
  lcd->print(myfocuser.backlash_out_enabled);
  lcd->setCursor(9, 2);
  lcd->print(myfocuser.backlashsteps_out);
}

#endif  // #if defined(LCD1604)

#if defined(LCD1602)
void displaylcd1602pg1() {
  lcd->print(postxt);
  lcd->print(fcurrentposition);
  lcd->setCursor(0, 1);
  lcd->print(targtxt);
  lcd->print(ftargetposition);
}

void displaylcd1602pg2() {
  lcd->setCursor(0, 0);
  lcd->print("CoilPwr=");
  lcd->print(myfocuser.coilpower);

  lcd->setCursor(0, 1);
  lcd->print("RevDir =");
  lcd->print(myfocuser.reversedirection);
}

void displaylcd1602pg3() {
  // display values on LCD1602
  lcd->print("Temp   =");
  if (tprobe1 == 0) {
    lcd->print("--");
  } else {
    float tempval = lasttemp;
    if (myfocuser.tempmode == 0) {
      tempval = (tempval * 1.8) + 32;
    }
    lcd->print(tempval);
  }
  lcd->setCursor(0, 1);
  lcd->print("MaxStep=");
  lcd->print(myfocuser.maxstep);
}

void displaylcd1602pg4() {
  lcd->print("Speed   =");
  lcd->print(myfocuser.motorspeed);
  lcd->setCursor(0, 1);
  lcd->print("StepMode=");
  lcd->print(myfocuser.stepmode);
}

void displaylcd1602pg5() {
  lcd->setCursor(0, 0);
  lcd->print("TempComp=");
  lcd->print(myfocuser.tempcompenabled);
  lcd->setCursor(0, 1);
  lcd->print("TempMode=");
  if (myfocuser.tempmode == 1) {
    lcd->print("Celsius");
  } else {
    lcd->print("Fahren");
  }
}

void displaylcd1602pg6() {
  lcd->setCursor(0, 0);
  lcd->print("BLIN =");
  lcd->print(myfocuser.backlash_in_enabled);
  lcd->setCursor(9, 0);
  lcd->print(myfocuser.backlashsteps_in);
  lcd->setCursor(0, 1);
  lcd->print("BLOUT=");
  lcd->print(myfocuser.backlash_out_enabled);
  lcd->setCursor(9, 1);
  lcd->print(myfocuser.backlashsteps_out);
}
#endif  // #if defined(LCD1602)

void updatepositionlcd() {
  lcd->setCursor(0, 0);
  lcd->print(clearstr);
  lcd->setCursor(0, 0);
  lcd->print(postxt);
  lcd->print(fcurrentposition);
  lcd->setCursor(0, 1);
  lcd->print(clearstr);
  lcd->setCursor(0, 1);
  lcd->print(targtxt);
  lcd->print(ftargetposition);
}

void UpdateLCD(void) {
  unsigned static int displaybitmask = 1;
  unsigned long timenow = millis();

  if ((timenow - lastdisplayupdate) > ((unsigned long)(myfocuser.lcdpagetime * 1000)) || (timenow < lastdisplayupdate)) {
    DebugPrintln("DIS002");
    lastdisplayupdate = timenow;  // update the timestamp
    lcd->clear();                 // clrsc
    unsigned int page = 0;
    String mypage = String(myfocuser.displayoption, BIN);
#if defined(LCD1602)
    for (unsigned int i = 0; i < mypage.length(); i++) {
      page *= 2;
      if (mypage[i] == '1') {
        page++;
      }
    }
    // find the next page to display
    while ((page & displaybitmask) == 0)  // mask off one bit at a time
    {
      displaybitmask *= 2;      // skip this page as it is not enabled
      if (displaybitmask > 32)  // pages 1 to 6 [note: displaybitmask is multiples of 2]
      {
        displaybitmask = 1;
        break;
      }
    }                        // while((screenmask & displaybitmask) == 0)
    switch (displaybitmask)  // displaybitmask is now the page to display, 1=pg1, 2=pg2, 4=pg3, 8=pg4 etc
    {
      case 1: displaylcd1602pg1(); break;
      case 2: displaylcd1602pg2(); break;
      case 4: displaylcd1602pg3(); break;
      case 8: displaylcd1602pg4(); break;
      case 16: displaylcd1602pg5(); break;
      case 32: displaylcd1602pg6(); break;
      default: displaylcd1602pg1(); break;
    }
    displaybitmask *= 2;  // next page
#endif                    // #if defined(LCD1602)
#if defined(LCD1604)
    for (unsigned int i = 0; i < mypage.length(); i++) {
      page *= 2;
      if (mypage[i] == '1') {
        page++;
      }
    }
    // find the next page to display
    while ((page & displaybitmask) == 0)  // mask off one bit at a time
    {
      displaybitmask *= 2;     // skip this page as it is not enabled
      if (displaybitmask > 4)  // pages 1 to 3
      {
        displaybitmask = 1;
        break;
      }
    }                        // while((screenmask & displaybitmask) == 0)
    switch (displaybitmask)  // displaybitmask is now the page to display, 1=pg1, 2=pg2, 4=pg3, 8=pg4 etc
    {
      case 1: displaylcd1604pg1(); break;
      case 2: displaylcd1604pg2(); break;
      case 4: displaylcd1604pg3(); break;
      default: displaylcd1604pg1(); break;
    }
    displaybitmask *= 2;  // next page
#endif                    // #if defined(LCD1604)
#if defined(LCD2004)
    for (unsigned int i = 0; i < mypage.length(); i++) {
      page *= 2;
      if (mypage[i] == '1') {
        page++;
      }
    }
    // find the next page to display
    while ((page & displaybitmask) == 0)  // mask off one bit at a time
    {
      displaybitmask *= 2;     // skip this page as it is not enabled
      if (displaybitmask > 4)  // pages 1 to 3
      {
        displaybitmask = 1;
        break;
      }
    }                        // while((screenmask & displaybitmask) == 0)
    switch (displaybitmask)  // displaybitmask is now the page to display, 1=pg1, 2=pg2, 4=pg3, 8=pg4 etc
    {
      case 1: displaylcd2004pg1(); break;
      case 2: displaylcd2004pg2(); break;
      case 4: displaylcd2004pg3(); break;
      default: displaylcd2004pg1(); break;
    }
    displaybitmask *= 2;  // next page
#endif                    // #if defined(LCD2004)
  }
}
#endif  // LCD2004

// OLED DISPLAY ROUTINES
#if defined(OLEDDISPLAY)
void initoled(void) {
  lastdisplayupdate = millis();
  Wire.begin();
  // Setup the OLED, screen size is 128 x 64, so using characters at 6x8 this gives 21chars across and 8 lines down
  myoled = new SSD1306AsciiWire();  // instantiate the OLED object
  // myoled->set2X(); // Doble size text
#ifdef USE_SSD1306
  // For the OLED 128x64 0.96" display using the SSD1306 driver
  myoled->begin(&Adafruit128x64, OLED_ADDR);
#endif  // #ifdef USE_SSD1306
#ifdef USE_SSH1106
  // For the OLED 128x64 1.3" display using the SSH1106 driver
  myoled->begin(&SH1106_128x64, OLED_ADDR);
#endif  // #ifdef USE_SSH1106
  myoled->set400kHz();
  myoled->setFont(Adafruit5x7);
  myoled->clear();            // clrscr OLED
  myoled->Display_Normal();   // black on white
  myoled->Display_On();       // display ON
  myoled->Display_Rotate(0);  // portrait, not rotated
  myoled->Display_Bright();
#if defined(SHOWBOOTMSGS)
  myoled->println(programName);  // print startup screen
  myoled->println(programVersion);
  myoled->println(ProgramAuthor);
  delay(250);
#endif  // #if defined(SHOWBOOTMSGS)
}

void displaylcdpage0(void)  // displaylcd screen
{
  // Scrive sopra al contenuto precedente senza cancellare lo schermo (niente sfarfallio):
  // clearToEOL() toglie solo le cifre rimaste quando il numero si accorcia.
  myoled->home();
  myoled->print(currentpostxt);
  myoled->set2X();
  myoled->print(fcurrentposition);
  myoled->clearToEOL();
  myoled->set1X();
  myoled->setCursor(0, 3);

  myoled->print(targetpostxt);
  myoled->set2X();
  myoled->print(ftargetposition);
  myoled->clearToEOL();
  myoled->set1X();

 // Temperature
  myoled->setCursor(0, 6);
  myoled->print("Temp (C)= ");
  myoled->set2X();
  myoled->print(lasttemp);
  myoled->clearToEOL();
  myoled->set1X();

  // myoled->print(coilpwrtxt);
  // myoled->print(myfocuser.coilpower);
  // myoled->clearToEOL();
  // myoled->println();

  // myoled->print(revdirtxt);
  // myoled->print(myfocuser.reversedirection);
  // myoled->clearToEOL();
  // myoled->println();

  // stepmode setting
  // myoled->print("StepMode= ");
  // myoled->print(myfocuser.stepmode);
  // myoled->clearToEOL();
  // myoled->println();

  // Temperature
  // myoled->print("Temp    = ");
  // myoled->print(lasttemp);
  // myoled->print(" c");
  // myoled->clearToEOL();
  // myoled->println();

  // Motor Speed
  // myoled->print("MotorSpd= ");
  // myoled->print(myfocuser.motorspeed);
  // myoled->clearToEOL();
  // myoled->println();

  // MaxSteps
  // myoled->print("MaxSteps= ");
  // myoled->print(myfocuser.maxstep);
  // myoled->clearToEOL();
  // myoled->println();
}

void displaylcdpage1(void) {
  // temperature compensation
  myoled->print("TComp Steps = ");
  myoled->print(myfocuser.tempcoefficient);
  myoled->clearToEOL();
  myoled->println();
  myoled->print("TComp State = ");
  myoled->print(myfocuser.tempcompenabled);
  myoled->clearToEOL();
  myoled->println();
  myoled->print("TComp Dir   = ");
  myoled->print(myfocuser.tcdirection);
  myoled->clearToEOL();
  myoled->println();
  myoled->print("Backlash In = ");
  myoled->print(myfocuser.backlash_in_enabled);
  myoled->clearToEOL();
  myoled->println();
  myoled->print("Backlash Out= ");
  myoled->print(myfocuser.backlash_out_enabled);
  myoled->clearToEOL();
  myoled->println();
  myoled->print("Backlash In#= ");
  myoled->print(myfocuser.backlashsteps_in);
  myoled->clearToEOL();
  myoled->println();
  myoled->print("Backlash Ou#= ");
  myoled->print(myfocuser.backlashsteps_out);
  myoled->clearToEOL();
  myoled->println();
#ifndef BLUETOOTH
  myoled->print("Serial Mode");
#else
  myoled->print("Bluetooth Mode");
#endif  // #ifndef BLUETOOTH
  myoled->clearToEOL();
}

void updatepositionoled(void) {
  // myoled->setCursor(0, 0);
  // myoled->print(currentpostxt);
  // myoled->print(fcurrentposition);
  // myoled->clearToEOL();
  // myoled->println();

  // myoled->print(targetpostxt);
  // myoled->print(ftargetposition);
  // myoled->clearToEOL();
  // myoled->println();


  myoled->home();
  myoled->print(currentpostxt);
  myoled->set2X();
  myoled->print(fcurrentposition);
  myoled->clearToEOL();
  myoled->set1X();
  myoled->setCursor(0, 3);

  myoled->print(targetpostxt);
  myoled->set2X();
  myoled->print(ftargetposition);
  myoled->clearToEOL();
  myoled->set1X();
}

void UpdateOLED(void) {
  // Prima la schermata veniva cancellata e ridisegnata ogni lcdpagetime secondi (sfarfallio).
  // Ora si controlla ogni OLEDREFRESHTIME ms e si riscrive solo se un valore è cambiato.
  static long shownposition = -1;
  static long showntarget = -1;
  static float showntemp = -1000.0;
  unsigned long timenow = millis();

  if ((timenow - lastdisplayupdate) > OLEDREFRESHTIME) {
    lastdisplayupdate = timenow;  // update the timestamp
    if ((fcurrentposition != shownposition) || (ftargetposition != showntarget) || (lasttemp != showntemp)) {
      DebugPrintln("DIS002");
      shownposition = fcurrentposition;
      showntarget = ftargetposition;
      showntemp = lasttemp;
      displaylcdpage0();
    }
  }
}
#endif  // OLEDDISPLAY

#if defined(NOKIADISPLAY)
void initnokia(void) {
  lastdisplayupdate = millis();
  nokialcd = new LCD5110(8, 9, 10, 11, 12);
  nokialcd->InitLCD();
  nokialcd->setFont(SmallFont);
  nokialcd->clrScr();  // print the title of program and copyright message to lcd
#if defined(SHOWBOOTMSGS)
  nokialcd->print(programName, LEFT, 0);
  nokialcd->print(programVersion, LEFT, 8);
  delay(250);
#endif  // #if defined(SHOWBOOTMSGS)
}

void displaynokiapg1() {
  String str;
  char tempString[8];
  float tempval = 20.0;

  str = "Posn= " + String(fcurrentposition);
  nokialcd->print(str, LEFT, 0);
  str = "Targ= " + String(ftargetposition);
  nokialcd->print(str, LEFT, 8);
  str = "CPwr= ";
  if (myfocuser.coilpower == 1) {
    str = str + yesstr;
  } else {
    str = str + nostr;
  }
  nokialcd->print(str, LEFT, 16);
  str = "RDir= ";
  if (myfocuser.reversedirection == 1) {
    str = str + yesstr;
  } else {
    str = str + nostr;
  }
  nokialcd->print(str, LEFT, 24);

  str = "Temp= ";
  if (tprobe1 == 0) {
    str = str + "--";
  } else {
    tempval = lasttemp;
    if (myfocuser.tempmode == 1) {
      /* 4 is mininum width, 2 is precision; float value is copied onto str_temp*/
      dtostrf(tempval, 4, 2, tempString);
      str = str + tempString;
    } else {
      tempval = (tempval * 1.8) + 32;
      dtostrf(tempval, 4, 2, tempString);
      str = str + tempString;
    }
  }
  nokialcd->print(str, LEFT, 32);

  switch (myfocuser.motorspeed) {
    case SLOW: str = "MSpd= Slow"; break;
    case MED: str = "MSpd= Med"; break;
    case FAST: str = "MSpd= Fast"; break;
  }
  nokialcd->print(str, LEFT, 40);
}

void displaynokiapg2() {
  String str;
  char tempString[8];

  str = "StepMd=" + String(myfocuser.stepmode);
  nokialcd->print(str, LEFT, 0);

  // stepsize
  str = "StepSi= ";
  /* 4 is mininum width, 2 is precision; float value is copied onto str_temp*/
  dtostrf(myfocuser.stepsize, 4, 2, tempString);
  str = str + tempString;
  nokialcd->print(str, LEFT, 8);

  str = "Maxpos=" + String(myfocuser.maxstep);
  nokialcd->print(str, LEFT, 16);

  // temp comp state
  if (myfocuser.tempcompenabled == 1) {
    str = "TComp =Yes";
  } else {
    str = "TComp =No";
  }
  nokialcd->print(str, LEFT, 24);

  // temp coefficient
  str = "TCoeff= ";
  /* 4 is mininum width, 2 is precision; float value is copied onto str_temp*/
  dtostrf(myfocuser.tempcoefficient, 4, 2, tempString);
  str = str + tempString;
  nokialcd->print(str, LEFT, 32);
}

void displaynokiapg3() {
  String str;
  char tempString[8];

  str = "BLIn = ";
  if (myfocuser.backlash_in_enabled == 0) {
    str = str + '0';
  } else {
    str = str + '1';
  }
  nokialcd->print(str, LEFT, 0);

  str = "BLOut= ";
  if (myfocuser.backlash_out_enabled == 0) {
    str = str + '0';
  } else {
    str = str + '1';
  }
  nokialcd->print(str, LEFT, 8);

  str = "BLIn#= " + String(myfocuser.backlashsteps_in);
  nokialcd->print(str, LEFT, 16);

  str = "BLOu#= " + String(myfocuser.backlashsteps_out);
  nokialcd->print(str, LEFT, 24);
}

void updatepositionnokia() {
  String str;
  char tmpStr[] = "               ";

  nokialcd->print(tmpStr, LEFT, 0);
  str = "POS=" + String(fcurrentposition);
  nokialcd->print(str, LEFT, 0);

  nokialcd->print(tmpStr, LEFT, 0);
  str = "TAR=" + String(ftargetposition);
  nokialcd->print(str, LEFT, 8);
}

void UpdateNOKIA(void) {
  unsigned static int displaybitmask = 1;
  unsigned long timenow = millis();

  if ((timenow - lastdisplayupdate) > ((unsigned long)(myfocuser.lcdpagetime * 1000)) || (timenow < lastdisplayupdate)) {
    DebugPrintln("DIS002");
    lastdisplayupdate = timenow;  // update the timestamp
    nokialcd->clrScr();           // clrscr
    unsigned int page = 0;
    String mypage = String(myfocuser.displayoption, BIN);
    for (unsigned int i = 0; i < mypage.length(); i++) {
      page *= 2;
      if (mypage[i] == '1') {
        page++;
      }
    }
    // find the next page to display
    while ((page & displaybitmask) == 0)  // mask off one bit at a time
    {
      displaybitmask *= 2;     // skip this page as it is not enabled
      if (displaybitmask > 4)  // pages 1 to 3
      {
        displaybitmask = 1;
        break;
      }
    }                        // while((screenmask & displaybitmask) == 0)
    switch (displaybitmask)  // displaybitmask is now the page to display, 1=pg1, 2=pg2, 4=pg3, 8=pg4 etc
    {
      case 1: displaynokiapg1(); break;
      case 2: displaynokiapg2(); break;
      case 4: displaynokiapg3(); break;
      default: displaynokiapg1(); break;
    }
    displaybitmask *= 2;  // next page
  }
}
#endif  // #if defined(NOKIADISPLAY)

#if defined(UTFTDISPLAY)
// DRV8825HW203 #include <myUTFT.h>                 // Hardware-specific for 2.2" TFT
// mytft = new UTFT(QD_TM220, tftdin, tftsclk, tftcs, tftrst, tftdc);
// UTFT* mytft;

void initutft() {
  lastdisplayupdate = millis();
  mytft = new UTFT(QD_TM220, tftdin, tftsclk, tftcs, tftrst, tftdc);  // QD_TM220 is for ILI9341
  mytft->InitLCD();                                                   // initialise tft, landscape mode
  mytft->setFont(SmallFont);
  mytft->clrScr();

  mytft->setColor(0, 255, 255);     // RGB
  mytft->print(programName, 0, 0);  // print startup screen
  mytft->print(programVersion, 0, 15);
  mytft->print(copystr, 0, 30);
  delay(250);
}

void displayutftpg1() {
  // display values on tft
  // mytft->clrScr();
  // over-writing is just so much quicker, a clrscr takes like 3s
  String cp = String(fcurrentposition);
  String tp = String(ftargetposition);
  String ms = String(myfocuser.maxstep);
  String sm = String(myfocuser.stepmode);
  double tempval = 20.0;
  char tempstr[8];

  mytft->print(cptxt, 0, 0);
  mytft->print(cp, 160, 0);
  mytft->print(tptxt, 0, 20);
  mytft->print(tp, 160, 20);

  mytft->print(cpwrtxt, 0, 40);
  if (myfocuser.coilpower == 1) {
    mytft->print(ontxt, 160, 40);
  } else {
    mytft->print(offtxt, 160, 40);
  }

  mytft->print(rdtxt, 0, 60);
  if (myfocuser.reversedirection == 1) {
    mytft->print(ontxt, 160, 60);
  } else {
    mytft->print(offtxt, 160, 60);
  }

  // stepmode setting
  mytft->print(smtxt, 0, 80);
  mytft->print(sm, 160, 80);
  mytft->print(tetxt, 0, 100);
  tempval = lasttemp;
  if (myfocuser.tempmode == 1) {
    // no need to convert, already in C
    dtostrf(tempval, 4, 3, tempstr);
    mytft->print(tempstr, 160, 100);
    mytft->print(cstr, 220, 100);
  } else {
    // convert to F for display
    tempval = ((tempval * 9) / 5) + 32;
    dtostrf(tempval, 4, 3, tempstr);
    mytft->print(tempstr, 160, 100);
    mytft->print(fstr, 240, 100);
  }

  mytft->print(mstxt, 0, 120);
  switch (myfocuser.motorspeed) {
    case SLOW:
      mytft->print(slowstr, 160, 120);
      break;
    case MED:
      mytft->print(medstr, 160, 120);
      break;
    case FAST:
      mytft->print(faststr, 160, 120);
      break;
    default:
      mytft->print(faststr, 160, 120);
      break;
  }
  mytft->print(matxt, 0, 140);
  mytft->print(ms, 160, 140);
}

void displayutftpg2() {
  // display values on tft
  // mytft->clrScr();
  // over-writing is just so much quicker, a clrscr takes like 3s
  String bie = "BACKLASHIN   = " + String(myfocuser.backlash_in_enabled);
  String boe = "BACKLASHOUT  = " + String(myfocuser.backlash_out_enabled);
  String bis = "BACKLASHIN#  = " + String(myfocuser.backlashsteps_in);
  String bos = "BACKLASHOUT# = " + String(myfocuser.backlashsteps_out);
  String tce = "TEMPCOMPENSA = " + String(myfocuser.tempcompenabled);
  String tco = "TEMPCOEFFIC  = " + String(myfocuser.tempcoefficient);

  mytft->print(bie, 0, 0);
  mytft->print(boe, 0, 20);
  mytft->print(bis, 0, 40);
  mytft->print(bos, 0, 60);
  mytft->print(tce, 0, 80);
  mytft->print(tco, 0, 100);
}

// update position on display
void updatepositionutft() {
  String cp = String(fcurrentposition);
  String tp = String(ftargetposition);
  mytft->print(cptxt, 0, 0);
  mytft->print(cp, 160, 0);
  mytft->print(tptxt, 0, 20);
  mytft->print(tp, 160, 20);
}

void UpdateuTFT(void) {
  unsigned static int displaybitmask = 1;
  unsigned long timenow = millis();

  if ((timenow - lastdisplayupdate) > ((unsigned long)(myfocuser.lcdpagetime * 1000)) || (timenow < lastdisplayupdate)) {
    DebugPrintln("DIS002");
    lastdisplayupdate = timenow;  // update the timestamp
    delay(5);
    unsigned int page = 0;
    String mypage = String(myfocuser.displayoption, BIN);
    for (unsigned int i = 0; i < mypage.length(); i++) {
      page *= 2;
      if (mypage[i] == '1') {
        page++;
      }
    }
    // find the next page to display
    while ((page & displaybitmask) == 0)  // mask off one bit at a time
    {
      displaybitmask *= 2;     // skip this page as it is not enabled
      if (displaybitmask > 2)  // pages 1, 2
      {
        displaybitmask = 1;
        break;
      }
    }                        // while((screenmask & displaybitmask) == 0)
    switch (displaybitmask)  // displaybitmask is now the page to display, 1=pg1, 2=pg2, 4=pg3, 8=pg4 etc
    {
      case 1: displayutftpg1(); break;
      case 2: displayutftpg2(); break;
      default: displayutftpg1(); break;
    }
    displaybitmask *= 2;  // next page
  }
}
#endif  // #if defined(UTFTDISPLAY)

#if defined(TFTDISPLAY)
//#include <stdint.h>
//#include <myTFTv2.h>
//#include <SPI.h>
// update position on display

void inittft(void) {
  lastdisplayupdate = millis();
  TFT_BL_ON;      // turn on the background light
  Tft.TFTinit();  // init TFT library
  Tft.Rotation(rotation);
  Tft.fillScreen();
#if defined(SHOWBOOTMSGS)
  Tft.drawString(headerstr, 0, 0, TextSize + 1, WHITE);  // print header string size 3
  Tft.drawString(programName, 0, 40, TextSize, BLUE);
  Tft.drawString(verstr, 0, 60, TextSize, BLUE);
  Tft.drawString(programVersion, 86, 60, TextSize, BLUE);
  Tft.drawString(copystr, 0, 80, TextSize, BLUE);
  delay(250);
#endif
}

void updatepositiontft() {
  char cp[20];
  char tp[20];

  String cpstr = currentpos + String(fcurrentposition);
  String tpstr = targetpos + String(ftargetposition);

  memset(cp, 0, 20);
  memset(tp, 0, 20);
  cpstr.toCharArray(cp, 20);
  tpstr.toCharArray(tp, 20);
  Tft.fillScreen(0, 230, 40, 80, BLACK);  // black out previous value
  Tft.drawString(cp, 0, 40, TextSize, CPositionColor);
  Tft.drawString(tp, 0, 60, TextSize, TPositionColor);
}

// displaylcd first screen
void displaytftpg1() {
  char cp[20];
  char tp[20];
  char ms[20];
  char sm[4];
  char tempstr[8];
  float tempval = 20.0;

  String cpstr = currentpos + String(fcurrentposition);
  String tpstr = targetpos + String(ftargetposition);
  String msstr = maxstepstr + String(myfocuser.maxstep);
  String smstr = String(myfocuser.stepmode);

  // display values on tft
  Tft.fillScreen();
  Tft.Rotation(rotation);

  // print header string size 3
  Tft.drawString(headerstr, 0, 0, TextSize + 1, WHITE);

  memset(cp, 0, 20);
  memset(tp, 0, 20);
  memset(ms, 0, 20);
  cpstr.toCharArray(cp, 20);
  tpstr.toCharArray(tp, 20);
  msstr.toCharArray(ms, 20);
  Tft.drawString(cp, 0, 40, TextSize, CPositionColor);
  Tft.drawString(tp, 0, 60, TextSize, TPositionColor);

  Tft.drawString(coilpwrstr, 0, 80, TextSize, CoilPwrColor);
  if (myfocuser.coilpower == 1) {
    Tft.drawString(ontxt, 140, 80, TextSize, CoilPwrColor);
  } else {
    Tft.drawString(offtxt, 140, 80, TextSize, CoilPwrColor);
  }

  Tft.drawString(reversestr, 0, 100, TextSize, ReverseColor);
  if (myfocuser.reversedirection == 1) {
    Tft.drawString(ontxt, 140, 100, TextSize, ReverseColor);
  } else {
    Tft.drawString(offtxt, 140, 100, TextSize, ReverseColor);
  }

  // stepmode setting
  Tft.drawString(stepmodestr, 0, 120, TextSize, StepModeColor);
  memset(sm, 0, 4);
  smstr.toCharArray(sm, 4);
  Tft.drawString(sm, 140, 120, TextSize, StepModeColor);

  // temperature
  Tft.drawString(tempstr1, 0, 140, TextSize, TempColor);
  memset(tempstr, 0, 8);
  tempval = lasttemp;
  if (myfocuser.tempmode == 1) {
    // no need to convert, already in C
    dtostrf(tempval, 4, 3, tempstr);  // convert tempval into tempstr
    unsigned int lp = 0;
    while (lp < strlen(tempstr)) {
      if (tempstr[lp] == '.')
        tempstr[lp] = '>';
      lp++;
    }
    Tft.drawFloat(lasttemp, 140, 140, TextSize, TempColor);
    Tft.drawString(cstr, 230, 140, TextSize, TempColor);
  } else {
    // convert to F for display
    tempval = ((tempval * 9) / 5) + 32;
    dtostrf(tempval, 4, 3, tempstr);
    unsigned int lp = 0;
    while (lp < strlen(tempstr)) {
      if (tempstr[lp] == '.')
        tempstr[lp] = '>';
      lp++;
    }
    Tft.drawFloat(tempval, 140, 140, TextSize, TempColor);
    Tft.drawString(fstr, 230, 140, TextSize, TempColor);
  }

  Tft.drawString(mspeedstr, 0, 160, TextSize, MotorSpeedColor);
  if (myfocuser.motorspeed == 0) {
    Tft.drawString(slowstr, 140, 160, TextSize, MotorSpeedColor);
  } else if (myfocuser.motorspeed == 1) {
    Tft.drawString(medstr, 140, 160, TextSize, MotorSpeedColor);
  } else if (myfocuser.motorspeed == 2) {
    Tft.drawString(faststr, 140, 160, TextSize, MotorSpeedColor);
  }
  Tft.drawString(ms, 0, 180, TextSize, MaxStepsColor);
}

void displaytftpg2() {
  char cbie[22];
  char cboe[22];
  char cbis[22];
  char cbos[22];
  char ctce[22];
  char ctco[22];

  String bie = "BACKLASHIN   = " + String(myfocuser.backlash_in_enabled);
  String boe = "BACKLASHOUT  = " + String(myfocuser.backlash_out_enabled);
  String bis = "BACKLASHIN#  = " + String(myfocuser.backlashsteps_in);
  String bos = "BACKLASHOUT# = " + String(myfocuser.backlashsteps_out);
  String tce = "TEMPCOMPENSA = " + String(myfocuser.tempcompenabled);
  String tco = "TEMPCOEFFIC  = " + String(myfocuser.tempcoefficient);

  // display values on tft
  Tft.fillScreen();
  Tft.Rotation(rotation);

  // print header string size 3
  Tft.drawString(headerstr, 0, 0, TextSize + 1, WHITE);

  memset(cbie, 0, 22);
  memset(cboe, 0, 22);
  memset(cbis, 0, 22);
  memset(cbos, 0, 22);
  memset(ctce, 0, 22);
  memset(ctco, 0, 22);

  bie.toCharArray(cbie, bie.length());
  boe.toCharArray(cboe, boe.length());
  bis.toCharArray(cbis, bis.length());
  bos.toCharArray(cbos, bos.length());
  tce.toCharArray(ctce, tce.length());
  tco.toCharArray(ctco, tco.length());

  Tft.drawString(cbie, 0, 40, TextSize, CPositionColor);
  Tft.drawString(cboe, 0, 60, TextSize, CPositionColor);

  Tft.drawString(cbis, 0, 80, TextSize, TPositionColor);
  Tft.drawString(cbos, 0, 100, TextSize, TPositionColor);

  Tft.drawString(ctce, 0, 120, TextSize, CoilPwrColor);
  Tft.drawString(ctco, 0, 140, TextSize, CoilPwrColor);
}

void UpdateTFT(void) {
  unsigned static int displaybitmask = 1;
  unsigned long timenow = millis();

  if ((timenow - lastdisplayupdate) > ((unsigned long)(myfocuser.lcdpagetime * 1000)) || (timenow < lastdisplayupdate)) {
    DebugPrintln("DIS002");
    lastdisplayupdate = timenow;  // update the timestamp
    unsigned int page = 0;
    delay(5);
    String mypage = String(myfocuser.displayoption, BIN);
    for (unsigned int i = 0; i < mypage.length(); i++) {
      page *= 2;
      if (mypage[i] == '1') {
        page++;
      }
    }
    // find the next page to display
    while ((page & displaybitmask) == 0)  // mask off one bit at a time
    {
      displaybitmask *= 2;     // skip this page as it is not enabled
      if (displaybitmask > 2)  // pages 1 and 2
      {
        displaybitmask = 1;
        break;
      }
    }                        // while((screenmask & displaybitmask) == 0)
    switch (displaybitmask)  // displaybitmask is now the page to display, 1=pg1, 2=pg2, 4=pg3, 8=pg4 etc
    {
      case 1: displaytftpg1(); break;
      case 2: displaytftpg2(); break;
      default: displaytftpg1(); break;
    }
    displaybitmask *= 2;  // next page
  }
}
#endif  // #if defined(TFTDISPLAY)


#endif
