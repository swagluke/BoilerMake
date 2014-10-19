import blpapi
import datetime
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


def main():
    global options
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

    refDataService = session.getService("//blp/refdata")
    request = refDataService.createRequest("IntradayTickRequest")
    request.set("security", "ADCB DH Equity")
    request.getElement("eventTypes").appendValue("TRADE")
    request.getElement("eventTypes").appendValue("AT_TRADE")
    request.set("includeConditionCodes", True)

    #tradedOn = getPreviousTradingDate()
    tradedOn = datetime.date(2014,10,16)
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
                    #print msg
                    datasize = msg.getElement("tickData").getElement("tickData").numValues()
                    for num in range(0,datasize):
                        data = msg.getElement("tickData").getElement("tickData").getValueAsElement(num)
                        print data.getElementAsDatetime("time")
                        print data.getElementAsFloat("value")
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

