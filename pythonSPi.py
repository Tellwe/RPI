


#include <bcm2835.h>
import libbcm2835._bcm2835 as soc 
#include <stdio.h>

from ctypes import *
#include "MRF89XA.h"
trRESET = soc.RPI_V2_GPIO_P1_15 	
trCSCON = 26
trCSDATA = soc.RPI_V2_GPIO_P1_13 
#inputs
trIRQ0 =13 
trIRQ1 = soc.RPI_V2_GPIO_P1_11 

#void WriteSPI(unsigned char);
#unsigned char ReadSPI(void);

#void TransiverInitReceiving(void); 
#void TransiverInitTransmitter(void);
#void TransiverInit(void);
#void WriteControlRegTransiver(unsigned char , unsigned char);

#unsigned char RegisterRead(unsigned char);
#void RegisterSet(unsigned char address, unsigned char value);
#unsigned char ReadFIFO(void);
#void WriteFIFO(unsigned char);
#void TransmittString(unsigned char dataString[]);
def ReadSPI():

    value=soc.bcm2835_spi_transfer(0x00)
    return value
 
def ReadFIFO():
    soc.bcm2835_gpio_write(trCSDATA,0);
#    trCSDATA = 0;
    value = ReadSPI();
    soc.bcm2835_gpio_write(trCSDATA,1);
#    trCSDATA = 1;
    return value
	
def WriteSPI(databyte):


	soc.bcm2835_spi_transfer(databyte)
	soc.bcm2835_delayMicroseconds(30)	
	return
def WriteFIFO(Data):

    soc.bcm2835_gpio_write(trCSDATA, 0);
#    trCSDATA = 0;
    WriteSPI(Data);
    soc.bcm2835_gpio_write(trCSDATA, 1);
#    trCSDATA = 1;
    return

def RegisterRead(adress):
    soc.bcm2835_gpio_write(trCSCON,0);
    #trCSCON = 0;
    adress = ((adress<<1)|0x40);
    WriteSPI(adress);
    value=c_ubyte()	 
    value = ReadSPI();
    soc.bcm2835_gpio_write(trCSCON, 1);
    #trCSCON = 1;
    return value
def RegisterSet(adress, value):

    soc.bcm2835_gpio_write(trCSCON,0);
    #trCSCON = 0;
    adress = (adress<<1);
    WriteSPI(adress);
    WriteSPI(value);
    soc.bcm2835_gpio_write(trCSCON,1);

#    trCSCON = 1;
    return
def SetRFMode(mode):
	soc.bcm2835_gpio_write(trCSCON,0);
#	trCSCON = 0;
	mcparam0_read=c_ubyte()
	mcparam0_read = RegisterRead(0x00);
	if mode == 0x80:
		RegisterSet(0x00, (0x00 & 0x1F) | 0x80)
	elif mode == 0x60:				
		RegisterSet(0x00, (mcparam0_read & 0x1F) | 0x60)
	elif mode == 0x40:		
		RegisterSet(0x00, (mcparam0_read & 0x1F) | 0x40)
	elif mode == 0x20:			
		RegisterSet(0x00, (mcparam0_read & 0x1F) | 0x20)
	elif mode == 0x00:				
		RegisterSet(0x00, (mcparam0_read & 0x1F) | 0x00)
		
	soc.bcm2835_gpio_write(trCSCON,1);
#	trCSCON = 1;
	return


def TransiverInit():  
	RegisterSet(0x00, 0x30);					#Set to the right frequency 
	RegisterSet(0x01,(0xA8)); 				#Set transiver into buffer mode
	RegisterSet(0x02, 0x09);	#0x09				#Set the frequency deeviation to 40KHz
	RegisterSet(0x03, 0x07);	#0x09				#Set the bitrate to 25kbps	
	RegisterSet(0x05,(0x0A));				#Set the FIFO-size to 16 bytes and the treshhold for interrupts to 10
	RegisterSet(0x0D,(0x00|0xB0|0x09));	#IRQ0RX = nFIFOEmpty, IRQ1RX = FIFO_THRESHOLD, IRQ0TX = nFIFOEMPTY, IRQ1TX = TXDONE
	RegisterSet(0x0E,(0x01|0x10|0x01));	#	#Start to till FIFO when sync word is detected, start transmission when FIFO_not_full
	RegisterSet(0x10, 0xA3);					#FIltersetting for the transiver
	RegisterSet(0x12,(0x18|0x20|0x06));		#SYNC-word enabled, 32 bit size, 3 errors allowed
	RegisterSet(0x16,0x53);				#
	RegisterSet(0x17,0x59);				#
	RegisterSet(0x18,0x4E);				#
	RegisterSet(0x19,0x43);				#
	RegisterSet(0x1A, 0x72);			 		#Transmitt parameters
	RegisterSet(0x1B, 0x3C);					#Dissable CLKOUT
	RegisterSet(0x1F, 0x80);
	SetRFMode(0x40);					#Set the transiver to syntesize
	#Clear PLL_LOCK-flag so we can see it restore on the new frequency
	RegisterSet(0x0E,(RegisterRead(0x0E)|0x02));
	RegisterSet(0x00, (RegisterRead(0x00)|0x01));
	RegisterSet(0x06,119);					#R-value for 868.35MHz (old 0x5F)
	RegisterSet(0x07,95);					#P-value for 868.35MHz	(old 0x4C)
	RegisterSet(0x08,36);					#S-value for 868.35MHz (old 0x0E)
	RegisterSet(0x09,119);					#R-value for 868.35MHz (old 0x5F)
	RegisterSet(0x0A,95);					#P-value for 868.35MHz	(old 0x4C)
	RegisterSet(0x0B,36);					#S-value for 868.35MHz (old 0x0E)
	SetRFMode(0x40);					#Set the transiver to syntesize
	#Clear PLL_LOCK-flag so we can see it restore on the new frequency
	RegisterSet(0x0E,(RegisterRead(0x0E)|0x02));
	SetRFMode(0x00);
	return 
def TransmittString(dataString):

	#Local variables
	

	#Initiation of transmitt sequence
	SetRFMode(0x20);								#Transiver into Standby
	soc.bcm2835_delay(10);										#Wait for oscillator to wake up
	SetRFMode(0x40);							#Transiver into syntesize
	RegisterSet(0x0E,(RegisterRead(0x0E)|0x02));#Clear the bit for detection for the PLL Lock
	while (RegisterRead(0x0E & 0b00000010)) == 0:	#Wait for the PLL to lock
		h=0
	SetRFMode(0x80);							#Set the transiver into tranmitt mode
	soc.bcm2835_delayMicroseconds(500);									#Transmitter wake-up time


	WriteFIFO(0x53);
	WriteFIFO(0x59);
	WriteFIFO(0x4E);
	WriteFIFO(0x43);

	#Transmitt data
	for cnt in range(0,len(dataString)):
		WriteFIFO(ord(dataString[cnt]))

		

	#wait for transmitt done, set the transiver back to sleep
	while soc.bcm2835_gpio_lev(trIRQ1) == 0:
			q=1
	soc.bcm2835_delayMicroseconds(10);
	SetRFMode(0x00);
	soc.bcm2835_delay(1);
	return




def main():
   
	 #If you call this, it will not actually access the GPIO
# Use for testing
#        bcm2835_set_debug(1);
    if not soc.bcm2835_init():
      	print( "bcm2835_init failed. Are you running as root??")
      	return
    #}
    if not soc.bcm2835_spi_begin:
      	print ("bcm2835_spi_begin failedg. Are you running as root??")
      	return 
    #}    #Set the GPIO inputs and outs
    soc.bcm2835_gpio_fsel(trCSCON, soc.BCM2835_GPIO_FSEL_OUTP)
    soc.bcm2835_gpio_fsel(trCSDATA, soc.BCM2835_GPIO_FSEL_OUTP)
    soc.bcm2835_gpio_fsel(trRESET, soc.BCM2835_GPIO_FSEL_OUTP)
    soc.bcm2835_gpio_fsel(trIRQ0, soc.BCM2835_GPIO_FSEL_INPT)
    soc.bcm2835_gpio_fsel(trIRQ1, soc.BCM2835_GPIO_FSEL_INPT)
    # Configure the SPI comunication
    soc.bcm2835_spi_setBitOrder(soc.BCM2835_SPI_BIT_ORDER_MSBFIRST)     # The default
    soc.bcm2835_spi_setDataMode(soc.BCM2835_SPI_MODE0)                   # The default
    soc.bcm2835_spi_setClockDivider(soc.BCM2835_SPI_CLOCK_DIVIDER_512)  # 512 = 488.28125kHz on Rpi2, 781.25kHz on RPI3
    soc.bcm2835_spi_chipSelect(soc.BCM2835_SPI_CS0)                     # The default
    soc.bcm2835_spi_setChipSelectPolarity(soc.BCM2835_SPI_CS0, 0)      # the default
    soc.bcm2835_gpio_write(trCSCON, 1)
    soc.bcm2835_gpio_write(trCSDATA, 1)

    soc.bcm2835_gpio_write(trRESET, 1)
    soc.bcm2835_delayMicroseconds(100)
    soc.bcm2835_gpio_write(trRESET, 0)
    soc.bcm2835_delay(6)

          
    TransiverInit()
    TransmittString("N1BLINK")	
if __name__ == '__main__':
    main()



#**************************************************************************************
# Send one uint8_t on the SPI
#**************************************************************************************

#**************************************************************************************
# Read one byte on the SPI
#******************************************
#**************************************************************************************
# Initiate the transiver
#**************************************************************************************


#*********************************************************************
# * WORD RegisterRead()
# *
# * Overview:        
# *              This function access the control register of MRF89XA.
# *              The register address and the register settings are
# *              the input
# *
# * PreCondition:    
# *              None
# *
# * Input:       
# *          WORD    setting     The address of the register and its
# *                              corresponding settings
# *
# * Output:  None    
# *
# * Side Effects:    Register settings have been modified
# *
# ********************************************************************/


#*********************************************************************
# * void RegisterSet(uint8_t address, uint8_t value)
# *
# * Overview:        
# *              This function access the control register of MRF89XA.
# *              The register address and the register settings are
# *              the input
# *
# * PreCondition:    
# *            	 None
# *
# * Input:       
# *          WORD    setting     The address of the register and its
# *                              corresponding settings
# *
# * Output:  None    
# *
# * Side Effects:    Register settings have been modified
# *
# ********************************************************************/


#/*********************************************************************
# * uint8_t ReadFIFO(void)
# *
# * Overview:        
# *              The function reads one byte from the FIFO
# *
# * PreCondition:    
# *              MRF89XA transceiver has been properly initialized
# *
# * Input:       
# *              None
# *
# * Output:      Data from FIFO
# *
# * Side Effects:    
# *              The packet has been sent out
# *
# ********************************************************************/


#/*********************************************************************
# * void WriteFIFO(uint8_t Data)
# *
# * Overview:        
# *              This function fills the FIFO
# *
# * PreCondition:    
# *              MRF89XA transceiver has been properly initialized
# *
# * Input:       
# *              uint8_t   Data - Data to be sent to FIFO.
# *
# * Output:      None
# *
# * Side Effects:    
# *              The packet has been sent out
# *
# ********************************************************************/


