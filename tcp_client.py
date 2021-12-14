import socket, time
SERVER = "192.168.1.246"#"127.0.0.1"
PORT = 13370
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))



email = 'puppet@gmail.com'
discordID = 'skreee#8782'


tcp_on = True
tcp_state = -1 #send out ID
tcp_tlen = 2
tcp_t = 0
tcp_msg = b''

while tcp_on:
	if(tcp_state == -1):
		intro_msg = "%s,%s"%(email,discordID)
		intro_msg = bytes(intro_msg,'UTF-8')
		msg_len = len(intro_msg)
		bytes_val = msg_len.to_bytes(1, 'little')
		client.sendall(bytes_val + intro_msg)
		tcp_state = 0
		tcp_tlen = 2
		tcp_t = 0
		tcp_msg = b''
	data = client.recv(1024)
	#tcp_msg = data.decode()
	toDigest = len(data)
	c = 0
	while(c < toDigest):
		tcp_msg = tcp_msg + data[c:c+1]
		tcp_t += 1
		print(tcp_msg)
		if(tcp_state == 0 and tcp_t >= tcp_tlen): #receiving order length
			tcp_t = 0
			tcp_tlen = int.from_bytes(tcp_msg, "little")
			tcp_msg = b''
			tcp_state = 1
		elif(tcp_state == 1 and tcp_t >= tcp_tlen):
			tcp_t = 0
			#process order
			myorder = tcp_msg.decode()
			print("received order %s"%(myorder))

			while(True):
				code = 222
				bytes_val = code.to_bytes(2, 'little')
				client.sendall(bytes_val)
				time.sleep(10)

			for_delivery = './kitten.png'
			#send order when done
			f = open(for_delivery, 'rb')
			out = f.read()
			f.close()

			code = 101
			bytes_val = code.to_bytes(2, 'little')

			img_len = len(out)
			img_bytes = img_len.to_bytes(8, 'little')

			client.sendall(bytes_val+img_bytes+out)

			tcp_msg = b''
			tcp_state = -1 #restart the protocol
		c += 1
client.close()