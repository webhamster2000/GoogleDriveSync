# GoogleDrive Sync

This script will pull your GoogleDrive content into the local directory.
Incl. restoring the directory structure. With every run, only new files will become copied.
The script will not uploading files and it will NOT delete files, even when deleted on GoogleDrive.

How to use:
 * create a directory
 * get your personal client secrets
     * You need a "client_secrets.json" file, I can't provide because I'm not doing this commercially.
     * A very good get started page can be found at https://developers.google.com/drive/web/quickstart/python
       and a step-by-step process at https://github.com/jay0lee/GAM/wiki/Creating-client_secrets.json-and-oauth2service.json
     * place this file into <GoogleDriveSync-path>
 * call python <GoogleDriveSync-path>/drive.py
 * wait until the script finished downloading. Please be patient, it can take a while.

You will be asked for login information for your google account on first run.
If you are working on a remote system, use 

python drive.py --noauth_local_webserver for first start.

Feel free to add extensions or fork your own project.
Enjoy the script!
