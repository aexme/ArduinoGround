#include <VirtualWire.h>
#undef int
#undef abs
#undef double
#undef float
#undef round


//  RF Switch
//  ****************
#include <RemoteSwitch.h>



//Intantiate a new ActionSwitch remote, use pin 11
//ActionSwitch actionSwitch();

//Intantiate a new KaKuSwitch remote, also use pin 11 (same transmitter!)
KaKuSwitch kaKuSwitch(8);

//Intantiate a new Blokker remote, also use pin 11 (same transmitter!)
//BlokkerSwitch blokkerSwitch();
//****************************

// RGB 
//  * SDI - to digital pin 11 (MOSI pin)
//  * CLK - to digital pin 13 (SCK pin)
// inslude the SPI library:
#include <SPI.h>

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


void setup()
{
  // start serial port at 9600 bps:
  Serial.begin(9600);


  //  RFLink  ************
  
  // Initialise the IO and ISR
  vw_set_ptt_inverted(true); // Required for DR3100
  vw_setup(2000);	 // Bits per sec
  vw_rx_start();       // Start the receiver PLL running
  
  
  //   RGB *********
  // initialize SPI:
  SPI.begin();  
  
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
    
}

//  RF LINK ***************

void rfsend(char *msg){
    //byte counter = 0;
    uint8_t buf[VW_MAX_MESSAGE_LEN];
    uint8_t buflen = VW_MAX_MESSAGE_LEN;

    vw_send((uint8_t *)msg, strlen(msg));
    vw_wait_tx(); // Wait until the whole message is gone
    Serial.println("Sent");

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
  
}

//  RFSWITCH  *****************

void setRfSw(char ch, byte nr, byte state){

  kaKuSwitch.sendSignal(ch,nr,state);
  
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
        char gr = Serial.read();      
        byte command = Serial.read();      
        byte state = Serial.read();      
        byte g = Serial.read();  
        readCommand(gr, command);
        return;        
    }else{// error
        
      return;
    }   
  }   
}
void readCommand(byte group, byte command) {
  
  if (group == 1) // light
  {      
      if(command == 0){
      
      }
      else if(command == 1){
        
        setLight();
      }
  }
  else if (command == 2) // VFD
  {
                           
  }
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
  SPI.transfer(g);
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
