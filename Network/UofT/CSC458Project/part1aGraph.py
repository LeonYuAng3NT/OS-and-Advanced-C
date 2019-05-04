FILENAME = "11.csv"

from project import *
import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
import matplotlib as mpl

def draw_packetSize_graphs (packetSize):
      # draw the cdf of all packets size
    all_packets_size =[]
    for key in packetSize.keys():
        all_packets_size += packetSize[key]
    all_packets_size.sort()
    draw_cdf(all_packets_size,"Packet size/bytes","All Packet Size")
    
    # draw the cdf of UDP packet sizes
    packetSize['UDP'].sort() 
    draw_cdf(packetSize['UDP'],"Packet size/bytes","UDP Packet Size")
    
    # draw the cdf of TCP packet sizes
    packetSize['TCP'].sort()
    draw_cdf(packetSize['TCP'],"Packet size/bytes","TCP Packet Size")
    
    # draw the cdf of ip packet sizes
    ipPacketSize = ip_packets_size = packetSize['IPv4']  + packetSize['ICMPv6']
    ipPacketSize.sort()
    draw_cdf(ipPacketSize,"Packet size/bytes","IP Packet Size")
    
    # draw the cdf of Non-IP packet sizes
    non_ip_packets = [e for e in packetSize.keys() if e not in ('UDP', 'TCP','IPv4','ICMPv6')]
    all_non_ip_packets_size = []
    for item in non_ip_packets:
        all_non_ip_packets_size += packetSize[item]
    all_non_ip_packets_size.sort()
    draw_cdf(all_non_ip_packets_size,"Packet size/bytes","Non-IP Packet Size")


    
    
    
 
if __name__ == "__main__":
     
    data = getData(FILENAME)
    data.pop(0)
    dataLen = len(data)
     
    protocols = getProtocols(data)
    groupProtocols(data, protocols)
    (protocolCount, protocolPercent) = countPacket(protocols, dataLen)
    headerSize = packetHeaderSize(protocols)
    packetSize = packetSize(protocols)

    draw_packetSize_graphs (packetSize)
    
    # draw the cdf of header sizes
    headerSize['UDP'].sort()
    headerSize['TCP'].sort()
    ipHeaderSize = headerSize['IPv4'] + headerSize['ICMPv6']
    

    ipHeaderSize.sort()
    draw_cdf(headerSize['TCP'],"header size/bytes","TCP Header Size")
    draw_cdf(headerSize['UDP'],"header size/bytes","UDP Header Size")
    draw_cdf(ipHeaderSize,"header size/bytes","IP Header Size")
