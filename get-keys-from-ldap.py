#!/usr/bin/env python

import ldap
import sys
import syslog

adserver = 'sinatra.lwpca.net'
adport = '389'
binduser = 'CN=LDAP User,CN=Users,DC=lwpca,DC=net'
bindpw = 'w56aUH#8^+>jMxBG$v'

# open a syslog handle
syslog.openlog(facility=syslog.LOG_AUTH)

# check that we got a username on the command line, abort if one
# was not supplied and write a note in the auth.log.
try:
    search_target = sys.argv[1]
    if "@" in search_target:
        search_target = search_target.split("@")[0]
except IndexError:
    syslog.syslog(syslog.LOG_ERR, "User to check in LDAP not specified. Exiting with error.")
    sys.exit(1)

# write an info line in the syslog that we're going to try authenticating.
syslog.syslog(syslog.LOG_INFO, "running %s for authentication of %s." % (sys.argv[0],search_target))

# Initialize an LDAP handle and bind to the directory. Abort if we can't bind 
# and make a note in the syslog.
ldaphandle = ldap.initialize("ldap://%s:%s" %(adserver, adport))
try:
    ldaphandle.protocol_version = ldap.VERSION3
    ldaphandle.simple_bind_s(binduser, bindpw)
    valid = True
except Exception, error:
    syslog.syslog(syslog.LOG_ERR, "Error binding to LDAP: %s" %(error))
    sys.exit(1)

# Search the directory for the account name specified to see if it has
# sshPublicKeys defined.  Get that value back if it exists.
basedn = "CN=Users,dc=lwpca,dc=net"
search_filter = "(&(objectClass=user)(sAMAccountName=%s))" % search_target
search_attribute = ["sshPublicKeys"]
search_scope = ldap.SCOPE_SUBTREE

ldap_result_id = ldaphandle.search(basedn, search_scope, search_filter, search_attribute)
result_set = []
while 1:
    result_type, result_data = ldaphandle.result(ldap_result_id, 0)
    if (result_data == []):
        break
    else:
        if result_type == ldap.RES_SEARCH_ENTRY:
            result_set.append(result_data)
rtn_dn, rtn_vals =  result_set[0][0]
try:
    print rtn_vals['sshPublicKeys'][0].split(":")[1]
except KeyError:
    syslog.syslog(syslog.LOG_INFO, "No SSH keys in AD for %s." % (search_target))
    sys.exit(1)
    
# Completed successfully.  Return a syslog note.
syslog.syslog(syslog.LOG_INFO, "Returned an ssh key successfully.")

