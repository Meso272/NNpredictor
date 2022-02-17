import numpy as np 

import os
import argparse
#import torch
#import torch.nn as nn
from sklearn.linear_model import LinearRegression
import math
import random
from utils import *

def msc2d(array,x_start,x_end,y_start,y_end,error_bound,rate,maximum_rate,min_coeff_level,max_step,anchor_rate,rate_list=None,x_preded=False,y_preded=False,sz3_interp=False,multidim_level=10,lorenzo=-1,\
sample_rate=0.05,min_sampled_points=10,random_access=False,verbose=False,fix_algo="none",first_level=None,last_level=0,first_order="block"):#lorenzo:only check lorenzo fallback with level no larger than lorenzo level
    #x_y_start should be on the anchor grid
    size_x,size_y=array.shape
    #array=np.fromfile(args.input,dtype=np.float32).reshape((size_x,size_y))
    if lorenzo>=0:
        orig_array=np.copy(array)
    if random_access and lorenzo>=0:
        lorenzo=0
    #error_bound=args.error*rng
    #max_step=args.max_step
    #rate=args.rate
    max_level=int(math.log(max_step,2))
    selected_algos=[]


    qs=[ [] for i in range(max_level+1)]

    us=[]
    edge_qs=[]
#min_coeff_level=args.min_coeff_level
#anchor=args.anchor
    if max_step>0 and (first_level==None or max_level==first_level+1):
    
    #anchor_rate=args.anchor_rate
        if anchor_rate>0:
            anchor_eb=error_bound/anchor_rate
            if verbose:
                print("Anchor eb:%f" % anchor_eb)

            if max_level>=min_coeff_level:
                reg_xs=[]
                reg_ys=[]
                for x in range(x_start+max_step,x_end,max_step):
                    for y in range(y_start,max_step,y_end,max_step):
                        reg_xs.append(np.array([array[x-max_step][y-max_step],array[x-max_step][y],array[x][y-max_step]],dtype=np.float64))
                        reg_ys.append(array[x][y])
                        res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                        coef=res.coef_ 
                        ince=res.intercept_

        
            startx=max_step if x_preded else 0
            starty=max_step if y_preded else 0

            for x in range(x_start+startx,x_end,max_step):
                for y in range(y_start+starty,y_end,max_step):
                    orig=array[x][y]
                    if x and y and max_level>=min_coeff_level:
                        reg_block=np.array([array[x-max_step][y-max_step],array[x-max_step][y],array[x][y-max_step]],dtype=np.float64)
                        pred=np.dot(reg_block,coef)+ince

            
                
                    else:
                        f_01=array[x-max_step][y] if x else 0
                        f_10=array[x][y-max_step] if y else 0
            
                        f_00=array[x-max_step][y-max_step] if x and y else 0
                
                        pred=f_01+f_10-f_00
                
        
                
                    q,decomp=quantize(orig,pred,anchor_eb)
                    qs[max_level].append(q)
                    if q==0:
                        us.append(decomp)
                    array[x][y]=decomp
        else:
            anchor_eb=0
    else:
        pass#raise error
#print(len(qs))

    last_x=((x_end-1)//max_step)*max_step#remember that x_start is divisible by max_step
    last_y=((y_end-1)//max_step)*max_step   
    global_last_x=((size_x-1)//max_step)*max_step
    global_last_y=((size_y-1)//max_step)*max_step
    step=max_step//2
    if first_level==None:
        level=max_level-1
    else:
        level=first_level
    #maxlevel_q_start=len(qs[max_level])
    u_start=len(us)
    cumulated_loss=0.0
    while level>=last_level:#step>0:
        cur_qs=[]
        cur_us=[]
        if rate_list!=None:
            cur_eb=error_bound/rate_list[level]
        else:
            cur_eb=error_bound/min(maximum_rate,(rate**level))
        array_slice=np.copy(array[x_start:last_x+1:step,y_start:last_y+1:step])
        #cur_size_x,cur_size_y=array.shape
    #print(cur_size_x,cur_size_y)
        if verbose:
            print("Level %d started. Current step: %d. Current error_bound: %s." % (level,step,cur_eb))
        best_preds=None#need to copy
        best_absloss=None
        best_qs=[]#need to copy
        best_us=[]#need to copy
        doublestep=step*2
        triplestep=step*3
        x_start_offset=doublestep if x_preded else 0
        y_start_offset=doublestep if y_preded else 0
        
    #linear interp
        absloss=0
        selected_algo="none"
        if level<=multidim_level or not sz3_interp or fix_algo in ["linear","cubic","multidim"]:
            if fix_algo=="none" or fix_algo=="linear":
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+x_start_offset,last_x+1,doublestep):
                        for y in range(y_start+step,last_y+1,doublestep):
                            reg_xs.append(np.array([array[x][y-step],array[x][y+step]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_
            
            
                for x in range(x_start+x_start_offset,last_x+1,doublestep):
                    for y in range(y_start+step,last_y+1,doublestep):
                        #if y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if level>=min_coeff_level:
                            pred= np.dot( np.array([array[x][y-step],array[x][y+step]]),coef )+ince 
                        else:
                            pred=(array[x][y-step]+array[x][y+step])*0.5
                        if (not random_access) or level>lorenzo or x!=x_end-1:#or last_x!=size_x-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                        cur_qs.append(q)
                

                        if q==0:
                            cur_us.append(decomp)
                    #absloss+=abs(decomp)
                        array[x][y]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+step,last_x+1,doublestep):
                        for y in range(y_start+y_start_offset,last_y+1,doublestep):
                            reg_xs.append(np.array([array[x-step][y],array[x+step][y]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_
                for x in range(x_start+step,last_x+1,doublestep):
                    for y in range(y_start+y_start_offset,last_y+1,doublestep):
                        #if x==cur_size_x-1:
                            #continue
                        orig=array[x][y]
                        if level>=min_coeff_level:
                            pred= np.dot( np.array([array[x-step][y],array[x+step][y]]),coef )+ince 
                        else:
                            pred=(array[x-step][y]+array[x+step][y])*0.5
                        if (not random_access) or level>lorenzo or y!=y_end-1:# or last_y!=size_y-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
               
                        cur_qs.append(q)
                        if q==0:
                            cur_us.append(decomp)
                        
                        array[x][y]=decomp
                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(x_start+step,last_x+1,doublestep):
                        for y in range(y_start+step,last_y+1,doublestep):
                            md_reg_xs.append(np.array([array[x-step][y],array[x+step][y],array[x][y-step],array[x][y+step]],dtype=np.float64))
                            md_reg_ys.append(array[x][y])
                            md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                            md_coef=md_res.coef_ 
                            md_ince=md_res.intercept_

        
                for x in range(x_start+step,last_x+1,doublestep):
                    for y in range(y_start+step,last_y+1,doublestep):
                        #if x==cur_size_x-1 or y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if level>=min_coeff_level:
                            pred=np.dot(np.array([array[x-step][y],array[x+step][y],array[x][y-step],array[x][y+step]]),md_coef)+md_ince
                        else:
                            pred=(array[x-step][y]+array[x+step][y]+array[x][y-step]+array[x][y+step])*0.25
                        absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                
                        cur_qs.append(q)
                        if q==0:
                            cur_us.append(decomp)
                    #absloss+=abs(decomp)
                        array[x][y]=decomp

                best_preds=np.copy(array[x_start:last_x+1:step,y_start:last_y+1:step])
                best_absloss=absloss
                best_qs=cur_qs.copy()
                best_us=cur_us.copy()
                selected_algo="interp_linear"

        #print(len(cur_qs))


            #cubic interp
            #cubic=True
            #if cubic:
            #print("cubic")
            if fix_algo=="none" or fix_algo=="cubic":
                absloss=0
                cur_qs=[]
                cur_us=[]
                if selected_algo!=None:
                    array[x_start:last_x+1:step,y_start:last_y+1:step]=array_slice#reset array
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+x_start_offset,last_x+1,doublestep):
                        for y in range(y_start+triplestep,last_y+1,doublestep):
                            if y-triplestep<0 or (random_access and y-triplestep<y_start) or y+triplestep>global_last_y or (  (random_access or (first_order=="block" and level!=max_level-1)) and y+triplestep>last_y) :
                                continue
                            reg_xs.append(np.array([array[x][y-triplestep],array[x][y-step],array[x][y+step],array[x][y+triplestep]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_
                for x in range(x_start+x_start_offset,last_x+1,doublestep):
                    for y in range(y_start+step,last_y+1,doublestep):
                        #if y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if not (y-triplestep<0 or (random_access and y-triplestep<y_start) or y+triplestep>global_last_y or (  (random_access or (first_order=="block" and level!=max_level-1)) and y+triplestep>last_y)):
                            if level>=min_coeff_level:
                                pred=np.dot(coef,np.array([array[x][y-triplestep],array[x][y-step],array[x][y+step],array[x][y+triplestep]]) )+ince
                            else:
                                pred=(-array[x][y-triplestep]+9*array[x][y-step]+9*array[x][y+step]-array[x][y+triplestep])*0.0625
                        else:
                            pred=(array[x][y-step]+array[x][y+step])*0.5
                        if (not random_access) or level!=0 or x!=x_end-1:# or last_x!=size_x-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                        cur_qs.append(q)
                    
                        if q==0:
                            cur_us.append(decomp)
                            
                        array[x][y]=decomp     
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+step,last_x+1,doublestep):
                        for y in range(y_start+y_start_offset,last_y+1,doublestep):
                            if x-triplestep<0 or (random_access and x-triplestep<x_start) or x+triplestep>global_last_x or (  (random_access or (first_order=="block" and level!=max_level-1)) and x+triplestep>last_x):
                                continue
                            reg_xs.append(np.array([array[x-triplestep][y],array[x-step][y],array[x+step][y],array[x+triplestep][y]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_
                for x in range(x_start+step,last_x+1,doublestep):
                    for y in range(y_start+y_start_offset,last_y+1,doublestep):
                        #if x==cur_size_x-1:
                            #continue
                        orig=array[x][y]
                        if not (x-triplestep<0 or (random_access and x-triplestep<x_start) or x+triplestep>global_last_x or (  (random_access or (first_order=="block" and level!=max_level-1)) and x+triplestep>last_x)):
                            if level>=min_coeff_level:
                                pred=np.dot(coef,np.array([array[x-triplestep][y],array[x-step][y],array[x+step][y],array[x+triplestep][y]]) )+ince
                            else:
                                pred=(-array[x-triplestep][y]+9*array[x-step][y]+9*array[x+step][y]-array[x+triplestep][y])*0.0625
                        else:
                            pred=(array[x-step][y]+array[x+step][y])*0.5
                        if (not random_access) or level>lorenzo or y!=y_end-1:# or last_y!=size_y-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                    
                        cur_qs.append(q)
                        if q==0:
                            cur_us.append(decomp)
                        #absloss+=abs(decomp)
                        array[x][y]=decomp
                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(x_start+step,last_x+1,doublestep):
                        for y in range(y_start+step,last_y+1,doublestep):
                            md_reg_xs.append(np.array([array[x-step][y],array[x+step][y],array[x][y-step],array[x][y+step]],dtype=np.float64))
                            md_reg_ys.append(array[x][y])
                            md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                            md_coef=md_res.coef_ 
                            md_ince=md_res.intercept_

                for x in range(x_start+step,last_x+1,doublestep):
                    for y in range(y_start+step,last_y+1,doublestep):
                        #if x==cur_size_x-1 or y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if level>=min_coeff_level:
                            pred=np.dot(np.array([array[x-step][y],array[x+step][y],array[x][y-step],array[x][y+step]]),md_coef)+md_ince
                        else:
                            pred=(array[x-step][y]+array[x+step][y]+array[x][y-step]+array[x][y+step])*0.25
                        absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                    
                        cur_qs.append(q)
                        if q==0:
                            cur_us.append(decomp)
                            #absloss+=abs(decomp)
                        array[x][y]=decomp
                if selected_algo=="none" or absloss<best_absloss:
                    selected_algo="interp_cubic"
                    best_preds=np.copy(array[x_start:last_x+1:step,y_start:last_y+1:step])
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()

        #multidim
            if fix_algo=="none" or fix_algo=="multidim":
                absloss=0
                cur_qs=[]
                cur_us=[]
                if selected_algo!=None:
                    array[x_start:last_x+1:step,y_start:last_y+1:step]=array_slice#reset array
                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(x_start+step,last_x+1,doublestep):
                        for y in range(y_start+step,last_y+1,doublestep):
                            md_reg_xs.append(np.array([array[x-step][y-step],array[x-step][y+step],array[x+step][y-step],array[x+step][y+step]],dtype=np.float64))
                            md_reg_ys.append(array[x][y])
                            md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                            md_coef=md_res.coef_ 
                            md_ince=md_res.intercept_
                for x in range(x_start+step,last_x+1,doublestep):
                    for y in range(y_start+step,last_y+1,doublestep):
                        #if x==cur_size_x-1 or y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if level>=min_coeff_level:
                            pred=np.dot(np.array([array[x-step][y-step],array[x-step][y+step],array[x+step][y-step],array[x+step][y+step]]),md_coef)+md_ince
                        else:
                            pred=(array[x-step][y-step]+array[x-step][y+step]+array[x+step][y-step]+array[x+step][y+step])*0.25
                        absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                
                        cur_qs.append(q)
                        if q==0:
                            cur_us.append(decomp)
                            #absloss+=abs(decomp)
                        array[x][y]=decomp
                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for i,x in enumerate(range(x_start,last_x+1,step)):
                        for y in range((1-(i%2))*step+y_start,last_y+1,doublestep):
                            if (x==x_start and x_start_offset!=0) or (y==y_start and y_start_offset!=0) or x+step>last_x or y+step>last_y:
                                continue
                            md_reg_xs.append(np.array([array[x][y-step],array[x][y+step],array[x-step][y],array[x+step][y]],dtype=np.float64))
                            md_reg_ys.append(array[x][y])
                            md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                            md_coef=md_res.coef_ 
                            md_ince=md_res.intercept_

                for i,x in enumerate(range(x_start,last_x+1,step)):
                    if x==x_start and x_start_offset!=0:
                        continue
                    for y in range((1-(i%2))*step+y_start,last_y+1,doublestep):
                        if y==y_start and y_start_offset!=0:
                            continue
                    
                        orig=array[x][y]
                        if x and y and x+step<=last_x and y+step<=last_y:
                            if level>=min_coeff_level:
                                pred=np.dot(md_coef,np.array([array[x][y-step],array[x][y+step],array[x-step][y],array[x+step][y]]))+md_ince
                        
                            else:

                                pred=(array[x][y-step]+array[x][y+step]+array[x-step][y]+array[x+step][y])*0.25
                        elif x==0 or x+step>last_x:
                            pred=(array[x][y-step]+array[x][y+step])*0.5
                        else:
                            pred=(array[x-step][y]+array[x+step][y])*0.5
                        if (not random_access) or level>lorenzo or (x!=x_end-1 ) or (y!=y_end-1):
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                        cur_qs.append(q)
                

                        if q==0:
                            cur_us.append(decomp)
                    #absloss+=abs(decomp)
                        array[x][y]=decomp
                if selected_algo=="none" or absloss<best_absloss:
                    selected_algo="interp_fullmultidim"
                    best_preds=np.copy(array[x_start:last_x+1:step,y_start:last_y+1:step])
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()
        #sz3 pure 1D interp,linear and cubic, 2 directions.
        if sz3_interp or fix_algo in ["sz3_linear","sz3_cubic"]:
            #linear
            #y then x
            #print("testing sz3 interp") 
            if fix_algo=="none" or fix_algo=="sz3_linear":
                absloss=0
                cur_qs=[]
                cur_us=[]
                if selected_algo!=None:
                    array[x_start:last_x+1:step,y_start:last_y+1:step]=array_slice#reset array
                
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+x_start_offset,last_x+1,doublestep):
                        for y in range(y_start+step,last_y+1,doublestep):
                            reg_xs.append(np.array([array[x][y-step],array[x][y+step]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_
            

                for x in range(x_start+x_start_offset,last_x+1,doublestep):
                    for y in range(y_start+step,last_y+1,doublestep):
                        #if y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if level>=min_coeff_level:
                            pred= np.dot( np.array([array[x][y-step],array[x][y+step]]),coef )+ince 
                        else:
                            pred=(array[x][y-step]+array[x][y-step])*0.5
                        if (not random_access) or level>lorenzo or x!=x_end-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                        cur_qs.append(q)
                

                        if q==0:
                            cur_us.append(decomp)
                    #absloss+=abs(decomp)
                        array[x][y]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+step,last_x+1,doublestep):
                        for y in range(y_start+(step if y_start_offset>0 else 0),last_y+1,step):
                            reg_xs.append(np.array([array[x-step][y],array[x+step][y]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_
                for x in range(x_start+step,last_x+1,doublestep):
                    for y in range(y_start+(step if y_start_offset>0 else 0),last_y+1,step):
                        #if x==cur_size_x-1:
                            #continue
                        orig=array[x][y]
                        if level>=min_coeff_level:
                            pred= np.dot( np.array([array[x-step][y],array[x+step][y]]),coef )+ince 
                        else:
                            pred=(array[x-step][y]+array[x+step][y])*0.5
                        if (not random_access) or level>lorenzo or y!=y_end-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
               
                        cur_qs.append(q)
                        if q==0:
                            cur_us.append(decomp)
                        #absloss+=abs(decomp)
                        array[x][y]=decomp

                if selected_algo=="none" or absloss<best_absloss:

                    best_preds=np.copy(array[x_start:last_x+1:step,y_start:last_y+1:step])
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()
                    selected_algo="interp_sz3linear_yx"

        
            #x then y 
                absloss=0
                cur_qs=[]
                cur_us=[]

                array[x_start:last_x+1:step,y_start:last_y+1:step]=array_slice#reset array
                
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+step,last_x+1,doublestep):
                        for y in range(y_start+y_start_offset,last_y+1,doublestep):
                            reg_xs.append(np.array([array[x-step][y],array[x+step][y]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_
            

                for x in range(x_start+step,last_x+1,doublestep):
                    for y in range(y_start+y_start_offset,last_y+1,doublestep):
                        #if y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if level>=min_coeff_level:
                            pred= np.dot( np.array([array[x-step][y],array[x+step][y]]),coef )+ince 
                        else:
                            pred=(array[x-step][y]+array[x+step][y])*0.5
                        if (not random_access) or level>lorenzo or y!=y_end-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                        cur_qs.append(q)
                

                        if q==0:
                            cur_us.append(decomp)
                    #absloss+=abs(decomp)
                        array[x][y]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+(step if x_start_offset>0 else 0),last_x+1,step):
                        for y in range(y_start+step ,last_y+1,doublestep):
                            reg_xs.append(np.array([array[x][y-step],array[x][y+step]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_
                for x in range(x_start+(step if x_start_offset>0 else 0),last_x+1,step):
                    for y in range(y_start+step ,last_y+1,doublestep):
                        #if y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if level>=min_coeff_level:
                            pred= np.dot( np.array([array[x][y-step],array[x][y+step]]),coef )+ince 
                        else:
                            pred=(array[x][y-step]+array[x][y+step])*0.5
                        if (not random_access) or level>lorenzo or x!=x_end-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
               
                        cur_qs.append(q)
                        if q==0:
                            cur_us.append(decomp)
                        #absloss+=abs(decomp)
                        array[x][y]=decomp

                if absloss<best_absloss:

                    best_preds=np.copy(array[x_start:last_x+1:step,y_start:last_y+1:step])
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()
                    selected_algo="interp_sz3linear_xy"

            #cubic interp
            #yx
            if fix_algo=="none" or fix_algo=="sz3_cubic":
                absloss=0
                cur_qs=[]
                cur_us=[]
                if selected_algo!=None:
                    array[x_start:last_x+1:step,y_start:last_y+1:step]=array_slice#reset array
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]

                    

                    for x in range(x_start+x_start_offset,last_x+1,doublestep):
                        for y in range(y_start+step,last_y+1,doublestep):
                            if y-triplestep<0 or (random_access and y-triplestep<y_start) or y+triplestep>global_last_y or (  (random_access or (first_order=="block" and level!=max_level-1)) and y+triplestep>last_y):
                                continue
                            reg_xs.append(np.array([array[x][y-triplestep],array[x][y-step],array[x][y+step],array[x][y+triplestep]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_



                for x in range(x_start+x_start_offset,last_x+1,doublestep):
                    for y in range(y_start+step,last_y+1,doublestep):
                        #if y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if not (y-triplestep<0 or (random_access and y-triplestep<y_start) or y+triplestep>global_last_y or (  (random_access or (first_order=="block" and level!=max_level-1)) and y+triplestep>last_y) ):
                            if level>=min_coeff_level:
                                pred=np.dot(coef,np.array([array[x][y-triplestep],array[x][y-step],array[x][y+step],array[x][y+triplestep]]) )+ince
                            else:
                                pred=(-array[x][y-triplestep]+9*array[x][y-step]+9*array[x][y+step]-array[x][y+triplestep])*0.0625
                        else:
                            pred=(array[x][y-step]+array[x][y+step])*0.5
                        if (not random_access) or level>lorenzo or x!=x_end-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                        cur_qs.append(q)
                    
                        if q==0:
                            cur_us.append(decomp)
                            #absloss+=abs(decomp)
                        array[x][y]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+step,last_x+1,doublestep):
                        for j,y in enumerate(range(y_start+(step if y_start_offset>0 else 0),last_y+1,step)):

                            if x-triplestep<0 or (random_access and x-triplestep<x_start) or x+triplestep>global_last_x or (  (random_access or (first_order=="block" and level!=max_level-1)) and x+triplestep>last_x and (y-y_start)%doublestep):
                                continue
                            reg_xs.append(np.array([array[x-triplestep][y],array[x-step][y],array[x+step][y],array[x+triplestep][y]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_


                for x in range(x_start+step,last_x+1,doublestep):
                    for y in range(y_start+(step if y_start_offset>0 else 0),last_y+1,step):
                        #if y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if not (x-triplestep<0 or (random_access and x-triplestep<x_start) or x+triplestep>global_last_x or (  (random_access or (first_order=="block" and level!=max_level-1)) and x+triplestep>last_x and (y-y_start)%doublestep)):
                            if level>=min_coeff_level:
                                pred=np.dot(coef,np.array([array[x-triplestep][y],array[x-step][y],array[x+step][y],array[x+triplestep][y]]) )+ince
                            else:
                                pred=(-array[x-triplestep][y]+9*array[x-step][y]+9*array[x+step][y]-array[x+triplestep][y])*0.0625
                        else:
                            pred=(array[x-step][y]+array[x+step][y])*0.5
                        if (not random_access) or level>lorenzo or y!=y_end-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                    
                        cur_qs.append(q)
                        if q==0:
                            cur_us.append(decomp)
                            #absloss+=abs(decomp)
                        array[x][y]=decomp


            
                if selected_algo=="none" or absloss<best_absloss:
                    selected_algo="sz3interp_cubic_yx"
                    best_preds=np.copy(array[x_start:last_x+1:step,y_start:last_y+1:step])
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()


                #xy 
                absloss=0
                cur_qs=[]
                cur_us=[]
                array=np.copy(array)#reset array
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+step,last_x+1,doublestep):
                        for y in range(y_start+y_start_offset,last_y+1,doublestep):
                            if x-triplestep<0 or (random_access and x-triplestep<x_start) or x+triplestep>global_last_x or (  (random_access or (first_order=="block" and level!=max_level-1)) and x+triplestep>last_x):
                                continue
                            reg_xs.append(np.array([array[x-triplestep][y],array[x-step][y],array[x+step][y],array[x+triplestep][y]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_



                for x in range(x_start+step,last_x+1,doublestep):
                    for y in range(y_start+y_start_offset,last_y+1,doublestep):
                        #if x==cur_size_x-1:
                            #continue
                        orig=array[x][y]
                        if not (x-triplestep<0 or (random_access and x-triplestep<x_start) or x+triplestep>global_last_x or (  (random_access or (first_order=="block" and level!=max_level-1)) and x+triplestep>last_x )):
                            if level>=min_coeff_level:
                                pred=np.dot(coef,np.array([array[x-triplestep][y],array[x-step][y],array[x+step][y],array[x+triplestep][y]]) )+ince
                            else:
                                pred=(-array[x-triplestep][y]+9*array[x-step][y]+9*array[x+step][y]-array[x+triplestep][y])*0.0625
                        else:
                            pred=(array[x-step][y]+array[x+step][y])*0.5
                        if (not random_access) or level>lorenzo or y!=y_end-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                        cur_qs.append(q)
                    
                        if q==0:
                            cur_us.append(decomp)
                            #absloss+=abs(decomp)
                        array[x][y]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(x_start+(step if x_start_offset>0 else 0),last_x+1,step):
                        for y in range(y_start+step,last_y+1,doublestep):
                            if y-triplestep<0 or (random_access and y-triplestep<y_start) or y+triplestep>global_last_y or (  (random_access or (first_order=="block" and level!=max_level-1)) and y+triplestep>last_y and (x-x_start)%doublestep):
                                continue
                            reg_xs.append(np.array([array[x][y-triplestep],array[x][y-step],array[x][y+step],array[x][y+triplestep]],dtype=np.float64))
                            reg_ys.append(array[x][y])
                            res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                            coef=res.coef_ 
                            ince=res.intercept_


                for x in range(x_start+(step if x_start_offset>0 else 0),last_x+1,step):
                    for y in range(y_start+step,last_y+1,doublestep):
                        #if y==cur_size_y-1:
                            #continue
                        orig=array[x][y]
                        if not (y-triplestep<0 or (random_access and y-triplestep<y_start) or y+triplestep>global_last_y or (  (random_access or (first_order=="block" and level!=max_level-1)) and y+triplestep>last_y and (x-x_start)%doublestep)):
                            if level>=min_coeff_level:
                                pred=np.dot(coef,np.array([array[x][y-triplestep],array[x][y-step],array[x][y+step],array[x][y+triplestep]]) )+ince
                            else:
                                pred=(-array[x][y-triplestep]+9*array[x][y-step]+9*array[x][y+step]-array[x][y+triplestep])*0.0625
                        else:
                            pred=(array[x][y-step]+array[x][y+step])*0.5
                        if (not random_access) or level>lorenzo or x!=x_end-1:
                            absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                    
                        cur_qs.append(q)
                        if q==0:
                            cur_us.append(decomp)
                            #absloss+=abs(decomp)
                        array[x][y]=decomp


            
                if selected_algo=="none" or absloss<best_absloss:
                    selected_algo="sz3interp_cubic_xy"
                    best_preds=np.copy(array[x_start:last_x+1:step,y_start:last_y+1:step])
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()











        #Lorenzo fallback
        if level<=lorenzo:
            absloss=0
        #cur_qs=[]
        #cur_us=[]
        #array=np.copy(array[0:last_x+1:step,0:last_y+1:step])#reset array
            x_start_offset=step if x_preded else 0
            y_start_offset=step if y_preded else 0
            cur_orig_array=orig_array[x_start:last_x+1:step,y_start:last_y+1:step]
            x_end_offset=1 if (random_access and last_x==size_x-1 and level==0) else 0
            y_end_offset=1 if (random_access and last_y==size_y-1 and level==0) else 0
            total_points=[(x,y) for x in range(cur_orig_array.shape[0]-1) for y in range(cur_orig_array.shape[1]-1) if (max_step<=0 or ((x*step)%max_step!=0 and (y*step)%max_step!=0))]
            if len(total_points)<min_sampled_points:
                num_sumples=len(total_points)
                sampled_points=total_points
            else:
                num_sumples=max(min_sampled_points,int(len(total_points)*sample_rate) )
                sampled_points=random.sample(total_points,num_sumples)
            for x,y in sampled_points:
                orig=cur_orig_array[x][y]
                f_01=cur_orig_array[x-1][y] if x else 0
                if x and max_step>0 and ((x-1)*step)%max_step==0 and (y*step)%max_step==0:
                    f_01+=anchor_eb*(2*np.random.rand()-1)
                elif x:
                    f_01+=cur_eb*(2*np.random.rand()-1)

                f_10=cur_orig_array[x][y-1] if y else 0
                if y and max_step>0 and (x*step)%max_step==0 and ((y-1)*step)%max_step==0:
                    f_10+=anchor_eb*(2*np.random.rand()-1)
                elif y:
                    f_10+=cur_eb*(2*np.random.rand()-1)
            
                f_00=cur_orig_array[x-1][y-1] if x and y else 0
                if x and y and max_step>0 and ((x-1)*step)%max_step==0 and ((y-1)*step)%max_step==0:
                    f_00+=anchor_eb*(2*np.random.rand()-1)
                elif x and y:
                    f_00+=cur_eb*(2*np.random.rand()-1)
                
                pred=f_01+f_10-f_00

                absloss+=abs(orig-pred)
            #print(absloss*len(total_points)/len(sampled_points))
            #print(best_absloss)
            #print(cumulated_loss)
            if absloss*len(total_points)/len(sampled_points)<best_absloss+cumulated_loss:
                selected_algo="lorenzo_fallback"
                best_absloss=0
                array[x_start:last_x+1:step,y_start:last_y+1:step]=orig_array[x_start:last_x+1:step,y_start:last_y+1:step]#reset array
                best_qs=[]
                best_us=[]
           
            #qs[max_level]=qs[:maxlevel_q_start]
                for i in range(max_level-1,level,-1):
                    qs[i]=[]
                us=us[:u_start]
                for x in range(x_start+x_start_offset*step,last_x+1-x_end_offset*step,step):
                    for y in range(y_start+y_start_offset*step,last_y+1-y_end_offset*step,step):
                    
                        if max_step>0 and x%max_step==0 and y%max_step==0:
                            #print(x,y)
                            continue
                        orig=array[x][y]
                        f_01=array[x-step][y] if  x-step>=x_start or (x-step>=0 and not random_access) else 0
                
                        f_10=array[x][y-step] if y-step>=y_start or (y-step>=0 and not random_access) else 0
            
                        f_00=array[x-step][y-step] if (x-step>=x_start or (x-step>=0 and not random_access)) and (y-step>=y_start or (y-step>=0 and not random_access)) else 0
                
                        pred=f_01+f_10-f_00
                
        
                        best_absloss+=abs(orig-pred)
                        q,decomp=quantize(orig,pred,cur_eb)
                        best_qs.append(q)
                        if q==0:
                            best_us.append(decomp)
                #absloss+=abs(decomp)
                        array[x][y]=decomp
            

        #print(len(best_qs))




        mean_l1_loss=best_absloss/len(best_qs)

        
        if selected_algo!="lorenzo_fallback":
            array[x_start:last_x+1:step,y_start:last_y+1:step]=best_preds
            cumulated_loss+=best_absloss
        
        else:
            cumulated_loss=best_absloss
        
        #print(np.max(np.abs(array[0:last_x+1:step,0:last_y+1:step]-best_preds)))
    
        #if args.lorenzo_fallback_check:
        #    print(np.max(np.abs(orig_array-array))/rng)
        qs[level]+=best_qs
        us+=best_us
        selected_algos.append(selected_algo)
        #print(len(qs))
        if verbose:
            print ("Level %d finished. Selected algorithm: %s. Mean prediction abs loss: %f." % (level,selected_algo,mean_l1_loss))
        print(np.max(np.abs(orig_array-array)))
        step=step//2
        level-=1
        #print(sum([len(_) for _ in qs] ))
        #print(best_absloss)
        #print(cumulated_loss)



    def lorenzo_2d(array,x_start,x_end,y_start,y_end):
        for x in range(x_start,x_end):
            for y in range(y_start,y_end):

                orig=array[x][y]
        
                f_01=array[x-1][y] if x else 0
                f_10=array[x][y-1] if y else 0
            
                f_00=array[x-1][y-1] if x and y else 0
                
                pred=f_01+f_10-f_00
                
        
                
                q,decomp=quantize(orig,pred,error_bound)
                edge_qs.append(q)
                if q==0:
                    us.append(decomp)
                array[x][y]=decomp
    offset_x1=1 if x_preded else 0
    offset_y1=1 if y_preded else 0
    offset_x2=1 if random_access else 0
    offset_y2=1 if random_access else 0
    lorenzo_2d(array,offset_x1,last_x+1,last_y+1,size_y-offset_y2)
    lorenzo_2d(array,last_x+1,size_x-offset_x2,offset_y1,size_y-offset_y2)
    return array,qs,edge_qs,us,selected_algos


    
if __name__=="__main__":
 



    parser = argparse.ArgumentParser()

    parser.add_argument('--error','-e',type=float,default=1e-3)
    parser.add_argument('--input','-i',type=str)
    parser.add_argument('--output','-o',type=str)
    parser.add_argument('--quant','-q',type=str,default="ml2_q.dat")
    parser.add_argument('--unpred','-u',type=str,default="ml2_u.dat")
    parser.add_argument('--max_step','-s',type=int,default=-1)
    parser.add_argument('--min_coeff_level','-cl',type=int,default=99)
    parser.add_argument('--rate','-r',type=float,default=1.0)
    parser.add_argument('--rlist',type=float,default=-1,nargs="+")
    parser.add_argument('--maximum_rate','-m',type=float,default=10.0)
    parser.add_argument('--cubic','-c',type=int,default=1)
    parser.add_argument('--multidim_level','-d',type=int,default=99)
    parser.add_argument('--lorenzo_fallback_check','-l',type=int,default=-1)
    parser.add_argument('--fallback_sample_ratio','-p',type=float,default=0.05)
    parser.add_argument('--anchor_rate','-a',type=float,default=0.0)

    parser.add_argument('--size_x','-x',type=int,default=1800)
    parser.add_argument('--size_y','-y',type=int,default=3600)
    parser.add_argument('--sz_interp','-n',type=int,default=0)
    parser.add_argument('--fix','-f',type=str,default="none")
    args = parser.parse_args()
    print(args)
    array=np.fromfile(args.input,dtype=np.float32).reshape((args.size_x,args.size_y))
    orig_array=np.copy(array)
    error_bound=args.error*(np.max(array)-np.min(array))
    max_level=int(math.log(args.max_step,2))
    rate_list=args.rlist
    #print(rate_list)
    if ((isinstance(rate_list,int) or isinstance(rate_list,float)) and  rate_list>0) or (isinstance(rate_list,list ) and rate_list[0]>0):

        if isinstance(rate_list,int) or isinstance(rate_list,float):
            rate_list=[rate_list]

        while len(rate_list)<max_level:
            rate_list.insert(0,rate_list[0])
    else:
        rate_list=None
    array,qs,edge_qs,us,_=msc2d(array,0,args.size_x,0,args.size_y,error_bound,args.rate,args.maximum_rate,args.min_coeff_level,args.max_step,args.anchor_rate,rate_list=rate_list,x_preded=False,y_preded=False,\
        sz3_interp=args.sz_interp,multidim_level=args.multidim_level,lorenzo=args.lorenzo_fallback_check,sample_rate=args.fallback_sample_ratio,min_sampled_points=100,random_access=False,verbose=True,fix_algo=args.fix)
    quants=np.concatenate( (np.array(edge_qs,dtype=np.int32),np.array(sum(qs,[]),dtype=np.int32) ) )
    unpreds=np.array(us,dtype=np.float32)
    array.tofile(args.output)
    quants.tofile(args.quant)
    unpreds.tofile(args.unpred)
    '''
    for x in range(args.size_x):
        for y in range(args.size_y):
            if array[x][y]==orig_array[x][y] and x%args.max_step!=0 and y%args.max_step!=0:
                print(x,y)
    '''