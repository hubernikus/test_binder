'''
Obstacle Avoidance Algorithm script with vecotr field

@author LukasHuber
@date 2018-02-15
'''

# Command to automatically reload libraries -- in ipython before exectureion
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

import time

from dynamic_obstacle_avoidance.dynamical_system.dynamical_system_representation import *
from dynamic_obstacle_avoidance.obstacle_avoidance.obstacle import *
from dynamic_obstacle_avoidance.obstacle_avoidance.modulation import *
from dynamic_obstacle_avoidance.obstacle_avoidance.obs_common_section import *
from dynamic_obstacle_avoidance.obstacle_avoidance.obs_dynamic_center_3d import *
from dynamic_obstacle_avoidance.obstacle_avoidance.linear_modulations import *

def pltLines(pos0, pos1, xlim=[-100,100], ylim=[-100,100]):
    if pos1[0]-pos0[0]: # m < infty
        m = (pos1[1] - pos0[1])/(pos1[0]-pos0[0])
        
        ylim=[0,0]
        ylim[0] = pos0[1] + m*(xlim[0]-pos0[0])
        ylim[1] = pos0[1] + m*(xlim[1]-pos0[0])
    else:
        xlim = [pos1[0], pos1[0]]
    
    plt.plot(xlim, ylim, '--', color=[0.3,0.3,0.3], linewidth=2)


def Simulation_vectorFields(x_range=[0,10],y_range=[0,10], point_grid=10, obs=[], sysDyn_init=False, xAttractor = np.array(([0,0])), saveFigure = False, figName='default', noTicks=True, showLabel=True, figureSize=(7.,6), obs_avoidance_func=obs_avoidance_interpolation_moving, attractingRegion=False, drawVelArrow=False, colorCode=False, streamColor=[0.05,0.05,0.7], obstacleColor=[], plotObstacle=True, plotStream=True, figHandle=[], alphaVal=1, dynamicalSystem=linearAttractor):

    start_time = time.time()
    
    # Numerical hull of ellipsoid 
    for n in range(len(obs)): 
        obs[n].draw_ellipsoid(numPoints=50) # 50 points resolution 

    # Adjust dynamic center 
    intersection_obs = obs_common_section(obs)  

    # Create meshrgrid of points
    if type(point_grid)==int:
        N_x = N_y = point_grid
        YY, XX = np.mgrid[y_range[0]:y_range[1]:N_y*1j, x_range[0]:x_range[1]:N_x*1j]

    else:
        N_x = N_y = 1
        XX, YY = np.array([[point_grid[0]]]), np.array([[point_grid[1]]])

    if attractingRegion: # Forced to attracting Region
        def obs_avoidance_temp(x, xd, obs):
            return obs_avoidance_func(x, xd, obs, xAttractor)
        
        obs_avoidance= obs_avoidance_temp
    else:
        obs_avoidance = obs_avoidance_func
        
    xd_init = np.zeros((2,N_x,N_y))
    xd_mod  = np.zeros((2,N_x,N_y))

    for ix in range(N_x):
        for iy in range(N_y):
            pos = np.array([XX[ix,iy],YY[ix,iy]])
            xd_init[:,ix,iy] = dynamicalSystem(pos, x0=xAttractor) # initial DS
                
            xd_mod[:,ix,iy] = obs_avoidance(pos, xd_init[:,ix,iy], obs) # modulataed DS with IFD
    
    if sysDyn_init:
        fig_init, ax_init = plt.subplots(figsize=(5,2.5))
        res_init = ax_init.streamplot(XX, YY, xd_init[0,:,:], xd_init[1,:,:], color=[(0.3,0.3,0.3)])
        
        ax_init.plot(xAttractor[0],xAttractor[1], 'k*')
        plt.gca().set_aspect('equal', adjustable='box')

        plt.xlim(x_range)
        plt.ylim(y_range)

    indOfnoCollision = obs_check_collision_2d(obs, XX, YY)

    dx1_noColl = np.squeeze(xd_mod[0,:,:]) * indOfnoCollision
    dx2_noColl = np.squeeze(xd_mod[1,:,:]) * indOfnoCollision

    end_time = time.time()
    print('Modulation calulcation total: {} s'.format(np.round(end_time-start_time), 4))
    print('Average time: {} ms'.format(np.round((end_time-start_time)/(N_x*N_y)*1000),3) )

    if len(figHandle): 
        fig_ifd, ax_ifd = figHandle[0], figHandle[1] 
    else:
        fig_ifd, ax_ifd = plt.subplots(figsize=figureSize) 

    if plotStream:
        if colorCode:
            velMag = np.linalg.norm(np.dstack((dx1_noColl, dx2_noColl)), axis=2 )/6*100

            strm = res_ifd = ax_ifd.streamplot(XX, YY,dx1_noColl, dx2_noColl, color=velMag, cmap='winter', norm=matplotlib.colors.Normalize(vmin=0, vmax=10.) )
        else:
            # Normalize
            normVel = np.sqrt(dx1_noColl**2 + dx2_noColl**2)
            dx1_noColl, dx2_noColl = dx1_noColl/normVel, dx2_noColl/normVel

            res_ifd = ax_ifd.streamplot(XX, YY,dx1_noColl, dx2_noColl, color=streamColor)

        ax_ifd.plot(xAttractor[0],xAttractor[1], 'k*',linewidth=18.0, markersize=18)

    plt.gca().set_aspect('equal', adjustable='box')

    ax_ifd.set_xlim(x_range)
    ax_ifd.set_ylim(y_range)

    if noTicks:
        plt.tick_params(axis='both', which='major',bottom=False, top=False, left=False, right=False, labelbottom=False, labelleft=False)

    if showLabel:
        plt.xlabel(r'$\xi_1$', fontsize=16)
        plt.ylabel(r'$\xi_2$', fontsize=16)

    plt.tick_params(axis='both', which='major', labelsize=14)
    plt.tick_params(axis='both', which='minor', labelsize=12)

    if plotObstacle:
        obs_polygon = []

        for n in range(len(obs)):
            x_obs_sf = obs[n].x_obs_sf # todo include in obs_draw_ellipsoid
            obs_polygon.append( plt.Polygon(obs[n].x_obs))
            if len(obstacleColor)==len(obs):
                obs_polygon[n].set_color(obstacleColor[n])
            else:
                obs_polygon[n].set_color(np.array([176,124,124])/255)
            plt.gca().add_patch(obs_polygon[n])
            
            plt.plot([x_obs_sf[i][0] for i in range(len(x_obs_sf))],
                [x_obs_sf[i][1] for i in range(len(x_obs_sf))], 'k--')

            ax_ifd.plot(obs[n].x0[0],obs[n].x0[1],'k.')
            if hasattr(obs[n], 'center_dyn'):# automatic adaptation of center 
                ax_ifd.plot(obs[n].center_dyn[0],obs[n].center_dyn[1], 'k+', linewidth=18, markeredgewidth=4, markersize=13)

            if drawVelArrow and np.linalg.norm(obs[n].xd)>0:
                col=[0.5,0,0.9]
                fac=5 # scaling factor of velocity
                ax_ifd.arrow(obs[n].x0[0], obs[n].x0[1], obs[n].xd[0]/fac, obs[n].xd[1]/fac, head_width=0.3, head_length=0.3, linewidth=10, fc=col, ec=col, alpha=1)

    plt.ion()
    plt.show()
    
    if saveFigure:
        plt.savefig('fig/' + figName + '.eps', bbox_inches='tight')
        return fig_ifd, ax_ifd
