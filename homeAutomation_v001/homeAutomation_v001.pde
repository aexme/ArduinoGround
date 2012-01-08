#include <VirtualWire.h>
#undef int
#undef abs
#undef double
#undef float
#undef round


<<<<<<< HEAD
=======

>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
//  RF Switch
//  ****************
#include <RemoteSwitch.h>

<<<<<<< HEAD


//Intantiate a new ActionSwitch remote, use pin 11
//ActionSwitch actionSwitch();

//Intantiate a new KaKuSwitch remote, also use pin 11 (same transmitter!)
KaKuSwitch kaKuSwitch(8);

//Intantiate a new Blokker remote, also use pin 11 (same transmitter!)
//BlokkerSwitch blokkerSwitch();
=======
//Intantiate a new KaKuSwitch remote, also use pin 11 (same transmitter!)
KaKuSwitch kaKuSwitch(12);
ActionSwitch actionSwitch(12);

>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
//****************************

// RGB 
//  * SDI - to digital pin 11 (MOSI pin)
//  * CLK - to digital pin 13 (SCK pin)
// inslude the SPI library:
<<<<<<< HEAD
#include <SPI.h>
=======
//#include <SPI.h>
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1

#define channelCount 6

#define checkByte1 0x55 
#define checkByte2 0xAA

struct CHANNEL{
  byte r;
  byte g;
  byte b;
};
CHANNEL group1[channelCount];
//***********


// VFD
//***********
int dout =  7;    // LED connected to digital pin 13
int stb =  6;
int clk =  5;
int din =  4;
int led =  9;
byte digits = 14; 
byte pulse_width = B00000011;  //0-7 Brightness
//******************

<<<<<<< HEAD
=======
// RF Link
//*************

boolean sw_state[] = {false, false, false, false};

int akkuspannungpin = 1;   
int spannung = 1000;       
int debouncecount = 0;     
int debouncecount_lim = 6000;  // command 4
int sw1_up_lim = 580;      // command 5
int sw2_up_lim = 700;       // command 6
int sw1_sw2_up_lim = 0;    // command 7
boolean sw_activ = true;    // command 8

//***********************
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1

void setup()
{
  // start serial port at 9600 bps:
  Serial.begin(9600);


  //  RFLink  ************
  
  // Initialise the IO and ISR
  vw_set_ptt_inverted(true); // Required for DR3100
<<<<<<< HEAD
  vw_setup(2000);	 // Bits per sec
=======
  vw_setup(1000);	 // Bits per sec
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
  vw_rx_start();       // Start the receiver PLL running
  
  
  //   RGB *********
  // initialize SPI:
<<<<<<< HEAD
  SPI.begin();  
=======
  //SPI.begin();  
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
  
  for (int i =0; i<channelCount; i++)
  {
      group1[i].r = 0;
      group1[i].g = 0;
      group1[i].b = 0;
  }
  setLight();
  // ****************
  
  // VFD
  //****************
  pinMode(dout, OUTPUT);     
  pinMode(din, INPUT);
  digitalWrite(dout, LOW); 
  
  pinMode(stb, OUTPUT);    
  digitalWrite(stb, HIGH); 
  
  pinMode(clk, OUTPUT);     
  digitalWrite(clk, LOW);
  
  pinMode(led, OUTPUT);
  digitalWrite(led, LOW);

  digitalWrite(stb, HIGH);
  delayMicroseconds(2);                  // wait for a second

  command_disp_mode(digits);
  digitalWrite(stb, HIGH); 
  delayMicroseconds(2);                  // wait for a second
  digitalWrite(stb, LOW);
  command_displ_ctrl(1, pulse_width);
  delayMicroseconds(2);                  // wait for a second
  digitalWrite(stb, HIGH); 
  delayMicroseconds(2);                  // wait for a second
  
  digitalWrite(stb, LOW);
  delayMicroseconds(2);                  // wait for a second
  command_set_address(0);
  delayMicroseconds(2); 
  
  //clear display ram
  for(int i=0; i < 46; i++){
    write_data(0x0);
    delayMicroseconds(1); 
  }
  
  digitalWrite(stb, HIGH); 
  delayMicroseconds(2);       
  
  //***************************
  
   
}

void loop()
{
    pollSerialPort();   
<<<<<<< HEAD
    
=======
    pollRFLink();
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
}

//  RF LINK ***************

<<<<<<< HEAD
=======
void pollRFLink()
{

    uint8_t buf[VW_MAX_MESSAGE_LEN];
    uint8_t buflen = VW_MAX_MESSAGE_LEN;

    if (vw_get_message(buf, &buflen) && buflen > 4) // Non-blocking
    {
        Serial.println(buflen, HEX);
	int i;

	Serial.print("Got: ");
	
	    Serial.print(buf[0]);
	    Serial.print(" ");
	
            if(buf[0] == 'B')
            { // RGB gr B

                byte ch = buf[1];      
                byte r = buf[2];      
                byte g = buf[3];      
                byte b = buf[4];      
                //setColor(r, g, b, ch, 'A');
                return;        
      
            }else if(buf[0] == 'D') 
            {// Switch
                byte sw = buf[1];      
                byte state = buf[2];  
                byte g = buf[3];      
                byte b = buf[4];          
                setLokalValue('D', sw, state, g, b);
                return;        
            }else if(buf[0] == 'Z')
            {// Command
                byte gr = buf[1];      
                byte command = buf[2];      
                byte byte1 = buf[3];      
                byte byte2 = buf[4];  
                //setLokalValue('Z', sw, state);
                return;        
            }else
            {// error
                return;
            } 

	Serial.println("");
    
  }
}
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
void rfsend(char *msg){
    //byte counter = 0;
    uint8_t buf[VW_MAX_MESSAGE_LEN];
    uint8_t buflen = VW_MAX_MESSAGE_LEN;

    vw_send((uint8_t *)msg, strlen(msg));
    vw_wait_tx(); // Wait until the whole message is gone
    Serial.println("Sent");
<<<<<<< HEAD

    // Wait at most 200ms for a reply
    if (vw_wait_rx_max(700))
    {
	if (vw_get_message(buf, &buflen)) // Non-blocking
	{
	    int i;
	    
	    // Message with a good checksum received, dump it.
	    Serial.print("Got: ");
	    
	    for (i = 0; i < buflen; i++)
	    {
		Serial.print(buf[i]);
		Serial.print(" ");
	    }
	    Serial.println("");
	}

    }
    else{
      Serial.println("fail");
      //if(counter<10) rfsend(*msg);
    }
  
}

void setSW(byte sw, byte state){  
    
  char msg[] = {'D', sw, state, '0', '0', '\0'};
  
  rfsend(msg);
  
=======
}

void setSW(byte sw, byte state){  
  
  char msg[] = {'D', sw, state, '0', '0', '\0'};
  rfsend(msg);  
}

void setLokalValue(char type, byte sw, byte state, byte byte1, byte byte2){  
  
   if(type == 'D'){
     int bigInt = byte2 * 256 + byte1;
          Serial.println("state");
     Serial.println(state,HEX);
       if(sw<'4') sw_state[sw - '0' - 1] = state - '0';
       else if(sw == '4')    debouncecount_lim = bigInt;
       else if(sw == '5')    sw1_up_lim = bigInt;   
       else if(sw == '6')    sw2_up_lim = bigInt;
       else if(sw == '7')    sw1_sw2_up_lim = bigInt;  
       else if(sw=='8') sw_activ = ( (byte1 - '0') == true);
   }
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
}

//  RFSWITCH  *****************

void setRfSw(char ch, byte nr, byte state){
<<<<<<< HEAD

  kaKuSwitch.sendSignal(ch,nr,state);
  
=======
  boolean bool_state = false;
  if((state - '0') == 1) bool_state = true;
  
  kaKuSwitch.sendSignal(ch, nr - '0',bool_state);

>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
}


void pollSerialPort() {
  byte data; 
  
  if (Serial.available() >= 5) {     // if at least 4 bytes are in the buffer

    data = Serial.read();     
    if (data == 'A'){ 
      // RGB gr A 

        byte ch = Serial.read();      
        byte r = Serial.read();      
        byte g = Serial.read();      
        byte b = Serial.read(); 
<<<<<<< HEAD

=======
        
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
        setColor(r, g, b, ch-1, 'A');
        return;        
      
    }else if(data == 'B'){ // RGB gr B

        byte ch = Serial.read();      
        byte r = Serial.read();      
        byte g = Serial.read();      
        byte b = Serial.read();      
        setColor(r, g, b, ch, 'A');
        return;        
      
    }else if(data == 'C'){ 
      // VFD
        byte addr = Serial.read();      
        byte data = Serial.read();  
        byte g = Serial.read();      
        byte b = Serial.read();          
        setVFD(addr, data);
        return;        
    }else if(data == 'D') {// Switch
        byte sw = Serial.read();      
        byte state = Serial.read();  
        byte g = Serial.read();      
        byte b = Serial.read();          
        setSW(sw, state);
        return;        
    }else if(data == 'E') {// RF Switch
      
        char ch = Serial.read();      
        byte nr = Serial.read();      
        byte state = Serial.read();      
        byte g = Serial.read();      
        setRfSw(ch, nr, state);
        return;        
    }else if(data == 'Z'){// Command
<<<<<<< HEAD
        char gr = Serial.read();      
        byte command = Serial.read();      
        byte state = Serial.read();      
        byte g = Serial.read();  
        readCommand(gr, command);
=======
        byte gr = Serial.read();      
        byte command = Serial.read();      
        byte byte1 = Serial.read();      
        byte byte2 = Serial.read();  
        readCommand(gr, command, byte1, byte2);
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
        return;        
    }else{// error
        
      return;
    }   
  }   
}
<<<<<<< HEAD
void readCommand(byte group, byte command) {
=======
void readCommand(byte group, byte command, byte byte1, byte byte2) {
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
  
  if (group == 1) // light
  {      
      if(command == 0){
      
      }
      else if(command == 1){
        
        setLight();
      }
  }
<<<<<<< HEAD
  else if (command == 2) // VFD
  {
                           
  }
=======
  else if (group == 2) // VFD
  {
                           
  }
  else if (group == 'D') // SW
  {
      if(command == '0'){
         char msg[] = {'Z', 'D', '0', '0', '0', '\0'};
         rfsend(msg);
      }else if(command == '1'){
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
      }else if(command == 'Z'){
         char msg[] = {'Z', 'Z', '0', '0', '0', '\0'};
         rfsend(msg);
      }else{ 
        char msg[] = {'Z', 'D', command, byte1, byte2, '\0'}; 
        rfsend(msg);
      } 
  }
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
}




// RGB ****************
void setColor(byte r,byte g,byte b,byte ch, char group){
  
  if(group == 'A'){
      group1[ch].r = r;
      group1[ch].g = g;
      group1[ch].b = b;

  }else if(group=='B'){
      const char *msg = "hello";
  
    //rfsend(*msg);
    //rfsend(group, ch, r, g, b)
  }
}
void setLight(){

  for (int i=0; i < channelCount; i++) 
  {
    byte r  = group1[i].r;
    byte g  = group1[i].g;
    byte b  = group1[i].b;

    digitalPotWrite(g);
    digitalPotWrite(r);
    digitalPotWrite(b);

    delayMicroseconds(600);                 
  }
  
}

int digitalPotWrite(byte g) {
  //  send in the address and value via SPI:
<<<<<<< HEAD
  SPI.transfer(g);
=======
  //SPI.transfer(g);
>>>>>>> 45a51d82630a03174ae9a8453d55a6d37aa2b6b1
}

//*******************


// VFD
//*******************

void setVFD(byte addr, byte data){

delayMicroseconds(2);                  // wait for a second
  digitalWrite(stb, LOW);
  delayMicroseconds(2);                  // wait for a second
  command_data_settings(0,1,0);
  delayMicroseconds(2);                 // wait for a second
  digitalWrite(stb, HIGH);
  delayMicroseconds(2); 

  digitalWrite(stb, LOW); 
  delayMicroseconds(2);  

  command_set_address(addr);  
  write_data(data);
  
  digitalWrite(stb, HIGH); 
  delayMicroseconds(2);  
  
  digitalWrite(stb, LOW); 
  delayMicroseconds(2); 
  command_disp_mode(digits);
  digitalWrite(stb, HIGH);
  delayMicroseconds(2); 
  digitalWrite(stb, LOW); 
  delayMicroseconds(2); 
  command_displ_ctrl(1 ,pulse_width);
  digitalWrite(stb, HIGH);  
}

void command_disp_mode(byte digits){
  /*
    0XXX : 8 digits, 20 segments
    1000: 9 digits, 19 segments
    1001: 10 digits,18 segments
    1010: 11 digits, 17 segments
    1011: 12 digits, 16 segments
    1100: 13 digits, 15 segments
    1101: 14 digits, 14 segments
    1110: 15 digits, 13 segments
    1111: 16 digits, 12 segments
  */
  byte data = B00000000;
  
  if(digits > 8)
  {
    data = digits - 1; 
  }
  
  write_data(data);
  
  delayMicroseconds(2); 
}

void command_data_settings(boolean mode, boolean increment, byte rwmode){
  /*
    The Data Setting Commands executes the Data Write or Data Read Modes for PT6318. The data
    Setting Command, the bits 5 and 6 (b4, b5) are ignored, bit 7 (b6) is given the value of “1” while bit 8 (b7)
    is given the value of “0”. Please refer to the diagram below.
    When power is turned ON, bit 4 to bit 1 (b3 to b0) are given the value of “0”.
    
    rwmode
    0 write data to diplay
    1 write data to LED
    2 Read key data
    3 Read SW data
    
    Increment
    0 increment address after write
    1 fix address
    
    mode
    0 Normal
    1 Test
  */
  
 byte data = B01000000;
 
 if(mode==1){
   data = data + B00001000;
 } 
 
 if(increment==1){
   data = data + B00000100; 
 }
 if(rwmode <= 3){
   data = data + rwmode;
 }else{
   Serial.print("bad rwmode");
 }
 
 write_data(data); 
}



void command_led(byte led){
  write_data(led);
  
}

void command_switch(){
  
  
}


void command_set_address(byte address){
  byte data = B11000000;
  
  if(address < 0x30){
    data = data + address;
  }else{
    Serial.print("address error");
  }
  
  write_data(data); 
}

void command_displ_ctrl(boolean on, byte pulse_width){
  /*
    The Display Control Commands are used to turn ON or OFF a display. It also used to set the pulse
    width. Please refer to the diagram below. When the power is turned ON, a 1/16 pulse width is selected
    and the displaye is turned OFF (the key scanning is stopped).    
    Dimming pulse_width
    0 -> 1/16
    7 -> 14/16
  */
  
  byte data=B10000000;
  
  if(on==1){
    data = data + B00001000;
  }
  if(pulse_width < 8){
    data = data + pulse_width;
  }else{
    Serial.print("bad pulse with");
  }
  write_data(data);
}

void write_data(byte data){
  
  for(int i=0; i < 8; i++){
    
    digitalWrite(clk, LOW);
    delayMicroseconds(1);
    
    if( bitRead(data ,i) ){
      digitalWrite(dout, HIGH);
    }else{
      digitalWrite(dout, LOW);
    }
    
    delayMicroseconds(1);
    digitalWrite(clk, HIGH);
    delayMicroseconds(1);
    
  }
}

//***************************
