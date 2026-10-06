//-----------------------------------------------------------------------
// myFocuserPro2 Driver Board Code
// (c) R Brown, 2014-2023, All rights reserved.
//-----------------------------------------------------------------------
#include <Arduino.h>
#include "myDefines.h"
#include "myBoardDefs.h"
#include "myBoards.h"
#include "focuserconfig.h"
#if defined(HOMEPOSITIONSWITCH)
#include <Bounce2.h>           // needed to debounce Home Position switch
Bounce hpswbounce = Bounce();  // setup debouncer for hp switch
#endif
#include <TimerOne.h>  // https://github.com/PaulStoffregen/TimerOne

// v1 of the home position switch which has switch normally open to D12 and ground
// when home position switch is NOT activated (contacts open), D12 = 5V = HIGH
// when home position switch is activated (contacts closed), D12 = GND = LOW
// Normal operation, home switch not activated, contacts open, D12 high, motor can move
// Fault operation, D12 (disconnected switch or power) floats high, motor can move

//-----------------------------------------------------------------------
// DEFINES
//-----------------------------------------------------------------------

//-----------------------------------------------------------------------
// Externs
//-----------------------------------------------------------------------
extern struct config_t myfocuser;
extern long fcurrentposition;  // current focuser position
extern long ftargetposition;   // target position
extern byte isMoving;          // is the motor currently moving
extern byte MainStateMachine;
extern byte movedirection;  // holds direction of new planned move
extern DriverBoard* driverboard;
extern void MotorStepClockwise(void);
extern void MotorStepAntiClockwise(void);


//-----------------------------------------------------------------------
// Local Data
//-----------------------------------------------------------------------
volatile bool hpswstate;

//-----------------------------------------------------------------------
// void timer_stepmotor(void)
// Run by Timer1, steps motor till fcurrentposition == ftargetposition
//-----------------------------------------------------------------------
void timer_stepmotor() {
  if (fcurrentposition == ftargetposition)  // must come first else cannot halt
  {
    driverboard->stop_motortimer();
    DebugPrint("MAS013");
    MainStateMachine = State_MoveEnded;
    DebugPrint("MAS010");
  } else {
    // focuser not finished the move yet
    (movedirection == MOVINGIN) ? MotorStepAntiClockwise() : MotorStepClockwise();
    (movedirection == MOVINGIN) ? fcurrentposition-- : fcurrentposition++;
    // no need for validation as target has already been validated before move
    driverboard->update_ramp();

#if defined(HOMEPOSITIONSWITCH)
    // if moving in. check if hpsw closed or position = 0
    if (movedirection == MOVINGIN) {
      // if switch state = CLOSED and position >= 0
      // need to back OUT a little till switch opens and then set position to 0
      hpswstate = driverboard->get_hpsw();
      if ((hpswstate == true) && (fcurrentposition >= 0)) {
        driverboard->stop_motortimer();
        //isMoving = 1;
        fcurrentposition = ftargetposition = 0;
        MainStateMachine = State_SetHomePosition;
        DebugPrintln("MAS014");
        HPSWDebugPrintln("hpswstate=closed, pos >= 0");
      }
      // else if switchstate = OPEN and Position = 0
      // need to move IN a little till switch CLOSES then
      else if ((hpswstate == false) && (fcurrentposition == 0)) {
        driverboard->stop_motortimer();
        //isMoving = 1;
        fcurrentposition = ftargetposition = 0;
        MainStateMachine = State_FindHomePosition;
        DebugPrintln("MAS015");
        HPSWDebugPrintln("HPSW=Open, position=0");
        HPSWDebugPrintln("State -> State_FindHomePosition");
      }
    }   // if (movedirection == MOVINGIN)
#endif  // home position switch
  }
}

//-----------------------------------------------------------------------
// DRIVERBOARD CLASS
//-----------------------------------------------------------------------
DriverBoard::DriverBoard(byte brdtype)
  : boardtype(brdtype) {
  if (boardtype == DRV8825 || boardtype == DRV8825RE) {
    pinMode(DRV8825ENABLE, OUTPUT);
    pinMode(DRV8825DIR, OUTPUT);
    pinMode(DRV8825STEP, OUTPUT);
    digitalWrite(DRV8825ENABLE, HIGH);
    pinMode(DRV8825M2, OUTPUT);
    pinMode(DRV8825M1, OUTPUT);
    pinMode(DRV8825M0, OUTPUT);
  } else if (boardtype == DRV8825TFT22) {
    pinMode(DRV8825ENABLETFT, OUTPUT);
    pinMode(DRV8825DIRTFT, OUTPUT);
    pinMode(DRV8825STEPTFT, OUTPUT);
    digitalWrite(DRV8825ENABLETFT, HIGH);
    pinMode(DRV8825M2TFT, OUTPUT);
    pinMode(DRV8825M1TFT, OUTPUT);
    pinMode(DRV8825M0TFT, OUTPUT);
  }
  hpswstate = false;
  HPSWDebugPrintln("init HPSW");
  init_hpsw();
  HPSWDebugPrintln("Read HPSW");
  hpswstate = get_hpsw();
  set_stepmode();
  _motortimerstate = false;
}

//-----------------------------------------------------------------------//-----------------------------------------------------------------------
// void driverboard->init_hpsw()
// If HPSW defined then initialise hpsw
//-----------------------------------------------------------------------
void DriverBoard::init_hpsw(void) {
#if defined(HOMEPOSITIONSWITCH)
  pinMode(HPSWPIN, INPUT_PULLUP);  // set up the Home Position Switch pin as an input
  hpswbounce.attach(HPSWPIN);      // setup defaults for debouncing hp Switch
  hpswbounce.interval(5);          // sets debounce time
  hpswbounce.update();
#endif
}

//-----------------------------------------------------------------------//-----------------------------------------------------------------------
// bool driverboard->get_hpsw()
// hpsw pin has 470K pullup, hpsw open = high, hpsw closed = low
// return state of hpswstate needs to return high = sw closed, low = sw open
//-----------------------------------------------------------------------
bool DriverBoard::get_hpsw(void) {
#if defined(HOMEPOSITIONSWITCH)
  hpswbounce.update();
  return !(hpswbounce.read());
#else
  // no switch
  return false;
#endif
}

//-----------------------------------------------------------------------
// void DriverBoard::set_motorpower(bool state)
// turn coil power on, turn coil power off
//-----------------------------------------------------------------------
void DriverBoard::set_motorpower(bool state) {
  if (state == true) {
    // power on
    if (boardtype == DRV8825 || boardtype == DRV8825RE) {
      digitalWrite(DRV8825ENABLE, LOW);
    } else if (boardtype == DRV8825TFT22) {
      digitalWrite(DRV8825ENABLETFT, LOW);
    }
    delay(1);  // need to wait 1ms before driver chip is ready for stepping
  } else {
    // power off
    if (this->boardtype == DRV8825 || this->boardtype == DRV8825RE) {
      digitalWrite(DRV8825ENABLE, HIGH);
    } else if (boardtype == DRV8825TFT22) {
      digitalWrite(DRV8825ENABLETFT, HIGH);
    }
  }
}

//-----------------------------------------------------------------------
// void driverboard->init_motortimer(void);
// initialise motor timer
//-----------------------------------------------------------------------
void DriverBoard::init_motortimer(void) {
  Timer1.initialize();
  Timer1.attachInterrupt(timer_stepmotor);
  set_motortimerstate(false);
}

//-----------------------------------------------------------------------
// void driverboard->set_motortimerstate(bool);
// set state of motor timer
//-----------------------------------------------------------------------
void DriverBoard::set_motortimerstate(bool state) {
  if (state == false) {
    Timer1.setPeriod(get_motortimerinterval());
    Timer1.stop();
    _motortimerstate = false;
    DebugPrintln("BRD005");
  } else {
    Timer1.setPeriod(get_motortimerinterval());
    Timer1.start();
    _motortimerstate = true;
  }
}

//-----------------------------------------------------------------------
// unsigned long driverboard->get_motortimerinterval(void);
// get the delay interval for the motor timer
//-----------------------------------------------------------------------
unsigned long DriverBoard::get_motortimerinterval() {
  unsigned long stepdelay;
  switch (myfocuser.stepmode) {
    case STEP1:
      stepdelay = driverboard->get_stepdelay();
      break;
    case STEP2:
      stepdelay = driverboard->get_stepdelay() / 2;
      break;
    case STEP4:
      stepdelay = driverboard->get_stepdelay() / 4;
      break;
    case STEP8:
      stepdelay = driverboard->get_stepdelay() / 8;
      break;
    case STEP16:
      stepdelay = driverboard->get_stepdelay() / 8;
      break;
    case STEP32:
      stepdelay = driverboard->get_stepdelay() / 8;
      break;
    default:
      stepdelay = driverboard->get_stepdelay();
      break;
  }
  return stepdelay;
}

//-----------------------------------------------------------------------
// bool driverboard->get_motortimerstate(void);
// return motor timer state
//-----------------------------------------------------------------------
bool DriverBoard::get_motortimerstate(void) {
  return _motortimerstate;
}

//-----------------------------------------------------------------------
// void driverboard->start_motortimer(void);
// enable motor timer, stepper starts moving
//-----------------------------------------------------------------------
void DriverBoard::start_motortimer(void) {
  set_motortimerstate(true);
}

//-----------------------------------------------------------------------
// void driverboard->stop_motortimer(void);
// stop motor timer, stepper stops moving
//-----------------------------------------------------------------------
void DriverBoard::stop_motortimer(void) {
  _rampenabled = false;
  set_motortimerstate(false);
}

//-----------------------------------------------------------------------
// Movimento con rampa: parte a MOVE_STARTSPEED, accelera di MOVE_ACCEL fino alla
// velocità massima e decelera in modo da arrivare al target a MOVE_STARTSPEED.
// La velocità dipende dai passi già fatti e da quelli mancanti:
//   v = min( sqrt(v0^2 + 2*a*fatti), sqrt(v0^2 + 2*a*mancanti), vmax )
//-----------------------------------------------------------------------
void DriverBoard::start_rampmove(void) {
  // la velocità motore lenta/media riduce la massima come fa get_stepdelay()
  _rampmaxspeed = MOVE_MAXSPEED * (float)myfocuser.stepdelay / (float)get_stepdelay();
  _rampmaxspeed = (_rampmaxspeed < MOVE_STARTSPEED) ? MOVE_STARTSPEED : _rampmaxspeed;
  _rampstartposition = fcurrentposition;
  _rampspeed = MOVE_STARTSPEED;
  _rampperiod = (unsigned long)(1000000.0 / MOVE_STARTSPEED);
  _rampenabled = true;
  Timer1.setPeriod(_rampperiod);
  Timer1.start();
  _motortimerstate = true;
}

void DriverBoard::update_ramp(void) {
  if (!_rampenabled) {
    return;
  }
  float done = (float)labs(fcurrentposition - _rampstartposition);
  float left = (float)labs(ftargetposition - fcurrentposition);
  float v0sq = MOVE_STARTSPEED * MOVE_STARTSPEED;
  float vsq = v0sq + 2.0 * MOVE_ACCEL * ((done < left) ? done : left);
  float vmaxsq = _rampmaxspeed * _rampmaxspeed;
  _rampspeed = (vsq > vmaxsq) ? _rampmaxspeed : sqrt(vsq);
  unsigned long period = (unsigned long)(1000000.0 / _rampspeed);
  if (period != _rampperiod) {
    _rampperiod = period;
    Timer1.setPeriod(_rampperiod);  // siamo nell'interrupt del timer: il contatore è a zero
  }
}

// Stop con decelerazione: sposta il target alla distanza necessaria per rallentare.
// Restituisce false se non c'è un movimento con rampa in corso (stop immediato come prima).
bool DriverBoard::ramp_stop(void) {
  noInterrupts();
  if (!_rampenabled || !_motortimerstate) {
    interrupts();
    return false;
  }
  float v0sq = MOVE_STARTSPEED * MOVE_STARTSPEED;
  float vsq = _rampspeed * _rampspeed;
  long stopsteps = (vsq > v0sq) ? (long)((vsq - v0sq) / (2.0 * MOVE_ACCEL)) : 0;
  long left = labs(ftargetposition - fcurrentposition);
  if (stopsteps < left) {
    ftargetposition = (movedirection == MOVINGIN) ? fcurrentposition - stopsteps : fcurrentposition + stopsteps;
  }
  interrupts();
  return true;
}

//-----------------------------------------------------------------------
// unsigned long driverboard->get_stepdelay(void);
// get the delay interval for the motor timer
//-----------------------------------------------------------------------
unsigned long DriverBoard::get_stepdelay(void) {
  unsigned long sdelay = myfocuser.stepdelay;
  switch (myfocuser.motorspeed) {
    case SLOW:
      sdelay *= 2.5;
      break;
    case MED:
      sdelay *= 2;
      break;
    case FAST:
      //
      break;
    default:
      //
      break;
  }
  return sdelay;
}

//-----------------------------------------------------------------------
// void driverboard->set_stepdelay(unsigned long);
// deprecated
//-----------------------------------------------------------------------


//-----------------------------------------------------------------------
// void driverboard->movemotor(byte);
// move stepper motor in the specified direction
//-----------------------------------------------------------------------
void DriverBoard::movemotor(byte ddir) {
  if (this->boardtype == DRV8825 || this->boardtype == DRV8825RE) {
    digitalWrite(DRV8825DIR, ddir);
    digitalWrite(DRV8825STEP, HIGH);
    delayMicroseconds(MOTORPULSETIME);
    digitalWrite(DRV8825STEP, LOW);
  } else if (boardtype == DRV8825TFT22) {
    digitalWrite(DRV8825DIRTFT, ddir);
    digitalWrite(DRV8825STEPTFT, HIGH);
    delayMicroseconds(MOTORPULSETIME);
    digitalWrite(DRV8825STEPTFT, LOW);
  }
#if defined(HOMEPOSITIONSWITCH)
  if (ddir == MOVINGIN) {
    hpswstate = get_hpsw();
  }
#endif
}

int DriverBoard::get_stepmode(void) {
  return myfocuser.stepmode;
}

void DriverBoard::set_stepmode() {
  switch (this->boardtype) {
    case DRV8825:
    case DRV8825RE:
      switch (myfocuser.stepmode) {
        case 1:
          digitalWrite(DRV8825M0, 0);
          digitalWrite(DRV8825M1, 0);
          digitalWrite(DRV8825M2, 0);
          break;
        case 2:
          digitalWrite(DRV8825M0, 1);
          digitalWrite(DRV8825M1, 0);
          digitalWrite(DRV8825M2, 0);
          break;
        case 4:
          digitalWrite(DRV8825M0, 0);
          digitalWrite(DRV8825M1, 1);
          digitalWrite(DRV8825M2, 0);
          break;
        case 8:
          digitalWrite(DRV8825M0, 1);
          digitalWrite(DRV8825M1, 1);
          digitalWrite(DRV8825M2, 0);
          break;
        case 16:
          digitalWrite(DRV8825M0, 0);
          digitalWrite(DRV8825M1, 0);
          digitalWrite(DRV8825M2, 1);
          break;
        case 32:
          digitalWrite(DRV8825M0, 1);
          digitalWrite(DRV8825M1, 0);
          digitalWrite(DRV8825M2, 1);
          break;
        default:  // full stepping
          digitalWrite(DRV8825M0, 0);
          digitalWrite(DRV8825M1, 0);
          digitalWrite(DRV8825M2, 0);
          break;
      }
      break;
    case DRV8825TFT22:
      switch (myfocuser.stepmode) {
        case 1:
          digitalWrite(DRV8825M0TFT, 0);
          digitalWrite(DRV8825M1TFT, 0);
          digitalWrite(DRV8825M2TFT, 0);
          break;
        case 2:
          digitalWrite(DRV8825M0TFT, 1);
          digitalWrite(DRV8825M1TFT, 0);
          digitalWrite(DRV8825M2TFT, 0);
          break;
        case 4:
          digitalWrite(DRV8825M0TFT, 0);
          digitalWrite(DRV8825M1TFT, 1);
          digitalWrite(DRV8825M2TFT, 0);
          break;
        case 8:
          digitalWrite(DRV8825M0TFT, 1);
          digitalWrite(DRV8825M1TFT, 1);
          digitalWrite(DRV8825M2TFT, 0);
          break;
        case 16:
          digitalWrite(DRV8825M0TFT, 0);
          digitalWrite(DRV8825M1TFT, 0);
          digitalWrite(DRV8825M2TFT, 1);
          break;
        case 32:
          digitalWrite(DRV8825M0TFT, 1);
          digitalWrite(DRV8825M1TFT, 0);
          digitalWrite(DRV8825M2TFT, 1);
          break;
        default:  // full stepping
          digitalWrite(DRV8825M0TFT, 0);
          digitalWrite(DRV8825M1TFT, 0);
          digitalWrite(DRV8825M2TFT, 0);
          break;
      }
      break;
  }
}
