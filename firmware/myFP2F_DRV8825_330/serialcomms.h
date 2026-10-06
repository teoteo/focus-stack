//-----------------------------------------------------------------------
// myFocuserPro2 Comms Routines
// (c) R Brown, 2014-2023, All rights reserved.
// (c) Holger Manz, 2019-2021, All rights reserved.
//-----------------------------------------------------------------------
#ifndef serialcomms_h
#define serialcomms_h

//-----------------------------------------------------------------------
// Includes
//-----------------------------------------------------------------------
#include <Arduino.h>
#include "focuserconfig.h"

//-----------------------------------------------------------------------
// extern routines
//-----------------------------------------------------------------------
extern volatile bool hpswstate;
extern char programName[];
extern byte tempcompavailable;
extern long maxSteps;
extern long ftargetposition;
extern long fcurrentposition;
extern int displaypages;

extern void updatestepperpowerdetect(void);
extern void software_Reboot(void);
extern void setfocuserdefaults(void);
extern void writeEEPROMNow(void);

//-----------------------------------------------------------------------
// SERIAL AND BLUETOOTH COMMUNICATIONS
//-----------------------------------------------------------------------
void SendMessage(const char *str) {
  DebugPrint("SER002 ");
  DebugPrintln(str);
  // for serial mode
  Serial.print(str);
#if defined(BLUETOOTH)
  // for bluetooth
  btSerial.print(str);
#endif
}

void SendPacket(const char token, const char *str) {
  char buff[32];
  snprintf(buff, sizeof(buff), "%c%s%c", token, str, EOFSTR);
  SendMessage(buff);
}

void SendPacket(const char token, const int val) {
  char buff[32];
  snprintf(buff, sizeof(buff), "%c%d%c", token, val, EOFSTR);
  SendMessage(buff);
}

void SendPacket(const char token, double val) {
  char result[8];
  dtostrf(val, 2, 2, result);
  SendPacket(token, result);
}

void SendPacket(const char token, const long val) {
  char buff[32];
  snprintf(buff, sizeof(buff), "%c%lu%c", token, val, EOFSTR);
  SendMessage(buff);
}

void SendPacket(const char token, const unsigned long val) {
  char buff[32];
  snprintf(buff, sizeof(buff), "%c%lu%c", token, val, EOFSTR);
  SendMessage(buff);
}

// Serial Commands
void ser_comms() {
  int cmdval;
  String receiveString = "";
  String WorkString = "";
  int paramval;
  String replystr = "";
  long tmppos;

  if (queue.count() == 0) {
    return;
  }
  receiveString = (String)queue.pop();
  String cmdstr = receiveString.substring(0, 2);
  cmdval = cmdstr.toInt();
  WorkString = receiveString.substring(2, receiveString.length());
  DebugPrint("SER003 ");
  DebugPrintln(receiveString);
  DebugPrint("SER004 ");
  DebugPrintln(cmdstr);
  DebugPrint("SER005 ");
  DebugPrintln(WorkString);

  switch (cmdval) {
    // all the get go first followed by set
    case 0:  // get focuser position
      SendPacket('P', fcurrentposition);
      break;
    case 1:  // ismoving
      SendPacket('I', isMoving);
      break;
    case 2:  // get controller status
      SendPacket('E', "OK");
      break;
    case 3:  // get firmware version
      SendPacket('F', programVersion);
      break;
    case 4:  // get firmware name
      {
        char buff[32];
        snprintf(buff, sizeof(buff), "%s%c%c%s", programName, '\r', '\n', programVersion);
        SendPacket('F', buff);
      }
      break;
    case 6:  // get temperature
      SendPacket('Z', lasttemp);
      break;
    case 8:  // get maxStep
      SendPacket('M', myfocuser.maxstep);
      break;
    case 10:  // get maxIncrement
      SendPacket('Y', myfocuser.maxstep);
      break;
    case 11:  // get coilpower setting, 0 off, 1 on
      SendPacket('O', myfocuser.coilpower);
      break;
    case 13:  // get reverse direction setting, 0 off, 1 on
      SendPacket('R', myfocuser.reversedirection);
      break;
    case 21:  // get temp probe resolution
      SendPacket('Q', myfocuser.tempresolution);
      break;
    case 24:  // get status of temperature compensation (enabled | disabled)
      SendPacket('1', myfocuser.tempcompenabled);
      break;
    case 25:                               // get IF temperature compensation is available
      SendPacket('A', tempcompavailable);  // this focuser supports temperature compensation
      break;
    case 26:  // get temperature coefficient steps/degree
      SendPacket('B', myfocuser.tempcoefficient);
      break;
    case 29:  // get stepmode
      SendPacket('S', myfocuser.stepmode);
      break;
    case 32:  // get if stepsize is enabled
      SendPacket('U', myfocuser.stepsizeenabled);
      break;
    case 33:  // get stepsize
      SendPacket('T', myfocuser.stepsize);
      break;
    case 34:  // get the time that an LCD screen is displayed for
      SendPacket('X', (myfocuser.lcdpagetime * 1000));
      break;
    case 37:  // get displaystatus
      SendPacket('D', myfocuser.displayenabled);
      break;
    case 38:  // get Temperature mode 1=Celsius, 0=Fahrenheight
      SendPacket('b', myfocuser.tempmode);
      break;
    case 39:  // get the new motor position (target) XXXXXX
      SendPacket('N', ftargetposition);
      break;
    case 43:  // get motorspeed
      SendPacket('C', myfocuser.motorspeed);
      break;
    case 45:  // get motorspeedchangethreshold value
      SendPacket('G', 0);
      break;
    case 47:  // get motorspeedchange enabled? on/off
      SendPacket('J', 0);
      break;
    case 49:  // :49#         aXXXXX
      SendPacket('a', "b552efd");
      break;
    case 50:  // get if HOMEPOSITIONSWITCH is enabled in firmware
#if defined(HOMEPOSITIONSWITCH)
      SendPacket('l', 1);
#else
      SendPacket('l', 0);
#endif
      break;
    case 53:  // get number of pages to display
      SendPacket('$', displaypages);
      break;
    case 55:
      SendPacket('0', myfocuser.stepdelay);
      break;
    case 62:  // get update of position on lcd when moving (0=disable, 1=enable)
      SendPacket('L', myfocuser.lcdupdateonmove);
      break;
    case 63:  // get status of home position switch. high = closed, low = open
#if defined(HOMEPOSITIONSWITCH)
      hpswstate = driverboard->get_hpsw();
      HPSWDebugPrint("serialcomms: :63, get HPSW state: ");
      HPSWDebugPrintln(hpswstate);
#endif
      SendPacket('H', hpswstate);
      break;
    case 66:  // get jogging state enabled/disabled
      SendPacket('K', jogging);
      break;
    case 68:  // get jogging direction, 0=IN, 1=OUT
      SendPacket('V', joggingDirection);
      break;
    case 69:  // get push button steps (0-255)
      SendPacket('?', myfocuser.pbsteps);
      break;
    case 72:  // get delayaftermove
      SendPacket('3', myfocuser.delayaftermove);
      break;
    case 74:  // get backlash in enabled status
      SendPacket('4', myfocuser.backlash_in_enabled);
      break;
    case 76:  // get backlash OUT enabled status
      SendPacket('5', myfocuser.backlash_out_enabled);
      break;
    case 78:  // get number of backlash steps IN
      SendPacket('6', myfocuser.backlashsteps_in);
      break;
    case 80:  // get number of backlash steps OUT
      SendPacket('7', myfocuser.backlashsteps_out);
      break;
    case 83:  // get if there is a temperature probe
      SendPacket('c', tprobe1);
      break;
    case 87:  // get tc direction
      SendPacket('k', myfocuser.tcdirection);
      break;
    case 89:  // get stepper power
      DebugPrintln("STP001");
      updatestepperpowerdetect();
      // for ULN2003 powered from  9V with 4.7VZ, reading was 3.72V = 763
      // for DRV8825 powered from 12V with 4.7VZ, reading was 4.07V = 834
      // Each digit = .00488millivolts
      SendPacket('9', stepperpower);
      break;
    case 93:  // get page display option
      {
        // convert the decimal to a string of 0's and 1's
        char buff[10];
        memset(buff, 0, 10);
        if (displaypages == 0) {
          buff[0] = '0';
          buff[1] = 0x00;
          SendPacket('l', buff);
        } else {
          String answer = String(myfocuser.displayoption, BIN);
          String reply = answer.substring(answer.indexOf('1'));
          reply.toCharArray(buff, reply.length() + 1);
          SendPacket('l', buff);
        }
      }
      break;
    case 95:  // get DelayedDisplayUpdate (0=disabled, 1-enabled)
      // deprecated
      SendPacket('n', 0);
      break;

    // only the set commands are listed here as they do not require a response
    case 28:  // home the motor to position 0
      if (isMoving == 0) {
        ftargetposition = 0;  // if this is a home then set target to 0
        isMoving = 1;
      }
      break;
    case 97:  // Focus Stack: numero di build del firmware (vedi fsbuild.h)
      SendPacket('B', (long)FSBUILD);
      break;
    case 5:  // set new target position to xxxxxx (and focuser initiates immediate move to xxxxxx)
      // only if not already moving
      if (stepperpower == 1) {
        if (isMoving == 0) {
          WorkString = receiveString.substring(2, receiveString.length());
          tmppos = (long)WorkString.toInt();
          tmppos = (tmppos < 0) ? 0 : tmppos;
          tmppos = (tmppos > myfocuser.maxstep) ? myfocuser.maxstep : tmppos;
          ftargetposition = tmppos;
#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
          updatepositionlcd();
#endif
#if defined(OLEDDISPLAY)
          updatepositionoled();
#endif
          writenow = 1;
          isMoving = 1;
        }
      }
      break;
    case 7:  // set maxsteps
      WorkString = receiveString.substring(2, receiveString.length());
      // an .toInt() call actually returns a long value
      tmppos = WorkString.toInt();
      tmppos = (tmppos >= FOCUSERUPPERLIMIT) ? FOCUSERUPPERLIMIT : tmppos;
      tmppos = (tmppos < fcurrentposition) ? fcurrentposition : tmppos;
      tmppos = (tmppos < FOCUSERLOWERLIMIT) ? FOCUSERLOWERLIMIT : tmppos;
      myfocuser.maxstep = tmppos;
      maxSteps = myfocuser.maxstep;
      writenow = 1;
      break;
    case 12:  // set coil power
      paramval = receiveString[2] - '0';
      myfocuser.coilpower = (byte)paramval;
      (myfocuser.coilpower == 1) ? driverboard->set_motorpower(true) : driverboard->set_motorpower(false);
      writenow = 1;
      break;
    case 14:  // set reverse direction
      if (isMoving == 0) {
        int val = receiveString[2] - '0';
        myfocuser.reversedirection = (byte)val;
        writenow = 1;
      }
      break;
    case 15:  // set motorspeed
      WorkString = receiveString.substring(2, receiveString.length());
      paramval = (byte)WorkString.toInt() & 3;
      myfocuser.motorspeed = (byte)paramval;
      writenow = 1;
      break;
    case 16:                   // set display to celsius
      myfocuser.tempmode = 1;  // temperature display mode, Celcius=1, Fahrenheit=0
      writenow = 1;
      break;
    case 17:                   // set display to fahrenheit
      myfocuser.tempmode = 0;  // temperature display mode, Celcius=1, Fahrenheit=0
      writenow = 1;
      break;
    case 18:
      // :180#    None    set the return of user specified stepsize to be OFF - default
      // :181#    None    set the return of user specified stepsize to be ON - reports what user specified as stepsize
      paramval = receiveString[2] - '0';
      myfocuser.stepsizeenabled = (byte)paramval;
      writenow = 1;
      break;
    case 19:  // set the step size value - double type, eg 2.1
      {
        WorkString = receiveString.substring(2, receiveString.length());
        double tempstepsize = WorkString.toDouble();
        tempstepsize = (tempstepsize < 0) ? 0.0 : tempstepsize;
        tempstepsize = (tempstepsize > MAXIMUMSTEPSIZE) ? MAXIMUMSTEPSIZE : tempstepsize;
        myfocuser.stepsize = tempstepsize;
      }
      writenow = 1;
      break;
    case 20:  // set the temperature resolution setting for the DS18B20 temperature probe
      WorkString = receiveString.substring(2, receiveString.length());
      paramval = WorkString.toInt();
      paramval = (paramval < 9) ? 9 : paramval;
      paramval = (paramval > 12) ? 12 : paramval;
      myfocuser.tempresolution = (byte)paramval;
      // to reprogram the temperature probe with new resolution
#if defined(TEMPERATUREPROBE)
      // to reprogram the temperature probe with new resolution
      sensor1.setResolution(tpAddress, myfocuser.tempresolution);
#endif
      writenow = 1;
      break;
    case 22:  // set the temperature compensation value to xxx
      WorkString = receiveString.substring(2, receiveString.length());
      paramval = WorkString.toInt();
      paramval = (paramval < 0) ? 0 : paramval;
      paramval = (paramval > 400) ? 400 : paramval;
      myfocuser.tempcoefficient = (byte)paramval;
      writenow = 1;
      break;
    case 23:  // set the temperature compensation ON (1) or OFF (0)
      if (tprobe1 != 0) {
        paramval = receiveString[2] - '0';
        myfocuser.tempcompenabled = (byte)paramval;
        writenow = 1;
      }
      break;
    case 27:  // stop a move - like a Halt
      if (driverboard->ramp_stop()) {
        // decelera fino a fermarsi; isMoving torna a 0 a fine movimento
        writenow = 1;
        break;
      }
      ftargetposition = fcurrentposition;
      isMoving = 0;
      writenow = 1;
      break;
    case 30:  // set step mode
      WorkString = receiveString.substring(2, receiveString.length());
      paramval = WorkString.toInt();
      paramval = (paramval < STEP1) ? STEP1 : paramval;
      paramval = (paramval > MAXSTEPMODE) ? MAXSTEPMODE : paramval;
      myfocuser.stepmode = paramval;
      driverboard->set_stepmode();
      writenow = 1;
      break;
    case 31:  // set focuser position
      if (isMoving == 0) {
        WorkString = receiveString.substring(2, receiveString.length());
        {
          long newPos = (long)WorkString.toInt();
          newPos = (newPos < 0) ? 0 : newPos;
          newPos = (newPos > myfocuser.maxstep) ? myfocuser.maxstep : newPos;
          myfocuser.fposition = newPos;
          fcurrentposition = ftargetposition = newPos;
        }
      }
      writenow = 1;
      break;
    case 35:  // set length of time an LCD page is displayed for [2 - 10 meaning 2s to 10s]
      WorkString = receiveString.substring(2, receiveString.length());
      paramval = WorkString.toInt();
      paramval = (paramval < DISPLAYPAGETIMEMIN) ? DISPLAYPAGETIMEMIN : paramval;
      paramval = (paramval > DISPLAYPAGETIMEMAX) ? DISPLAYPAGETIMEMAX : paramval;
      myfocuser.lcdpagetime = (byte)paramval;
      writenow = 1;
      break;
    case 36:
      // :360#    None    Disable Display
      // :361#    None    Enable Display
      paramval = receiveString[2] - '0';
      myfocuser.displayenabled = (byte)(paramval);
#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
      if (myfocuser.displayenabled == 1) {
        // set the text color to white
        lcd->display();
        lcd->backlight();
      } else {
        // disable the screen by setting clearing the screen and then the text color to black
        // clear the screen
        lcd->noDisplay();
        lcd->noBacklight();
      }
#endif
#if defined(OLEDDISPLAY)
      if (myfocuser.displayenabled == 1) {
        myoled->Display_On();
      } else {
        myoled->Display_Off();
      }
#endif
      writenow = 1;
      break;
    case 40:  // Reset Arduino myFocuserPro2E controller
      software_Reboot();
      break;
    case 42:  // Reset focuser defaults
      DebugPrintln("CFG002");
      setfocuserdefaults();
      ftargetposition = fcurrentposition = myfocuser.fposition;
      break;
    case 44:  // set motorspeed threshold when moving - switches to slowspeed when nearing destination
      // ignore
      break;
    case 46:  // enable/disable motorspeed change when moving
      // ignore
      break;
    case 48:  // save settings to EEPROM
      myfocuser.validdata = VALIDDATAFLAG;
      myfocuser.fposition = fcurrentposition;  // need to forth save setting????????
      writeEEPROMNow();
      break;
    case 56:  // set motorspeed delay for current speed setting
      {
        WorkString = receiveString.substring(2, receiveString.length());
        unsigned long msdelay = (unsigned long)WorkString.toInt();
        msdelay = (msdelay < 3000) ? 3000 : msdelay;
        msdelay = (msdelay > 8000) ? 8000 : msdelay;
        myfocuser.stepdelay = msdelay;
        writenow = 1;
      }
      break;
    case 61:  // set update of position on lcd when moving (0=disable, 1=enable)
      paramval = receiveString[2] - '0';
      myfocuser.lcdupdateonmove = (byte)paramval;
      writenow = 1;
      break;
    case 64:  // Move a specified number of steps
      if (isMoving == 0) {
        WorkString = receiveString.substring(2, receiveString.length());
        tmppos = (long)WorkString.toInt() + fcurrentposition;
        tmppos = (tmppos < 0) ? 0 : tmppos;
        tmppos = (tmppos > myfocuser.maxstep) ? myfocuser.maxstep : tmppos;
        ftargetposition = tmppos;
#if defined(LCD1602) || defined(LCD1604) || defined(LCD2004)
        updatepositionlcd();
#endif
#if defined(OLEDDISPLAY)
        updatepositionoled();
#endif
        writenow = 1;
        isMoving = 1;
      }
      break;
    case 65:  // Set jogging state enable/disable
      if (stepperpower == 1) {
        paramval = receiveString[2] - '0';
        jogging = (byte)paramval;
        writenow = 1;
      }
      break;
    case 67:  // Set jogging direction, 0=IN, 1=OUT
      if (stepperpower == 1) {
        paramval = receiveString[2] - '0';
        joggingDirection = (byte)paramval;
        writenow = 1;
      }
      break;
    case 70:  // set push button steps (0-255)
      WorkString = receiveString.substring(2, receiveString.length());
      paramval = WorkString.toInt();
      paramval = (paramval < 0) ? 0 : paramval;
      paramval = (paramval > 255) ? 255 : paramval;
      myfocuser.pbsteps = (byte)paramval;
      writenow = 1;
      break;
    case 71:  // set delayaftermove in milliseconds
      WorkString = receiveString.substring(2, receiveString.length());
      paramval = WorkString.toInt();
      paramval = (paramval < 0) ? 0 : paramval;
      paramval = (paramval > 255) ? 255 : paramval;
      myfocuser.delayaftermove = (byte)paramval;
      writenow = 1;
      break;
    case 73:  // Disable/enable backlash IN (going to lower focuser position)
      paramval = receiveString[2] - '0';
      myfocuser.backlash_in_enabled = (byte)paramval;
      writenow = 1;
      break;
    case 75:  // Disable/enable backlash OUT (going to lower focuser position)
      paramval = receiveString[2] - '0';
      myfocuser.backlash_out_enabled = (byte)paramval;
      writenow = 1;
      break;
    case 77:  // set backlash in steps
      WorkString = receiveString.substring(2, receiveString.length());
      paramval = WorkString.toInt();
      paramval = (paramval < 0) ? 0 : paramval;
      paramval = (paramval > 255) ? 255 : paramval;
      myfocuser.backlashsteps_in = (byte)paramval;
      writenow = 1;
      break;
    case 79:  // set backlash OUT steps
      WorkString = receiveString.substring(2, receiveString.length());
      paramval = WorkString.toInt();
      paramval = (paramval < 0) ? 0 : paramval;
      paramval = (paramval > 255) ? 255 : paramval;
      myfocuser.backlashsteps_out = (byte)paramval;
      writenow = 1;
      break;
    case 81:               // get STALL_VALUE (for TMC2209 stepper modules)
      SendPacket('8', 0);  // not used for myFP2M
      break;
    case 82:  // set STALL_VALUE (for TMC2209 stepper modules)
      // ignore, not used for myFP2M
      break;
    case 88:  // set tc direction
      paramval = receiveString[2] - '0';
      myfocuser.tcdirection = (byte)paramval;
      writenow = 1;
      break;
    case 92:  // set page display option, input=string, output=decimal
      WorkString = receiveString.substring(2, receiveString.length());
      // if no display is enabled in firmware, displaypages = 0;
      if (displaypages == 0) {
        myfocuser.displayoption = 0;
        break;
      } else {
        // truncate the string to be within the range of pages for the display type
        if ((int)WorkString.length() > displaypages) {
          WorkString = WorkString.substring(0, displaypages);
        }

        // generate the decimal from the display option string
        int num = 0;
        for (int idx = 0; idx < (int) WorkString.length(); idx++) {
          num *= 2;
          if (WorkString[idx] == '1') num++;
        }
        myfocuser.displayoption = (byte)num;
      }
      writenow = 1;
      break;
    case 94:  // set DelayedDisplayUpdate (0=disabled, 1-enabled)
      // deprecated
      break;
  }
}

void clearSerialPort() {
  while (Serial.available())
    Serial.read();
}

// SerialEvent occurs whenever new data comes in the serial RX.
void serialEvent() {
  // : starts the command, # ends the command, do not store these in the command buffer
  // read the command until the terminating # character
  while (Serial.available()) {
    char inChar = Serial.read();
    switch (inChar) {
      case ':':  // start
        line = "";
        break;
      case EOFSTR:  // eoc
        queue.push(line);
        break;
      default:  // anything else
        line = line + inChar;
        break;
    }
  }
}

#if defined(BLUETOOTH)
void clearbtPort() {
  while (btSerial.available()) {
    btSerial.read();
  }
}

void btSerialEvent() {
  // : starts the command, # ends the command, do not store these in the command buffer
  // read the command until the terminating # character
  while (btSerial.available()) {
    char inChar = btSerial.read();
    switch (inChar) {
      case ':':  // start
        btline = "";
        break;
      case EOFSTR:  // eoc
        queue.push(btline);
        break;
      default:  // anything else
        btline = btline + inChar;
        break;
    }
  }
}
#endif

// (IL: Needed on Pro Micro Clone otherwise serial input is never processed) -------------------------------------------------------------------------------
// On some boards serialEvent() is never called as serialEventRun is not defined
// properly by the IDE. If so this function provides the missing definition.
// Typically you will get a timeout error when you try to connect to the focuser
// using the ASCOM driver or focuser app then you need to uncomment FORCE_SERIALEVENT
// Checks to see if there is data in the Hardware Serial and if so calls serialEvent()
// to process it. This is called automatically between each loop() run and calls
// serialEvent() if there is data in the Hardware Serial that needs processing.
//-------------------------------------------------------------------------------
#if defined(CONTROLLERISAMICRO)
void serialEventRun() {
  if (Serial.available()) {
    serialEvent();
  }
}
#endif
// (IL: End of extra Pro Micro function) -------------------------------------------------------------------------------

#endif
