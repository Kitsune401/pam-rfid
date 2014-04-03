"""
PyRfid

Requirements:
~# apt-get install python-serial

@see http://www.seeedstudio.com/wiki/index.php?title=Electronic_brick_-_125Khz_RFID_Card_Reader#Demo_code
@see https://github.com/johannrichard/SeeedRFIDLib/blob/master/SeeedRFIDLib.cpp

Copyright 2014 Philipp Meisberger (PM Code Works).
All rights reserved. 
"""

import serial
import os
import utilities


class PyRfid(object):
    """
    A python written library for an 125kHz RFID reader.

    Flag for RFID connection start.
    @var hex RFID_STARTCODE

    Flag for RFID connection end.
    @var hex RFID_ENDCODE

    UART serial connection via PySerial.
    @var Serial __serial

    Holds the complete tag after reading.
    @var string __rawTag
    """
    
    RFID_STARTCODE = 0x02
    RFID_ENDCODE = 0x03
    __serial = None
    __rawTag = None
    
    def __init__(self, port = '/dev/ttyUSB0', baudRate = 9600):
        """
        Constructor
        
        @param string port
        @param integer baudRate
        """
        
        ## Validates port
        if ( os.path.exists(port) == False ):
            raise Exception('The RFID sensor port "' + port + '" was not found!')
            
        ## Initializes connection
        self.__serial = serial.Serial(port = port, baudrate = baudRate, bytesize = serial.EIGHTBITS, timeout = 1)

    def __del__(self):
        """
        Destructor

        """
        
        ## Closes connection if established
        if ( ( self.__serial != None ) and ( self.__serial.isOpen() == True ) ):
            self.__serial.close()
    
    def __read(self):
        """
        Reads the complete tag and returns status.
        
        @return boolean
        """
        
        self.__rawTag = None
        rawTag = ''
        calculatedChecksum = 0
        receivedPacketData = []
        index = 0

        while ( True ):
            
            ## Reads on byte
            receivedFragment = self.__serial.read()
            
            ## Collects RFID data
            if ( len(receivedFragment) != 0 ):

                ## Start and stop bytes are string encoded and must be byte encoded
                if ( ( index == 0 ) or ( index == 13 ) ):
                    receivedFragment = utilities.stringToByte(receivedFragment)
                else:
                    rawTag += receivedFragment
                    receivedFragment = int(receivedFragment, 16)

                ## Collects RFID data (hexadecimal) 
                receivedPacketData.append(receivedFragment)
                index += 1              

            ## Packet completly received
            if ( index == 14 ):
            
                ## Checks for invalid packet data
                if ( ( receivedPacketData[0] != self.RFID_STARTCODE ) or ( receivedPacketData[13] != self.RFID_ENDCODE ) ): 
                    raise Exception('Invalid start or stop bytes!')
                
                ## Calculates packet checksum
                for i in range(1, 11, 2):
                    byte = utilities.leftShift(receivedPacketData[i], 4)
                    byte = byte | utilities.leftShift(receivedPacketData[i+1], 0)
                    calculatedChecksum = calculatedChecksum ^ byte
                    
                ## Gets received packet checksum
                receivedChecksum = utilities.leftShift(receivedPacketData[11], 4)
                receivedChecksum = receivedChecksum | utilities.leftShift(receivedPacketData[12], 0)
                
                ## Checks for wrong checksum
                if ( calculatedChecksum != receivedChecksum ):
                    raise Exception('Calculated checksum is wrong!')

                ## Sets complete tag for other methods
                self.__rawTag = rawTag
                
                return True

    def readTag(self):
        """
        Reads out raw tag.

        @return boolean
        """
        
        try:
            while ( self.__read() != True ):
                pass

        except KeyboardInterrupt:
            return False

        return True
            
    @property
    def rawTag(self):
        """
        Returns read raw tag.

        @return string
        """
        
        return self.__rawTag

    @property
    def tagType(self):
        """
        Returns type of read tag.
        
        @return hex (2 bytes)
        """
        
        if ( self.__rawTag != None ):
            return hex(int(self.__rawTag[0:4], 16))
        
        return None
        
    @property
    def tagId(self):
        """
        Returns ID of read tag.
        
        @return string (10 bytes)
        """
        if ( self.__rawTag != None ):

            ## Length of ID is 10 anyway 
            return '%010i' % int(self.__rawTag[4:10], 16)

        return None
            
    @property
    def tagChecksum(self):
        """
        Returns checksum of read tag.
        
        @return hex (1 bytes)
        """
        
        if ( self.__rawTag != None ):
            return hex(int(self.__rawTag[10:12], 16))

        return None
