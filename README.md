ProfileSigner
=======

ProfileSigner is a Python script that will encrypt and/or sign a .mobileconfig profile.

Currently, this only works with certificates stored in the Keychain.

## Usage

```
./profile_signer.py -h
usage: profile_signer.py [-h] [-k KEYCHAIN] -n NAME
                         {sign,encrypt,both} infile outfile

Sign or encrypt mobileconfig profiles, using either a cert + key file, or a
keychain certificate.

positional arguments:
  {sign,encrypt,both}   Choose to sign, encrypt, or do both on a profile.
  infile                Path to input .mobileconfig file
  outfile               Path to output .mobileconfig file. Defaults to
                        outputting into the same directory.

optional arguments:
  -h, --help            show this help message and exit

Keychain arguments:
  Use these if you wish to sign with a Keychain certificate.

  -k KEYCHAIN, --keychain KEYCHAIN
                        Name of keychain to search for cert. Defaults to
                        login.keychain
  -n NAME, --name NAME  Common name of certificate to use from keychain.
```

Note that the infile and outfile **must** be named differently.  You cannot overwrite the infile with the outfile.

### Sign a profile

If I wanted to sign a profile such as my [AcrobatPro.mobileconfig](https://github.com/nmcspadden/Profiles/blob/master/AcrobatPro.mobileconfig) with my "3rd Party Mac Developer Application" certificate from the Apple developer site, I'd use this command:  
`./profile_signer.py -n "3rd Party Mac Developer Application" sign AcrobatPro.mobileconfig AcrobatProSigned.mobileconfig`

Signing a profile will change the red "Unverified" text underneath the profile name in the Profiles pane of the System Preferences to a green "Verified" text.  Signed profiles cannot be tampered with without breaking the signing validation.

Note that whatever certificate you sign your profiles with must be trusted on your clients, otherwise they will refuse to install it without warning messages.

### Encrypt a profile

If I wanted to encrypt that profile above, with the same certificate, I'd use this command:  
`./profile_signer.py -n "3rd Party Mac Developer Application" encrypt AcrobatPro.mobileconfig AcrobatProEnc.mobileconfig`

Encrypted profiles (that are unsigned) will have encrypted payloads.  While the overall profile structure is visible as XML (and can be modified), the payload itself will be encrypted with the **public key of the certificate** you choose.

Note that the client machine you want to install the profile on must have the **private key of the certificate you signed with** in order to decrypt the profile.  If the client can't decrypt the profile, it can't install it.

If you want to encrypt a profile and ensure only a specific client will be able to receive / use it, you'll want to encrypt it using a machine-specific certificate for that client - and that setup is way outside of the scope of this project.  You could use something like Puppet certs for this.

### Encrypt & Sign profiles

To both encrypt & sign, use this command:  
`./profile_signer.py -n "3rd Party Mac Developer Application" both AcrobatPro.mobileconfig AcrobatProBoth.mobileconfig`

The same rules apply as above - encrypting with the public key means it must be decrypted on the client with the private key.  Signing the profile means the client will complain if the certificate isn't trusted.