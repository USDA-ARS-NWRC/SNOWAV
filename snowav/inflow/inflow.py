
import pandas as pd
import os
from datetime import datetime
import copy
import seaborn as sns
from matplotlib import pyplot as plt
import snowav.framework.figures

def inflow(args, logger):
    '''
    Plot inflow and SWI.

    Currently this is only configured for the Tuolumne.

    Args
    ----------
    args : dict
        dictionary with required inputs, see swi() figure for more information.

    logger : list
        snowav logger

    '''

    inflow_summary = args['inflow_summary']
    inflow_headings = args['inflow_headings']
    inflow_summary = inflow_summary.cumsum()

    plotorder = args['plotorder']
    labels = args['labels']
    barcolors = args['barcolors']
    barcolors.insert(0,'black')
    swi_summary = args['swi_summary']
    swi_end_val = copy.deepcopy(swi_summary)
    swi_title = 'SWI and Reservoir Inflow'

    sns.set_style('darkgrid')
    sns.set_context("notebook")

    plt.close(0)
    f = plt.figure(num=0, figsize=(8,5), dpi=args['dpi'])
    a = plt.gca()

    for iters, (name, basin) in enumerate(zip(plotorder[1::], inflow_headings)):
        if iters == 0:
            lblswi = 'SWI'
            lblin = 'inflow'
        else:
            lblswi = '__nolabel__'
            lblin = '__nolabel__'

        swi_summary[name].plot(ax = a, color = barcolors[iters],
                               linestyle=':', linewidth = 0.8, label = lblswi)
        inflow_summary[name].plot(ax = a, color = barcolors[iters],
                                  label = lblin)

    x_end_date = args['end_date']

    a.set_xlim((datetime(args['wy']-1, 10, 1), x_end_date))
    a.legend(loc = 'upper left')

    for tick in a.get_xticklabels():
        tick.set_rotation(30)

    a.set_xlabel('')
    a.axes.set_title(swi_title)
    a.set_ylabel(r'[{}]'.format(args['vollbl']))

    del barcolors[0]

    fig_name_short = 'inflow_'
    fig_name = '{}{}{}.png'.format(args['figs_path'],fig_name_short,args['directory'])
    if logger is not None:
        logger.info(' saving {}'.format(fig_name))

    snowav.framework.figures.save_fig(f, fig_name)

    return fig_name_short

def excel_to_csv(args, logger):
    '''
    Read in summary inflow data from operators, pull full natural flow
    calculations, and write out summary csv file.

    Args
    ------
    args : dict
    logger : object

    '''

    path = args['path']
    csv_file = args['csv_file']
    basin_headings = args['basin_headings']
    inflow_headings = args['inflow_headings']
    file_base = args['file_base']
    sheet_name = args['sheet_name']
    skiprows = args['skiprows']
    date_idx = args['date_idx']
    wy = args['wy']
    overwrite = args['overwrite']
    convert = args['convert']

    # recipe depending on basin?
    if True:
        date_heading = '        HETCH HETCHY WATER AND POWER SYSTEM'

    # if convert == float(0.0098):
    #     ulbl = 'TAF'

    if not os.path.isfile(csv_file):
        if logger is not None:
            logger.info(' {} not a file, creating it...'.format(csv_file))

        date_range = pd.date_range(datetime(wy,10,1),datetime(wy,10,1),freq='D')
        csv = pd.DataFrame(index = date_range, columns = basin_headings)

    else:
        csv = pd.read_csv(csv_file, parse_dates=[0], index_col = 0)

    files = os.listdir(path)

    for file in files:
        if file_base in file:
            # get date from loading in full file
            f = pd.read_excel(os.path.join(path,file),
                              sheet_name = sheet_name,
                              skiprows = 0)
            inflow_date = pd.to_datetime(f[date_heading].values[date_idx])
            data = pd.read_excel(os.path.join(path,file),
                                 sheet_name=sheet_name,
                                 skiprows=skiprows)

            if not inflow_date.date() in csv.index or overwrite:
                for basin,heading in zip(basin_headings,inflow_headings):
                    if logger is not None:
                        logger.info(' Assigning basin inflow in {}: {}, {} to '
                                      '{}'.format(file, inflow_date, heading, basin))
                    csv.loc[inflow_date,basin] = data[heading].values[11]*convert

    csv.sort_index(inplace=True)
    csv.to_csv(csv_file)
