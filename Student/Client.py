import time
from tkinter import *
from PIL import Image, ImageTk
import socket
import threading
# from tkinter import messagebox
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = -1
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3

    serverInfo = {}
    clientInfo = {}

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtpThread = None
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ####
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        ####
        self.loadedFrame = []
        self.setup = None
        self.start = None
        self.pause = None
        self.teardown = None
        self.fileWritelock = threading.Lock()

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

    def setupMovie(self):
        if self.state == self.INIT:
            self.state = self.SETUP
            self.clientInfo['event'] = threading.Event()
            self.clientInfo['event'].clear()
            threading.Thread(target=self.recvRtspReply).start()
            self.rtspSeq += 1
            reply = "SETUP " + self.fileName + " RTSP/1.0\nCSeq: " + str(self.rtspSeq)
            reply += "\nTransport: RTP/UDP; client_port= " + str(self.rtpPort)
            reply = reply.encode('utf-8')
            self.rtspSocket.send(reply)
        else:
            print("[SET UP ERROR] Something went wrong! Please try again!")

    def exitClient(self):
        if self.state != self.INIT:
            self.rtspSeq += 1
            self.state = self.TEARDOWN
            reply = "TEARDOWN " + self.fileName + " RTSP/1.0\nCSeq: " + str(self.rtspSeq)
            reply += "\nSession: " + str(self.sessionId)
            reply = reply.encode('utf-8')
            self.rtspSocket.send(reply)
            self.clientInfo['event'].set()
            self.rtpSocket.close()
            print("[RtpPacket] Packets received :", len(self.loadedFrame))
            print("[RtpPacket] Packets sent by host :", self.frameNbr)
            print("[RtpPacket] Packets loss rate :", 1 - len(self.loadedFrame)/self.frameNbr)
        self.rtspSocket.close()
        self.master.destroy()

    def pauseMovie(self):
        if self.state == self.PLAY:
            self.rtspSeq += 1
            self.state = self.PAUSE
            reply = "PAUSE " + self.fileName + " RTSP/1.0\nCSeq: " + str(self.rtspSeq)
            reply += "\nSession: " + str(self.sessionId)
            reply = reply.encode('utf-8')
            self.rtspSocket.send(reply)
            self.serverInfo['event'].set()
        else:
            print("[PAUSE ERROR] Something went wrong! Please try again!")

    def playMovie(self):
        if self.state == self.SETUP or self.state == self.PAUSE:
            self.state = self.PLAY
            reply = "PLAY " + self.fileName + " RTSP/1.0\nCSeq: " + str(self.rtspSeq)
            reply += "\nSession: " + str(self.sessionId)
            reply = reply.encode('utf-8')
            self.rtspSocket.send(reply)
            self.openRtpPort()
            self.serverInfo['event'] = threading.Event()
            self.serverInfo['event'].clear()
            threading.Thread(target=self.listenRtp).start()
        else:
            print("[PLAY ERROR] Something went wrong! Please try again!")

    def listenRtp(self):
        while True:
            if self.serverInfo['event'].isSet():
                print("[RTP] RTP PACKET CLOSED")
                break
            data = self.rtpSocket.recv(30720)
            if data:
                self.fileWritelock.acquire()  # acquire lock for writing image file to the disk
                try:
                    print("[RTP 200] RTP data received")
                    packet = RtpPacket()
                    packet.decode(data)
                    if self.frameNbr < packet.seqNum():  # ignore late packets with lower sequence number
                        self.frameNbr = packet.seqNum()
                        movieFile = "cache-" + str(self.sessionId) + ".jpg"
                        with open(movieFile, "wb") as tmp:  # write binary
                            tmp.write(packet.getPayload())  # write actual data
                        self.loadedFrame.append(packet)
                        time.sleep(0.05)  # pause for 50 milliseconds for synchronized with server sending interval
                        photo = ImageTk.PhotoImage(Image.open(movieFile))
                        self.label.configure(image=photo, height=288)
                        self.label.image = photo
                        if photo:
                            print("Success")
                finally:
                    self.fileWritelock.release()  # release the lock
        # self.processRtspRequest(data.decode("utf-8"))

        """Listen for RTP packets."""

        # def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        # pass

        # def updateMovie(self, imageFile):
        # pass
        """Update the image file as video frame in the GUI."""

    def connectToServer(self):
        self.rtspSocket.connect((self.serverAddr, self.serverPort))

    # def sendRtspRequest(self, requestCode):
    # pass
    # """Send RTSP request to the server."""

    def recvRtspReply(self):
        while True:
            if self.clientInfo['event'].isSet():
                print("[RTSP] RTSP PACKET CLOSED \n")
                break
            rtspReply = self.rtspSocket.recv(256)
            if rtspReply:
                rtspReply = rtspReply.decode("utf-8")
                self.parseRtspReply(rtspReply)

        """Receive RTSP reply from the server."""

    def parseRtspReply(self, data):

        reply = data.split("\n")
        message = (reply[0]).split(' ')[1]
        sequence = (reply[1]).split(' ')[1]
        session = (reply[2]).split(' ')[1]
        if message != '200' or sequence != str(self.rtspSeq):
            print('[RTSP MESSAGE ERROR] Something went wrong!')
        else:
            self.sessionId = session
            print('[RTSP SERVER 200] OK \n')

    def openRtpPort(self):
        """Open RTP socket bound to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)
        self.rtpSocket.bind((socket.gethostbyname(socket.gethostname()), self.rtpPort))
        # Set the timeout value of the socket to 0.5sec

    def handler(self):
        self.exitClient()
        """Handler on explicitly closing the GUI window."""