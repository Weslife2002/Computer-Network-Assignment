import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]	 # "192.168.1.3"
		serverPort = sys.argv[2]	 # "5050" 	sys.argv[2]
		rtpPort = sys.argv[3]	 # "9999" 	sys.argv[3]
		fileName = sys.argv[4]		# "movie.Mjpeg" 	sys.argv[4]
	except:
		print("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")	
	
	root = Tk()
	
	# Create a new client
	app = Client(root, serverAddr, serverPort, rtpPort, fileName)
	app.master.title("RTPClient")	
	root.mainloop()
	