from project import *
FILENAME = "11.csv"
OUT = '1a.txt'

# get the empty dict of all different link types in the data set
def getLink(data):
    link = dict()
    for line in data:
        if (len(line) > 6):
            link[line[6]] = []
        else:
            print(line)
    return link

# add the protocols into their respective dictionary
def groupLinks(data, protocols):
    for line in data:
        protocols[line[6]].append(line)

def getNetworkLayer(data):
    out = []
    for packet in data:
        if ('4' == packet[8]) or ('6' == packet[8]):
            out.append(packet)
    return out

if __name__ == "__main__":
    output = open(OUT, "w")
    
    # get the data from the file
    data = getData(FILENAME)
    data.pop(0)
    dataLen = len(data)
    
    # get the link data set
    links = getLink(data)
    groupLinks(data, links)
    linkSize = packetSize(links)
    
    output.write('Total number of packets: ' + str(dataLen) + '\n')
    output.write('Link Layer packets: \n')
    for key in links.keys():
        output.write('   ' + key + ' type packets: ' + str(len(links[key])))
        output.write('\n        accounting for ' + str((len(links[key]) / dataLen) * 100) + '%\n')
        output.write('        ' + str(sum(linkSize[key])) + 'bytes\n')
    
    protocols = getProtocols(data)
    groupProtocols(data, protocols)
    protocolSize = packetSize(protocols)
    
    otherSize = 0
    otherPackets = 0
    output.write('Network Layer Packets: \n')
    for key in protocols.keys():
        if key in ['ICMP', 'IPv4', 'IPv6', 'ARP']:
            output.write('    ' + key + ' type packets: ' + str(len(protocols[key])))
            output.write('\n        accounting for ' + str((len(protocols[key]) / dataLen) * 100) + '%\n')
            output.write('        ' + str(sum(protocolSize[key])) + 'bytes\n')
        else:
            otherPackets += len(protocols[key])
            otherSize += sum(protocolSize[key])
    
    output.write('    other' + ' type packets: ' + str(otherPackets))
    output.write('\n        accounting for ' + str((otherPackets / dataLen) * 100) + '%\n')
    output.write('        ' + str(otherSize) + 'bytes\n')    
            
    
    output.write('Transport Layer Packets: \n')
    output.write('Network Layer Packets: \n')
    
    otherSize = 0
    otherPackets = 0
    
    for key in protocols.keys():
        if key in ['TCP', 'UDP']:
            output.write('    ' + key + ' type packets: ' + str(len(protocols[key])))
            output.write('\n        accounting for ' + str((len(protocols[key]) / dataLen) * 100) + '%\n')
            output.write('        ' + str(sum(protocolSize[key])) + 'bytes\n')    
        else:
            otherPackets += len(protocols[key])
            otherSize += sum(protocolSize[key])        
    output.write('    other' + ' type packets: ' + str(otherPackets))
    output.write('\n        accounting for ' + str((otherPackets / dataLen) * 100) + '%\n')
    output.write('        ' + str(otherSize) + 'bytes\n')    

    output.close()
    
    
    