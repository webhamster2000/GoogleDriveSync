import httplib2
import os
from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient import errors
import datetime, time
import sys

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
        
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'

def get_credentials():
    credential_dir = os.path.join(".", '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print ('Storing credentials to ' + credential_path)
    return credentials

credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('drive', 'v2', http = http)
    
def getObjects():
    result = {}
    page_token = None
    print ("Loading objects from Google ")
    start = time.time()
    while True:
        if time.time() - start > 10:
            sys.stdout.write(".")
            sys.stdout.flush()
            start = time.time()        
        try:
            param = {}
            if page_token:
                param['pageToken'] = page_token
            files = service.files().list(**param).execute()
            items = files["items"]
            for item in items:
                if item["labels"]["trashed"] == True:
                    continue
                result[item["id"]] = item
            page_token = files.get('nextPageToken')
            if not page_token:
                break
        except errors.HttpError as error:
            print ('An error occurred: %s' % error)
            break
    print("")
    return result  
  
def getPath(dirs, parents):
    if len(parents) == 0:
        return ""
    if parents[0]["isRoot"] == True:
        return "." + os.path.sep
    key = parents[0]["id"]
    if not key in dirs: return None
    dir = dirs[key]
    return getPath(dirs, dir["parents"]) + dir["title"] + os.path.sep

def createFile(name, content, timestamp):
    print( "Updating file " + name.encode('ascii', 'replace')) 
    basedir = os.path.dirname(name)
    
    if not os.path.exists(basedir):
        os.makedirs(basedir, mode=0o777)
    try:
        os.remove(name) # prevent strange permission errors if using existing files. start from scratch
    except:
        pass

    f = open(name, "wb+")
    f.write(content)
    f.close()
    
    try:
        os.utime(name, (timestamp, timestamp))
    except:
        print ("Set date failed for file" + name + ". Try to run with root permissions.")

def parseTime(s):   
    return time.mktime(datetime.datetime.strptime(s,"%Y-%m-%dT%H:%M:%S.%fZ").timetuple())
    
def main():
    start = time.time()
    print ("Starting syncronization at " + time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()) + "...")
    obj = getObjects()
    dirs = {}
    files = {}
    for o in obj:
        if obj[o]["mimeType"] == 'application/vnd.google-apps.folder':
            dirs[o] = obj[o]
        else:
            files[o] = obj[o]
        
    print ("Reading files started at "  + str(time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())) + "...")
    
    for id in files:
        try:
            if files[id]["title"].strip() == "": continue
            if "hidden" in files[id] and files[id]["hidden"] == True: continue
            parents = files[id]["parents"]
            try:
                name = getPath(dirs, parents)
                if name == None: continue
            except Exception as e:
                print ("getPath() failed"  + str(e)) #parent directory was not found -> is trashed -> skip files also
                continue

            if files[id]["shared"] == True:
                if not "ownedByMe" in files[id] or files[id]["ownedByMe"] == False:
                    name = "." + os.sep + "SharedWithMe" + os.sep
  
            ext = ""
            if files[id]["mimeType"].startswith("application/vnd.google-apps."):
                ext = ".pdf"
                if "SharedWithMe" not in name:
                    name = "." + os.sep + "GoogleDocs" + os.sep
                if "exportLinks" not in files[id]:
                    if files[id]["mimeType"].startswith("application/vnd.google-apps.map"): continue
                    if files[id]["mimeType"].startswith("application/vnd.google-apps.form"): continue                 
                    print ("No PDF export found for " + files[id]["title"] + " (mime: " + files[id]["mimeType"] + ") .. skip")
                    continue
                url = files[id]["exportLinks"]["application/pdf"]
            else:
                if "downloadUrl" not in files[id]:
                    print ("URL not found for " + name + ".. skip")
                    continue
                url = files[id]["downloadUrl"]

            name = name + files[id]["title"] + ext
            timestamp = parseTime(files[id]["modifiedDate"])

            if os.path.isfile(name):
                last_modified_date = int(os.path.getmtime(name))
                if last_modified_date == int(timestamp):
                    continue

            resp, content = service._http.request(url)
            if resp["status"] == "200":
                createFile(name, content, timestamp)
            else:
                print ("error " + resp["status"] + " during read of " + name.encode('ascii', 'replace')) 
        except Exception as e:
            try:
                print ("error reading " +  files[id] + " with exception: " + e)
            except:
                pass

    print ("Syncing done in " + str(int(time.time()-start)) + " seconds..")        

if __name__ == '__main__':
    main()
 
