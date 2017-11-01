import socket
import threading
import argparse
import os
import os.path
import json
import mimetypes

CRLF = "\r\n"

#TODO: add in debug printing messages
#TODO: add in the command line arguments the assignment describes

def run_server(host, port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((host, port))
        listener.listen(5)
        print('File server is listening at', port)
        while True:
            conn, addr = listener.accept()
            threading.Thread(target=handle_client, args=(conn, addr, host, port)).start()
    finally:
        listener.close()

def get_file_dir():
    current_dir = os.getcwd()
    file_dir = current_dir + "\\files\\"
    return file_dir

def get_filename(parsedData):
    if parsedData[1] == '\\' or parsedData[1] == '/':
        return
    return parsedData[1][1:]

def get_file_mimetype(filename):
    #TODO: add error handling if file doesn't exist
    print("I am here")
    print(get_file_dir() + filename)
    if(os.path.isfile(get_file_dir() + filename) == False):
        print("1")
        raise IOError("File " + filename + " does not exist.")
    print("Hello")    
    file_dir = get_file_dir()
    mimetypes.init()
    return mimetypes.guess_type(file_dir + filename)

def get_headers(data):
    headers = {}
    parsedData = data.split(CRLF)
    for i in range(1, len(parsedData)):
        header = parsedData[i]
        #If we reached the empty line between header and body, stop reading header elements
        if header == '':
            break
        headerComponents = header.split(": ")
        headers[headerComponents[0]] = headerComponents[1]
    print(headers)
    return headers

def handle_get(parsedData):
    file_dir = get_file_dir()
    filename = get_filename(parsedData)
    if(os.path.isfile(file_dir + filename) == False):
        print("2")
        print(file_dir + filename)
        raise IOError("File " + filename + " does not exist for GET.")
        
    if not filename:
        return str(os.listdir(file_dir)).encode('utf-8')
    else:
        #TODO: add error handling for if file doesn't exist
        response_body = b''
        with open(file_dir + filename, 'rb') as file:
            while True:
                newData = file.read(1024)
                if not newData:
                    break
                response_body += newData
        return response_body

def handle_post(parsedData, header_data, body_data):
    file_dir = get_file_dir()
    post_command = parsedData[1]
    if(post_command == '/' or post_command == '\\'):
        print("3")
        raise SystemError("Command did not contain a file.")
        
    #TODO: add error handling for if command does not contain a filename (as in, it is just /)
    #TODO: add error handling for if the filename is an invalid filename
    filename = post_command[1:]
    if('$' in filename or ',' in filename or '/' in filename):
        print("4")
        raise IOError("File " + filename + " is an invalid filename.")
    
    overwrite = True
    headers = get_headers(header_data)
    if headers and 'overwrite' in headers:
        overwrite = (headers['overwrite'] == 'true')
    if not overwrite:
        file_list = os.listdir(file_dir)
        if filename in file_list:
            if(os.path.isfile(filename) == True and overwrite == False):
                print("5")
                raise SystemError("File " + filename + " already exists for POST and overwrite was false.")
            #TODO: error message here for if overwrite is false and there is already a file with the requested name
            return
    
    file = open(file_dir + filename, 'wb')
    print("body_data is...")
    print(body_data)
    if(body_data == CRLF.encode('utf-8')):
        print("6")
        raise SystemError("Message body was empty.")
    #TODO: add error handling if message body is null
    file.write(body_data)

def checkIfGoodDirectory(filename):
    cwd = get_file_dir()
    print("Current working directory is: " + cwd)
    print("....")
    print(filename)

def handle_client(conn, addr, host, port):
    print('New client from', addr)
    #try:
    data = b''
    conn.settimeout(0.50)
    #Read in data from the socket until there is a timeout. Then we know there is no more to read
    while True:
        try:
            newData = conn.recv(1024)
            print(newData)
            if not newData:
                break
            data +=  newData
        except:
            break
    
    #Because the body of the message is often binary, we cannot decode it. So look for /r/n/r/n which marks the start of the body and parse header and body separately
    crlf_count = 0
    header_data = b''
    body_data = b''
    for bit in data:
        bit = bit.to_bytes(1, byteorder='big')
        if crlf_count < 4:
            header_data += bit
            if (crlf_count == 0 or crlf_count == 2) and bit == b'\r':
                crlf_count += 1
            elif (crlf_count == 1 or crlf_count == 3) and bit == b'\n':
                crlf_count += 1
            else:
                crlf_count = 0
        else:
            body_data += bit
    print(header_data)
    print(body_data)
    header_data = header_data.decode('utf-8')
    print("data\n\n")
    print(header_data)
    parsedData = header_data.split()
    #print(parsedData)
    response_body = ""
    #TODO: edit the response message if there is an error. Should have a 4xx type response code and a fitting message
    try:
        response = "HTTP/1.1 200 OK%sConnection: keep-alive%sServer: %s%s"%(CRLF, CRLF, host, CRLF)
        if parsedData[0] == "GET":
            filename = get_filename(parsedData)
            checkIfGoodDirectory(filename)
            if filename:
                print("Now I am...")
                type = get_file_mimetype(filename)
                print("Here")
                print(type)
                print("TYPETYPETYPE")
                filetype = type[0]
                if(filetype is None):
                    filetype = ""
                response = response + "Content-Disposition: attachment;filename=\"" + filename + "\"" + CRLF + "Content-Type: " + filetype + CRLF
                print("Good")
            response_body = handle_get(parsedData)
        #TODO: fix post so that it works with binary data like the GET does
        elif parsedData[0] == "POST":
            print("Here")
            response_body = handle_post(parsedData, header_data, body_data)
            print("Now here")
        bytes = response.encode('utf-8')
        print("Great")
        if response_body:
            bytes = bytes + CRLF.encode('utf-8')
            bytes = bytes + response_body
            bytes = bytes + CRLF.encode('utf-8')
        print("Perfect")
        conn.sendall(bytes)
        #finally:
        #    conn.close()
        conn.close()
    except IOError as IO:
        response = "HTTP/1.1 404 ERROR: File could not be found%sConnection: keep-alive%sServer: %s%s"%(CRLF, CRLF, host, CRLF)
        print(response)
        print(IO)
        bytes = response.encode('utf-8')
        conn.sendall(bytes)
    except SystemError as SE:
        response = "HTTP/1.1 400 ERROR: Bad Request%sConnection: keep-alive%sServer: %s%s"%(CRLF, CRLF, host, CRLF)
        print(response)
        print(SE)
        bytes = response.encode('utf-8')
        conn.sendall(bytes)
    except Exception as e:
        response = "HTTP/1.1 300 ERROR: It should not be going here%sConnection: keep-alive%sServer: %s%s"%(CRLF, CRLF, host, CRLF)
        response = response + "Should not be here."
        print(response)
        bytes = response.encode('utf-8')
        conn.sendall(bytes)

# Usage python httpfileserver.py [--port port-number]
parser = argparse.ArgumentParser()
parser.add_argument("--port", help="file server port", type=int, default=8007)
args = parser.parse_args()
run_server('localhost', args.port)

checkIfGoodDirectory("Hello")
