import numpy as np 

import os
import argparse
#import torch
#import torch.nn as nn
from sklearn.linear_model import LinearRegression
import math
import random
from utils import *

def msc3d(array,error_bound,rate,maximum_rate,min_coeff_level,max_step,anchor_rate,rate_list=None,x_preded=False,y_preded=False,z_preded=False,multidim_level=10,sz_interp=False,lorenzo=-1,\
sample_rate=0.05,min_sampled_points=10,random_access=False,verbose=False,fix_algo="none",fix_algo_list=None,first_level=None,last_level=0,fake_compression=False):#lorenzo:only check lorenzo fallback with level no larger than lorenzo level

    size_x,size_y,size_z=array.shape
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
    if anchor_rate>0:
        anchor_eb=error_bound/anchor_rate
    else:
        anchor_eb=0
    startx=max_step if x_preded else 0
    starty=max_step if y_preded else 0
    startz=max_step if z_preded else 0
    if (first_level==None or max_level==first_level+1) and anchor_rate>0:
    
    #anchor_rate=args.anchor_rate
        
        anchor_eb=error_bound/anchor_rate
        if verbose:
            print("Anchor eb:%f" % anchor_eb)

        if max_level>=min_coeff_level :
            reg_xs=[]
            reg_ys=[]
            for x in range(max_step,size_x,max_step):
                for y in range(max_step,size_y,max_step):
                    for z in range(max_step,size_z,max_step):
                        reg_xs.append(np.array(array[x-max_step:x+1,y-max_step:y+1,z-max_step:z+1][:7],dtype=np.float64))
                        reg_ys.append(array[x][y][z])
                        res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                        coef=res.coef_ 
                        ince=res.intercept_

 
        
        for x in range(startx,size_x,max_step):
            for y in range(starty,size_y,max_step):
                for z in range(startz,size_y,max_step):
                    orig=array[x][y][z]
                    if x and y and z and max_level>=min_coeff_level:
                        reg_block=array[x-max_step:x+1,y-max_step:y+1,z-max_step:z+1][:7]
                        pred=np.dot(reg_block,coef)+ince

            
                
                    else:
                        f_011=array[x-max_step][y][z] if x else 0
                        f_101=array[x][y-max_step][z] if y else 0
                        f_110=array[x][y][z-max_step] if z else 0
                        f_001=array[x-max_step][y-max_step][z] if x and y else 0
                        f_100=array[x][y-max_step][z-max_step] if y and z else 0
                        f_010=array[x-max_step][y][z-max_step] if x and z else 0
                        f_000=array[x-max_step][y-max_step][z-max_step] if x and y and z else 0
                
                        pred=f_000+f_011+f_101+f_110-f_001-f_010-f_100
                
        
                
                        q,decomp=quantize(orig,pred,anchor_eb)
                        qs[max_level].append(q)
                        if q==0:
                            us.append(decomp)
                        array[x][y][z]=decomp
       
    elif (first_level==None or max_level==first_level+1) and anchor_rate==0:
        pass
#print(len(qs))

    last_x=((size_x-1)//max_step)*max_step
    last_y=((size_y-1)//max_step)*max_step 
    last_z=((size_z-1)//max_step)*max_step   
    step=max_step//2
    level=max_level-1
    if first_level==None:
        first_level=max_level-1
    #maxlevel_q_start=len(qs[max_level])
    u_start=len(us)
    cumulated_loss=0.0
    loss_dict=[{} for i in range(max_level)]
    while level>=last_level:#step>0:
        cur_qs=[]
        cur_us=[]
        if rate_list!=None:
            cur_eb=error_bound/rate_list[level]
        else:
            cur_eb=error_bound/min(maximum_rate,(rate**level))
        cur_array=np.copy(array[0:last_x+1:step,0:last_y+1:step,0:last_z+1:step])
        #print(cur_array.shape)
        cur_size_x,cur_size_y,cur_size_z=cur_array.shape
    #print(cur_size_x,cur_size_y)
        if verbose:
            print("Level %d started. Current step: %d. Current error_bound: %s." % (level,step,cur_eb))
        best_preds=None#need to copy
        best_absloss=None
        best_qs=[]#need to copy
        best_us=[]#need to copy
        xstart=2 if x_preded else 0
        ystart=2 if y_preded else 0
        zstart=2 if y_preded else 0
    #linear interp
        absloss=0
        selected_algo="none"
        if fix_algo_list!=None:
            fix_algo=fix_algo_list[level]
        if (fix_algo=="none" and level<=multidim_level) or fix_algo in ["linear","cubic","multidim"] or not sz_interp:
            if fix_algo=="none" or fix_algo=="linear":

                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(1,cur_size_z,2):
                                reg_xs.append(np.array([cur_array[x][y][z-1],cur_array[x][y][z+1]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_
            

                for x in range(xstart,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                            #if z==cur_size_z-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred= np.dot( np.array([cur_array[x][y][z-1],cur_array[x][y][z+1]]),coef )+ince 
                            else:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (y!=cur_size_y-1 or last_y!=size_y-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(1,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                reg_xs.append(np.array([cur_array[x][y-1][z],cur_array[x][y+1][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(xstart,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                            #if y==cur_size_y-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred= np.dot( np.array([cur_array[x][y-1][z],cur_array[x][y+1][z]]),coef )+ince 
                            else:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp 

                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                reg_xs.append(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(1,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                            #if x==cur_size_x-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred= np.dot( np.array([cur_array[x-1][y][z],cur_array[x+1][y][z]]),coef )+ince 
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z])*0.5
                            if (not random_access) or level!=0 or ((y!=cur_size_y-1 or last_y!=size_y-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp     

                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(1,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                md_reg_xs.append(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y-1][z],cur_array[x][y+1][z]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_

        
                for x in range(1,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                    
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred=np.dot(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y-1][z],cur_array[x][y+1][z]]),md_coef)+md_ince
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z]+cur_array[x][y-1][z]+cur_array[x][y+1][z])*0.25

                            if (not random_access) or level!=0 or z!=cur_size_z-1 or last_z!=size_z-1:
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                    
                            cur_qs.append(q)
                            if q==0:
                                cur_us.append(decomp)
                    #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp

                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(1,cur_size_z,2):
                                md_reg_xs.append(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y][z-1],cur_array[x][y][z+1]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_

        
                for x in range(1,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                    
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred=np.dot(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y][z-1],cur_array[x][y][z+1]]),md_coef)+md_ince
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z]+cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.25
                            if (not random_access) or level!=0 or y!=cur_size_y-1 or last_y!=size_y-1:
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                
                            cur_qs.append(q)
                            if q==0:
                                cur_us.append(decomp)
                    
                            cur_array[x][y][z]=decomp

                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(1,cur_size_y,2):
                            for z in range(1,cur_size_z,2):
                                md_reg_xs.append(np.array([cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y][z-1],cur_array[x][y][z+1]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_

                for x in range(xstart,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                    
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred=np.dot(np.array([cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y][z-1],cur_array[x][y][z+1]]),md_coef)+md_ince
                            else:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z]+cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.25
                            if (not random_access) or level!=0 or x!=cur_size_x-1 or last_x!=size_x-1:
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                
                            cur_qs.append(q)
                            if q==0:
                                cur_us.append(decomp)
                    #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp
            
                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(1,cur_size_y,2):
                            for z in range(1,cur_size_z,2):
                                md_reg_xs.append(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y][z-1],cur_array[x][y][z+1]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_

                for x in range(1,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                    
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred=np.dot(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y][z-1],cur_array[x][y][z+1] ]),md_coef)+md_ince
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z]+cur_array[x][y-1][z]+cur_array[x][y+1][z]+cur_array[x][y][z-1]+cur_array[x][y][z+1])/6
                            absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                
                            cur_qs.append(q)
                            if q==0:
                                cur_us.append(decomp)
                    
                            cur_array[x][y][z]=decomp

                loss_dict[level]["linear"]=absloss
                best_preds=np.copy(cur_array)
                best_absloss=absloss
                best_qs=cur_qs.copy()
                best_us=cur_us.copy()
                selected_algo="linear"

            #print(len(cur_qs))


            #cubic interp
            #cubic=True
            #if cubic:
            #print("cubic")
            if fix_algo=="none" or fix_algo=="cubic":
                absloss=0
                cur_qs=[]
                cur_us=[]
                cur_array=np.copy(array[0:last_x+1:step,0:last_y+1:step,0:last_z+1:step])#reset cur_array
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(3,cur_size_z,2):
                                if z+3>=cur_size_z:
                                    continue
                                reg_xs.append(np.array([cur_array[x][y][z-3],cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y][z+3]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_
                for x in range(xstart,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                    
                            orig=cur_array[x][y][z]
                            if z>=3 and z+3<cur_size_z:
                                if level>=min_coeff_level:
                                    pred=np.dot(coef,np.array([cur_array[x][y][z-3],cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y][z+3]]) )+ince
                                else:
                                    pred=(-cur_array[x][y][z-3]+9*cur_array[x][y][z-1]+9*cur_array[x][y][z+1]-cur_array[x][y][z+3])*0.0625
                            else:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (y!=cur_size_y-1 or last_y!=size_y-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                    
                            if q==0:
                                cur_us.append(decomp)
                                #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp     


                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(3,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                if y+3>=cur_size_y:
                                    continue
                                reg_xs.append(np.array([cur_array[x][y-3][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y+3][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_
                for x in range(xstart,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                    
                            orig=cur_array[x][y][z]
                            if y>=3 and y+3<cur_size_y:
                                if level>=min_coeff_level:
                                    pred=np.dot(coef,np.array([cur_array[x][y-3][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y+3][z]]) )+ince
                                else:
                                    pred=(-cur_array[x][y-3][z]+9*cur_array[x][y-1][z]+9*cur_array[x][y+1][z]-cur_array[x][y+3][z])*0.0625
                            else:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                    
                            if q==0:
                                cur_us.append(decomp)
                                #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp

                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(3,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                if x+3>=cur_size_x:
                                    continue
                                reg_xs.append(np.array([cur_array[x-3][y][z],cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x+3][y][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_
                for x in range(1,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                    
                            orig=cur_array[x][y][z]
                            if x>=3 and x+3<cur_size_x:
                                if level>=min_coeff_level:
                                    pred=np.dot(coef,np.array([cur_array[x-3][y][z],cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x+3][y][z]]) )+ince
                                else:
                                    pred=(-cur_array[x-3][y][z]+9*cur_array[x-1][y][z]+9*cur_array[x+1][y][z]-cur_array[x+3][y][z])*0.0625
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z])*0.5
                            if (not random_access) or level!=0 or ( (y!=cur_size_y-1 or last_y!=size_y-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                    
                            if q==0:
                                cur_us.append(decomp)
                                #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp  



                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(1,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                md_reg_xs.append(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y-1][z],cur_array[x][y+1][z]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_

        
                for x in range(1,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                    
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred=np.dot(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y-1][z],cur_array[x][y+1][z]]),md_coef)+md_ince
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z]+cur_array[x][y-1][z]+cur_array[x][y+1][z])*0.25
        
                            if (not random_access) or level!=0 or z!=cur_size_z-1 or last_z!=size_z-1:
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                    
                            cur_qs.append(q)
                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp

                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(1,cur_size_z,2):
                                md_reg_xs.append(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y][z-1],cur_array[x][y][z+1]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_

        
                for x in range(1,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                        
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred=np.dot(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y][z-1],cur_array[x][y][z+1]]),md_coef)+md_ince
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z]+cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.25
                            if (not random_access) or level!=0 or y!=cur_size_y-1 or last_y!=size_y-1:
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                    
                            cur_qs.append(q)
                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp

                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(1,cur_size_y,2):
                            for z in range(1,cur_size_z,2):
                                md_reg_xs.append(np.array([cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y][z-1],cur_array[x][y][z+1]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_

                for x in range(xstart,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                        
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred=np.dot(np.array([cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y][z-1],cur_array[x][y][z+1]]),md_coef)+md_ince
                            else:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z]+cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.25
                            if (not random_access) or level!=0 or (x!=cur_size_x-1 or last_x!=size_x-1) :
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                    
                            cur_qs.append(q)
                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp
                
                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(1,cur_size_y,2):
                            for z in range(1,cur_size_z,2):
                                md_reg_xs.append(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y][z-1],cur_array[x][y][z+1]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_

                for x in range(1,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                        
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred=np.dot(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y][z-1],cur_array[x][y][z+1] ]),md_coef)+md_ince
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z]+cur_array[x][y-1][z]+cur_array[x][y+1][z]+cur_array[x][y][z-1]+cur_array[x][y][z+1])/6
                            absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                    
                            cur_qs.append(q)
                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp
                loss_dict[level]["cubic"]=absloss
                if selected_algo=="none" or absloss<best_absloss:
                    selected_algo="cubic"
                    best_preds=np.copy(cur_array)
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()
        
            #full multidim
            if fix_algo=="none" or fix_algo=="multidim":
                absloss=0
                cur_qs=[]
                cur_us=[]
                cur_array=np.copy(array[0:last_x+1:step,0:last_y+1:step,0:last_z+1:step])#reset cur_array
                #center
                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(1,cur_size_y,2):
                            for z in range(1,cur_size_y,2):
                                md_reg_xs.append(np.array(cur_array[x-1:x+2:2,y-1:y+2:2,z-1:z+2:2],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_
                for x in range(1,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(1,cur_size_y,2):
                            if x==cur_size_x-1 or y==cur_size_y-1:
                                continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred=np.dot(cur_array[x-1:x+2:2,y-1:y+2:2,z-1:z+2:2],md_coef)+md_ince
                            else:
                                pred=np.mean(cur_array[x-1:x+2:2,y-1:y+2:2,z-1:z+2:2])
                            absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                
                            cur_qs.append(q)
                            if q==0:
                                cur_us.append(decomp)
                                #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp

                #face
                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(0,cur_size_x):
                        for y in range(1-(x%2),cur_size_y,2-(x%2)):

                            for z in range((x+y)%2,cur_size_z,2):
                                if (x==0 and xstart!=0) or (y==0 and ystart!=0) or (z==0 and zstart!=0) or x==cur_size_x-1 or y==cur_size_y-1 or z==cur_size_z-1:
                                    continue
                                md_reg_xs.append(np.array([cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x-1][y][z],cur_array[x+1][y][z]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_
                
                for x in range(0,cur_size_x):
                    for y in range(1-(x%2),cur_size_y,2-(x%2)):

                        for z in range((x+y)%2,cur_size_z,2):
                            if (x==0 and xstart!=0) or (y==0 and ystart!=0) or (z==0 and zstart!=0):
                                 continue
                    
                            orig=cur_array[x][y][z]
                            if x and y and z and x!=cur_size_x-1 and y!=cur_size_y-1 and z!=cur_size_z-1:
                                if level>=min_coeff_level:
                                    pred=np.dot(md_coef,np.array([cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x-1][y][z],cur_array[x+1][y][z]]))+md_ince
                        
                                else:

                                    pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1]+cur_array[x][y-1][z]+cur_array[x][y+1][z]+cur_array[x-1][y][z]+cur_array[x+1][y][z])/6
                            elif x and y and x!=cur_size_x-1 and y!=cur_size_y-1:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z]+cur_array[x-1][y][z]+cur_array[x+1][y][z])/4
                            elif x and z and x!=cur_size_x-1 and z!=cur_size_z-1:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1]+cur_array[x-1][y][z]+cur_array[x+1][y][z])/4
                            elif y and z and y!=cur_size_y-1 and z!=cur_size_z-1:
                              
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1]+cur_array[x][y-1][z]+cur_array[x][y+1][z])/4



                            elif x and x!=cur_size_x-1:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z])/2
                            elif y and y!=cur_size_y-1:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z])/2
                            else:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1])/2
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (y!=cur_size_y-1 or last_y!=size_y-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                   
                            cur_array[x][y][z]=decomp
                #edge
                if level>=min_coeff_level:
                    md_reg_xs=[]
                    md_reg_ys=[]
                    for x in range(0,cur_size_x):
                        for y in range(0,cur_size_y,1+(x%2)):

                            for z in range(1-((x+y)%2),cur_size_z,2):
                                if (x==0 and xstart!=0) or (y==0 and ystart!=0) or (z==0 and zstart!=0) or x==cur_size_x-1 or y==cur_size_y-1 or z==cur_size_z-1:
                                    continue
                                md_reg_xs.append(np.array([cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x-1][y][z],cur_array[x+1][y][z]],dtype=np.float64))
                                md_reg_ys.append(cur_array[x][y][z])
                                md_res=LinearRegression(fit_intercept=True).fit(md_reg_xs, md_reg_ys)
                                md_coef=md_res.coef_ 
                                md_ince=md_res.intercept_
                
                for x in range(0,cur_size_x):
                    for y in range(0,cur_size_y,1+(x%2)):

                        for z in range(1-((x+y)%2),cur_size_z,2):
                            if (x==0 and xstart!=0) or (y==0 and ystart!=0) or (z==0 and zstart!=0):
                                 continue
                    
                            orig=cur_array[x][y][z]
                            if x and y and z and x!=cur_size_x-1 and y!=cur_size_y-1 and z!=cur_size_z-1:
                                if level>=min_coeff_level:
                                    pred=np.dot(md_coef,np.array([cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x-1][y][z],cur_array[x+1][y][z]]))+md_ince
                        
                                else:

                                    pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1]+cur_array[x][y-1][z]+cur_array[x][y+1][z]+cur_array[x-1][y][z]+cur_array[x+1][y][z])/6
                            elif x and y and x!=cur_size_x-1 and y!=cur_size_y-1:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z]+cur_array[x-1][y][z]+cur_array[x+1][y][z])/4
                            elif x and z and x!=cur_size_x-1 and z!=cur_size_z-1:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1]+cur_array[x-1][y][z]+cur_array[x+1][y][z])/4
                            elif y and z and y!=cur_size_y-1 and z!=cur_size_z-1:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1]+cur_array[x][y-1][z]+cur_array[x][y+1][z])/4



                            elif x and x!=cur_size_x-1:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z])/2
                            elif y and y!=cur_size_y-1:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z])/2
                            else:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1])/2
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (y!=cur_size_y-1 or last_y!=size_y-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                   
                            cur_array[x][y][z]=decomp

                loss_dict[level]["multidim"]=absloss
                if selected_algo=="none" or absloss<best_absloss:
                    selected_algo="multidim"
                    best_preds=np.copy(cur_array)
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()


        if (fix_algo=="none" and sz_interp) or fix_algo in ["sz3_linear","sz3_cubic","sz3_linear_zyx","sz3_linear_xyz","sz3_cubic_zyx","sz3_cubic_xyz"]:
            #1D linear
            #zyx
            if fix_algo=="none" or fix_algo=="sz3_linear" or fix_algo=="sz3_linear_zyx":
                absloss=0
                cur_qs=[]
                cur_us=[]
                cur_array=np.copy(array[0:last_x+1:step,0:last_y+1:step,0:last_z+1:step])#reset cur_array
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(1,cur_size_z,2):
                                reg_xs.append(np.array([cur_array[x][y][z-1],cur_array[x][y][z+1]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_
            

                for x in range(xstart,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                            #if z==cur_size_z-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred= np.dot( np.array([cur_array[x][y][z-1],cur_array[x][y][z+1]]),coef )+ince 
                            else:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (y!=cur_size_y-1 or last_y!=size_y-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(1,cur_size_y,2):
                            for z in range(1 if zstart>0 else 0,cur_size_z,1):
                                reg_xs.append(np.array([cur_array[x][y-1][z],cur_array[x][y+1][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(xstart,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(1 if zstart>0 else 0,cur_size_z,1):
                            #if y==cur_size_y-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred= np.dot( np.array([cur_array[x][y-1][z],cur_array[x][y+1][z]]),coef )+ince 
                            else:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp 

                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(1 if ystart>0 else 0,cur_size_y,1):
                            for z in range(1 if zstart>0 else 0,cur_size_z,1):
                                reg_xs.append(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(1,cur_size_x,2):
                    for y in range(1 if ystart>0 else 0,cur_size_y,1):
                        for z in range(1 if zstart>0 else 0,cur_size_z,1):
                            if x==cur_size_x-1:
                                continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred= np.dot( np.array([cur_array[x-1][y][z],cur_array[x+1][y][z]]),coef )+ince 
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z])*0.5
                            if (not random_access) or level!=0 or ((y!=cur_size_y-1 or last_y!=size_y-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp 
                loss_dict[level]["sz3_linear_zyx"]=absloss
                if selected_algo=="none" or absloss<best_absloss :
                    selected_algo="sz3_linear_zyx"
                    best_preds=np.copy(cur_array)
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()


            if fix_algo=="none" or fix_algo=="sz3_linear" or fix_algo=="sz3_linear_xyz":
                #xyz
                absloss=0
                cur_qs=[]
                cur_us=[]
                cur_array=np.copy(array[0:last_x+1:step,0:last_y+1:step,0:last_z+1:step])#reset cur_array
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(1,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                reg_xs.append(np.array([cur_array[x-1][y][z],cur_array[x+1][y][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_
            

                for x in range(1,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                            #if z==cur_size_z-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred= np.dot( np.array([cur_array[x-1][y][z],cur_array[x+1][y][z]]),coef )+ince 
                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z])*0.5
                            if (not random_access) or level!=0 or ((z!=cur_size_z-1 or last_z!=size_z-1) and (y!=cur_size_y-1 or last_y!=size_y-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(1 if xstart>0 else 0,cur_size_x,1):
                        for y in range(1,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                reg_xs.append(np.array([cur_array[x][y-1][z],cur_array[x][y+1][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(1 if xstart>0 else 0,cur_size_x,1):
                    for y in range(1,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                            #if y==cur_size_y-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred= np.dot( np.array([cur_array[x][y-1][z],cur_array[x][y+1][z]]),coef )+ince 
                            else:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp 

                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(1 if xstart>0 else 0,cur_size_x,1):
                        for y in range(1 if ystart>0 else 0,cur_size_y,1):
                            for z in range(1 ,cur_size_z,2):
                                reg_xs.append(np.array([cur_array[x][y][z-1],cur_array[x][y][z+1]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(1 if xstart>0 else 0,cur_size_x,1):
                    for y in range(1 if ystart>0 else 0,cur_size_y,1):
                        for z in range(1,cur_size_z,2):
                            #if x==cur_size_x-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if level>=min_coeff_level:
                                pred= np.dot( np.array([cur_array[x][y][z-1],cur_array[x][y][z+1]]),coef )+ince 
                            else:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.5
                            if (not random_access) or level!=0 or ((y!=cur_size_y-1 or last_y!=size_y-1) and (x!=cur_size_x-1 or last_x!=size_x-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp 
                loss_dict[level]["sz3_linear_xyz"]=absloss
                if selected_algo=="none" or absloss<best_absloss:
                    selected_algo="sz3_linear_xyz"
                    best_preds=np.copy(cur_array)
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()

            #1D cubic
            #ZYX
            if fix_algo=="none" or fix_algo=="sz3_cubic" or fix_algo=="sz3_cubic_zyx":
                absloss=0
                cur_qs=[]
                cur_us=[]
                cur_array=np.copy(array[0:last_x+1:step,0:last_y+1:step,0:last_z+1:step])#reset cur_array
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(3,cur_size_z,2):
                                if z+3>=cur_size_z:
                                    continue
                                reg_xs.append(np.array([cur_array[x][y][z-3],cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y][z+3]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_
            

                for x in range(xstart,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(1,cur_size_z,2):
                            #if z==cur_size_z-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if z>=3 and z+3<cur_size_z:
                                if level>=min_coeff_level:
                                    pred= np.dot( np.array([cur_array[x][y][z-3],cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y][z+3]]),coef )+ince 
                                else:
                                    pred=(-cur_array[x][y][z-3]+9*cur_array[x][y][z-1]+9*cur_array[x][y][z+1]-cur_array[x][y][z+3])*0.0625
                            else:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (y!=cur_size_y-1 or last_y!=size_y-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(xstart,cur_size_x,2):
                        for y in range(3,cur_size_y,2):
                            for z in range(1 if zstart>0 else 0,cur_size_z,1):
                                if y+3>=cur_size_y:
                                    continue
                                reg_xs.append(np.array([cur_array[x][y-3][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y+3][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(xstart,cur_size_x,2):
                    for y in range(1,cur_size_y,2):
                        for z in range(1 if zstart>0 else 0,cur_size_z,1):
                            #if y==cur_size_y-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if y>=3 and y+3<cur_size_y:
                                if level>=min_coeff_level:
                                    pred= np.dot( np.array([cur_array[x][y-3][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y+3][z]]),coef )+ince 
                                else:
                                    pred=(-cur_array[x][y-3][z]+9*cur_array[x][y-1][z]+9*cur_array[x][y+1][z]-cur_array[x][y+3][z])*0.0625


                            else:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp 

                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(3,cur_size_x,2):
                        for y in range(1 if ystart>0 else 0,cur_size_y,1):
                            for z in range(1 if zstart>0 else 0,cur_size_z,1):
                                if x+3>=cur_size_x:
                                    continue
                                reg_xs.append(np.array([cur_array[x-3][y][z],cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x+3][y][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(1,cur_size_x,2):
                    for y in range(1 if ystart>0 else 0,cur_size_y,1):
                        for z in range(1 if zstart>0 else 0,cur_size_z,1):
                            if x==cur_size_x-1:
                                continue
                            orig=cur_array[x][y][z]
                            if x>=3 and x+3<cur_size_x:
                                if level>=min_coeff_level:
                                    pred= np.dot( np.array([cur_array[x-3][y][z],cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x+3][y][z]]),coef )+ince 
                                else:
                                    pred=(-cur_array[x-3][y][z]+9*cur_array[x-1][y][z]+9*cur_array[x+1][y][z]-cur_array[x+3][y][z])*0.0625

                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z])*0.5
                            if (not random_access) or level!=0 or ((y!=cur_size_y-1 or last_y!=size_y-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp 
                loss_dict[level]["sz3_cubic_zyx"]=absloss
                if selected_algo=="none" or absloss<best_absloss:
                    selected_algo="sz3_cubic_zyx"
                    best_preds=np.copy(cur_array)
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()



            #xyz
            if fix_algo=="none" or fix_algo=="sz3_cubic" or fix_algo=="sz3_cubic_xyz":
                absloss=0
                cur_qs=[]
                cur_us=[]
                cur_array=np.copy(array[0:last_x+1:step,0:last_y+1:step,0:last_z+1:step])#reset cur_array
                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(3,cur_size_x,2):
                        for y in range(ystart,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                if x+3>=cur_size_x:
                                    continue
                                reg_xs.append(np.array([cur_array[x-3][y][z],cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x+3][y][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_
            

                for x in range(1,cur_size_x,2):
                    for y in range(ystart,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                            #if z==cur_size_z-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if x>=3 and x+3<cur_size_x:
                                if level>=min_coeff_level:
                                    pred= np.dot( np.array([cur_array[x-3][y][z],cur_array[x-1][y][z],cur_array[x+1][y][z],cur_array[x+3][y][z]]),coef )+ince 
                                else:
                                    pred=(-cur_array[x-3][y][z]+9*cur_array[x-1][y][z]+9*cur_array[x+1][y][z]-cur_array[x+3][y][z])*0.0625

                            else:
                                pred=(cur_array[x-1][y][z]+cur_array[x+1][y][z])*0.5
                            if (not random_access) or level!=0 or ((z!=cur_size_z-1 or last_z!=size_z-1) and (y!=cur_size_y-1 or last_y!=size_y-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp    



                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(1 if xstart>0 else 0,cur_size_x,1):
                        for y in range(3,cur_size_y,2):
                            for z in range(zstart,cur_size_z,2):
                                if y+3>=cur_size_y:
                                    continue
                                reg_xs.append(np.array([cur_array[x][y-3][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y+3][z]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(1 if xstart>0 else 0,cur_size_x,1):
                    for y in range(1,cur_size_y,2):
                        for z in range(zstart,cur_size_z,2):
                            #if y==cur_size_y-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if y>=3 and y+3<cur_size_y:
                                if level>=min_coeff_level:
                                    pred= np.dot( np.array([cur_array[x][y-3][z],cur_array[x][y-1][z],cur_array[x][y+1][z],cur_array[x][y+3][z]]),coef )+ince 
                                else:
                                    pred=(-cur_array[x][y-3][z]+9*cur_array[x][y-1][z]+9*cur_array[x][y+1][z]-cur_array[x][y+3][z])*0.0625

                            else:
                                pred=(cur_array[x][y-1][z]+cur_array[x][y+1][z])*0.5
                            if (not random_access) or level!=0 or ((x!=cur_size_x-1 or last_x!=size_x-1) and (z!=cur_size_z-1 or last_z!=size_z-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp 

                if level>=min_coeff_level:
                    reg_xs=[]
                    reg_ys=[]
                    for x in range(1 if xstart>0 else 0,cur_size_x,1):
                        for y in range(1 if ystart>0 else 0,cur_size_y,1):
                            for z in range(3 ,cur_size_z,2):
                                if z+3>=cur_size_z:
                                    continue
                                reg_xs.append(np.array([cur_array[x][y][z-3],cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y][z+3]],dtype=np.float64))
                                reg_ys.append(cur_array[x][y][z])
                                res=LinearRegression(fit_intercept=True).fit(reg_xs, reg_ys)
                                coef=res.coef_ 
                                ince=res.intercept_

                for x in range(1 if xstart>0 else 0,cur_size_x,1):
                    for y in range(1 if ystart>0 else 0,cur_size_y,1):
                        for z in range(1,cur_size_z,2):
                            #if x==cur_size_x-1:
                                #continue
                            orig=cur_array[x][y][z]
                            if z>=3 and z+3<cur_size_z:
                                if level>=min_coeff_level:
                                    pred= np.dot( np.array([cur_array[x][y][z-3],cur_array[x][y][z-1],cur_array[x][y][z+1],cur_array[x][y][z+3]]),coef )+ince 
                                else:
                                    pred=(-cur_array[x][y][z-3]+9*cur_array[x][y][z-1]+9*cur_array[x][y][z+1]-cur_array[x][y][z+3])*0.0625

                            else:
                                pred=(cur_array[x][y][z-1]+cur_array[x][y][z+1])*0.5
                            if (not random_access) or level!=0 or ((y!=cur_size_y-1 or last_y!=size_y-1) and (x!=cur_size_x-1 or last_x!=size_x-1)):
                                absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            cur_qs.append(q)
                

                            if q==0:
                                cur_us.append(decomp)
                        #absloss+=abs(decomp)
                            cur_array[x][y][z]=decomp 
                loss_dict[level]["sz3_cubic_xyz"]=absloss
                if selected_algo=="none" or absloss<best_absloss:
                    selected_algo="sz3_cubic_xyz"
                    best_preds=np.copy(cur_array)
                    best_absloss=absloss
                    best_qs=cur_qs.copy()
                    best_us=cur_us.copy()







        
        #Lorenzo fallback
        if level<=lorenzo:
            absloss=0
        #cur_qs=[]
        #cur_us=[]
        #cur_array=np.copy(array[0:last_x+1:step,0:last_y+1:step])#reset cur_array
            xstart=1 if x_preded else 0
            ystart=1 if y_preded else 0
            zstart=1 if z_preded else 0 
            cur_orig_array=orig_array[0:last_x+1:step,0:last_y+1:step,0:last_z+1:step]
            x_end_offset=1 if (random_access and last_x==size_x-1 and level==0) else 0
            y_end_offset=1 if (random_access and last_y==size_y-1 and level==0) else 0
            z_end_offset=1 if (random_access and last_z==size_z-1 and level==0) else 0
            total_points=[(x,y,z) for x in range(cur_orig_array.shape[0]-1) for y in range(cur_orig_array.shape[1]-1) for z in range(cur_orig_array.shape[2]-1) if (max_step<=0 or ((x*step)%max_step!=0 and (y*step)%max_step!=0 and (z*step)%max_step!=0 ))  ]
            if len(total_points)<min_sampled_points:
                num_sumples=len(total_points)
                sampled_points=total_points
            else:
                num_sumples=max(min_sampled_points,int(len(total_points)*sample_rate) )
                sampled_points=random.sample(total_points,num_sumples)
            for x,y,z in sampled_points:
                '''
                f_011=array[x-max_step][y][z] if x else 0
                f_101=array[x][y-max_step][z] if y else 0
                f_110=array[x][y][z-max_step] if z else 0
                f_001=array[x-max_step][y-max_step][z] if x and y else 0
                f_100=array[x][y-max_step][z-max_step] if y and z else 0
                f_010=array[x-max_step][y][z-max_step] if x and z else 0
                f_000=array[x-max_step][y-max_step][z-max_step] if x and y and z else 0
                
                pred=f_000+f_011+f_101+f_110-f_001-f_010-f_100
                '''
                orig=cur_orig_array[x][y][z]
                f_011=cur_orig_array[x-1][y][z] if x else 0
                if x and max_step>0 and ((x-1)*step)%max_step==0 and (y*step)%max_step==0 and (z*step)%max_step==0:
                    f_011+=anchor_eb*(2*np.random.rand()-1)
                elif x:
                    f_011+=cur_eb*(2*np.random.rand()-1)


                f_101=cur_orig_array[x][y-1][z] if y else 0
                if y and max_step>0 and (x*step)%max_step==0 and ((y-1)*step)%max_step==0 and (z*step)%max_step==0:
                    f_101+=anchor_eb*(2*np.random.rand()-1)
                elif y:
                    f_101+=cur_eb*(2*np.random.rand()-1)
                 
                f_110=cur_orig_array[x][y][z-1] if z else 0
                if z and max_step>0 and (x*step)%max_step==0 and (y*step)%max_step==0 and ((z-1)*step)%max_step==0:
                    f_110+=anchor_eb*(2*np.random.rand()-1)
                elif z:
                    f_110+=cur_eb*(2*np.random.rand()-1)


                f_001=cur_orig_array[x-1][y-1][z] if x and y else 0
                if x and y and max_step>0 and ((x-1)*step)%max_step==0 and ((y-1)*step)%max_step==0 and (z*step)%max_step==0:
                    f_001+=anchor_eb*(2*np.random.rand()-1)
                elif x and y:
                    f_001+=cur_eb*(2*np.random.rand()-1)

                f_100=cur_orig_array[x][y-1][z-1] if y and z else 0
                if y and z and max_step>0 and (x*step)%max_step==0 and ((y-1)*step)%max_step==0 and ((z-1)*step)%max_step==0:
                    f_100+=anchor_eb*(2*np.random.rand()-1)
                elif y and z:
                    f_100+=cur_eb*(2*np.random.rand()-1)

                f_010=cur_orig_array[x-1][y][z-1] if x and z else 0
                if x and z and max_step>0 and ((x-1)*step)%max_step==0 and (y*step)%max_step==0 and ((z-1)*step)%max_step==0:
                    f_010+=anchor_eb*(2*np.random.rand()-1)
                elif x and z:
                    f_010+=cur_eb*(2*np.random.rand()-1)

                f_000=cur_orig_array[x-1][y-1][z-1] if x and y and z else 0
                if x and y and z and max_step>0 and ((x-1)*step)%max_step==0 and ((y-1)*step)%max_step==0 and ((z-1)*step)%max_step==0:
                    f_000+=anchor_eb*(2*np.random.rand()-1)
                elif x and y and z:
                    f_000+=cur_eb*(2*np.random.rand()-1)


                
                pred=f_000+f_011+f_101+f_110-f_001-f_010-f_100

                absloss+=abs(orig-pred)
            #print(absloss*len(total_points)/len(sampled_points))
            #print(best_absloss)
            #print(cumulated_loss)
            if absloss*len(total_points)/len(sampled_points)<best_absloss+cumulated_loss:
                selected_algo="lorenzo_fallback"
                best_absloss=0
                best_preds=np.copy(cur_orig_array)
                best_qs=[]
                best_us=[]
           
            #qs[max_level]=qs[:maxlevel_q_start]
                for i in range(max_level-1,level,-1):
                    qs[i]=[]
                us=us[:u_start]
                for x in range(xstart,cur_size_x-x_end_offset):
                    for y in range(ystart,cur_size_y-y_end_offset):
                        for z in range(zstart,cur_size_z-z_end_offset):
                    
                            if max_step>0 and (x*step)%max_step==0 and (y*step)%max_step==0 and (z*step)%max_step==0:
                            #print(x,y)
                                continue
                            orig=best_preds[x][y][z]
                            f_011=best_preds[x-1][y][z] if x else 0
                            f_101=best_preds[x][y-1][z] if y else 0
                            f_110=best_preds[x][y][z-1] if z else 0
                            f_001=best_preds[x-1][y-1][z] if x and y else 0
                            f_100=best_preds[x][y-1][z-1] if y and z else 0
                            f_010=best_preds[x-1][y][z-1] if x and z else 0
                            f_000=best_preds[x-1][y-1][z-1] if x and y and z else 0
                
                            pred=f_000+f_011+f_101+f_110-f_001-f_010-f_100
                        
                
        
                            best_absloss+=abs(orig-pred)
                            q,decomp=quantize(orig,pred,cur_eb)
                            best_qs.append(q)
                            if q==0:
                                best_us.append(decomp)
                #absloss+=abs(decomp)
                            best_preds[x][y][z]=decomp
            

        #print(len(best_qs))




        mean_l1_loss=best_absloss/len(best_qs)
        if not fake_compression:
            array[0:last_x+1:step,0:last_y+1:step,0:last_z+1:step]=best_preds
        if selected_algo!="lorenzo_fallback":
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
        step=step//2
        level-=1
        #print(sum([len(_) for _ in qs] ))
        #print(best_absloss)
        #print(cumulated_loss)



    def lorenzo_3d(array,x_start,x_end,y_start,y_end,z_start,z_end):
        for x in range(x_start,x_end):
            for y in range(y_start,y_end):
                for z in range(z_start,z_end):
                    if x<=last_x and y<=last_y and z<=last_z:
                        continue

                    orig=array[x][y][z]
                    f_011=array[x-1][y][z] if x else 0
                    f_101=array[x][y-1][z] if y else 0
                    f_110=array[x][y][z-1] if z else 0
                    f_001=array[x-1][y-1][z] if x and y else 0
                    f_100=array[x][y-1][z-1] if y and z else 0
                    f_010=array[x-1][y][z-1] if x and z else 0
                    f_000=array[x-1][y-1][z-1] if x and y and z else 0
                
                    pred=f_000+f_011+f_101+f_110-f_001-f_010-f_100
        
                
                
        
                
                    q,decomp=quantize(orig,pred,error_bound)
                    edge_qs.append(q)
                    if q==0:
                        us.append(decomp)
                    array[x][y]=decomp
    offset_x1=1 if x_preded else 0
    offset_y1=1 if y_preded else 0
    offset_z1=1 if y_preded else 0
    offset_x2=1 if random_access else 0
    offset_y2=1 if random_access else 0
    offset_z2=1 if random_access else 0
    lorenzo_3d(array,offset_x1,size_x-offset_x2,offset_y1,size_y-offset_y2,offset_z1,size_z-offset_z2)
    #lorenzo_2d(array,last_x+1,,offset_y1,size_y-offset_y2)
    return array,qs,edge_qs,us,selected_algos,loss_dict


    
if __name__=="__main__":
 



    parser = argparse.ArgumentParser()

    parser.add_argument('--error','-e',type=float,default=1e-3)
    parser.add_argument('--input','-i',type=str)
    parser.add_argument('--output','-o',type=str)
    parser.add_argument('--quant','-q',type=str,default="ml3_q.dat")
    parser.add_argument('--unpred','-u',type=str,default="ml3_u.dat")
    parser.add_argument('--max_step','-s',type=int,default=16)
    parser.add_argument('--min_coeff_level','-cl',type=int,default=99)
    parser.add_argument('--rate','-r',type=float,default=1.0)
    parser.add_argument('--rlist',type=float,default=-1,nargs="+")
    parser.add_argument('--maximum_rate','-m',type=float,default=10.0)
    #parser.add_argument('--cubic','-c',type=int,default=1)
    parser.add_argument('--multidim_level','-d',type=int,default=99)
    parser.add_argument('--lorenzo_fallback_check','-l',type=int,default=-1)
    parser.add_argument('--fallback_sample_ratio','-p',type=float,default=0.05)
#parser.add_argument('--level_rate','-lr',type=float,default=1.0)
    parser.add_argument('--anchor_rate','-a',type=float,default=0.0)
    parser.add_argument('--sz_interp','-n',type=int,default=0)

    parser.add_argument('--size_x','-x',type=int,default=129)
    parser.add_argument('--size_y','-y',type=int,default=129)
    parser.add_argument('--size_z','-z',type=int,default=129)
    parser.add_argument('--fix_algo','-f',type=str,default="none")
    parser.add_argument('--autotuning','-t',type=float,default=0.0)
#parser.add_argument('--level','-l',type=int,default=2)
#parser.add_argument('--noise','-n',type=bool,default=False)
#parser.add_argument('--intercept','-t',type=bool,default=False)
    args = parser.parse_args()
    print(args)
    array=np.fromfile(args.input,dtype=np.float32).reshape((args.size_x,args.size_y,args.size_z))
    orig_array=np.copy(array)
    rng=np.max(array)-np.min(array)
    error_bound=args.error*rng
    max_level=int(math.log(args.max_step,2))
    rate_list=args.rlist
    #print(rate_list)
    if args.autotuning!=0:
        #pid=os.getpid()
        alpha_list=[1,1.25,1.5,1.75,2]
        #beta_list=[2,4,4,6,6]
        beta_list=[2,4,4,4,4]
        rate_list=None
        block_num_x=(args.size_x-1)//args.max_step
        block_num_y=(args.size_y-1)//args.max_step
        block_num_z=(args.size_z-1)//args.max_step
        steplength=int(args.autotuning**(1/3))
        bestalpha=1
        bestbeta=1
        #bestpdb=0
        bestb=9999
        #bestb_r=9999
        bestp=0
        #bestp_r=0
        pid=os.getpid()
        tq_name="%s_tq.dat"%pid
        tu_name="%s_tu.dat"%pid
        max_step=args.max_step
        for m,alpha in enumerate(alpha_list):
            beta=beta_list[m]
            test_qs=[[] for i in range(max_level+1)]
            test_us=[]
            square_error=0
            #zero_square_error=0
            element_counts=0
            themax=-9999999999999
            themin=99999999999999
            #themean=0
            #print(themean)
            for i in range(0,block_num_x,steplength):
                for j in range(0,block_num_y,steplength):
                    for k in range(0,block_num_z,steplength):
                        x_start=max_step*i
                        y_start=max_step*j
                        z_start=max_step*k
                        x_end=x_start+max_step+1
                        y_end=y_start+max_step+1
                        z_end=z_start+max_step+1
                        #print(x_start)
                        #print(y_start)
                        cur_array=np.copy(array[x_start:x_end,y_start:y_end,z_start:z_end])
                        '''
                        curmax=np.max(cur_array)
                        curmin=np.min(cur_array)
                        if curmax>themax:
                            themax=curmax
                        if curmin<themin:
                            themin=curmin
                        '''
                        cur_array,cur_qs,edge_qs,cur_us,_,lsd=msc3d(cur_array,error_bound,alpha,beta,9999,args.max_step,args.anchor_rate,rate_list=None,x_preded=False,y_preded=False,\
                                                sz_interp=args.sz_interp,multidim_level=args.multidim_level,lorenzo=-1,sample_rate=0.0,min_sampled_points=100,random_access=False,verbose=False,fix_algo=args.fix_algo)
                        #print(len(cur_qs[max_level]))
                        #print(len(test_qs[max_level]))
                        for level in range(max_level+1):
                            #print(level)
                            test_qs[level]+=cur_qs[level]
                        test_us+=cur_us
                        #zero_square_error=np.sum((array[x_start:x_end,y_start:y_end]-themean*np.ones((max_step+1,max_step+1)) )**2)
                        square_error+=np.sum((array[x_start:x_end,y_start:y_end,z_start:z_end]-cur_array)**2)
                        
                        element_counts+=(max_step+1)**3 
            t_mse=square_error/element_counts
            #zero_mse=zero_square_error/element_counts
            psnr=20*math.log(rng,10)-10*math.log(t_mse,10)
            #zero_psnr=20*math.log(themax-themin,10)-10*math.log(zero_mse,10)
            #print(zero_psnr)
          
            np.array(sum(test_qs,[]),dtype=np.int32).tofile(tq_name)
            np.array(sum(test_us,[]),dtype=np.int32).tofile(tu_name)
            with os.popen("sz_backend %s %s" % (tq_name,tu_name)) as f:
                lines=f.read().splitlines()
                cr=eval(lines[4].split("=")[-1])
                if args.anchor_rate==0:
                    anchor_ratio=1/(args.max_step**3)
                    cr=1/((1-anchor_ratio)/cr+anchor_ratio)
                bitrate=32/cr
            os.system("rm -f %s;rm -f %s" % (tq_name,tu_name))
            #pdb=(psnr-zero_psnr)/bitrate
            if psnr<=bestp and bitrate>=bestb:
                continue
            elif psnr>=bestp and bitrate<=bestb:

                    bestalpha=alpha
                    bestbeta=beta
               
                    bestb=bitrate
                    bestp=psnr
                   
            else:
                if psnr>bestp:
                    new_error_bound=1.2*error_bound
                else:
                    new_error_bound=0.8*error_bound
                test_qs=[[] for i in range(max_level+1)]
                test_us=[]
                square_error=0
                #zero_square_error=0
                element_counts=0
                themax=-9999999999999
                themin=99999999999999
                #themean=0
                #print(themean)
                for i in range(0,block_num_x,steplength):
                    for j in range(0,block_num_y,steplength):
                        for k in range(0,block_num_z,steplength):
                            x_start=max_step*i
                            y_start=max_step*j
                            z_start=max_step*k
                            x_end=x_start+max_step+1
                            y_end=y_start+max_step+1
                            z_end=z_start+max_step+1
                            #print(x_start)
                            #print(y_start)
                            cur_array=np.copy(array[x_start:x_end,y_start:y_end,z_start:z_end])
                            '''
                            curmax=np.max(cur_array)
                            curmin=np.min(cur_array)
                            if curmax>themax:
                                themax=curmax
                            if curmin<themin:
                                themin=curmin
                            '''
                            cur_array,cur_qs,edge_qs,cur_us,_,lsd=msc3d(cur_array,new_error_bound,alpha,beta,9999,args.max_step,args.anchor_rate,rate_list=None,x_preded=False,y_preded=False,\
                                                    sz_interp=args.sz_interp,multidim_level=args.multidim_level,lorenzo=-1,sample_rate=0.0,min_sampled_points=100,random_access=False,verbose=False,fix_algo=args.fix_algo)
                            #print(len(cur_qs[max_level]))
                            #print(len(test_qs[max_level]))
                            for level in range(max_level+1):
                                #print(level)
                                test_qs[level]+=cur_qs[level]
                            test_us+=cur_us
                            #zero_square_error=np.sum((array[x_start:x_end,y_start:y_end]-themean*np.ones((max_step+1,max_step+1)) )**2)
                            square_error+=np.sum((array[x_start:x_end,y_start:y_end,z_start:z_end]-cur_array)**2)
                            
                            element_counts+=(max_step+1)**3
                t_mse=square_error/element_counts
                #zero_mse=zero_square_error/element_counts
                psnr_r=20*math.log(rng,10)-10*math.log(t_mse,10)
                #zero_psnr=20*math.log(themax-themin,10)-10*math.log(zero_mse,10)
                #print(zero_psnr)
              
                np.array(sum(test_qs,[]),dtype=np.int32).tofile(tq_name)
                np.array(sum(test_us,[]),dtype=np.int32).tofile(tu_name)
                with os.popen("sz_backend %s %s" % (tq_name,tu_name)) as f:
                    lines=f.read().splitlines()
                    cr=eval(lines[4].split("=")[-1])
                    if args.anchor_rate==0:
                        anchor_ratio=1/(args.max_step**3)
                        cr=1/((1-anchor_ratio)/cr+anchor_ratio)
                    bitrate_r=32/cr
                os.system("rm -f %s;rm -f %s" % (tq_name,tu_name))
                a=(psnr-psnr_r)/(bitrate-bitrate_r)
                b=psnr-a*bitrate
                #print(a)
                #print(b)
                reg=a*bestb+b
                if reg>bestp:
                    bestalpha=alpha
                    bestbeta=beta
               
                    bestb=bitrate
                    bestp=psnr

                
                
               


        print("Autotuning finished. Selected alpha: %f. Selected beta: %f. Best bitrate: %f. Best PSNR: %f."\
        %(bestalpha,bestbeta,bestb,bestp) )
        args.rate=bestalpha
        args.maximum_rate=bestbeta

        if args.fix_algo=="none":
            print("Start predictor tuning.")
            #tune predictor
            fix_algo_list=[]
            for level in range(max_level-1,-1,-1):
                loss_dict={}
                pred_candidates=[]
                if args.sz_interp:
                    pred_candidates+=["sz3_linear_xyz","sz3_linear_zyx","sz3_cubic_xyz","sz3_cubic_zyx"]
                if level<=args.multidim_level:
                    pred_candidates+=["linear","cubic","multidim"]
                for i in range(0,block_num_x,steplength):
                    for j in range(0,block_num_y,steplength):
                        for k in range(0,block_num_z,steplength):
                  
                            x_start=max_step*i
                            y_start=max_step*j
                            z_start=max_step*k
                            x_end=x_start+max_step+1
                            y_end=y_start+max_step+1
                            z_end=z_start+max_step+1
                            #print(x_start)
                            #print(y_start)
                            cur_array=np.copy(array[x_start:x_end,y_start:y_end,z_start:z_end])
                            for predictor in pred_candidates:
                                cur_array,cur_qs,edge_qs,cur_us,_,lsd=msc3d(cur_array,error_bound,alpha,beta,9999,args.max_step,args.anchor_rate,rate_list=None,x_preded=False,y_preded=False,\
                                                                        sz_interp=args.sz_interp,multidim_level=args.multidim_level,lorenzo=-1,sample_rate=0.0,\
                                                                        min_sampled_points=100,random_access=False,verbose=False,first_level=level,last_level=level,fix_algo=predictor,fake_compression=True)
                                cur_loss=lsd[level][predictor]
                                if predictor not in loss_dict:
                                    loss_dict[predictor]=cur_loss
                                else:
                                    loss_dict[predictor]+=cur_loss
                best_predictor="none"
                min_loss=9e20
                for pred in loss_dict:
                    pred_loss=loss_dict[pred]
                    if pred_loss<min_loss:
                        min_loss=pred_loss
                        best_predictor=pred 

                print("Level %d tuned. Best predictor: %s." % (level,best_predictor))
                fix_algo_list.append(best_predictor)
                '''
                for i in range(0,block_num_x,steplength):
                    for j in range(0,block_num_y,steplength):
                        for k in range(0,block_num_z,steplength):
                  
                            x_start=max_step*i
                            y_start=max_step*j
                            z_start=max_step*k
                            x_end=x_start+max_step+1
                            y_end=y_start+max_step+1
                            z_end=z_start+max_step+1
                        #print(x_start)
                        #print(y_start)
                            #cur_array=np.copy(array[x_start:x_end,y_start:y_end,z_start:z_end])
                           
                            array[x_start:x_end,y_start:y_end,z_start:z_end],cur_qs,edge_qs,cur_us,_,lsd=msc3d(array[x_start:x_end,y_start:y_end,z_start:z_end],error_bound,alpha,beta,9999,args.max_step,args.anchor_rate,rate_list=None,x_preded=False,y_preded=False,\
                                                                    sz_interp=args.sz_interp,multidim_level=args.multidim_level,lorenzo=-1,sample_rate=0.0,\
                                                                    min_sampled_points=100,random_access=False,verbose=False,first_level=level,last_level=level,fix_algo=best_predictor,fake_compression=False)
                '''

            fix_algo_list.reverse()
            print(fix_algo_list)
            '''
            for i in range(0,block_num_x,steplength):
                    for j in range(0,block_num_y,steplength):
                        for k in range(0,block_num_z,steplength):
                  
                            x_start=max_step*i
                            y_start=max_step*j
                            z_start=max_step*k
                            x_end=x_start+max_step+1
                            y_end=y_start+max_step+1
                            z_end=z_start+max_step+1
                            array[x_start:x_end,y_start:y_end,z_start:z_end]=orig_array[x_start:x_end,y_start:y_end,z_start:z_end]
            '''
            
        else:
            fix_algo_list=None


            

    else:
        fix_algo_list=None
        if ((isinstance(rate_list,int) or isinstance(rate_list,float)) and  rate_list>0) or (isinstance(rate_list,list ) and rate_list[0]>0):

            if isinstance(rate_list,int) or isinstance(rate_list,float):
                rate_list=[rate_list]

            while len(rate_list)<max_level:
                rate_list.insert(0,rate_list[0])
        else:
            rate_list=None

    #print(rate_list)
    array,qs,edge_qs,us,_,lsd=msc3d(array,error_bound,args.rate,args.maximum_rate,args.min_coeff_level,args.max_step,args.anchor_rate,rate_list=rate_list,x_preded=False,y_preded=False,z_preded=False,\
        sz_interp=args.sz_interp,multidim_level=args.multidim_level,lorenzo=args.lorenzo_fallback_check,sample_rate=args.fallback_sample_ratio,min_sampled_points=100,random_access=False,verbose=True,fix_algo=args.fix_algo,fix_algo_list=fix_algo_list)

    quants=np.concatenate( (np.array(edge_qs,dtype=np.int32),np.array(sum(qs,[]),dtype=np.int32) ) )
    unpreds=np.array(us,dtype=np.float32)
    array.tofile(args.output)
    quants.tofile(args.quant)
    unpreds.tofile(args.unpred)

    '''
    for x in range(args.size_x):
        for y in range(args.size_y):
            for z in range(args.size_z):
                if array[x][y][z]==orig_array[x][y][z] and x%args.max_step!=0 and y%args.max_step!=0 and z%args.max_step!=0:
                    print(x,y,z)
    '''