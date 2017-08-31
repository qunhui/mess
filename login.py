#!/usr/bin/python

import os
import sys
import pty
import time
import getpass
import hashlib
import base64
import re
import subprocess

if len(sys.argv) != 3:
    print '''\nThis is used to login hosts and do some operations automatically,
If you want to operate for a batch of hosts and pass multiple commands to a host, 
seperate hosts and commands by a comma<,>, and closed them by quotes<\">. 
And please escape special symbols, such as <$,`> if your command has them.
'''
    print 'Useage:'
    print ''.join(['       ',sys.argv[0],' \"A.B.C.D,A.B.C.D,...\" \"command,command,...\"\n'])
    exit()

user='root'
#passwd=sys.argv[2]
hosts=sys.argv[1].split(',')
cmds=sys.argv[2].split(',')


try:
    user=raw_input("Username: ")
    passwd=getpass.getpass("Password: ")
except:
    print '\n % quit by accident'
    exit()
if not passwd:
    print ('Input a password!')
    exit()

deadhosts=[]
invalidhosts=[]
validhosts=[]
alivehosts=[]
portclose=[]

for ind,host in enumerate(hosts):
    mac=re.sub(r'[:\-\.]','',host)
    if len(host.split('.'))==4: 
        if not re.match(r'^((\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])$', host):  
            invalidhosts.append(host) 
            #print host,'is not a valid host IP address!'
            #exit()
        else:
            validhosts.append(host)
    else:
        #print host,'is not a valid host IP or MAC address'
        invalidhosts.append(host) 
        #exit()


if invalidhosts:
    print '\nFollowing hosts are not invalid:\n *','\n * '.join(invalidhosts)
    try:
        yesno=raw_input('\nDo you want to continue?(yes/no) ')
    except:
        print '\n % quit by accident'
        exit()
    if yesno != 'yes':
       exit() 
            
sys.stdout.write('\nValid hosts network connection checking...')

if validhosts:
    for host in validhosts:
        with open(os.devnull,'w') as fnull:
            result=subprocess.call(' '.join(['ping -W1 -c1',host]),shell=True,stdout=fnull,stderr=fnull)
            if result!=0:
                deadhosts.append(host)
            else:
                alivehosts.append(host)
    sys.stdout.write(', Done\n')
else:
    print 'All hosts are not invalid, quit process\n'
    exit()

if len(deadhosts)>0:
    print '\nFollowing hosts failed to connect:\n * ','\n * '.join(deadhosts)
    try:
        yesno=raw_input('\nDo you want to continue?(yes/no) ')
    except:
        print '\n % quit by accident'
        exit()
    if yesno != 'yes':
       exit() 
if not alivehosts:
    print 'All hosts are not in active, quit process\n'
    exit() 

#def pylogin():
switch=0
for ind,host in enumerate(alivehosts):
    print ''.join(['\n','-'*41,'>>>\n','No.',str(ind+1),' starting, the host is ',host,'.\n']) 
    commands=[
        '/usr/bin/ssh',
        user+'@'+host,
        '-o', 'NumberOfPasswordPrompts=1',
        '-o', 'StrictHostKeyChecking=no',
    ]
    
    pid,child_fd=pty.fork()
    
    if pid==0:
        os.execv(commands[0],commands)
    else:
        while True:
            try:
                #sys.stdout.flush()
                output=os.read(child_fd, 1000).strip()
                print 'ab'
            except:
                print 'Fetal Error!'
                exit() 
            if output:
                if output[-9:-1].lower()=='password':
                    if switch==0:
                        os.write(child_fd,''.join([passwd,b'\n']))
                        switch=1
                    else:
                        os.write(child_fd,''.join(['admin',b'\n']))
                        switch=0
                elif output[-1:]=='>':
                    os.write(child_fd,''.join([b'devshell',b'\n']))
                elif output[-3:]==':~#':
                    break
                elif output[:17].lower()=='permission denied':
                    print ' %',host,'SSH password wrong! \n'
                    exit()
                elif output[-18:].lower()=='connection refused':
                    print ' %',host,'Connection refused! \n'
                    exit()
            time.sleep(0.1)
            print output
        passcounter=0
        for cmd in cmds:
            os.write(child_fd,''.join([cmd,b'\n']))
            #os.waitpid(pid,0)
            while True:
                try:
                    #sys.stdout.flush()
                    output=os.read(child_fd, 1000).strip()
                except:
                    exit()
                if output[-1:]=='#':
                    break
                elif output[-1:]=='?': #support scp command to copy files
                    os.write(child_fd,''.join(['yes',b'\n'])) 
                elif output[-9:-1].lower()=='password':
                    os.write(child_fd,''.join(['admin',b'\n'])) 
                elif output[:17].lower()=='permission denied':
                    print ' %',host,'SSH/SCP password wrong! \n'
                    exit()
                print output

#if __name__=='__main__':
#    pylogin()
