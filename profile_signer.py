#!/usr/bin/python

import argparse
import subprocess
import os
import sys
import tempfile
#try:
#    import FoundationPlist as plistlib
#except ImportError:
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
        # Encrypting a profile:
        # 1. Extract payload content into its own file
        # 2. Serial that file as its own plist
        # 3. CMS-envelope that content (using openssl for now)
        # 4. Remove "PayloadContent" key and replace with "EncryptedPayloadContent" key
        # 5. Replace the PayloadContent <array> with <data> tags instead

        # Step 1: Extract payload content into its own file
        myProfile = plistlib.readPlist(args.infile)
        payloadContent = myProfile['PayloadContent']

        # Step 2: Serialize that file into its own plist
        (pContentFile, pContentPath) = tempfile.mkstemp()
        plistlib.writePlist(payloadContent, pContentPath)
        
        # Step 3: Use openssl to encrypt that content
        # First, we need to extract the certificate we want to use from the keychain
        security_cmd = ['/usr/bin/security', 'find-certificate', '-c', args.name, '-p' ]
        if args.keychain:
            security_cmd += ['args.keychain']
        proc = subprocess.Popen(security_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (sout, serr) = proc.communicate()
        if serr:
            print >> sys.stderr, "Error: %s" % serr
            sys.exit(1)
        # Now write the certificate to a temp file
        (certfile, certpath) = tempfile.mkstemp('.pem')
        try:
            with open(certpath, 'wb') as f:
                f.write(sout)
        except IOError:
            print >> sys.stderr, "Could not write to file!"
            sys.exit(1)      
        # Now use openssl to encrypt the payload content using that certificate
        (encPContentfile, encPContentPath) = tempfile.mkstemp('.plist')
        enc_cmd = ['/usr/bin/openssl', 'smime', '-encrypt', '-aes256', '-outform', 'pem', 
                '-in', pContentPath, '-out', encPContentPath]
        enc_cmd += [certpath] 
        proc = subprocess.Popen(enc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (encout, encerr) = proc.communicate()
        if encerr:
            print >> sys.stderr, "Error: %s" % encerr
            sys.exit(1)
        # openssl smime -encrypt produces no output if successful
        
        # Step 4: Add the new encrypted payload content back into the plist
        with open(encPContentPath, 'rb') as f:
            content = f.readlines()
            content = content[1:-1] #this is to skip the ---BEGIN PKCS7--- and ----END PKCS7---- lines
        encPayload = ""
        for line in content:
            encPayload += ''.join(line.rstrip()) # to get rid of Python's \n everywhere
        del myProfile['PayloadContent']

        # Step 5: Use plistlib.Data to properly encode the content
        myProfile['EncryptedPayloadContent'] = plistlib.Data(encPayload)
        # now save the profile
        plistlib.writePlist(myProfile, args.outfile)
        
        # Now clean up after ourselves
    
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