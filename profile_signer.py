#!/usr/bin/python

import argparse
import subprocess
import os
import sys
try:
    import FoundationPlist as plistlib
except ImportError:
    import plistlib as plistlib

def main():
    parser = argparse.ArgumentParser(description='Sign or encrypt mobileconfig profiles, using either a cert + key file, or a keychain certificate.')
    parser.add_argument('sign', choices=('sign', 'encrypt', 'both'), help='Choose to sign, encrypt, or do both on a profile.')
    key_group = parser.add_argument_group('Keychain arguments', description='Use these if you wish to sign with a Keychain certificate.')
    key_group.add_argument('-k', '--keychain', help='Name of keychain to search for cert. Defaults to login.keychain',
                        default='login.keychain')
    key_group.add_argument('-n', '--name', help='Common name of certificate to use from keychain.', required=True)
    parser.add_argument('infile', help='Path to input .mobileconfig file')
    parser.add_argument('outfile', help='Path to output .mobileconfig file. Defaults to outputting into the same directory.')
    args = parser.parse_args()
    print "fuck yeah"
    
    if args.sign == 'encrypt' or args.sign == 'both':
        # encrypt the profile only, do not sign
        with open(args.infile, mode='rb') as inprofile:
            myProfile = plistlib.readPlist(inprofile)
        payloadContent = myProfile['PayloadContent']
        cmd = ['/usr/bin/openssl', 'smime', '-encrypt', '-aes256', '-outform', 'pem', 
                '-in', args.infile, '-out', args.outfile]
        security_cmd = ['/usr/bin/security', 'find-certificate', '-c', args.name, '-p' ]
        if args.keychain:
            security_cmd += ['args.keychain']
        proc = subprocess.Popen(security_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (sout, serr) = proc.communicate()
    
    if args.sign == 'sign' or args.sign == 'both':
        # sign the profile only
        # Keychain check:
        if not args.name:
            print >> sys.stderr, 'Error: A certificate common name is required to sign profiles with the Keychain.'
            sys.exit(22)
        cmd = ['/usr/bin/security', 'cms', '-S', '-N', args.name, '-i', args.infile, '-o', args.outfile ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (sout, serr) = proc.communicate()
        if serr:
            print >> sys.stderr, 'Error: %s' % serr
            sys.exit(1)
        
if __name__ == '__main__':
    main()