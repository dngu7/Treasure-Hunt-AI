#           Sample Agent for Text-Based Adventure Game      #
#           Implemented in Python3.6                        #
import socket



class Agent:
    def __init__(self, ip_address, port_no, view_size):
        self.view_window = [[0] * view_size for i in range(view_size))]
        self.TCP_Socket = TCPSocketManager(ip_address, port_no, view_size)

    def print_view():

class TCPSocketManager:
    def __init__(self, ip_address, port_no, view_size):
        self.ip_address = ip_address
        self.port_no = port_no
        self.view_size = view_size
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip_address,port_no))
	    self.sd = self.sock.makefile( 'rw', 0 )
    
    def send_action(self, action):
    
        try:
            self.sd.write(action)
            self.sd.flush()
        except KeyboardInterrupt:
            raise
        return True

    def recv_data(self):
        try:
            while len(msg) != msglen:
    		    data = self.sd.read( min(2048, msglen - len(msg)) )
            if not len(data):
                break
            msg += data
        except KeyboardInterrupt:
            raise
        return msg
        
    def recv_map(self):
        map_data = self.recv_data()
        for i in range(self.view_size):
            for j in range(self.view_size):
                if (i != 2) and (j != 2):
                    
                    

    def close(self):
    	self.sock.close()
		self.sock = None


# Input: python3 Agent -p 31415
port_no = int(sys.argv[2])
ip_address = '127.0.0.1'
view_size = 5


new_agent = Agent(ip_address, port_no)

        


