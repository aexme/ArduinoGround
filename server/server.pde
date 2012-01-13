// server.pde
//
// Simple example of how to use VirtualWire to send and receive messages
// with a DR3100 module.
// Wait for a message from another arduino running the 'client' example,
// and send a reply.
// You can use this as the basis of a remote control/remote sensing system
//
// See VirtualWire.h for detailed API docs
// Author: Mike McCauley (mikem@open.com.au)
// Copyright (C) 2008 Mike McCauley
// $Id: server.pde,v 1.1 2008/04/20 09:24:17 mikem Exp $

#include <VirtualWire.h>

int sw1 = 6; 
int sw2 = 7;
int sw3 = 8;
int sw4 = 9;

boolean sw_state[] = {false, false, false, false};

int akkuspannungpin = 1;   
int spannung = 1020;       
int debouncecount = 0;     
int debouncecount_lim = 5000;  // command 4
int sw1_up_lim = 1022;      // command 5
int sw2_up_lim = 1022;       // command 6
int sw1_sw2_up_lim = 0;    // command 7
boolean sw_activ = true;    // command 8

void setup()
{
    Serial.begin(9600);	// Debugging only
    Serial.println("setup");

    // Initialise the IO and ISR
    vw_set_ptt_inverted(true); // Required for DR3100
    vw_setup(1000);	 // Bits per sec
    vw_rx_start();       // Start the receiver PLL running
    
    pinMode(sw1, OUTPUT);     
    digitalWrite(sw1, HIGH); 
    
    pinMode(sw2, OUTPUT);    
    digitalWrite(sw2, HIGH); 
    
    pinMode(sw3, OUTPUT);     
    digitalWrite(sw3, LOW);
    
    pinMode(sw4, OUTPUT);
    digitalWrite(sw4, LOW);
}

void loop()
{
    spannung = analogRead(akkuspannungpin);

    if(debouncecount > debouncecount_lim){ 
      debouncecount = 0;
      Serial.println(spannung);
    }
  
    if(spannung < sw2_up_lim && debouncecount == 0 && sw_activ ){
      
        if(spannung < sw1_up_lim && spannung > sw1_sw2_up_lim){ 
          sw_state[0] = !sw_state[0];
          Serial.println("sw1 flip");
      
        }
        if(spannung < sw2_up_lim && spannung > sw1_up_lim){
          //sw_state[1] = !sw_state[1]; 
          //Serial.println("sw2 flip");
          //Serial.println(spannung);
      
        }
        if(spannung < sw1_sw2_up_lim){
          //sw_state[1] = !sw_state[1];
          //sw_state[0] = !sw_state[0]; 
          //Serial.println("sw1&sw2 LOW");    
        }
        char tmp = '0';
        digitalWrite(sw1, sw_state[0]);
        digitalWrite(sw3, !sw_state[0]);
        if(sw_state[0]==true) tmp = '1';
        char msg[] = {'D', '1', tmp, '0', '0', '\0'};

        rfsend(msg);
        rfsend(msg);
        //digitalWrite(sw2, sw_state[1]);    
    }
    
    debouncecount++;
    
    const char *msg = "hello";
    uint8_t buf[VW_MAX_MESSAGE_LEN];
    uint8_t buflen = VW_MAX_MESSAGE_LEN;

    // Wait for a message
    //vw_wait_rx();
    
    if (vw_get_message(buf, &buflen) && buflen > 4) // Non-blocking
    {
	int i;
	const char *msg = "goodbye";

	Serial.print("Got: ");
	
	    Serial.print(buf[0]);
	    Serial.print(" ");
	
            if(buf[0] == 'D') {// Switch
                byte sw = buf[1];      
                byte state = buf[2];  
                byte g = buf[3];      
                byte b = buf[4];          
                setSW(sw, state);
                return;        
            }else if(buf[0] == 'Z'){// Command
                byte gr = buf[1];      
                byte command = buf[2];      
                byte byte1 = buf[3];      
                byte byte2 = buf[4];  
                readCommand(gr, command, byte1, byte2);
                return;        
            }else{// error       
                return;
            } 

	Serial.println("");       
    }
}

void setSW(byte sw, byte state){  
  
  boolean stat = false; 
  if(state > '1'){
   if(state < '0') return;
  }  
  if(sw > '2'){
   if(sw < '1') return;
  }  
  
  sw = sw - '0'; // ascii to int

  if(state == '1')stat = true;
  sw_state[sw-1] = stat;

  digitalWrite(sw + 5, sw_state[sw - 1]);
  digitalWrite(sw + 7, !sw_state[sw - 1]);
}

void readCommand(byte group, byte command, byte byte1, byte byte2) {
  
  if (group == 1) // light
  {      
      if(command == 0){      
      }
      else if(command == 1){
        //setLight();
      }
  }
  else if (group == 2) // VFD
  {                           
  }
  else if (group == 'D') // SW
  {
      int bigInt = byte2 * 256 + byte1;
      
      if(command == '0'){
         char msg[] = {'Z', 'D', '0', '0', '0', '\0'};
      }
      else if(command == '4')    debouncecount_lim = bigInt;
      else if(command == '5')    sw1_up_lim = bigInt;   
      else if(command == '6')    sw2_up_lim = bigInt;
      else if(command == '7')    sw1_sw2_up_lim = bigInt; 
      else if(command == '8')    sw_activ = ( (byte1 - '0') == true);
      
  }
  else if(group == 'Z'){
    Serial.print("debouncecount_lim: ");
      Serial.println(debouncecount_lim, HEX);
    Serial.print("sw1_up_lim: ");
      Serial.println(sw1_up_lim, HEX);
    Serial.print("sw2_up_lim: ");
      Serial.println(sw2_up_lim, HEX);
    Serial.print("sw1_sw2_up_lim: ");
      Serial.println(sw1_sw2_up_lim, HEX); 
    Serial.print("sw1_activ: ");
      Serial.println(sw_activ, HEX);
    Serial.print("spannung: ");
      Serial.println(spannung, HEX);
    Serial.print("sw_state0: ");
      Serial.println(sw_state[0], HEX);
    Serial.print("sw_state1: ");
      Serial.println(sw_state[1], HEX);
    Serial.print("sw_state2: ");
      Serial.println(sw_state[2], HEX);
    Serial.print("sw_state3: ");
      Serial.println(sw_state[3], HEX);
  }
}

void rfsend(char *msg){

    vw_send((uint8_t *)msg, strlen(msg));
    vw_wait_tx(); // Wait until the whole message is gone
    Serial.println("Sent");
    delay(400);
}

