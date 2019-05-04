FILENAME = "11-1.csv"
OUTPUT = "states.txt"

import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['agg.path.chunksize'] = 10000
plt.style.use('seaborn') # pretty matplotlib plots

def draw_cdf(flow,label_name,title):

    x = np.array(flow)

    y_cdf = 1. * np.arange(len(x))/(len(x) - 1)

    # Plot both
    plt.plot(x, y_cdf,label='cdf')
    plt.title(title)
    plt.xscale('log')
    plt.xlabel(label_name)
    plt.ylabel("Probability")
    plt.show()



def getData(fileName):
    f = open(fileName, "r")
    data = []
    for i in f:
        data.append(i)
    f.close()
     
    counter = 0
    while (counter < len(data)):
        data[counter] = data[counter].replace('\n', '')
        data[counter] = data[counter].replace('"', '')
        data[counter] = data[counter].split(',')
        if (len(data[counter]) > 24):
            data[counter][23] = ','.join(data[counter][23:])
            data[counter] = data[counter][:24]
        counter += 1
    return data
 
# function for getting specific packet types
def getPacket(data, protocol):
    protocolPacket = []
    for line in data:
        if line[4] == protocol:
            protocolPacket.append(line)
    return protocolPacket

def getIPCount(data):
    i = 0
    for packet in data:
        if packet[7] in ['4', '6']:
            i += 1
    return i

# get the empty dict of all different protocols in this dataset
def getProtocols(data):
    protocols = dict()
    for line in data:
        protocols[line[4]] = []
    return protocols
 
# add the protocols into their respective dictionary
def groupProtocols(data, protocols):
    for line in data:
        protocols[line[4]].append(line)
 

 
# count the num of packets per protocol
def countPacket(protocolDict, dataLen):
    protocolCount = dict()
    percent = dict()
    for key in protocolDict:
        protocolCount[key] = len(protocolDict[key])
        percent[key] = (len(protocolDict[key])/dataLen) * 100
    return (protocolCount, percent)
 
# get the size of each packet type
def packetHeaderSize(protocolDict):
    protocolSize = dict()
    for key in protocolDict:
        protocolSize[key] = []
    for key in protocolDict:
        if key not in  ['TCP', 'UDP', 'ICMP', 'IPv4', 'IPv6']:
            for packet in protocolDict[key]:
                protocolSize[key].append(int(packet[5]))
        else:
            for packet in protocolDict[key]:
                if key == 'UDP':
                    protocolSize[key].append(8)
                elif key in ['ICMP', 'IPv4', 'IPv6']:
                    protocolSize[key].append(int(packet[8]))
                else:
                    """
                    info = packet[-1]
                    lenSubStr = info[info.index('Len='):]
                    lenSubStr = lenSubStr.replace('Len=', '')
                    lenSub = lenSubStr.split()
                    packetlen = lenSub[0]
                    i = 0
                    while (i < len(packetlen)) and packetlen[i].isdigit():
                        i += 1
                    packetlen = packetlen[:i]
                    protocolSize[key].append(int(packet[5]) - int(packetlen))
                    """
                    protocolSize[key].append(int(packet[20]))
    return protocolSize
 
def packetSize(protocolDict):
    protocolSize = dict()
    for key in protocolDict:
        protocolSize[key] = []
    for key in protocolDict:
        for packet in protocolDict[key]:
            protocolSize[key].append(int(packet[5]))
    return protocolSize    
 
 
 
def getPort(packet):
    if (packet[4] == 'TCP'):
        src = int(packet[9])
        dest = int(packet[10])
    else:
        src = int(packet[21])
        dest = int(packet[22])
    return (src, dest)
     
 
def sortFlow(flowList):
    if len(flowList) > 1:
        mid = len(flowList)//2
        left = sortFlow(flowList[:mid])
        right = sortFlow(flowList[mid:])
 
        return mergeList(left, right)
 
    return flowList
 
def mergeList(left, right):
    out = []
    i=0
    j=0
    while i < len(left) and j < len(right):
        if float(left[i][1]) < float(right[j][1]):
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
 
    out += left[i:]
    out += right[j:]
 
    return out
 
 
def flowInterval(curFlow):
    # curFlow is sorted in ascending time
    out = []
    i = 0
    j = 1
    k = 0
    while j < len(curFlow):
        # THIS IS ASSUMING THAT THE TIME OF THE GRAPH IS IN SECONDS NOT MINUTES
        if (float(curFlow[j][1]) - float(curFlow[i][1])) > 5400:
            out.append(curFlow[k:j])
            k = j
        i += 1
        j += 1
    out.append(curFlow[k:j])
    return out
 
 
def getFlow(packetList):
    flows = dict()
    for packet in packetList:
        (srcPort, destPort) = getPort(packet)
         
        if ((packet[2], packet[3], srcPort, destPort) in flows.keys()):
            flows[(packet[2], packet[3], srcPort, destPort)].append(packet)
        elif ((packet[3], packet[2], destPort, srcPort) in flows.keys()): 
            flows[(packet[3], packet[2], destPort, srcPort)].append(packet)
        else:
            flows[(packet[2], packet[3], srcPort, destPort)] = []
            flows[(packet[2], packet[3], srcPort, destPort)].append(packet)
     
    # sort the flows of each key
    for key in flows.keys():
        curFlow = flows[key]
        curFlow = sortFlow(curFlow)
         
        curFlow = flowInterval(curFlow)
         
        flows[key] = curFlow
     
    return flows



def getHostFlows(tcpFlowDict):
    flows = dict()
    for key in tcpFlowDict.keys():
         
        if ((key[0], key[1]) in flows.keys()):
            flows[(key[0], key[1])] += tcpFlowDict[key]
        elif ((key[1], key[0]) in flows.keys()):
            flows[(key[1], key[0])] += tcpFlowDict[key]
        else:
            flows[(key[0], key[1])] = []
            flows[(key[0], key[1])] += tcpFlowDict[key]
     
    return flows
 
def flowPacketCount(flowDict):
    out = dict()
    for key in flowDict:
        out[key] = []
        for flow in flowDict[key]:
            out[key].append(len(flow))
    return out
 
def flowDuration(flowDict):
    out = dict()
    for key in flowDict:
        out[key] = []
        for flow in flowDict[key]:
            out[key].append(float(flow[-1][1]) - float(flow[0][1]))
    return out
 
def tcpOHRatio(tcpFlowDict):
    flowRatio = dict()
     
    for key in tcpFlowDict.keys():
        flowRatio[key] = []
        for flow in tcpFlowDict[key]:
            hSize = 0
            dSize = 0
            for packet in flow:
                packetlen = float(packet[18])
                hSize += float(packet[5]) - packetlen
                dSize += packetlen
            if dSize == 0:
                flowRatio[key].append(9999)
            else:
                flowRatio[key].append(hSize/dSize)
    return flowRatio
 
 
# calculate interpacket arrival time
def arrivalTime(flowDict):
    out = dict()
    for key in flowDict:
        
        out[key] = []
        for flow in flowDict[key]:
            # as stated, only need to look at the flow between one side
            # so only consider one onstant source and destination port
            (src, dest) = getPort(flow[0])
            flowTime = []
            prevPacket = None
            for packet in flow:
                (curSrc, curDest) = getPort(packet)
                if (curSrc == src) and (curDest == dest):
                    if prevPacket == None:
                        flowTime.append(0)
                        prevPacket = packet
                    else:
                        flowTime.append(float(packet[1]) - float(prevPacket[1]))
                    prevPacket = packet
            out[key].append(flowTime)
    return out

# given a flow (list of packets) determinen the flow state
def getState(flow, endTime):
    i = len(flow) - 1

    if 'SYN' in flow[-1][-1]:
        return 'Request'
    elif 'RST' in flow[-1][-1]:
        return 'Reset'
    
    fin = 0
    ack = 0
    
    while i >= 0:
        if 'ACK' in flow[i][-1]:
            ack += 1
        if 'FIN' in flow[i][-1]:
            fin += 1
        
        
        if (ack == 2) and (fin == 2):
            return 'Finish'
        if fin == 2:
            break
        i -= 1
    
    if (abs(float(flow[-1][1]) - endTime) <= 300):
        return 'Ongoing'
    else:
        return 'Failed'


# get tcp flow states
def flowState(tcpFlowDict, endTime):
    out = dict()
    for key in tcpFlowDict:
        out[key] = []
        
        for flow in tcpFlowDict[key]:
            out[key].append(getState(flow, endTime))
    return out

def outFlowStates(flowStates):
    states = []
    for key in flowStates:
        states += flowStates[key]
    req = states.count('Request')
    rst = states.count('Reset')
    fin = states.count('Finish')
    ongoing = states.count('Ongoing')
    failed = states.count('Failed')
    total = len(states)

    output = open(OUTPUT, "w")

    output.write("The total number of flows: " + str(total))
    output.write("\nThe total number of Request: " + str(req))
    output.write("\nThe total number of Reset: " + str(rst))
    output.write("\nThe total number of Finish: " + str(fin))
    output.write("\nThe total number of Ongoing: " + str(ongoing))
    output.write("\nThe total number of Failed: " + str(failed))

    output.close()
    
    

def getCurMin(top):
    curMin = 0
    i = 1
    while (i < len(top)):
        if (top[i][1] < top[curMin][1]):
            curMin = i
        i += 1
    return curMin



def draw_AllFlowDuration(tcpFlowDict,udpFlowDict):
    # draw the cdf of TCP flow duration
    tcpFlowDur = flowDuration(tcpFlowDict)
    all_tcp_dur = []
    for key in tcpFlowDur.keys():
        all_tcp_dur.append(tcpFlowDur[key][0])
 
    all_tcp_dur.sort()
    draw_cdf(all_tcp_dur,"Flow Duration/seconds","TCP Flow Duration")
    
    # draw the cdf of UDP flow duration
    udpFlowDur = flowDuration(udpFlowDict)    
    all_udp_dur = []
    for key in udpFlowDur.keys():
        all_udp_dur.append(udpFlowDur[key][0])

    all_udp_dur.sort()
    draw_cdf(all_udp_dur,"Flow Duration/seconds","UDP Flow Duration")     
    
    
    # draw the cdf of all flow duration
    udpFlowDur = flowDuration(udpFlowDict)  
    all_dur = all_udp_dur + all_tcp_dur
    all_dur.sort()
    draw_cdf(all_dur,"Flow Duration/seconds","All Flow Duration")     

def numFlows(flowDict):
    flows = 0
    for key in flowDict:
        flows += len(flowDict[key])
    return flows
 
if __name__ == "__main__":
    
    # part 1b
    
    p1b = open('part1b.txt', "w")
     
    data = getData(FILENAME)
    data.pop(0)
    dataLen = len(data)
    tcpPackets = getPacket(data, 'TCP')
    udpPackets = getPacket(data, 'UDP')

    ipPackets = getIPCount(data)
    
    p1b.write("Number of IP packets: " + str(ipPackets))
    p1b.write("\nNumber of TCP packets: " + str(len(tcpPackets)))
    p1b.write("\nNumber of UDP packets: " + str(len(udpPackets)))
    
    protocols = getProtocols(data)
    groupProtocols(data, protocols)
    (protocolCount, protocolPercent) = countPacket(protocols, dataLen)
    headerSize = packetHeaderSize(protocols)
    packetSize = packetSize(protocols)
    
     
    tcpFlowDict = getFlow(tcpPackets)
    udpFlowDict = getFlow(udpPackets)
    
    numTCPFlow = numFlows(tcpFlowDict)
    numUDPFlow = numFlows(udpFlowDict)
     
    tcpFlowPacketCount = flowPacketCount(tcpFlowDict)
    udpFlowPacketCount = flowPacketCount(udpFlowDict)
    
    draw_AllFlowDuration(tcpFlowDict,udpFlowDict)
     
    # draw the cdf of tcp flow size
    tcp_PacketSize = []
    tcp_flowSize = []
    for key in tcpFlowDict.keys():
        total_packet_size = 0
        for i in range(len(tcpFlowDict[key][0])):
            packet_size = tcpFlowDict[key][0][i][5]
            total_packet_size += int(packet_size)
        tcp_PacketSize.append((key,total_packet_size))
        tcp_flowSize.append(total_packet_size)
    tcp_PacketSize.sort(key=lambda tup: tup[1])
    tcp_flowSize.sort()
    draw_cdf(tcp_flowSize,"Flow Size/bytes","TCP Flow Size")   
    
    # draw the cdf of udp flow size
    udp_flowSize = []
    for key in udpFlowDict.keys():
        total_packet_size = 0
        for i in range(len(udpFlowDict[key][0])):
            packet_size = udpFlowDict[key][0][i][5]
            total_packet_size += int(packet_size)
        udp_flowSize.append(total_packet_size)
    udp_flowSize.sort()
    draw_cdf(udp_flowSize,"Flow Size/bytes","UDP Flow Size") 
    
    # draw the total flow size
    total_flowSize = tcp_flowSize + udp_flowSize
    total_flowSize.sort()
    draw_cdf(total_flowSize,"Flow Size/bytes","Total Flow Size")   

    #draw the cdf of tcp flow size in packet count
    tcp_flowSize_PacketCount = []
    for key in tcpFlowPacketCount.keys():
        tcp_flowSize_PacketCount.append(tcpFlowPacketCount[key][0])
    tcp_flowSize_PacketCount.sort()
    draw_cdf(tcp_flowSize_PacketCount,"Flow Size/Packet count","TCP Flow Packets Count")   

    # draw the cdf of udp flow size
    udp_flowSize_PacketCount = []
    for key in udpFlowPacketCount.keys():
        udp_flowSize_PacketCount.append(udpFlowPacketCount[key][0])
    udp_flowSize_PacketCount.sort()
    draw_cdf(udp_flowSize_PacketCount,"Flow Size/Packet count","UDP Flow Packets Count")   

    # draw the total flow size
    total_flowSize_PacketCount = tcp_flowSize_PacketCount + udp_flowSize_PacketCount
    total_flowSize_PacketCount.sort()
    draw_cdf(total_flowSize_PacketCount,"Flow Size/Packet count","Total Flow Packets Count")   

    
    # draw overhead ratio
    tcp_hitRatio = tcpOHRatio(tcpFlowDict)
    hitList = []
    for key in tcp_hitRatio.keys():
        hitList += tcp_hitRatio[key]
    hitList.sort()
    draw_cdf(hitList,"Hit Ratio","TCP OverHead Ratio")    

    tcp_arrivalTime_dict = arrivalTime(tcpFlowDict)
    udp_arrivalTime_dict = arrivalTime(udpFlowDict)

    # draw the cdf o all TCP inter-arrival time
    all_tcp_arrivalTime = []
    for key in tcp_arrivalTime_dict.keys():
        all_tcp_arrivalTime += tcp_arrivalTime_dict[key][0]
    all_tcp_arrivalTime.sort()
    draw_cdf(all_tcp_arrivalTime,"inter-arrival time/seconds","TCP Inter-Arrival Time")
    
    
    # draw the cdf o all UDP inter-arrival time
    all_udp_arrivalTime = []
    for key in udp_arrivalTime_dict.keys():
        all_udp_arrivalTime +=  udp_arrivalTime_dict[key][0]
        
    all_udp_arrivalTime.sort()
    draw_cdf(all_udp_arrivalTime,"inter-arrival time/seconds","UDP Inter-Arrival Time")
    
    all_arrivalTime = all_udp_arrivalTime + all_tcp_arrivalTime
    all_arrivalTime.sort()
    draw_cdf(all_arrivalTime,"inter-arrival time/seconds","All Inter-Arrival Time")


    lastPacketTime = float(data[-1][1])
    flowStates = flowState(tcpFlowDict, lastPacketTime)
    outFlowStates(flowStates)
    
    
    p1b.close()