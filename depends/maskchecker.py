# coding=utf-8
def checkpart(banmask, hostmask, i=0):
    banmask = banmask.replace("**", "*")
    
    if i > 50:
        raise Exception("Maximum recursion depth exceeded!")
    i +=1

    if banmask == hostmask:
        return True
    if banmask.replace("**", "*") == "*":
        return True
    if "*" in banmask:
        parts = banmask.split("*")
        
        done = (" * ".join(parts)).split(" ")
        
        for part in parts:
            if part in hostmask:
                hostmask = hostmask.replace(part, "", 1)
            else:
                return False
            done.remove(part)
        return checkpart("".join(done), hostmask, i)
    return False

def checkbanmask(banmask, hostmask):
    if not isinstance(banmask, str):
        raise TypeError("Banmask must be a string!")
    elif not isinstance(hostmask, str):
        raise TypeError("Hostmask must be a string!")
    
    elif not "!" in banmask or not "@" in banmask:
        raise Exception("Banmask must be of the form 'a!b@c'")
    elif not "!" in hostmask or not "@" in hostmask:
        raise Exception("Hostmask must be of the form 'a!b@c'")
    
    elif "*" in hostmask:
        raise Exception("Hostmask must not contain '*'")
    elif banmask == "*!*@*":
        return False
    
    a = {}
    b = {}
    
    a["nick"]  = banmask.split("!")[0]
    a["ident"] = banmask.split("!")[1].split("@")[0]
    a["host"]  = banmask.split("@")[1]
    
    b["nick"]  = hostmask.split("!")[0]
    b["ident"] = hostmask.split("!")[1].split("@")[0]
    b["host"]  = hostmask.split("@")[1]
    
    if ( a["nick"] == b["nick"] and
         a["ident"] == b["ident"] and
         a["host"] == b["host"] ):
        return True

    return ( checkpart(a["nick"], b["nick"]) and 
             checkpart(a["ident"], b["ident"]) and 
             checkpart(a["host"], b["host"]) )
