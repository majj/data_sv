# -*-coding:utf-8 -*
import time


def parse_ip(ip):
    """
    IP地址分解，用于根据IP获取所需信息（工位、工单、零件等）
    type, key, val, ip 
    """
    
    timestamp = 1000*time.time()
    
    numbers = ip.split(".")
    lastv = int(numbers[3])    
    
    last_a = lastv%10
    
    if last_a == 1:
        
        group = "ws:{}".format(lastv)
        return 1, lastv, numbers, ip, group, timestamp
    else:
        
        ipkey = lastv//10 * 10 + 1
        
        group = "ws:{}".format(ipkey)
        
        zcopy = numbers[:3]
        zcopy.append(str(ipkey))
        return last_a, ipkey, numbers,  ".".join(zcopy), group, timestamp