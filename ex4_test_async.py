import random
import re
import os
import os.path
from sys import stdout
import time
import subprocess
import multiprocessing
import argparse


VERBOSE = False
TESTS = 20 # number of tests to run
TESTS_ASYNC = 5

class bcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    OKCYAN = '\033[96m'
    CEND = '\033[0m'


def print_v(obj):
    global VERBOSE
    VERBOSE and print(obj)

def start_server():
    global server_pid
    proc = subprocess.Popen("./ex4_srv.o",shell=True)
    #server_pid = proc.pid
    proc2 = subprocess.Popen("pgrep -n ex4_srv.o",shell=True,stdout=subprocess.PIPE)
    time.sleep(4)
    output = proc2.stdout.read() #get the output from the process run
    print_v(output)
    server_pid = int(output.decode())
    return server_pid

def start_client(server_pid):
    # generate random input to start client with
    num1 = random.randint(0,99)
    operator = random.randint(1,4)
    num2 = random.randint(0,99)
    if(operator==1):
        print("testing: "+str(num1)+"+"+str(num2))
        expected = num1+num2
    elif(operator==2): 
        print("testing: "+str(num1)+"-"+str(num2))
        expected = num1-num2
    elif(operator==3):
        print("testing: "+str(num1)+"*"+str(num2))
        expected = num1*num2
    elif(operator==4):
        if(num2==0): num2=1
        print("testing: "+str(num1)+"/"+str(num2))
        expected = num1//num2

    proc = subprocess.Popen("./ex4_client.o " + str(server_pid)+ " " +str(num1)+ " "+str(operator)+" "+str(num2),shell=True,stdout=subprocess.PIPE)
    output = proc.stdout.read() #get the output from the process run
    output = int(output.decode())
    if output== expected:
        print(bcolors.OKGREEN+"Expected: "+str(expected)+" Got: "+str(output)+" Correct"+bcolors.CEND)
    else:
        print(bcolors.FAIL+"Expected: "+str(expected)+" Got: "+str(output)+" Wrong"+bcolors.CEND)
        raise AssertionError

def test_zero_div(server_pid):
    num1 = random.randint(0,99)
    proc = subprocess.Popen("./ex4_client.o " + str(server_pid)+ " " +str(num1)+ " "+"4"+" "+"0",shell=True,stdout=subprocess.PIPE)
    output = proc.stdout.read() #get the output from the process run
    output = (output.decode())
    expected = "CANNOT_DIVIDE_BY_ZERO\n"
    print("testing: "+str(num1)+"/"+"0")
    if output== expected:
        print(bcolors.OKGREEN+"Expected: "+str(expected)+" Got: "+str(output)+" Correct"+bcolors.CEND)
    else:
        print(bcolors.FAIL+"Expected: "+str(expected)+" Got: "+str(output)+" Wrong"+bcolors.CEND)
        raise AssertionError

def test_results():
    try:
        server_pid = start_server()
        time.sleep(3)
        # create #TESTS clients to run
        for i in range(TESTS):
            start_client(server_pid)
        test_zero_div(server_pid)
        try:
            test_results_async()
        except Exception as e:
            print_v(e)
            return False
        return True # if we haven't failed an assert of one of the clients
    except Exception as e:
        print_v(e)
        return False

def test_results_async():
    print("testing async client results: ")
    global server_pid
    arr = []
    for i in range(TESTS_ASYNC):
        arr.append(multiprocessing.Process(target=start_client,args=(server_pid,)))
    for p in arr:
        p.start()
    for p in arr:
        p.join()
    
# check for files left over after process
def test_cleanup():
    filename_re = '/to_srv(\..*)?/'
    for filename in os.listdir("."):
        if re.search(filename_re, filename):
            print("to_srv not cleaned")
            return False
    filename_re = 'to_client_\d+(\..*)?'
    for filename in os.listdir("."):
        if re.search(filename_re, filename):
                print("to_client not cleaned")
                return False
    return True

def test_zombies():
    proc = subprocess.Popen("pgrep ex4_srv.o",shell=True,stdout=subprocess.PIPE)
    output = proc.stdout.read() #get the output from the process run
    if(output==b''): return True
    return False

def make():
    proc = subprocess.Popen("make",shell=True,stdout=subprocess.PIPE)
    output = proc.stdout.read() #get the output from the process run
    print_v(output.decode())
    if("error" in output.decode()):
        return False
    else: return True
    

def main():
    try:
        assert make()
    except Exception as e:
        print_v(e)
        print(bcolors.FAIL+"Compilation failed"+bcolors.FAIL)
        exit(-1)

    try:
        assert test_results()
        print(bcolors.OKGREEN+"Passed results"+bcolors.CEND)
        print(bcolors.OKCYAN+"sleeping for timeout"+bcolors.CEND)
        time.sleep(60)
    except AssertionError as e:
        print_v(e)
        print(bcolors.FAIL+"Check results failed"+bcolors.FAIL)
        subprocess.run("pkill -f ex4_srv.o",shell=True) #kill processes left behind
        exit()
    
   
    try:
        assert test_zombies()
        print(bcolors.OKGREEN+"Passed zombie children"+bcolors.CEND)
    except AssertionError as e:
        print_v(e)
        print(bcolors.FAIL+"Failed zombie children"+bcolors.FAIL)
        subprocess.run("pkill -f ex4_srv.o",shell=True) #kill processes left behind
        exit()
    
    try:
        assert test_cleanup()
        print(bcolors.OKGREEN+"Passed cleanup"+bcolors.CEND)
    except AssertionError as e:
        print_v(e)
        print(bcolors.FAIL+"Failed cleanup"+bcolors.FAIL)
        subprocess.run("pkill -f ex4_srv.o",shell=True) #kill processes left behind
        exit()

def get_args():
    global VERBOSE
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()
    VERBOSE = args.verbose
    
if __name__ == "__main__":
    get_args()
    try:
        main()
    except Exception as e:
        print_v(e)
        exit(-1)