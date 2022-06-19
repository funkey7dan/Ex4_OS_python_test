import atexit
import random
import re
import os
import os.path
from sys import stdout
import time
import subprocess
import multiprocessing
import argparse
import difflib


VERBOSE = False
IS_ASYNC = False
TESTS = 20 # number of tests to run
TESTS_ASYNC = 3

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
    time.sleep(5)
    output = proc2.stdout.read() #get the output from the process run
    print_v("Server PID: "+output.decode())
    server_pid = int(output.decode())
    return server_pid

def test_argc():
    print("testing argument num: ")
    proc = subprocess.Popen("./ex4_client.o",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE) # test no arguments
    output = proc.stdout.read().decode()
    expected = "ERROR_FROM_EX4\n"
    print("Testing: "+("./ex4_client.o"))
    if output== expected:
        print(bcolors.OKGREEN+"Expected: "+str(expected)+" Got: "+(output)+" Correct"+bcolors.CEND)
    else:
        print(bcolors.FAIL+"Expected: "+str(expected)+" Got: "+(output)+" Wrong"+bcolors.CEND)
        raise AssertionError   
    # test 6 args    
    proc = subprocess.Popen("./ex4_client.o " + str(server_pid)+" "+"42"+ " "+"2"+" "+"3"+" foo",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print("Testing: "+("./ex4_client.o " + str(server_pid)+" "+"42"+ " "+"2"+" "+"3"+" foo"))
    output = proc.stdout.read().decode()
    if output== expected:
        print(bcolors.OKGREEN+"Expected: "+str(expected)+" Got: "+str(output)+" Correct"+bcolors.CEND)
    else:
        print(bcolors.FAIL+"Expected: "+str(expected)+" Got: "+str(output)+" Wrong"+bcolors.CEND)
        raise AssertionError   


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
    proc = subprocess.Popen("./ex4_client.o " + str(server_pid)+ " " +str(num1)+ " "+str(operator)+" "+str(num2),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output = proc.stdout.read() #get the output from the process run
    errors = proc.stderr.read()
    if(errors!=b''): print_v(errors.decode())
    try:
        output = int(output.decode())
    except ValueError as e:
        print_v(e)
        print(bcolors.FAIL+"Expected: "+str(expected)+" Got: "+str(output.decode())+" Wrong"+bcolors.CEND)
        raise AssertionError
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
        diff = (difflib.ndiff(expected,output))
        print("Differences: ")
        for change in diff:
          if change[0] == "-":
            print(b"Missing:"+change[2:].encode())
          elif change[0] == "+":
            print(b"Redundant:"+change[2:].encode())
        raise AssertionError

def test_results():
    global IS_ASYNC
    try:
        # create #TESTS clients to run
        for i in range(TESTS):
            start_client(server_pid)
        test_zero_div(server_pid)
        try:
            if IS_ASYNC:test_results_async()
            else:pass
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
    try:
        for p in arr:
            p.start()
        for p in arr:
            p.join()
    except Exception as e:
        print_v(e)
        return False
    
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
    global server_pid
    try:
        assert make()
    except Exception as e:
        print_v(e)
        print(bcolors.FAIL+"Compilation failed"+bcolors.FAIL)
        exit(-1)
    
    try:
        server_pid = start_server()
    except Exception as e:
        print_v(e)
        print(bcolors.FAIL+"Failed to start server"+bcolors.FAIL)
        exit(-1) 

    try:
        test_argc()
        pass
    except Exception as e:
        print_v(e)
        print(bcolors.FAIL+"Arguments num failed"+bcolors.FAIL)
        exit(-1) 

    try:
        assert test_results()
        print(bcolors.OKGREEN+"Passed results"+bcolors.CEND)
        print(bcolors.OKCYAN+"sleeping for timeout"+bcolors.CEND)
        time.sleep(65)
    except AssertionError as e:
        print_v(e)
        print(bcolors.FAIL+"Check results failed"+bcolors.FAIL)
        exit()
    
    try:
        assert test_zombies()
        print(bcolors.OKGREEN+"Passed zombie children"+bcolors.CEND)
    except AssertionError as e:
        print_v(e)
        print(bcolors.FAIL+"Failed zombie children"+bcolors.FAIL)
        exit()
    
    try:
        assert test_cleanup()
        print(bcolors.OKGREEN+"Passed cleanup"+bcolors.CEND)
    except AssertionError as e:
        print_v(e)
        print(bcolors.FAIL+"Failed cleanup"+bcolors.FAIL)
        exit()

def get_args():
    global VERBOSE
    global TESTS
    global TESTS_ASYNC
    global IS_ASYNC

    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',help='turn verbose on')
    parser.add_argument('--atests', '-t',help='number of async tests to run')
    parser.add_argument('--asynctest', '-a', action='store_true',help='run async tests')
    args = parser.parse_args()
    VERBOSE = args.verbose
    IS_ASYNC = args.asynctest
    
    if(args.atests is not None):TESTS_ASYNC = int(args.atests)



def exit_handler():
    print_v("Exiting...")
    #subprocess.run("pkill -f ex4_srv.o",shell=True)

    
if __name__ == "__main__":
    atexit.register(exit_handler)
    get_args()
    try:
        main()
    except Exception as e:
        print_v(e)
        exit(-1)
