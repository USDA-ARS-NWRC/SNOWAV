
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import seaborn as sns
import cmocean
import matplotlib.patches as mpatches
import pandas as pd
import snowav.framework.figures

def cold_content(args, logger):
    '''
    SWE unavailable for melt based on snowpack cold content.

    Args
    ----------
    args : dict
        dictionary of values and options for figure. See CoreConfig.ini
            for more information. Use config option [plots]
            print_args_dict: True to print args to the screen if desired.

            df: standard subbasin by elevation dataframe from
                snowav.database.database.collect()
                       Extended Tuolumne  Tuolumne  Cherry Creek  Eleanor
                3000      0.008              0.008         0.000    0.000
                ...
            image: 2D array of cold content
            swe: 2D array of SWE to mask cold content
            title: figure title
            directory: figure directory name
            figs_path: base directory for saving figures
            edges: array of elevation bins in min, max, step
            plotorder: list of basins from topo.nc
            labels: dictionary of labels to use with plotorder
            lims: more figure specs from snowav.plotting.plotlims(plotorder)
            masks: masks made from topo.nc and snowav_masks()
            figsize: figure size
            dpi: figure dpi
            depthlbl: depth label
            vollbl: volume label
            dplcs: decimal places to round outputs
            barcolors: list of colors for bar plots
            xlims: xlims
            elevlbl: elevation label
            depth_clip: lower limit on image depths for plotting
            percent_min: quantile min for image
            percent_max: quantile max for image

        logger : dict
            snowav logger
    '''
    # print to screen for each figure if desired
    if args['print']:
        print('cold_content() figure args:\n','omitting masks, image, and swe...\n')
        for name in args.keys():
            if name not in ['masks','image','swe']:
                print(name, ': ', args[name])

    masks = args['masks']
    swe = args['swe']
    image = args['image']
    df = args['df']
    plotorder = args['plotorder']
    lims = args['lims']
    edges = args['edges']
    labels = args['labels']
    barcolors = args['barcolors']

    clims2 = (-5,0)
    pmask = masks[plotorder[0]]['mask']
    ixo = pmask == 0
    ixz = swe == 0
    image[ixz] = 1

    mymap1 = plt.cm.Spectral_r
    image[ixo] = np.nan
    mymap1.set_bad('white')
    mymap1.set_over('lightgrey',1)

    sns.set_style('darkgrid')
    sns.set_context("notebook")

    plt.close(1)
    fig,(ax,ax1) = plt.subplots(num=1, figsize=args['figsize'],
                                facecolor = 'white', dpi=args['dpi'],
                                nrows = 1, ncols = 2)

    h = ax.imshow(image, clim=clims2, cmap = mymap1)

    for name in masks:
        ax.contour(masks[name]['mask'],cmap = "Greys",linewidths = 1)

    # Do pretty stuff for the left plot
    h.axes.get_xaxis().set_ticks([])
    h.axes.get_yaxis().set_ticks([])
    h.axes.set_title(args['title'])
    divider = make_axes_locatable(ax)
    cax2 = divider.append_axes("right", size="5%", pad=0.2)
    cbar = plt.colorbar(h, cax = cax2)
    cbar.set_label('[MJ/$m^3$]')
    cbar.ax.tick_params()

    patches = [mpatches.Patch(color='grey', label='snow free')]

    # If there is meaningful snow-free area, include path and label
    if sum(sum(ixz)) > 1000:
        patches = [mpatches.Patch(color='grey', label='snow free')]
        ax.legend(handles=patches, bbox_to_anchor=(lims.pbbx, 0.05),
                  loc=2, borderaxespad=0. )

    # basin total and legend
    ax1.legend(loc=(lims.legx,lims.legy),markerscale = 0.5)

    for iters,name in enumerate(lims.sumorder):

        if args['dplcs'] == 0:
            ukaf = str(np.int(np.nansum(df[name])))
        else:
            ukaf = str(np.round(np.nansum(df[name]),args['dplcs']))

        if iters == 0:
            ax1.bar(range(0,len(edges)),df[name],
                    color = barcolors[iters],
                    edgecolor = 'k',
                    label = labels[name] + ': {} {}'.format(ukaf,args['vollbl']))

        else:
            ax1.bar(range(0,len(edges)),df[name],
                    bottom = pd.DataFrame(df[lims.sumorder[0:iters]]).sum(axis = 1).values,
                    color = barcolors[iters], edgecolor = 'k',
                    label = labels[name] + ': {} {}'.format(ukaf,args['vollbl']))

    if 'ylims' in args.keys():
        ax1.set_ylim(args['ylims'])

    else:
        ylims = ax1.get_ylim()
        max = ylims[1] + ylims[1]*0.5
        min = 0
        ax1.set_ylim((min, max))

    ax1.xaxis.set_ticks(range(0,len(edges)))
    plt.tight_layout()
    ax1.set_xlim((args['xlims'][0]-0.5,args['xlims'][1]-0.5))

    edges_lbl = []
    for i in range(0,len(edges)):
        edges_lbl.append(str(int(edges[int(i)])))

    ax1.set_xticklabels(str(i) for i in edges_lbl)
    for tick in ax1.get_xticklabels():
        tick.set_rotation(30)

    ax1.set_xlim((args['xlims'][0]-0.5,args['xlims'][1]+0.5))

    ax1.set_xlabel('elevation [{}]'.format(args['elevlbl']))
    ax1.set_ylabel('{} '.format(args['vollbl']))
    ax1.yaxis.set_label_position("right")
    ax1.yaxis.tick_right()
    ax1.legend(loc = 2, fontsize = 10)

    for tick in ax1.get_xticklabels():
        tick.set_rotation(30)

    ax1.set_xlim((args['xlims'][0]-0.5,args['xlims'][1]-0.5))
    fig.tight_layout()
    fig.subplots_adjust(top=0.92,wspace = 0.2)

    fig_name_short = 'cold_content_'
    fig_name = '{}{}{}.png'.format(args['figs_path'],fig_name_short,args['directory'])
    if logger is not None:
        logger.info(' saving {}{}{}.png'.format(args['figs_path'],fig_name,args['directory']))
    snowav.framework.figures.save_fig(fig, fig_name)

    return fig_name_short
