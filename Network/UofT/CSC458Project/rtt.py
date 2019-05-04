from project import *
import statistics


def sortTime(flowList):
    if len(flowList) > 1:
        mid = len(flowList)//2
        left = sortFlow(flowList[:mid])
        right = sortFlow(flowList[mid:])
 
        return mergeTime(left, right)
 
    return flowList
 
def mergeTime(left, right):
    out = []
    i=0
    j=0
    while i < len(left) and j < len(right):
        if float(left[i][0]) < float(right[j][0]):
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
 
    out += left[i:]
    out += right[j:]
 
    return out

def rtt_estimation(f1,drawing):

    flow = sortTime(f1)

    arriveTimes = []
    all_SRTTs = []
    sample_RTTs = []
    beta = 1/4
    alpha = 1/8
    start = flow[0][0]
    represented_start = start
    end = flow[0][1]
    R = end- start
    SRTT = R
    RTTVAR = SRTT/2
    all_SRTTs.append(SRTT)
    sample_RTTs.append(R)
    arriveTimes.append(end)
    for i in range(1,len(flow)):
        
        RTTVAR = (1- beta) * RTTVAR + beta * abs(SRTT- R)
        SRTT = (1- alpha)* SRTT + alpha * R
        start = flow[i][0]
        end = flow[i][1]
        R = end - start
        all_SRTTs.append(SRTT)
        sample_RTTs.append(R)
        arriveTimes.append(end)
    if drawing == True:
        draw_RTT(all_SRTTs,sample_RTTs,arriveTimes)
    representative_RTT = statistics.median(all_SRTTs)
    return representative_RTT,represented_start



def draw_chart(list_represented_RTT_flows,list_start_time):


    plt.plot(list_start_time,list_represented_RTT_flows)
    plt.title('Starting time vs Representative RTTs')
  
    plt.ylabel('Representative flow ')
    plt.xlabel("Starting time")
    plt.show()
        


def draw_RTT(estimated_RTT,sample_RTT,list_start_time):    

    plt.plot(list_start_time,estimated_RTT)
    plt.title('Arrive time vs Estimated_RTTs')
   
    plt.ylabel('Estimated_RTTs')
    plt.xlabel("Arrive time")
    plt.show()


    plt.plot(list_start_time,sample_RTT)
    plt.title(' Arrive time vs Sample_RTTs')
   
    plt.ylabel('Sample_RTTs')
    plt.xlabel("Arrive time")
    plt.show()

def packetKey(packet):
    info = packet[-1]
    syn = packet[13] == 'Set'
    reset = packet[16] == 'Set'
    fin = packet[15] == 'Set'
    ack = packet[14] == 'Set'
    lenNum = int(packet[18])
    ackNum = int(packet[19])
    
    i = info.index('Seq=')
    seqNum = info[i:].replace('Seq=', '')
    x = 0
    while seqNum[x].isdigit():
        x += 1
    seqNum = int(seqNum[:x])
    return (syn, reset, fin, ack, seqNum, ackNum, lenNum)

# given a list of packets for a flow match the packet to a response
def matchFlow(flow):
    (p1, p2) = getPort(flow[0])
    p1Out = dict()
    p1ToP2 = []
    p2Out = dict()
    p2ToP1 = []
    p1blackList = set()
    p2blackList = set()    
    for packet in flow:
        (src, dest) = getPort(packet)
        # key = [syn, reset, fin, ack, seqNum, ackNum, lenNum]
        key = packetKey(packet)
        if src == p1:
            if key not in p1Out.keys():
                p1ToP2.append(packet)
                p1Out[key] = [packet]
            else:
                p1blackList.add(key)
        else:
            if key not in p2Out.keys():
                p2ToP1.append(packet)
                p2Out[key] = [packet]
            else:
                p2blackList.add(key)
    for key in p1blackList:
        p1Out.pop(key)
    for key in p2blackList:
        p2Out.pop(key)
    
    p2ToP1 = sortFlow(p2ToP1)
    p1ToP2 = sortFlow(p1ToP2)
    
    for key in p1Out.keys():
        packet = p1Out[key][0]
        #key = packetKey(packet)
        # find the packet that this packet would map to
        # syn, only one per sinde
        if (key[0] and not key[3]):
            # look for the packet that ack the syn
            i = 0
            while (len(p1Out[key]) < 2) and (i < len(p2ToP1)):
                incKey = packetKey(p2ToP1[i])
                if incKey[0] and incKey[3]:
                    p1Out[key].append(p2ToP1[i])
                i += 1
        # else if this is a RST or FIN packet
        # CURRENTLY ASSUMING THAT WE DO NOT CARE FOR FIN PACKETS SKEWING DATA
        elif key[2] or key[1]:
            continue
        # ack packets
        elif key[6] != 0:
            """
            assuming that we are not worried about window, so that
            response for an ACK is not taken into consideration
            as per
            https://bb-2018-09.teach.cs.toronto.edu/t/keep-track-of-window-size-when-doing-rtt-estimation/644
            
            # look for the matching incoming
            if key[6] == 0:
                # look for the packet where equivalent to seqNum
                curSeq = key[4]
                i = 0
                # ### find the index of the first packet that has time greather than the packet in p1Out[key]
                while (len(p1Out[key]) < 2) and (i < len(p2ToP1)):
                    incKey = packetKey(p2ToP1[i])
                    if incKey[5] == curSeq:
                        p1Out[key].append(p2ToP1[i])
                    i += 1     
            else:
            """
        
            # look for the packet that acks seq+num
            # [syn, reset, fin, ack, seqNum, ackNum, lenNum]
            seqNum = key[4]
            lenNum = key[6]
            i = 0
            # ### find the index of the first packet that has time greather than the packet in p1Out[key]
            
            incPacket = p2ToP1[i]
            incTime = float(incPacket[1])
            curTime = float(p1Out[key][0][1])
            while (incTime < curTime):
                i += 1
                if (i >= len(p2ToP1)):
                    break
                incPacket = p2ToP1[i]
                incTime = float(incPacket[1])               
                
            
            while (len(p1Out[key]) < 2) and (i < len(p2ToP1)):
                incKey = packetKey(p2ToP1[i])
                if seqNum + lenNum == incKey[5]:
                    p1Out[key].append(p2ToP1[i])
                i += 1
        
    for key in p2Out.keys():
        packet = p2Out[key][0]
        #key = packetKey(packet)
        # find the packet that this packet would map to
        # syn, only one per sinde
        if (key[0] and not key[3]):
            # look for the packet that ack the syn
            i = 0
            while (len(p2Out[key]) < 2) and (i < len(p1ToP2)):
                incKey = packetKey(p1ToP2[i])
                if incKey[0] and incKey[3]:
                    p2Out[key].append(p1ToP2[i])
                i += 1
        # else if this is a RST or FIN packet
        # CURRENTLY ASSUMING THAT WE DO NOT CARE FOR FIN PACKETS SKEWING DATA
        elif key[2] or key[1]:
            continue
        # ack packets
        elif key[6] != 0:
            # look for the packet that acks seq+num
            # [syn, reset, fin, ack, seqNum, ackNum, lenNum]
            seqNum = key[4]
            lenNum = key[6]
            i = 0
            # ### find the index of the first packet that has time greather than the packet in p2Out[key]
            
            incPacket = p1ToP2[i]
            incTime = float(incPacket[1])
            curTime = float(p2Out[key][0][1])
            while (incTime < curTime):
                i += 1
                if (i >= len(p1ToP2)):
                    break
                incPacket = p1ToP2[i]
                incTime = float(incPacket[1])                
                

            while (len(p2Out[key]) < 2) and (i < len(p1ToP2)):
                incKey = packetKey(p1ToP2[i])
                if seqNum + lenNum == incKey[5]:
                    p2Out[key].append(p1ToP2[i])
                i += 1
                    
    return (p1Out, p2Out)



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

def getTop3(hostFlows):
    out = []
    top = []
    for key in hostFlows.keys():
        top.append([key, len(hostFlows[key])])

    i = 0
    while (len(top) > 0):
        if (i < 3):
            out.append(top.pop())
            i += 1
        else:
            curMin = getCurMin(out)
            cur = top.pop()
            if (cur[1] > out[curMin][1]):
                out[curMin] = cur

    for i in range(0, len(out)):
        out[i] = hostFlows[out[i][0]]

    return out

def getRTT(flowMap):
    out = []
    for key in flowMap:
        if len(flowMap[key]) == 2:
            out.append([float(flowMap[key][0][1]), float(flowMap[key][1][1])])
    return out

def compute_estimatedRTTs_and_sampleRTTS(all_top_threes,tcpFlowDict):
    
    all_flow_matches = []
    for key in all_top_threes:
        sampleFlow = tcpFlowDict[key][0]
        
        (f1, f2) = matchFlow(sampleFlow)
        f1Time = getRTT(f1)
        f2Time = getRTT(f2)
        fTime = f1Time + f2Time
        all_flow_matches.append(fTime)

  
    all_representedRTT = []
    all_startTime = []
    for flow in all_flow_matches:
        if len(flow) != 0:
            respresented_RTT,start = rtt_estimation(flow,True)

if __name__ == "__main__":
    data = getData(FILENAME)
    data.pop(0)
    dataLen = len(data)
    tcpPackets = getPacket(data, 'TCP')

    tcpFlowDict = getFlow(tcpPackets)
    tcpFlowPacketCount = flowPacketCount(tcpFlowDict)

    # matching test start

    tcpFlowDur = flowDuration(tcpFlowDict)
    topThree_Duration = []

    for key in tcpFlowDur.keys():
        topThree_Duration.append((key,tcpFlowDur[key][0]))
    topThree_Duration.sort(key=lambda tup: tup[1])

    # Append top three
    final_topThree_Duration = []
    final_topThree_Duration.append(topThree_Duration[len(topThree_Duration)-1][0])
    final_topThree_Duration.append(topThree_Duration[len(topThree_Duration)-2][0])
    final_topThree_Duration.append(topThree_Duration[len(topThree_Duration)-3][0])
   
    tcp_PacketSize = []
    for key in tcpFlowDict.keys():
        total_packet_size = 0
        for i in range(len(tcpFlowDict[key][0])):
            packet_size = tcpFlowDict[key][0][i][5]
            total_packet_size += int(packet_size)
        tcp_PacketSize.append((key,total_packet_size))
    tcp_PacketSize.sort(key=lambda tup: tup[1])
    
    # Top 3 largest TCP flows in terms of packet size:
    final_topThree_PacketSize = []
    final_topThree_PacketSize.append(tcp_PacketSize[len(tcp_PacketSize)-1][0])
    final_topThree_PacketSize.append(tcp_PacketSize[len(tcp_PacketSize)-2][0])
    final_topThree_PacketSize.append(tcp_PacketSize[len(tcp_PacketSize)-3][0])
  
  
    
    
    # Top 3 largest TCP flows in terms of packet number:
    topThree_PacketNumber = []
 
    for key in tcpFlowPacketCount.keys():
        topThree_PacketNumber.append((key,tcpFlowPacketCount[key][0]))
    topThree_PacketNumber.sort(key=lambda tup: tup[1])

    # Append top three
    final_topThree_PacketNumber = []
    final_topThree_PacketNumber.append(topThree_PacketNumber[len(topThree_PacketNumber)-1][0])
    final_topThree_PacketNumber.append(topThree_PacketNumber[len(topThree_PacketNumber)-2][0])
    final_topThree_PacketNumber.append(topThree_PacketNumber[len(topThree_PacketNumber)-3][0])
  
    
    compute_estimatedRTTs_and_sampleRTTS(final_topThree_PacketNumber,tcpFlowDict)
    compute_estimatedRTTs_and_sampleRTTS(final_topThree_PacketSize,tcpFlowDict)
    
    compute_estimatedRTTs_and_sampleRTTS(final_topThree_Duration,tcpFlowDict)



    ### Part 2

    hostFlows = getHostFlows(tcpFlowDict)
    top3_flows = getTop3(hostFlows)

    all_top3_flow_matches = []
    for host in top3_flows:
        curPair = []
        for flow in host:
            (f1, f2) = matchFlow(flow)
            f1Time = getRTT(f1)
            f2Time = getRTT(f2)
            fTime = f1Time + f2Time
            curPair.append(fTime)
        all_top3_flow_matches.append(curPair)

    # get all the mappings from Jack
    
    all_representedRTT = []
    all_startTime = []
    for pair in all_top3_flow_matches:
        curPair = []
        curPairStart = []
        for flow in pair:
            if len(flow) != 0:
                respresented_RTT,start = rtt_estimation(flow,False)
                curPair.append(respresented_RTT)
                curPairStart.append(start)
        all_representedRTT.append(curPair)
        all_startTime.append(curPairStart)
    for i in range(0, len(all_representedRTT)):
        draw_chart(all_representedRTT[i],all_startTime[i])
    




