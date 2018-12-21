
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import seaborn as sns
import copy
import cmocean
import matplotlib.patches as mpatches
from snowav import database
from snowav.database.tables import Basins
import pandas as pd


def cold_content(snow):
    '''

    '''

    state = copy.deepcopy(snow.outputs['swe_z'][snow.ixe])
    state = np.multiply(state,snow.depth_factor)
    cold = copy.deepcopy(snow.outputs['coldcont'][snow.ixe])
    cold = np.multiply(cold,0.000001)

    clims2 = (-5,0)
    pmask = snow.masks[snow.plotorder[0]]['mask']
    ixo = pmask == 0

    # Prepare no-snow and outside of the basin for the colormaps
    ixz = state == 0
    cold[ixz] = 1

    mymap1 = plt.cm.Spectral_r
    cold[ixo] = np.nan
    mymap1.set_bad('white')
    mymap1.set_over('lightgrey',1)

    sns.set_style('darkgrid')
    sns.set_context("notebook")

    plt.close(1)
    fig,(ax,ax1) = plt.subplots(num=1, figsize=snow.figsize,
                                facecolor = 'white', dpi=snow.dpi,
                                nrows = 1, ncols = 2)

    h = ax.imshow(cold, clim=clims2, cmap = mymap1)

    if snow.basin == 'LAKES':
        ax.set_xlim(snow.imgx)
        ax.set_ylim(snow.imgy)

    # Basin boundaries
    for name in snow.masks:
        ax.contour(snow.masks[name]['mask'],cmap = "Greys",linewidths = 1)

    # Do pretty stuff for the left plot
    h.axes.get_xaxis().set_ticks([])
    h.axes.get_yaxis().set_ticks([])
    h.axes.set_title('Cold Content \n %s'%(snow.report_date.date().strftime("%Y-%-m-%-d")))
    divider = make_axes_locatable(ax)
    cax2 = divider.append_axes("right", size="5%", pad=0.2)
    cbar = plt.colorbar(h, cax = cax2)
    cbar.set_label('[MJ/$m^3$]')
    cbar.ax.tick_params()

    patches = [mpatches.Patch(color='grey', label='snow free')]

    # Make legend/box defaults and adjust as needed
    pbbx = 0.15
    pbby = 0.05

    if snow.basin in ['KAWEAH', 'RCEW']:
        pbbx = 0.1

    # snow-free
    ax.legend(handles=patches, bbox_to_anchor=(pbbx, pbby),
              loc=2, borderaxespad=0. )

    nonmelt = pd.DataFrame(index = snow.edges, columns = snow.plotorder)

    for bid in snow.plotorder:
        r2 = database.database.query(snow, snow.start_date, snow.end_date,
                                    snow.run_name, bid, 'swe_unavail')

        for elev in snow.edges:
            v2 = r2[(r2['elevation'] == str(elev))
                  & (r2['date_time'] == snow.end_date)
                  & (r2['basin_id'] == Basins.basins[bid]['basin_id'])]
            nonmelt.loc[elev,bid] = v2['value'].values[0]

    lim = np.max(np.max(nonmelt[snow.plotorder[0]]))
    if lim <= 1:
        lim = 1

    ylim = np.max(lim) + np.max(lim)*0.2
    ix = len(snow.barcolors)
    # Total basin label

    if len(snow.plotorder) > 1:
        sumorder = snow.plotorder[1::]
    else:
        sumorder = snow.plotorder

    for iters,name in enumerate(sumorder):

        if snow.dplcs == 0:
            ukaf = str(np.int(np.nansum(nonmelt[name])))
        else:
            ukaf = str(np.round(np.nansum(nonmelt[name]),snow.dplcs))

        if iters == 0:
            ax1.bar(range(0,len(snow.edges)),nonmelt[name],
                    color = snow.barcolors[iters],
                    edgecolor = 'k',label = name + ': {} {}'.format(ukaf,snow.vollbl))

        else:
            ax1.bar(range(0,len(snow.edges)),nonmelt[name],
                    bottom = pd.DataFrame(nonmelt[sumorder[0:iters]]).sum(axis = 1).values,
                    color = snow.barcolors[iters], edgecolor = 'k',label = name + ': {} {}'.format(ukaf,snow.vollbl))

    xts = ax1.get_xticks()
    if len(xts) < 6:
        dxt = xts[1] - xts[0]
        xts = np.arange(xts[0],xts[-1] + 1 ,dxt/2)
        ax1.set_xticks(xts)

    edges_lbl = []
    for i in xts[0:len(xts)-1]:
        edges_lbl.append(str(int(snow.edges[int(i)])))

    ax1.set_xticklabels(str(i) for i in edges_lbl)
    ax1.set_xlabel('elevation [{}]'.format(snow.elevlbl))
    ax1.set_ylabel('{} - per elevation band'.format(snow.vollbl))
    ax1.yaxis.set_label_position("right")
    ax1.yaxis.tick_right()
    ax1.legend(loc = 2, fontsize = 10)
    ax1.set_ylim((0,ylim))

    for tick in ax1.get_xticklabels():
        tick.set_rotation(30)

    ax1.set_xlim((snow.xlims[0]-0.5,snow.xlims[1]))
    fig.tight_layout()
    fig.subplots_adjust(top=0.92,wspace = 0.2)

    snow._logger.info('saving figure to %scold_content_%s.png'%(snow.figs_path,snow.name_append))
    plt.savefig('%scold_content_%s.png'%(snow.figs_path,snow.name_append))