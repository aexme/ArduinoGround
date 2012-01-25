#undef int
#undef abs
#undef double
#undef float
#undef round

//  RF Switch
//  ****************
#include <RemoteSwitch.h>
#include <RemoteReceiver.h>

//Intantiate a new KaKuSwitch remote, also use pin 11 (same transmitter!)
KaKuSwitch kaKuSwitch(3);

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
int stb =  5;
int clk =  6;
int din =  4;
int led =  13;
byte digits = 14; 
byte pulse_width = B00000011;  //0-7 Brightness

int key1pin = 4;   
int key2pin = 5; 
int encpin = 3; 

//******************

// RF Link
//*************
#include <VirtualWire.h>

boolean sw_state[] = {false, false, false, false};

int akkuspannungpin = 1;   
int spannung = 1000;       
int debouncecount = 0;     
int debouncecount_lim = 11000;  // command 4
int sw1_up_lim = 580;      // command 5
int sw2_up_lim = 700;       // command 6
int sw1_sw2_up_lim = 0;    // command 7
boolean sw_activ = true;    // command 8

//***********************

void setup()
{
  // start serial port at 9600 bps:
  Serial.begin(57600);
  
  // VFD
  initVFD();
  
  // RFSwitch  
  RemoteReceiver::init(0, 1, showCode);
  
  //  RFLink  ***********
  // Initialise the IO and ISR
  vw_set_tx_pin(3);
  vw_set_ptt_inverted(true); // Required for DR3100
  vw_setup(1000);	 // Bits per sec
  vw_rx_start();       // Start the receiver PLL running
  
  //   RGB *********
  //    initialize SPI:
  SPI.begin();  
  
  for (int i =0; i<channelCount; i++)
  {
      group1[i].r = 0;
      group1[i].g = 0;
      group1[i].b = 0;
  }
  setLight();
  
}

void loop()
{
    pollSerialPort();   
    pollRFLink();
    
    if(debouncecount > debouncecount_lim){ 
      debouncecount = 0;
      getKeys();
    }
    debouncecount++;

}

void setLokalValue(char type, byte sw, byte state, byte byte1, byte byte2){  
  
   if(type == 'D'){
       int bigInt = byte2 * 256 + byte1;
          
       if(sw<'4') sw_state[sw - '0' - 1] = state - '0';
       else if(sw == '4')    debouncecount_lim = bigInt;
       else if(sw == '5')    sw1_up_lim = bigInt;   
       else if(sw == '6')    sw2_up_lim = bigInt;
       else if(sw == '7')    sw1_sw2_up_lim = bigInt;  
       else if(sw=='8') sw_activ = ( (byte1 - '0') == true);
   }
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
        byte gr = Serial.read();      
        byte command = Serial.read();      
        byte byte1 = Serial.read();      
        byte byte2 = Serial.read();  
        readCommand(gr, command, byte1, byte2);
        return;        
    }else{// error
        
      return;
    }   
  }   
}
void readCommand(byte group, byte command, byte byte1, byte byte2) {
  
  if (group == 1) // light
  {      
      if(command == 0){
      
      }
      else if(command == 1){
        
        setLight();
      }
  }
  else if (group == 2) // VFD
  {
                           
  }
  else if (group == 'D') // SW
  {
      if(command == '0'){
         char msg[] = {'Z', 'D', '0', '0', '0', '\0'};
         rfsend(msg);
      }else if(command == '1'){
          Serial.print("LS;debouncecount_lim;");
            Serial.println(debouncecount_lim, HEX);
          Serial.print("LS;sw1_up_lim;");
            Serial.println(sw1_up_lim, HEX);
          Serial.print("LS;sw2_up_lim;");
            Serial.println(sw2_up_lim, HEX);
          Serial.print("LS;sw1_sw2_up_lim;");
            Serial.println(sw1_sw2_up_lim, HEX); 
          Serial.print("LS;sw1_activ;");
            Serial.println(sw_activ, HEX);
          Serial.print("LS;spannung;");
            Serial.println(spannung, HEX);
          Serial.print("LS;sw_state0: ");
            Serial.println(sw_state[0], HEX);
          Serial.print("LS;sw_state1;");
            Serial.println(sw_state[1], HEX);
          Serial.print("LS;sw_state2;");
            Serial.println(sw_state[2], HEX);
          Serial.print("LS;sw_state3;");
            Serial.println(sw_state[3], HEX);       
      }else if(command == 'Z'){
         char msg[] = {'Z', 'Z', '0', '0', '0', '\0'};
         rfsend(msg);
      }else{ 
        char msg[] = {'Z', 'D', command, byte1, byte2, '\0'}; 
        rfsend(msg);
      } 
  }
}




//  ***********************
//  RF LINK ***************
//  ***********************

void pollRFLink()
{
    uint8_t buf[VW_MAX_MESSAGE_LEN];
    uint8_t buflen = VW_MAX_MESSAGE_LEN;

    if (vw_get_message(buf, &buflen) && buflen > 4) // Non-blocking
    {
	int i;

	Serial.print("RF;");
	
	    Serial.print(buf[0]);
	    Serial.print(buf[1]);
            Serial.print(buf[2]);
            Serial.print(buf[3]);
	    Serial.print(buf[4]);
            Serial.print("\n");
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
    
    }
}
void rfsend(char *msg){
    //byte counter = 0;
    uint8_t buf[VW_MAX_MESSAGE_LEN];
    uint8_t buflen = VW_MAX_MESSAGE_LEN;

    vw_send((uint8_t *)msg, strlen(msg));
    vw_wait_tx(); // Wait until the whole message is gone
    Serial.println("VW;Send");
}

void setSW(byte sw, byte state){  
  
  char msg[] = {'D', sw, state, '0', '0', '\0'};
  rfsend(msg);  
}



//  ***************************
//  RFSWITCH  *****************
//  ***************************

void setRfSw(char ch, byte nr, byte state){
  boolean bool_state = false;
  if((state - '0') == 1) bool_state = true;
  
  kaKuSwitch.sendSignal(ch, nr - '0',bool_state);
  Serial.println("RF;Send");

}

//Callback function is called only when a valid code is received.
void showCode(unsigned long receivedCode, unsigned int period) {
  //Note: interrupts are disabled. You can re-enable them if needed.
  
  //Print the received code.
  Serial.print("RF;");
  Serial.print(receivedCode);
  Serial.println(";");

}

// ********************
// RGB ****************
// ********************

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
  //SPI.transfer(g);
}



// *******************
// VFD
// *******************


void initVFD(){

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
    write_data(0);
    delayMicroseconds(1); 
  }  
  digitalWrite(stb, HIGH); 
  delayMicroseconds(2); 

}

void getKeys(){
  
    int spannung1=0;
    int spannung2=0;
    int spannung3=0;
    spannung1 = analogRead(key1pin);
    spannung2 = analogRead(key2pin);
    spannung3 = analogRead(encpin);

    if(spannung1 < 250 && spannung1 > 220){
          Serial.println("VFDkey;TA;");
    }
    if(spannung1 < 350 && spannung1 > 320){
          Serial.println("VFDkey;PTY;");
    }
    if(spannung1 < 170 && spannung1 > 130){
          Serial.println("VFDkey;AF;");
    }    
    if(spannung1 < 110 && spannung1 > 70){
          Serial.println("VFDkey;Power;");
    }
    if(spannung1 < 65 && spannung1 > 20){
          Serial.println("VFDkey;DSP;");
    }
    if(spannung1 < 460 && spannung1 > 420){
          Serial.println("VFDkey;MODE;");
    }
    if(spannung1 < 900 && spannung1 > 860){
          Serial.println("VFDkey;EQ;");
    }
    if(spannung1 < 820 && spannung1 > 780){
          Serial.println("VFDkey;SCN;");
    }  
    if(spannung2 < 20){
          Serial.println("VFDkey;1;");
    } 
    if(spannung2 < 185 && spannung2 > 150){
          Serial.println("VFDkey;2;");
    } 
    if(spannung2 < 340 && spannung2 > 315){
          Serial.println("VFDkey;3;");
    } 
    if(spannung2 < 500 && spannung2 > 470){
          Serial.println("VFDkey;4;");
    } 
    if(spannung2 < 645 && spannung2 > 615){
          Serial.println("VFDkey;5;");
    } 
    if(spannung2 < 765 && spannung2 > 730){
          Serial.println("VFDkey;6;");
    } 
    if(spannung2 < 1015 && spannung2 > 985){
          Serial.println("VFDkey;8;");
    } 
    if(spannung2 < 870 && spannung2 > 840){
          Serial.println("VFDkey;BAND;");
    } 
     if(spannung2 < 955 && spannung2 > 925){
          Serial.println("VFDkey;9;");
    } 
}

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
   Serial.println("VFD;bad_rwmode");
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
    Serial.println("VFD;address_error");
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
    Serial.println("VFD;bad_pulse_with");
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
