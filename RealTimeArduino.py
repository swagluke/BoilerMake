import blpapi
import datetime
import serial
import time
from optparse import OptionParser


def parseCmdLine():
    parser = OptionParser(description="Retrieve reference data.")
    parser.add_option("-a",
                      "--ip",
                      dest="host",
                      help="server name or IP (default: %default)",
                      metavar="ipAddress",
                      default="localhost")
    parser.add_option("-p",
                      dest="port",
                      type="int",
                      help="server port (default: %default)",
                      metavar="tcpPort",
                      default=8194)

    (options, args) = parser.parse_args()

    return options


def getPreviousTradingDate():
    tradedOn = datetime.date.today()

    while True:
        try:
            tradedOn -= datetime.timedelta(days=1)
        except OverflowError:
            return None

        if tradedOn.weekday() not in [5, 6]:
            return tradedOn

def updateMean(companyMath,companyMean):
	return (companyMath[len(companyMath)-1]+(companyMean)*(len(companyMath)-1))/(len(companyMath))

def main():
    global options
    global companyMath
    global companyMean
    companyMath = []
    companyMean = 0.0
    arduino = serial.Serial("/dev/ttyUSB0", 19200, timeout = 1)
    options = parseCmdLine()
    

    # Fill SessionOptions
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(options.host)
    sessionOptions.setServerPort(options.port)

    session = blpapi.Session(sessionOptions)

    if not session.start():
        print "Failed to start session."
        return

    if not session.openService("//blp/refdata"):
        print "Failed to open //blp/refdata"
        return

    who = "ADCB DH Equity"
    what = "security"

    refDataService = session.getService("//blp/refdata")
    request = refDataService.createRequest("IntradayTickRequest")
    request.set(what, who)
    request.getElement("eventTypes").appendValue("TRADE")
    request.getElement("eventTypes").appendValue("AT_TRADE")
    request.set("includeConditionCodes", True)

    #tradedOn = getPreviousTradingDate()
    tradedOn = datetime.date(2014,10,16) #(year, month, day)
    #if not tradedOn:
    #    print "unable to get previous trading date"
    #    return

    startTime = datetime.datetime.combine(tradedOn, datetime.time(01, 30))
    request.set("startDateTime", startTime)

    endTime = datetime.datetime.combine(tradedOn, datetime.time(22, 40))
    request.set("endDateTime", endTime)

    session.sendRequest(request)

    try:
        while(True):
            ev = session.nextEvent(500)
            for msg in ev:
                if msg.messageType()=="IntradayTickResponse":
                	#ALL DATA
                    #print msg
                    datasize = msg.getElement("tickData").getElement("tickData").numValues()
                    for num in range(0,datasize):
                    	time.sleep(.3333)
                        data = msg.getElement("tickData").getElement("tickData").getValueAsElement(num)
                        
                        companyMath.append(data.getElementAsFloat("value"))
                        print len(companyMath)
                        companyMean = updateMean(companyMath,companyMean)


                        timeString = data.getElementAsString("time")
                        valueString = str(data.getElementAsFloat("value"))
                        print "Date and Time: "+timeString
                        print "Value (USD): $"+valueString
                        print companyMean
                        arduinoString = who+"~"+what+"~"+valueString+"~"
                        arduino.write(who+"\0")
                        #ALL DATA
                        #print msg.getElement("tickData").getElement("tickData").getValueAsElement(num)
            if ev.eventType() == blpapi.Event.RESPONSE:
                break
    finally:
        session.stop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "Ctrl+C pressed. Stopping..."

