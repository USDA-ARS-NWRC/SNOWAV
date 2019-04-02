
from snowav.utils.MidpointNormalize import MidpointNormalize
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import seaborn as sns
import copy
import cmocean
import matplotlib.patches as mpatches
import pandas as pd
from snowav import database
from snowav.database.tables import Basins
import datetime
from datetime import timedelta
from snowav.plotting.plotlims import plotlims as plotlims


def flt_image_change(snow):
    '''
    This plots a second image_change fig, intended for flight updates

    '''
    # Get change in swe during the specified period

    # find closest
    s = min(snow.outputs['dates'],key=lambda x: abs(x-snow.flt_start_date))
    e = min(snow.outputs['dates'],key=lambda x: abs(x-snow.flt_end_date))
    ixs = np.where(snow.outputs['dates'] == s)[0][0]
    ixe = np.where(snow.outputs['dates'] == e)[0][0]

    if (ixs == ixe) and (len(snow.outputs['dates']) > 1):
        ixs = ixe - 1
        snow._logger.info('flt_start_date and/or flt_end_date not found, using '
                            'last two images as flight difference')
        print('flt_start_date and/or flt_end_date not found, using '
                            'last two images as flight difference')

    delta_swe = snow.outputs['swe_z'][ixe] - snow.outputs['swe_z'][ixs]
    delta_swe = np.multiply(delta_swe,snow.depth_factor)

    # Make df from database
    delta_swe_byelev = pd.DataFrame(index = snow.edges, columns = snow.plotorder)
    end_swe_byelev = pd.DataFrame(index = snow.edges, columns = snow.plotorder)

    for bid in snow.plotorder:
        r = database.database.query(snow, snow.flt_start_date, snow.flt_end_date,
                                    snow.run_name, bid, 'swe_vol')
        for elev in snow.edges:
            v = r[(r['elevation'] == str(elev)) & (r['date_time'] == snow.flt_start_date)]
            v2 = r[(r['elevation'] == str(elev)) & (r['date_time'] == snow.flt_end_date)]
            delta_swe_byelev.loc[elev,bid] = np.nansum(v2['value'].values - v['value'].values)
            end_swe_byelev.loc[elev,bid] = v2['value'].values

    # Make copy so that we can add nans for the plots, but not mess up the original
    delta_state = copy.deepcopy(delta_swe)
    qMin,qMax = np.nanpercentile(delta_state,[1,99.5])

    ix = np.logical_and(delta_state < qMin, delta_state >= np.nanmin(np.nanmin(delta_state)))
    delta_state[ix] = qMin + qMin*0.2
    vMin,vMax = np.nanpercentile(delta_state,[1,99])

    colorsbad = plt.cm.Set1_r(np.linspace(0., 1, 1))
    colors1 = cmocean.cm.matter_r(np.linspace(0., 1, 127))
    colors2 = plt.cm.Blues(np.linspace(0, 1, 128))
    colors = np.vstack((colorsbad,colors1, colors2))
    mymap = mcolors.LinearSegmentedColormap.from_list('my_colormap', colors)

    ixf = delta_state == 0
    delta_state[ixf] = -100000 # set snow-free
    pmask = snow.masks[snow.plotorder[0]]['mask']
    ixo = pmask == 0
    delta_state[ixo] = np.nan
    cmap = copy.copy(mymap)
    cmap.set_bad('white',1.)

    sns.set_style('darkgrid')
    sns.set_context("notebook")

    lims = plotlims(snow.basin, snow.plotorder)


    plt.close(6)
    fig,(ax,ax1) = plt.subplots(num=6, figsize=snow.figsize,
                                dpi=snow.dpi, nrows = 1, ncols = 2)
    h = ax.imshow(delta_state, interpolation='none',
        cmap = cmap, norm=MidpointNormalize(midpoint=0,
                                            vmin = vMin-0.01,vmax=vMax+0.01))

    if snow.basin == 'LAKES':
        ax.set_xlim(snow.imgx)
        ax.set_ylim(snow.imgy)

    # Basin boundaries
    for name in snow.masks:
        ax.contour(snow.masks[name]['mask'],cmap = "Greys",linewidths = 1)

    # if snow.basin == 'SJ':
    #     fix1 = np.arange(1275,1377)
    #     fix2 = np.arange(1555,1618)
    #     ax.plot(fix1*0,fix1,'k')
    #     ax.plot(fix2*0,fix2,'k')

    # Do pretty stuff
    h.axes.get_xaxis().set_ticks([])
    h.axes.get_yaxis().set_ticks([])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.2)
    cbar = plt.colorbar(h, cax = cax)

    if snow.units == 'TAF':
        cbar.set_label(r'$\Delta$ SWE [in]')
    if snow.units == 'SI':
        cbar.set_label(r'$\Delta$ SWE [mm]')

    start_date = snow.flt_start_date + timedelta(hours=1)
    d = snow.flt_end_date + timedelta(hours=1)

    h.axes.set_title('Change in SWE from Snow Depth Update\n{}'
                     .format(start_date.date().strftime("%Y-%-m-%-d")))

    # Plot the bar in order

    if snow.dplcs == 0:
        tlbl = '{}: {} {}'.format(snow.plotorder[0],
                             str(int(delta_swe_byelev[snow.plotorder[0]].sum())),
                             snow.vollbl)
    else:
        tlbl = '{}: {} {}'.format(snow.plotorder[0],
                             str(np.round(delta_swe_byelev[snow.plotorder[0]].sum(),
                                          snow.dplcs)),snow.vollbl)

    for iters,name in enumerate(lims.sumorder):

        if snow.dplcs == 0:
            lbl = '{}: {} {}'.format(name,
                                str(int(delta_swe_byelev[name].sum())),
                                snow.vollbl)
        else:
            lbl = '{}: {} {}'.format(name,
                                str(np.round(delta_swe_byelev[name].sum(),
                                snow.dplcs)),snow.vollbl)

        if iters == 0:
            ax1.bar(range(0,len(snow.edges)),delta_swe_byelev[name],
                    color = snow.barcolors[iters],
                    edgecolor = 'k',label = lbl)

        else:
            ax1.bar(range(0,len(snow.edges)),delta_swe_byelev[name],
                    bottom = pd.DataFrame(delta_swe_byelev[lims.sumorder[0:iters]]).sum(axis = 1).values,
                    color = snow.barcolors[iters], edgecolor = 'k',label = lbl)

    print('flt_image_change ', delta_swe_byelev.sum(skipna=True))
    print('flt_image_change ', end_swe_byelev.sum(skipna=True))
    print('flt_image_change percent change', delta_swe_byelev.sum(skipna=True)/end_swe_byelev.sum(skipna=True))

    plt.tight_layout()
    xts = ax1.get_xticks()
    edges_lbl = []
    for i in xts[0:len(xts)-1]:
        edges_lbl.append(str(int(snow.edges[int(i)])))

    ax1.set_xticklabels(str(i) for i in edges_lbl)
    for tick in ax1.get_xticklabels():
        tick.set_rotation(30)

    ylims = ax1.get_ylim()
    if ylims[0] < 0 and ylims[1] == 0:
        ax1.set_ylim((ylims[0]+(ylims[0]*0.3),ylims[1]+ylims[1]*0.3))
    if ylims[0] < 0 and ylims[1] > 0:
        ax1.set_ylim((ylims[0]+(ylims[0]*0.3),(ylims[1] + ylims[1]*0.9)))
        if (ylims[1] + ylims[1]*0.9) < abs(ylims[0]):
            ax1.set_ylim((ylims[0]+(ylims[0]*0.3),(-(ylims[0]*0.6))))

    if ylims[1] == 0:
        ax1.set_ylim((ylims[0]+(ylims[0]*0.3),(-ylims[0])*0.65))
    if ylims[0] == 0:
        ax1.set_ylim((ylims[0]+(ylims[0]*0.3),ylims[1]+ylims[1]*0.3))

    ax1.set_ylabel('%s - per elevation band'%(snow.vollbl))
    ax1.set_xlabel('elevation [%s]'%(snow.elevlbl))
    ax1.axes.set_title('Change in SWE')

    ax1.yaxis.set_label_position("right")
    ax1.tick_params(axis='x')
    ax1.tick_params(axis='y')
    ax1.yaxis.tick_right()

    patches = [mpatches.Patch(color='grey', label='snow free')]
    if snow.basin == 'SJ':
        ax.legend(handles=patches, bbox_to_anchor=(0.3, 0.05),
                  loc=2, borderaxespad=0. )
    elif snow.basin == 'RCEW':
        ax.legend(handles=patches, bbox_to_anchor=(-0.1, 0.05),
                  loc=2, borderaxespad=0. )
    else:
        ax.legend(handles=patches, bbox_to_anchor=(0.05, 0.05),
                  loc=2, borderaxespad=0. )

    # basin total and legend

    if len(snow.plotorder) > 1:
        ax1.legend(loc=(lims.legx,lims.legy))

    ax1.text(lims.btx,lims.bty,tlbl,horizontalalignment='center',
             transform=ax1.transAxes,fontsize = 10)

    plt.tight_layout()
    fig.subplots_adjust(top=0.88)

    snow._logger.info('saving {}dflt_swe_change_{}.png'.format(snow.figs_path,snow.name_append))
    plt.savefig('{}dflt_swe_change_{}.png'.format(snow.figs_path,snow.name_append))
