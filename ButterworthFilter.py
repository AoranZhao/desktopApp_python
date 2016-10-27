# Butterworth Filters, streaming
# Author: Linbo Shao 
# Date: 30 Dec 2015
# description: 


# http://www-users.cs.york.ac.uk/~fisher/mkfilter

#define NZEROS 8
#define NPOLES 8
#define GAIN   1.315523151e+00

# static float xv[NZEROS+1], yv[NPOLES+1];

# double filterloop(double input) {
    # xv[0] = xv[1]; xv[1] = xv[2]; xv[2] = xv[3]; xv[3] = xv[4]; xv[4] = xv[5]; xv[5] = xv[6]; xv[6] = xv[7]; xv[7] = xv[8];
    # xv[8] = input / GAIN;
    # yv[0] = yv[1]; yv[1] = yv[2]; yv[2] = yv[3]; yv[3] = yv[4]; yv[4] = yv[5]; yv[5] = yv[6]; yv[6] = yv[7]; yv[7] = yv[8];
    # yv[8] =   (xv[0] + xv[8]) - 4 * (xv[2] + xv[6]) + 6 * xv[4]
    # + ( -0.5778338981 * yv[0]) + ( -0.0000000000 * yv[1])
    # + (  2.6273036181 * yv[2]) + (  0.0000000001 * yv[3])
    # + ( -4.5041390915 * yv[4]) + ( -0.0000000001 * yv[5])
    # + (  3.4531851375 * yv[6]) + (  0.0000000000 * yv[7]);
    # return yv[8];
    
# }

import math

xv = []
yv = []

def filterloop(input, reset = 0 ):
    '''  Butterworth Filter from 1 Hz to 29 Hz, with sampling rate of 60 Hz. The input should be a 
list of float data. 
  This function has memory effect. i.e. the output is dependent on the inputs in history.
  if you want to reset the memory in the function, call with reset = 1.   '''
    global xv
    global yv
    
    GAIN = 1.315523151e+00
    ans = []
    
    if (len(xv) < 9) or (1 == reset) : 
        xv = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        yv = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    
    for each in input:
        xv.pop(0)
        #print("debug")
        #print(xv)
        xv.append(each/GAIN)
        yv.pop(0)
        yv.append(   (xv[0] + xv[8]) - 4 * (xv[2] + xv[6]) + 6 * xv[4]   \
                    + ( -0.5778338981 * yv[0]) + ( -0.0000000000 * yv[1])   \
                    + (  2.6273036181 * yv[2]) + (  0.0000000001 * yv[3])   \
                    + ( -4.5041390915 * yv[4]) + ( -0.0000000001 * yv[5])   \
                    + (  3.4531851375 * yv[6]) + (  0.0000000000 * yv[7])  )
        ans.append(yv[-1])
    
    return ans

    
# end of filterloop



#test code below
if __name__ == '__main__':
    from math import *
    a = []
    for i in range(0,500):
        tmp = filterloop(  [sin(float(i)/12.0 *  2 * pi) + 10] )
        a += tmp
    print(a)
    
