import numpy as np 

import os
import argparse
import torch
import torch.nn as nn
from sklearn.linear_model import LinearRegression



def quantize(data,pred,error_bound):
    radius=32768
    
    diff = data - pred
    quant_index = (int) (abs(diff)/ error_bound) + 1
    #print(quant_index)
    if (quant_index < radius * 2) :
        quant_index =quant_index>> 1
        half_index = quant_index
        quant_index =quant_index<< 1
        #print(quant_index)
        quant_index_shifted=0
        if (diff < 0) :
            quant_index = -quant_index
            quant_index_shifted = radius - half_index
        else :
            quant_index_shifted = radius + half_index
        
        decompressed_data = pred + quant_index * error_bound
        #print(decompressed_data)
        if abs(decompressed_data - data) > error_bound :
            #print("b")
            return 0,data
        else:
            #print("c")
            data = decompressed_data
            return quant_index_shifted,data
        
    else:
        #print("a")
        return 0,data

parser = argparse.ArgumentParser()
#parser.add_argument('--dropout','-d',type=float,default=0)
parser.add_argument('--error','-e',type=float,default=1e-3)
parser.add_argument('--input','-i',type=str)
parser.add_argument('--output','-o',type=str)
#parser.add_argument('--actv','-a',type=str,default='tanh')
#parser.add_argument('--checkpoint','-c',type=str,default=None)
parser.add_argument('--block','-b',type=int,default=0)
#parser.add_argument('--norm_max','-nx',type=float,default=1)
#parser.add_argument('--norm_min','-ni',type=float,default=-1)
#parser.add_argument('--max','-mx',type=float,default=1)
#parser.add_argument('--min','-mi',type=float,default=0)
parser.add_argument('--level','-l',type=int,default=2)
parser.add_argument('--noise','-n',type=bool,default=False)
parser.add_argument('--intercept','-t',type=bool,default=False)
parser.add_argument('--cubic','-c',type=bool,default=False)
args = parser.parse_args()
level=args.level

#actv_dict={"no":nn.Identity,"sigmoid":nn.Sigmoid,"tanh":nn.Tanh}
#actv=actv_dict[args.actv]
#model=nn.Sequential(nn.Linear(7,1),actv())
#model.load_state_dict(torch.load(args.checkpoint)["state_dict"])
#model.eval()
#for name,parameters in model.named_parameters():
#    print(name)
#    print(parameters.detach().numpy())
size_x=1800
size_y=3600
array=np.fromfile(args.input,dtype=np.float32).reshape((size_x,size_y))
#coefs=np.fromfile(args.checkpoint,dtype=np.float64)
error_bound=args.error*(np.max(array)-np.min(array))

def get_block_index(x,block):
    
    return x//block

#block_size=args.block
#blocked_size_x=(size_x-1)//block_size+1

size=level**2-1
intercept=0.0
reg_xs=[]
reg_ys=[]
for x in range(2*(level-1),size_x,2):
    for y in range(2*(level-1),size_y,2):
        block=array[x-2*(level-1):x+1:2,y-2*(level-1):y+1:2].flatten()
        #print(block)
        reg_x=block[:size]
        if args.noise:
            reg_x+=error_bound*np.random.rand(size)
        reg_y=block[size]
        reg_xs.append(block[:size])
        reg_ys.append(block[size])
res=LinearRegression(fit_intercept=args.intercept).fit(reg_xs, reg_ys)
coefs=res.coef_
if args.intercept:
    intercept=res.intercept_


#blocked_size_y=(size_y-1)//block_size+1

#coef_array=np.zeros((blocked_size_x,blocked_size_y,size),dtype=np.double)

#intercept_array=np.zeros((blocked_size_x,blocked_size_y),dtype=np.double)
qs=[]
us=[]
'''
for x_idx,x_start in enumerate(range(0,size_x,block_size)):
    for y_idx,y_start in enumerate(range(0,size_y,block_size)): 
        
        #x_end=min(x_start+block_size,size_x)
        #y_end=min(y_start+block_size,size_y)

        if block_size%2==0:
            #x_end-=1
            #y_end-=1
            compli=True
        else:
            compli=False
        
        for x in range(x_start,x_end,2):
            for y in range(y_start,y_end,2):
                f_01=array[x-2][y] if x>=2 else 0
                f_10=array[x][y-2] if y>=2 else 0
            
                f_00=array[x-2][y-2] if x>=2 and y>=2 else 0
                
                pred=f_01+f_10-f_00
                q,decomp=quantize(orig,pred,error_bound)
                qs_array[x-x_start][y-y_start]=q
                if 
                   
                
        reg_xs=np.array(reg_xs).astype(np.double)
        reg_ys=np.array(reg_ys).astype(np.double)
        res=LinearRegression(fit_intercept=args.intercept).fit(reg_xs, reg_ys)
        coef_array[x_idx][y_idx]=res.coef_
        intercept_array[x_idx][y_idx]=res.intercept_

print(coef_array[0][0].shape)

'''

for x in range(0,size_x,2):
    for y in range(0,size_y,2):
        if args.block>0 and x%args.block==0 and y%args.block==0:
            continue
        orig=array[x][y]
        if not (x>=2*(level-1) and y>=2*(level-1)):
            
        
            f_01=array[x-2][y] if x>=2 else 0
            f_10=array[x][y-2] if y>=2 else 0
            
            f_00=array[x-2][y-2] if x>=2 and y>=2 else 0
                
            pred=f_01+f_10-f_00
        else:
            block=array[x-2*(level-1):x+1:2,y-2*(level-1):y+1:2].flatten()[:size]
            pred=np.sum(block*coefs)+intercept
        
                
        q,decomp=quantize(orig,pred,error_bound/2)
        qs.append(q)
        if q==0:
            us.append(decomp)
        array[x][y]=decomp
for x in range(0,size_x,2):
    for y in range(1,size_y,2):
        if args.block>0 and x%args.block==0 and y%args.block==0:
            continue
        if y==size_y-1:
            continue
        orig=array[x][y]
        if (not args.cubic) or y-3<0 or y+3>=size_y:
            pred=(array[x][y-1]+array[x][y+1])/2
        else:
            pred=(-array[x][y-3]+9*array[x][y-1]+9*array[x][y+1]-array[x][y+3])/16
        q,decomp=quantize(orig,pred,error_bound)
        qs.append(q)
        if q==0:
            us.append(decomp)
        array[x][y]=decomp


for x in range(1,size_x,2):
    for y in range(0,size_y,2):
        if args.block>0 and x%args.block==0 and y%args.block==0:
            continue
        if x==size_x-1:
            continue
        orig=array[x][y]
        if (not args.cubic) or x-3<0 or x+3>=size_x:
            pred=(array[x-1][y]+array[x+1][y])/2
        else:
            pred=(-array[x-3][y]+9*array[x-1][y]+9*array[x+1][y]-array[x+3][y])/16
        q,decomp=quantize(orig,pred,error_bound)
        qs.append(q)
        if q==0:
            us.append(decomp)
        array[x][y]=decomp
for x in range(1,size_x,2):
    for y in range(1,size_y,2):
        if args.block>0 and x%args.block==0 and y%args.block==0:
            continue
        if x==size_x-1 or y==size_y-1:
            continue
        orig=array[x][y]
        pred=(array[x-1][y]+array[x+1][y]+array[x][y-1]+array[x][y+1])/4
        q,decomp=quantize(orig,pred,error_bound)
        qs.append(q)
        if q==0:
            us.append(decomp)
        array[x][y]=decomp
if size_x%2==0:

    for i in range(0,size_y-1):
        f_01=array[size_x-2][y] 
        f_10=array[size_x-1][y-1] if y else 0
            
        f_00=array[size_x-2][y-1] if y else 0
        orig=array[size_x-1][y]
        pred=f_01+f_10-f_00
        q,decomp=quantize(orig,pred,error_bound)
        qs.append(q)
        if q==0:
            us.append(decomp)
        array[size_x-1][y]=decomp
if size_y%2==0:
    for i in range(0,size_x):
        f_01=array[x-1][size_y-1] if x else 0
        f_10=array[x][size_y-2] 
            
        f_00=array[x-1][size_y-2] if x else 0
        orig=array[x][size_y-1]
        pred=f_01+f_10-f_00
        q,decomp=quantize(orig,pred,error_bound)
        qs.append(q)
        if q==0:
            us.append(decomp)
        array[x][size_y-1]=decomp

quants=np.array(qs,dtype=np.int32)
unpreds=np.array(us,dtype=np.float32)
array.tofile(args.output)
quants.tofile("cld_q.dat")
unpreds.tofile("cld_u.dat")