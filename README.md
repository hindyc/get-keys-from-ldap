# get-keys-from-ldap

An extension script for OpenSSH to enable fetching ssh public keys from an LDAP directory at login time.

## Deployment:
- Refer to [0] to configure an ActiveDirectory to hold the needed attribute.
- copy the script get-keys-from-ldap.py to /sbin on each host requiring it
- install the python-ldap module (apt-get install python-ldap for Debian, yum install python-ldap for CentOS)
- set ownership on get-keys-from-ldap.py root:root (chown root:root /sbin/get-keys-from-ldap.py)

If you're running selinux in enforcing mode:
- set the context on get-keys-from-ldap.py by reference to another file in /sbin (chcon --reference /sbin/genl /sbin/get-keys-from-ldap.py)
- set the authlogin_nsswitch_use_ldap boolean to true to allow the script to connect to the LDAP server in the context of the sshd process (setsebool -P authlogin_nsswitch_use_ldap 1)

Configure sshd:
- edit /etc/ssh/sshd_config and ensure these two lines appear:
  ```
  AuthorizedKeysCommand /sbin/get-keys-from-ldap.py
  AuthorizedKeysCommandUser nobody
  ```
- restart sshd: systemctl restart sshd
  
## Check:
Before logging in remotely for the first time, make sure your syslog daemon is sending AUTH facility messages somewhere useful.  In rsyslog for example, ensure you have a line like:
  ```auth.*                 /var/log/auth.log```
(it's beyond the scope of this document to show exhaustive examples; the key point is the script uses the AUTH facility to log its status to syslog, and if you don't send those somewhere, there's no convenient way to debug the script.)

Run the script by hand for a user that has the sshPublicKeys attribute defined, (e.g. /sbin/get-keys-from-ldap.py jdoe@yourdomain.com) then tail the auth.log or secure log.  There should be entries like:

  ```
  Feb  6 13:36:36 shell get-keys-from-ldap.py: running /sbin/get-keys-from-ldap.py for authentication of jdoe. 
  Feb  6 13:36:36 shell get-keys-from-ldap.py: Returned an ssh key successfully.
  ```
Run the script by hand for a user that *does not have* the sshPublicKeys attribute defined, then tail the auth.log or secure log.  There should be entries like:
  ```
  Feb  6 13:36:49 shell get-keys-from-ldap.py: running /sbin/get-keys-from-ldap.py for authentication of bsmith.
  Feb  6 13:36:49 shell get-keys-from-ldap.py: No SSH keys in AD for chindy.
  ```
If there are any error lines logged, either a user was not specified on the command line, or there was a problem binding to the directory.  There should be sufficient logging in the second case to make troubleshooting a reasonable task.

Now, try logging in remotely to the system as a user with the sshPublicKeys attribute defined.  You should not be prompted for a password.
  
## TODO:
- externalize the bind credentials in a config file
- support TLS-encrypted LDAP

## References:
[0] https://blog.laslabs.com/2016/08/storing-ssh-keys-in-active-directory/ -- Article shows how to add the extension attribute to a Microsoft ActiveDirectory schema.

[1] https://man.openbsd.org/sshd_config#AuthorizedKeysCommand -- manpage for sshd_config with details on the AuthorizedKeysCommand directive
