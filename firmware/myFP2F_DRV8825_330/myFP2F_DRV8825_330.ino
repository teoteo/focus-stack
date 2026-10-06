//-----------------------------------------------------------------------
// myFOCUSERPRO2 OFFICIAL FIRMWARE RELEASE 330 (24-Nov-2023)
// (c) Robert Brown 2014-2023. All Rights Reserved.
// (c) Holger, 2019-2021. All Rights Reserved.
// (c) Joel Collet, move-timer, 2021-2022, All rights reserved.
// Supports driver board DRV8825
//-----------------------------------------------------------------------


//-----------------------------------------------------------------------
// CONTRIBUTIONS
//-----------------------------------------------------------------------
// Please support the ongoing development of this project by using PayPal
// (paypal.com) to send your donation // to user rbb1brown@gmail.com
// (Robert Brown). All contributions are gratefully accepted.


//-----------------------------------------------------------------------
// PCB BOARD
// Display OLED, LCD, Push Buttons, Temperature Probe, LED's, Buzzer,
// Home Position Switch, Blue Tooth, Stepper Power, DRV8825
//-----------------------------------------------------------------------
// DRV8825-M-MT-F-BT  // https://sourceforge.net/projects/arduinoascomfocuserpro2diy/files/Gerber%20Files/DRV8825/


//-----------------------------------------------------------------------
// STRIP BOARDS
// https://sourceforge.net/projects/arduinoascomfocuserpro2diy/files/STRIPBOARDS/
//-----------------------------------------------------------------------
// STRIP BOARD DRV8825 EASYDRIVER Rotary Encoder
// Display OLED, LCD, Temperature Probe, LED's, Buzzer, Rotary Encoder,
// DRV8825

// STRIP BOARD DRV8825 UTFT 2.2" SPI ILI9341 320x240
// Display UTFT, Temperature Probe, LED's, Buzzer, DRV8825


//-----------------------------------------------------------------------
// FIRMWARE CODE START - INCLUDES AND LIBRARIES
//-----------------------------------------------------------------------
#include "myDefines.h"
#include "myBoards.h"
#include "focuserconfig.h"
#include "fsbuild.h"
#include <Arduino.h>
#include <myQueue.h>           // By Steven de Salas
#include <myEEPROM.h>          // needed for EEPROM
#include <myeepromanything.h>  // needed for EEPROM
#include <TimerOne.h>

#ifdef ROTARYENCODER
#include <myQuadrature.h>  // needed for Keyes 040 rotary encoder
#include <Bounce2.h>       // needed to debounce Home Position switch, see https://github.com/thomasfredericks/Bounce2
#endif


// ---------------------------------------------------------------------
// SPECIFY DRIVER BOARD IN focuserconfig.h
// Only 1 can be defined
// ---------------------------------------------------------------------
// Specify your driver board in focuserconfig.h


// ---------------------------------------------------------------------
// SPECIFY FOCUSER CONFIG
// ---------------------------------------------------------------------
// Enable your hardware options in focuserconfig.h


//-----------------------------------------------------------------------
// DRIVER BOARD DEFINITIONS - DO NOT CHANGE
//-----------------------------------------------------------------------
#if (DRVBRD == DRV8825)
char programName[] = "myFP2DRV";
#endif
#if (DRVBRD == DRV8825RE)
char programName[] = "myFP2DRVRE";
#endif
#if (DRVBRD == DRV8825TFT22)
char programName[] = "myFP2DRVTFT22";
#endif
DriverBoard* driverboard;


//-----------------------------------------------------------------------
// EXTERN DATA - DO NOT CHANGE
//-----------------------------------------------------------------------
extern void timer_stepmotor(void);
extern volatile bool hpswstate;
extern byte tprobe1;
extern float lasttemp;


//-----------------------------------------------------------------------
// NEW PUSHBUTTON DATA - DO NOT CHANGE
//-----------------------------------------------------------------------
enum btnval { Inbtn,
              Outbtn,
              Bothbtn,
              Nobtn };
btnval btn;


//-----------------------------------------------------------------------
// GLOBAL DATA - DO NOT CHANGE
//-----------------------------------------------------------------------

struct config_t myfocuser;
char programVersion[] = "330";
char ProgramAuthor[] = "R BROWN 2020";
byte MainStateMachine;

long fcurrentposition;  // current focuser position
long ftargetposition;
long maxSteps;
byte isMoving;
byte tempcompavailable;
int currentaddr;  // will be address in eeprom of the data stored
byte writenow;    // should we update values in eeprom
byte jogging;
byte joggingDirection;                  // defined jogging direction, 0 = IN, 1 = OUT
byte motorspeedchangethresholdenabled;  // change motorspeed to slow when nearing target position?
byte motorspeedchangethresholdsteps;    // number of steps at which stepper slows down as target position is approached
byte movedirection;                     // holds direction of new planned move
byte stepperpower;                      // stepperpower state 0 or 1
Queue<String> queue(QUEUELENGTH);       // receive serial queue of commands
String line;
String btline;

#if defined(BLUETOOTH)
#include <SoftwareSerial.h>  // needed for bt adapter - this library is already included when you install the Arduino IDE
SoftwareSerial btSerial(BTTX, BTRX);
#endif  // #if defined(BLUETOOTH)

#ifdef ROTARYENCODER
Quadrature myrotaryencoder(ROTENCPIN9, ROTENCPIN10);  //  Rotary encoder is connected to pins 9 and 10
long encswpress;                                      // how long PB of encoder is held down
int encswval;                                         // used to determine increment value of encoder, +1, +10, +100 per tick
bool RESWVal;                                         // state of Rotary Encoder Switch
Bounce RESWdb = Bounce();                             // setup debouncer for Rotary Encoder switch
#endif                                                // #ifdef ROTARYENCODER


//-----------------------------------------------------------------------
// NUMBER OF DISPLAY PAGES
//-----------------------------------------------------------------------
#if defined(LCD1602)
int displaypages = 6;  // pg1-pg6
#elif defined(LCD1604)
int displaypages = 3;           // pg1-pg3
#elif defined(LCD2004)
int displaypages = 3;           // pg1-pg3
#elif defined(OLEDDISPLAY)
int displaypages = 2;           // pg1-pg2
#elif defined(TFTDISPLAY)
int displaypages = 2;           // pg1-pg2
#elif defined(UTFTDISPLAY)
int displaypages = 2;  // pg1-pg2
#elif defined(NOKIADISPLAY)
int displaypages = 3;  // pg1-pg3
#else
int displaypages = 0;
#endif


//-----------------------------------------------------------------------
// CODE START
//-----------------------------------------------------------------------

#include "display.h"
#include "temperature.h"
#include "serialcomms.h"

// STEPPER MOTOR ROUTINES
void MotorStepClockwise() {
  (!myfocuser.reversedirection) ? driverboard->movemotor(1) : driverboard->movemotor(0);
}

void MotorStepAntiClockwise() {
  (!myfocuser.reversedirection) ? driverboard->movemotor(0) : driverboard->movemotor(1);
}

// EEPROM stuff
void writeEEPROMNow() {
  EEPROM_writeAnything(currentaddr, myfocuser);
  writenow = 0;
}

void resetdisplayoption() {
#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)

#if defined(LCD1602)
  myfocuser.displayoption = 63;  // 111111
#elif defined(LCD1604)
  myfocuser.displayoption = 7;  // 111
#elif defined(LCD2004)
  myfocuser.displayoption = 7;  // 111
#endif
#elif defined(OLEDDISPLAY)
  myfocuser.displayoption = 3;  // 11
#elif defined(UTFTDISPLAY)
  myfocuser.displayoption = 3;  // 11
#elif defined(TFTDISPLAY)
  myfocuser.displayoption = 3;  // 11
#elif defined(NOKIADISPLAY)
  myfocuser.displayoption = 7;  // 111
#else
  // no display
  myfocuser.displayoption = 1;
#endif
}

void setfocuserdefaults() {
  myfocuser.validdata = VALIDDATAFLAG;
  myfocuser.maxstep = DEFAULTMAXSTEP;
  maxSteps = DEFAULTMAXSTEP;
  myfocuser.fposition = DEFAULTPOSITION;
  // set to 1 or ON
  myfocuser.displayenabled = myfocuser.tcdirection = myfocuser.tempmode = myfocuser.stepmode = myfocuser.coilpower = 1;
  // set to 0 or OFF
  isMoving = myfocuser.backlash_out_enabled = myfocuser.backlash_in_enabled = myfocuser.backlashsteps_out = myfocuser.backlashsteps_in = myfocuser.delayaftermove = myfocuser.tempcoefficient = myfocuser.tempcompenabled = myfocuser.stepsizeenabled = myfocuser.reversedirection = 0;
  myfocuser.lcdpagetime = DISPLAYPAGETIMEMIN;
  myfocuser.stepsize = DEFAULTSTEPSIZE;  // default is celsius
  myfocuser.tempresolution = TEMPRESOLUTION;
  myfocuser.focuserdirection = MOVINGIN;
  myfocuser.motorspeed = FAST;
  myfocuser.pbsteps = 1;
  myfocuser.stepdelay = MSDELAY;
  resetdisplayoption();
  writeEEPROMNow();  // update values in EEPROM
}

// reboot the Arduino
void software_Reboot() {
  asm volatile("jmp 0");  // jump to the start of the program
}

btnval readpushbuttons(void) {
#if defined(PUSHBUTTONS)
  digitalWrite(PBSWITCHESPIN, HIGH);
  delay(5);
  int pbval = analogRead(PBSWITCHESPIN);
  //Serial.println(pbval);
  if (pbval > 650 && pbval < 720) {
    // sw1 ON and SW2 OFF
    //Serial.println("updatepushbuttons IN:");
    return Inbtn;
  } else if (pbval > 460 && pbval < 530) {
    // sw1 and sw2 ON
    //Serial.println("updatepushbuttons ZERO:");
    return Bothbtn;
  } else if (pbval > 310 && pbval < 380) {
    // sw2 ON and SW1 OFF
    // Serial.println("updatepushbuttons OUT:");
    return Outbtn;
  }
#endif
  // for any other value do nothing
  return Nobtn;
}

// Movimento continuo con pulsante tenuto premuto (vedi PB_SPEED* in focuserconfig.h)
bool pbmoving = false;              // true mentre il motore si muove per un pulsante tenuto premuto
btnval pbbutton = Nobtn;            // pulsante che ha avviato il movimento
unsigned long pbpressstart = 0;     // quando è iniziata la pressione
unsigned long pbstepperiod = 0;     // periodo del timer motore attualmente impostato, in us
long pbstartposition = 0;           // posizione alla pressione: un tocco breve fa comunque PB_STEPS passi

// tempo fra due passi in base a quanto il pulsante è tenuto premuto
unsigned long pushbuttonstepperiod(unsigned long heldtime) {
  unsigned long period = driverboard->get_motortimerinterval();
  unsigned long tierperiod = period;
  if (heldtime >= PB_SPEED4TIME) {
    tierperiod = PB_SPEED4PERIOD;
  } else if (heldtime >= PB_SPEED3TIME) {
    tierperiod = PB_SPEED3PERIOD;
  } else if (heldtime >= PB_SPEED2TIME) {
    tierperiod = PB_SPEED2PERIOD;
  }
  return (tierperiod < period) ? tierperiod : period;  // mai più lento della velocità normale
}

// porta il target poco più avanti della posizione attuale, così il motore non si ferma
// fra una lettura del pulsante e la successiva (copre ~150 ms di passi, anche durante
// l'aggiornamento del display), senza superare 0 e maxSteps
void pushbuttonleadtarget(void) {
  long lead = (long)(150000UL / pbstepperiod) + 2;
  noInterrupts();
  long target = (pbbutton == Inbtn) ? fcurrentposition - lead : fcurrentposition + lead;
  target = (target < 0) ? 0 : target;
  target = (target > maxSteps) ? maxSteps : target;
  ftargetposition = target;
  interrupts();
}

// chiamata nello stato State_Moving mentre pbmoving è true
void updatepushbuttonmove(void) {
  btnval b = readpushbuttons();
  if ((b != pbbutton) && (readpushbuttons() != pbbutton)) {
    // pulsante rilasciato (due letture concordi): fermarsi subito,
    // ma dopo almeno PB_STEPS passi, come faceva un tocco breve prima
    noInterrupts();
    long minimum = (pbbutton == Inbtn) ? pbstartposition - myfocuser.pbsteps : pbstartposition + myfocuser.pbsteps;
    minimum = (minimum < 0) ? 0 : minimum;
    minimum = (minimum > maxSteps) ? maxSteps : minimum;
    bool short_press = (pbbutton == Inbtn) ? (fcurrentposition > minimum) : (fcurrentposition < minimum);
    ftargetposition = short_press ? minimum : fcurrentposition;
    interrupts();
    pbmoving = false;
    return;
  }
  unsigned long period = pushbuttonstepperiod(millis() - pbpressstart);
  if (period != pbstepperiod) {
    pbstepperiod = period;
    noInterrupts();
    // solo se il timer gira ancora: setPeriod() lo riavvierebbe anche se il motore si è già fermato
    if (driverboard->get_motortimerstate() == true) {
      Timer1.setPeriod(pbstepperiod);
      TCNT1 = 0;  // evita che il contatore sia già oltre il nuovo limite (sarebbe una pausa lunga)
    }
    interrupts();
  }
  pushbuttonleadtarget();
}

void updatepushbuttons(void) {
#if defined(PUSHBUTTONS)
  btn = readpushbuttons();
  delay(5);
  if (readpushbuttons() == btn) {
    switch (btn) {
      case Inbtn:
      case Outbtn:
        if (myfocuser.pbsteps == 0) {  // PB_STEPS 0 = pulsanti disattivati
          break;
        }
        // avvia il movimento continuo; prosegue in State_Moving finché il pulsante resta premuto
        pbbutton = btn;
        pbpressstart = millis();
        pbstepperiod = driverboard->get_motortimerinterval();
        pbstartposition = fcurrentposition;
        pbmoving = true;
        pushbuttonleadtarget();
        if (ftargetposition == fcurrentposition) {  // già a 0 o al massimo
          pbmoving = false;
        }
        break;
      case Bothbtn:
#if defined(BUZZER)
        digitalWrite(BUZZERPIN, 1);  // turn on buzzer
#endif
        while (readpushbuttons() == Bothbtn)  // wait for pb to be released
          ;
        fcurrentposition = 0;
        ftargetposition = 0;
        break;
      case Nobtn:
        //
        break;
    }
  }
#endif
}

void updaterotaryencoder(void) {
  // ignore any move requests push buttons or jogging if temperature compensation is enabled
  // check for temperature compensation first!
  // do not process another move if already moving
#ifdef ROTARYENCODER
  if (isMoving == 0) {
    if (myfocuser.tempcompenabled == 0) {
      int lp = myrotaryencoder.getposition();
      if (lp != 0) {
        // adjust the target position
        long newPos = fcurrentposition + (myrotaryencoder.getposition() * encswval);
        newPos = (newPos < 0) ? 0 : newPos;
        ftargetposition = (newPos > myfocuser.maxstep) ? myfocuser.maxstep : newPos;
        myrotaryencoder.setposition(0);  // reset to avoid counting more than once
        writenow = 1;
      }
      // check rotary encoder push switch
      // if pushed (returns LOW) then halt focuser or perform, additional action
      RESWdb.update();
      if (RESWdb.fell())  // if pushed then halt focuser or perform, additional action
      {
        long encswstart = millis();  // start time of encoder sw press
        int PressTime = 1;
        beep(PressTime);
        while (!digitalRead(ENCODERSWPIN))  // wait for PB to be released
        {
          if ((int)(millis() - encswstart) > (PressTime * 1000)) {
            PressTime++;
            beep(PressTime);
          }
          if (PressTime == 4) {
            break;
          }
        }
        switch (PressTime) {
          case 1:
            myfocuser.motorspeed = SLOW;
            encswval = 1;
            break;
          case 2:
            myfocuser.motorspeed = MED;
            encswval = 10;
            break;
          case 3:
            myfocuser.motorspeed = FAST;
            myfocuser.pbsteps = 1;
            encswval = 100;
            break;
          case 4:
            encswval = 1;
            fcurrentposition = ftargetposition = 0;
            break;
          default:
            break;
        }
        writenow = 1;
      }
    }   // if (myfocuser.tempcompenabled == 1)
  }     // if (isMoving == 1)
#endif  // #ifdef ROTARYENCODER
}

// provide auditory feedback on encoder push switch
// note: beep will only be heard if there is a buzzer connected and the #define for the BUZZER is uncommented at the top of this file
void beep(int beeps) {
  for (int lp1 = 0; lp1 < beeps; lp1++) {
#if defined(BUZZER)
    digitalWrite(BUZZERPIN, 1);  // turn on buzzer
    delay(100);                  // beep for 100ms
    digitalWrite(BUZZERPIN, 0);  // turn off buzzer
    delay(50);                   // delay between beeps for 50ms
#endif                           // #if defined(BUZZER)
  }
}

void updatejogging(void) {
  if (joggingDirection == 0) {
    ftargetposition = ftargetposition - 1;
    ftargetposition = (ftargetposition < 0) ? 0 : ftargetposition;
  } else {
    ftargetposition = ftargetposition + 1;
    ftargetposition = (ftargetposition > myfocuser.maxstep) ? myfocuser.maxstep : ftargetposition;
  }
#if defined(SUPERSLOWJOGGING)
  delay(SLOWSPEEDJOGDELAY);
#endif  // SUPERSLOWJOGGING
  writenow = 1;
}

void updatestepperpowerdetect() {
#if defined(STEPPERPWRDETECT)
  stepperpower = (analogRead(STEPPERDETECTPIN)) > 600 ? 1 : 0;
  // for ULN2003 powered from  9V with 4.7VZ, reading was 3.72V = 763
  // for drv8825 powered from 12V with 4.7VZ, reading was 4.07V = 834
  // Each digit = .00488millivolts
#else
  stepperpower = 1;
#endif  // #if defined(STEPPERPWRDETECT)
}

// Setup
void setup() {
  int datasize;    // will hold size of the struct myfocuser - 6 bytes
  int nlocations;  // number of storage locations available in EEPROM
  byte found;

  line = "";
#if defined(BLUETOOTH)
  btline = "";
#endif

  Serial.begin(SERIALPORTSPEED);  // initialize serial port
  clearSerialPort();              // clear any garbage from serial buffer

#if defined(BLUETOOTH)
  btSerial.begin(BTPORTSPEED);  // start bt adapter
  clearbtPort();
#endif

#if defined(BUZZER)
  pinMode(BUZZERPIN, OUTPUT);  // turn ON the Buzzer - provide power ON beep
  digitalWrite(BUZZERPIN, 1);
#endif

#if defined(INOUTLEDS)
  DebugPrintln("LED001");
  pinMode(INLED, OUTPUT);  // turn ON both LEDS as power on cycle indicator
  pinMode(OUTLED, OUTPUT);
  digitalWrite(INLED, 1);
  digitalWrite(OUTLED, 1);
#endif

  stepperpower = 1;
#if defined(STEPPERPWRDETECT)
  pinMode(STEPPERDETECTPIN, INPUT);
  DebugPrintln("STP001");
  updatestepperpowerdetect();
#endif

  isMoving = writenow = jogging = joggingDirection = tprobe1 = 0;

  currentaddr = 0;  // start at 0 if not found later
  found = 0;
  datasize = sizeof(myfocuser);
  nlocations = EEPROMSIZE / datasize;
  for (int lp1 = 0; lp1 < nlocations; lp1++) {
    int addr = lp1 * datasize;
    EEPROM_readAnything(addr, myfocuser);
    if (myfocuser.validdata == VALIDDATAFLAG)  // check to see if the data is valid
    {
      currentaddr = addr;  // data was erased so write some default values
      found = 1;
      break;
    }
  }
  if (found == 1) {
    // set the focuser back to the previous settings
    // done after this in one hit
    // mark current eeprom address as invalid and use next one
    // each time focuser starts it will read current storage, set it to invalid, goto next location and
    // write values to there and set it to valid - so it doesnt always try to use same locations over and
    // over and destroy the eeprom
    // using it like an array of [0-nlocations], ie 100 storage locations for 1k EEPROM
    EEPROM_readAnything(currentaddr, myfocuser);
    myfocuser.validdata = 0;
    EEPROM_writeAnything(currentaddr, myfocuser);
    currentaddr += datasize;  // goto next free address and write data
    // bound check the eeprom storage and if greater than last index [0-EEPROMSIZE-1] then set to 0
    if (currentaddr >= (nlocations * datasize)) {
      currentaddr = 0;
    }
    myfocuser.validdata = VALIDDATAFLAG;
    writeEEPROMNow();  // update values in EEPROM
  } else {
    DebugPrintln("CFG002");
    setfocuserdefaults();  // set defaults because not found
  }

  DebugPrintln("TMP001");
  init_temp();

  tempcompavailable = 0;
  if (tprobe1 == 1) {
    tempcompavailable = 1;
  }

  myfocuser.tempcompenabled = 0;  // disable temperature compensation on startup else focuser will auto adjust whilst focusing!

  // range check focuser variables
  myfocuser.coilpower = myfocuser.coilpower & 0x01;
  myfocuser.reversedirection = myfocuser.reversedirection & 0x01;
  myfocuser.lcdpagetime = (myfocuser.lcdpagetime < DISPLAYPAGETIMEMIN) ? DISPLAYPAGETIMEMIN : myfocuser.lcdpagetime;
  myfocuser.lcdpagetime = (myfocuser.lcdpagetime > DISPLAYPAGETIMEMAX) ? DISPLAYPAGETIMEMAX : myfocuser.lcdpagetime;
  myfocuser.maxstep = (myfocuser.maxstep < FOCUSERLOWERLIMIT) ? FOCUSERLOWERLIMIT : myfocuser.maxstep;
  myfocuser.fposition = (myfocuser.fposition < 0) ? 0 : myfocuser.fposition;
  myfocuser.fposition = (myfocuser.fposition > myfocuser.maxstep) ? myfocuser.maxstep : myfocuser.fposition;
  myfocuser.stepsize = (myfocuser.stepsize <= 0) ? DEFAULTSTEPSIZE : myfocuser.stepsize;
  myfocuser.stepsize = (myfocuser.stepsize > MAXIMUMSTEPSIZE) ? MAXIMUMSTEPSIZE : myfocuser.stepsize;
  myfocuser.displayenabled = (myfocuser.displayenabled & 0x01);
  myfocuser.focuserdirection = myfocuser.focuserdirection & 0x01;
  myfocuser.lcdupdateonmove = myfocuser.lcdupdateonmove & 1;
  myfocuser.tempmode = myfocuser.tempmode & 1;
  myfocuser.stepsizeenabled = myfocuser.stepsizeenabled & 1;
  myfocuser.tempcompenabled = myfocuser.tempcompenabled & 1;
  myfocuser.tcdirection = myfocuser.tcdirection & 1;
  myfocuser.backlash_in_enabled = myfocuser.backlash_in_enabled & 1;
  myfocuser.backlash_out_enabled = myfocuser.backlash_out_enabled & 1;
  if (myfocuser.displayoption == 0) {
    resetdisplayoption();
  }
  movedirection = myfocuser.focuserdirection;

  DebugPrintln("BRD001");
  driverboard = new DriverBoard(DRVBRD);
  DebugPrintln("BRD002");

  if (myfocuser.coilpower == 0) {
    driverboard->set_motorpower(false);
  }

  fcurrentposition = ftargetposition = myfocuser.fposition;
  maxSteps = myfocuser.maxstep;
  DebugPrint("fcurrentposition=");
  DebugPrint(fcurrentposition);
  DebugPrint(", ftargetposition=");
  DebugPrintln(ftargetposition);
  writenow = 1;

  // set up timer
  driverboard->init_motortimer();

#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
  myfocuser.displayenabled = 1;
  initlcd();
  DebugPrintln("DIS001");
#endif

#if defined(OLEDDISPLAY)
  myfocuser.displayenabled = 1;
  initoled();
  DebugPrintln("DIS001");
#endif

#if defined(TFTDISPLAY)
  myfocuser.displayenabled = 1;
  inittft();
  DebugPrintln("DIS001");  
#endif

#ifdef ROTARYENCODER
  myrotaryencoder.minimum(-1000);  // setup defaults for rotary encoder
  myrotaryencoder.maximum(1000);
  encswval = 1;
  pinMode(ENCODERSWPIN, INPUT_PULLUP);
  RESWdb.attach(ENCODERSWPIN);  // setup defaults for debouncing Rotary Encoder Switch
  RESWdb.interval(5);
#endif

  DebugPrintln("TMP006");
  read_temp();

#if defined(INOUTLEDS)
  digitalWrite(INLED, 0);  // turn off the IN/OUT LEDS and BUZZER
  digitalWrite(OUTLED, 0);
#endif

#if defined(BUZZER)
  digitalWrite(BUZZERPIN, 0);
#endif

  MainStateMachine = State_Idle;

  DebugPrintln("Setup end");
}

// Main Loop
void loop() {
  static unsigned long timestampdelayaftermove = millis();
  static unsigned long timestampendmove = millis();
  static unsigned long previousMillis = millis();
  static byte backlash_count = 0;
  static byte backlash_enabled = 0;
  static byte updatecount = 0;
  static bool parked = true;
#if defined(HOMEPOSITIONSWITCH)
  static int stepstaken = 0;  // used with physical home position switch
#endif

#if defined(BLUETOOTH)
  btSerialEvent();  // check for command from bt adapter
#endif

  DebugPrintln("STP001");
  updatestepperpowerdetect();

  if (queue.count() >= 1)  // check for serial command
  {
    ser_comms();
  }

  switch (MainStateMachine) {
    case State_Idle:
      if (fcurrentposition != ftargetposition) {
        isMoving = 1;  // due to timing issue with TFT must be set here
        driverboard->set_motorpower(true);
        driverboard->set_motortimerstate(false);
        MainStateMachine = State_InitMove;
      } else {
        isMoving = 0;

        // update temperature
#if defined(TEMPERATUREPROBE)
        if (tprobe1 == 1) {
          update_temp();
        }
#endif

        // update display
        if (myfocuser.displayenabled == 1) {
#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)  // update displays
          UpdateLCD();
#endif
#if defined(OLEDDISPLAY)
          UpdateOLED();
#endif
#if defined(NOKIADISPLAY)
          UpdateNOKIA();
#endif
#if defined(UTFTDISPLAY)
          UpdateuTFT();
#endif
#if defined(TFTDISPLAY)
          UpdateTFT();
#endif
        }

        if (stepperpower == 1) {
          // update push buttons
          updatepushbuttons();

          // update rotary encoder
          updaterotaryencoder();

          // update jogging
          if (jogging == 1) {
            updatejogging();
          }
        }

        if (parked == false) {
          static unsigned long timenow;
          timenow = millis();
          if (((timenow - timestampendmove) > ENDMOVEDELAY) || (timenow < timestampendmove)) {
            timestampendmove = timenow;  // update the timestamp
            // need to obey rule - can only release motor if coil power is disabled
            if (myfocuser.coilpower == 0) {
              driverboard->set_motorpower(false);
              DebugPrintln("CPW000");
            }
            DebugPrintln("PAR001");
            parked = true;
          }  // if (parked == false)
        }

        // is it time to update EEPROM settings?
        if (writenow == 1) {
          // decide if we have waited 10s after the last move, if so, update the EEPROM
          static unsigned long currentMillis;
          currentMillis = millis();
          if (((currentMillis - previousMillis) > EEPROMWRITEINTERVAL) || (currentMillis < previousMillis)) {
            //Serial.println("Writing to eeprom");
            previousMillis = currentMillis;
            // copy current settings and write the data to EEPROM
            myfocuser.validdata = 99;
            myfocuser.fposition = fcurrentposition;
            // update values in EEPROM
            EEPROM_writeAnything(currentaddr, myfocuser);
            writenow = 0;
          }
        }

      }  // if (fcurrentposition != ftargetposition)
      break;

    case State_InitMove:
      isMoving = 1;
      if (ftargetposition < fcurrentposition) {
        movedirection = MOVINGIN;
        backlash_count = myfocuser.backlashsteps_in;
        backlash_enabled = myfocuser.backlash_in_enabled;
      } else {
        movedirection = MOVINGOUT;
        backlash_count = myfocuser.backlashsteps_out;
        backlash_enabled = myfocuser.backlash_out_enabled;
      }
      // enable leds
#if defined(INOUTLEDS)
      if (movedirection == MOVINGIN) {
        (!myfocuser.reversedirection) ? digitalWrite(OUTLED, 1) : digitalWrite(INLED, 1);
      } else  // moving out
      {
        (!myfocuser.reversedirection) ? digitalWrite(INLED, 1) : digitalWrite(OUTLED, 1);
      }
#endif
      if (movedirection != myfocuser.focuserdirection) {
        if (backlash_enabled == 1) {
          // apply backlash
          myfocuser.focuserdirection = movedirection;
          MainStateMachine = State_ApplyBacklash;
          DebugPrintln("MAS001");
        } else {
          // do not apply backlash, go straight to moving
          MainStateMachine = State_Moving;
          DebugPrintln("MAS002");
        }
      } else {
        MainStateMachine = State_Moving;
        DebugPrintln("MAS002");
      }
      break;

    case State_ApplyBacklash:
      if (backlash_count > 0) {
        (movedirection == MOVINGIN) ? MotorStepAntiClockwise() : MotorStepClockwise();
        delayMicroseconds(driverboard->get_stepdelay());
        backlash_count--;
      } else {
        MainStateMachine = State_Moving;
      }  // if (backlash_count)
      break;

    case State_Moving:
      if (driverboard->get_motortimerstate() == false) {
        // enable motor timer, start moving
        driverboard->set_motorpower(true);
#if defined(PUSHBUTTONS)
        if (pbmoving) {
          driverboard->start_motortimer();  // pulsanti: velocità a gradini, senza rampa
        } else {
          driverboard->start_rampmove();
        }
#else
        driverboard->start_rampmove();
#endif
      }

#if defined(PUSHBUTTONS)
      if (pbmoving) {
        updatepushbuttonmove();
      }
#endif

      if (myfocuser.lcdupdateonmove == 1) {
        updatecount++;
        if (updatecount > LCDUPDATESTEPCOUNT) {
          updatecount = 0;
#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
          updatepositionlcd();
#endif
#if defined(OLEDDISPLAY)
          updatepositionoled();
#endif
#if defined(NOKIADISPLAY)
          updatepositionnokia();
#endif
#if defined(UTFTDISPLAY)
          updatepositionutft();
#endif
#if defined(TFTDISPLAY)
          updatepositiontft();
#endif
        }
      }
      break;

    case State_FindHomePosition:
      // move in till home position switch closes
#if defined(HOMEPOSITIONSWITCH)
      stepstaken = 0;
      HPSWDebugPrintln("State_FindHomePosition: MoveIN till closed");
      static bool swstate = driverboard->get_hpsw();
      while (swstate == false) {
        // step IN till switch closes
        MotorStepAntiClockwise();
        delayMicroseconds(driverboard->get_stepdelay());
        stepstaken++;
        HPSWDebugPrintln(".");
        // this prevents the endless loop if the hpsw is not connected or is faulty
        if (stepstaken > HOMESTEPS) {
          HPSWDebugPrintln("HPSW MoveIN ERROR: HOMESTEPS exceeded");
          break;
        }
        swstate = driverboard->get_hpsw();
      }
      HPSWDebugPrintln();
      HPSWDebugPrint("HPSW state=");
      HPSWDebugPrint(driverboard->get_hpsw());
      HPSWDebugPrint("HP MoveIN stepstaken=");
      HPSWDebugPrintln(stepstaken);
      HPSWDebugPrintln("HP MoveIN finished");
#endif  // HOMEPOSITIONSWITCH
      MainStateMachine = State_SetHomePosition;
      HPSWDebugPrintln("State -> SetHomePosition");
      break;

    case State_SetHomePosition:
      // move out till home position switch opens
#if defined(HOMEPOSITIONSWITCH)
      stepstaken = 0;
      HPSWDebugPrintln("State_SetHomePosition Move out till HPSW is OPEN");
      // if the previous moveIN failed at HOMESTEPS and HPSWITCH is still open then the
      // following while() code will drop through and have no effect and position = 0
      myfocuser.focuserdirection = !movedirection;
      while (driverboard->get_hpsw() == true) {
        // step out till switch opens
        MotorStepClockwise();
        delayMicroseconds(driverboard->get_stepdelay());
        stepstaken++;
        HPSWDebugPrintln(".");
        if (stepstaken > HOMESTEPS)  // this prevents the endless loop if the hpsw is not connected or is faulty
        {
          HPSWDebugPrintln("HP MoveOUT ERROR: HOMESTEPS exceeded");
          break;
        }
      }
      HPSWDebugPrintln();
      HPSWDebugPrint("HP MoveOUT stepstaken=");
      HPSWDebugPrintln(stepstaken);
      HPSWDebugPrintln("HP MoveOUT finished");
      HPSWDebugPrintln("State -> State_MoveEnded");
#endif  // HOMEPOSITIONSWITCH
      timestampdelayaftermove = millis();
      MainStateMachine = State_MoveEnded;
      DebugPrintln("MAS012");
      break;

    case State_MoveEnded:
      timestampdelayaftermove = millis();
      MainStateMachine = State_DelayAfterMove;
      break;

    case State_DelayAfterMove:
      {
        static unsigned long timenow;
        timenow = millis();
        if (((timenow - timestampdelayaftermove) > myfocuser.delayaftermove) || (timenow < timestampdelayaftermove)) {
          timestampdelayaftermove = timenow;
          MainStateMachine = State_FinishedMove;
          DebugPrintln("MAS013");
        }
      }
      break;

    case State_FinishedMove:
#if defined(PUSHBUTTONS)
      pbmoving = false;  // es. fermato a 0/max o da un comando seriale di halt
#endif
      // turn off leds
#if defined(INOUTLEDS)
      digitalWrite(INLED, 0);
      digitalWrite(OUTLED, 0);
#endif
      if (myfocuser.coilpower == 0) {
        DebugPrintln("PAR000");
        parked = false;
        timestampendmove = millis();
      }
      isMoving = 0;
      writenow = 1;
      previousMillis = millis();
      MainStateMachine = State_Idle;
      DebugPrintln("MAS014");
      break;

    default:
      MainStateMachine = State_Idle;
      break;
  }
}  // end Loop()
