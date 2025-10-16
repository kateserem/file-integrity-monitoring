from hashlib import sha256 # for computing hashes to detect content changes

def sha256_file(path, chunk_size=1024 * 1024): #1 MB per chunk
    """
    return the SHA-256 hash of a file's contnent
    """
    h = sha256() # create a new SHA-256 object (comes from pythons built-in hashlib module)

    with open(path, "rb") as f: # open file in binary mode

        #read in chunks
        while True:
            chunk = f.read(chunk_size) # read 1 MB at a time
            if not chunk: # if there is nothing left to read, stop
                break
            h.update(chunk) # feed this chunk into the hash calculator
    return h.hexdigest() #return the final hash as a 64-char hexadecimal string
