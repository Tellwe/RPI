


#include <bcm2835.h>
import libbcm2835._bcm2835 as soc 
#include <stdio.h>
import select as select
from ctypes import *
from bluetooth import *

server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"







TransmittedString = [1024]
trRESET = soc.RPI_V2_GPIO_P1_15 	
trCSCON = 26
trCSDATA = soc.RPI_V2_GPIO_P1_13 
#inputs
trIRQ0 =13 
trIRQ1 = soc.RPI_V2_GPIO_P1_11 
#*************************************************************************************
# Read one byte on the SPI
#*************************************************************************************
def ReadSPI():
	value=soc.bcm2835_spi_transfer(0x00)
	return value
#*************************************************************************************
#	ReadFIFO()
#
#	Overview:
#			The function reads one byte from the FIFO
#
#	PreCondition:
#			MRF89XA transciever has been properly initialized
#
#	input:
#			None
#
#	Output:
#			Data from FIFO
#
#	Side effecs:
#			the packet has been sent out
#*************************************************************************************			
def ReadFIFO():
	soc.bcm2835_gpio_write(trCSDATA,0);
	value = ReadSPI();
	soc.bcm2835_gpio_write(trCSDATA,1);
	return value
#*************************************************************************************
# Send one uint8_t on the SPI
#*************************************************************************************	
def WriteSPI(databyte):
	soc.bcm2835_spi_transfer(databyte)
	soc.bcm2835_delayMicroseconds(30)	
	return
#*************************************************************************************
#
#	WriteFIFO(Data)
#
#	Overview:
#			This function fills the FIFO
#
#	PreCondition:
#			MRF89XA transceiver has been properly initialized
#
#	Input:
#			Data - Data to be sent to FIFO
#
#	Output:
#			None
#
#	Side effects:
#			The packet has been sent out
#*************************************************************************************
def WriteFIFO(Data):
	soc.bcm2835_gpio_write(trCSDATA, 0);
	WriteSPI(Data);
	soc.bcm2835_gpio_write(trCSDATA, 1);
	return
#************************************************************************************
#	RegisterRead(adress)
#
#	Overview:
#			This function access the control register of MRF89XA.
#			The register address and the register settings are
#			input.
#
#	PreCondition:
#			None
#
#	Input: 
#			Data
#
#	Output:
#			None
#
#	Side effects:
#			Register settings have been modified
#************************************************************************************
def RegisterRead(adress):
	soc.bcm2835_gpio_write(trCSCON,0);
	adress = ((adress<<1)|0x40);
	WriteSPI(adress);
	value=c_ubyte()	 
	value = ReadSPI();
	soc.bcm2835_gpio_write(trCSCON, 1);
	return value
#************************************************************************************
#	RegisterSet(adress, value)
#
#	Overview: 
#			This function access the control of MRF89XA.
#			The register adress and the register
#			settings are the input.
#
#	 PreCondition:
#			None
#
# 	Input: 
# 			adress, value
#
#	Output:
#			None
#
#	Side effects:
#			Register settings have been modified
#************************************************************************************
def RegisterSet(adress, value):
	soc.bcm2835_gpio_write(trCSCON,0);
	adress = (adress<<1);
	WriteSPI(adress);
	WriteSPI(value);
	soc.bcm2835_gpio_write(trCSCON,1);
	return

def SetRFMode(mode):
	soc.bcm2835_gpio_write(trCSCON,0);
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
	return

#************************************************************************************
# TransiverToReceive()
#
#function sets the transiver into receive mode
#************************************************************************************
def TransiverToReceive():
	SetRFMode(0x20)
	soc.bcm2835_delay(10)
	SetRFMode(0x40)
	RegisterSet(0x0E,(RegisterRead(0x0E)|0x02))
	while (RegisterRead(0x0E)&0b00000010)==0:
		x=1
	SetRFMode(0x60)
	soc.bcm2835_delayMicroseconds(500)
	return

#************************************************************************************
#TransiverReadFIFO()
#Function reads the fifo from the transiver and returns the data package
#************************************************************************************
def TransiverReadFIFO():
	global TransmittedString
	SetRFMode(0x20)
	i=0
	print 'Transiver read fifo:    '
	while soc.bcm2835_gpio_lev(13) == 1:
		tmp = ReadFIFO()
		
		print(bin(tmp))
		TransmittedString.append(tmp)
		if tmp == 44:
			print("New Packet:")
							
		i=i+1

	soc.bcm2835_delay(10)
	SetRFMode(0x00)
	return	
#************************************************************************************
# Initiate the transiver
#************************************************************************************
def TransiverInit():  
	RegisterSet(0x00, 0x30);				#Set to the right frequency 
	RegisterSet(0x01,(0xA8)); 				#Set transiver into buffer mode
	RegisterSet(0x02, 0x09);				#Set the frequency deeviation to 40KHz
	RegisterSet(0x03, 0x07);				#Set the bitrate to 25kbps	
	RegisterSet(0x05,(0x0A));				#Set the FIFO-size to 16 bytes and the treshhold for interrupts to 10
	RegisterSet(0x0D,(0x00|0xB0|0x09));			#IRQ0RX = nFIFOEmpty, IRQ1RX = FIFO_THRESHOLD, IRQ0TX = nFIFOEMPTY, IRQ1TX = TXDONE
	RegisterSet(0x0E,(0x01|0x10|0x01));			#Start to till FIFO when sync word is detected, start transmission when FIFO_not_full
	RegisterSet(0x10, 0xA3);				#FIltersetting for the transiver
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
 
def TransmittString(topic, value):
	#Initiation of transmitt sequence
	SetRFMode(0x20);					#Transiver into Standby
	soc.bcm2835_delay(10);					#Wait for oscillator to wake up
	SetRFMode(0x40);					#Transiver into syntesize
	RegisterSet(0x0E,(RegisterRead(0x0E)|0x02));		#Clear the bit for detection for the PLL Lock
	while (RegisterRead(0x0E & 0b00000010)) == 0:		#Wait for the PLL to lock
		h=0
	SetRFMode(0x80);					#Set the transiver into tranmitt mode
	soc.bcm2835_delayMicroseconds(500);			#Transmitter wake-up time


	WriteFIFO(0x53);
	WriteFIFO(0x59);
	WriteFIFO(0x4E);
	WriteFIFO(0x43);

	#Transmitt datat
	WriteFIFO(44)
	WriteFIFO(topic)
	WriteFIFO(value)
	writeFIFO(55)

	print 44, topic, value, 55
	#wait for transmitt done, set the transiver back to sleep
	while soc.bcm2835_gpio_lev(trIRQ1) == 0:
			q=1
	soc.bcm2835_delayMicroseconds(10);
	SetRFMode(0x00);
	soc.bcm2835_delay(1);
	return

def main():
 	global TransmittedString
	 
	 #If you call this, it will not actually access the GPIO
	# Use for testing
	#        bcm2835_set_debug(1);
	if not soc.bcm2835_init():
  		print( "bcm2835_init failed. Are you running as root??")
  		return

	if not soc.bcm2835_spi_begin:
  		print ("bcm2835_spi_begin failedg. Are you running as root??")
  		return 
	#Set the GPIO inputs and outs
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
	print "Initiation Complete"
	#while False:		
	#	TransiverToReceive()	
	#	while soc.bcm2835_gpio_lev(trIRQ1)==0:
	#		l=0
	#	TransiverReadFIFO()
		#client_soct.send("he")
		#print "sending [%s]" % data	
	advertise_service( server_sock, "SampleServer", service_id = uuid,service_classes = [ uuid, SERIAL_PORT_CLASS ],profiles = [ SERIAL_PORT_PROFILE ],)
                   
	print("Waiting for connection on RFCOMM channel %d" % port)

	client_sock, client_info = server_sock.accept()
	print("Accepted connection from ", client_info)
	client_sock.setblocking(0)
	TransiverToReceive()
	startMessage = False
	topicRecieved = False

	try:
    		while True:
		#	r,_,_ = select.select([client_sock],[],[])
		#	if r:
			try:
						
				data = client_sock.recv(1024)
 				if len(data)==0: break
				print(ord(data[0]))
				print(ord(data[1]))
				print(ord(data[2]))
				print(ord(data[3]))
				TransmittString(data[1],data[2])
						
				
								
			except Exception as e:
				l = 1
		#	client_sock.send("MOKKEL")
		#	if len(data) != 0:
		#		print("BT received %s " % data)
		#		TransmittStringd(data)
		#		TransiverToReceive()
		#	if data=="Flash":
		#		TransmittString(',' + '1' + '1' + '7' )
		#	if data=="Light":
		#		TransmittString("FLASHL")
		#	if data=="N1Flash":
		#		TransmittString("N1BLINK")
		#	if data=="N2Flash":
		#		TransmittString("N2BLINK")

		#	soc.bcm2835_delay(100)	
		#	print "Bustel com"	
			if soc.bcm2835_gpio_lev(trIRQ1)==1:
				TransiverReadFIFO()
				client_sock.send("BAJJJJJJA")
				#print("Bustel sent: %s" %TransmittedString)
			
				TransiverToReceive()	 	
	except IOError:
    		pass

		print("disconnected")

	client_sock.close()
	server_sock.close()
	print("all done") 	
if __name__ == '__main__':
    main()


