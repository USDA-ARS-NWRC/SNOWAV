
import numpy as np
import os
import copy
import pandas as pd
from datetime import datetime, timedelta
import logging
import coloredlogs
import netCDF4 as nc
from snowav.database.package_results import package
from snowav.database.database import delete, query
from snowav.utils.utilities import calculate, precip, snow_line, input_summary
from tablizer.defaults import Units
from tablizer.tablizer import get_existing_records
import time
import warnings

def process(args):
    '''
    Process AWSM model results made in awsm_daily format, remove any existing
    database results with the same run_name and date, and place results on
    database. See README.md and CoreConfig.ini for more information.

    Args
    ------
    args : dict

    Returns
    -------
    precip_total : array
    rain_total : array
    log : list
    density : array
    flag : bool

    '''

    pd.options.mode.chained_assignment = None
    warnings.filterwarnings('ignore')

    log = []
    cclimit = -5*1000*1000
    t = 0
    dem = args['dem']
    outputs = args['outputs']
    rundirs_dict = args['rundirs_dict']
    edges = args['edges']
    masks = args['masks']
    ixd = args['ixd']
    pixel = args['pixel']
    lbls = {}
    lbls['depthlbl'] = args['depthlbl']
    lbls['vollbl'] = args['vollbl']
    lbls['elevlbl'] = args['elevlbl']
    raw_out = ['swi_z','evap_z','snowmelt','swe_z','depth','density','coldcont']
    precip_path = '/smrfOutputs/precip.nc'
    proc_list = copy.deepcopy([*args['vars'].keys()])

    dz = pd.DataFrame(np.nan, index = edges, columns = masks.keys())
    precip_total = np.zeros((args['nrows'],args['ncols']))
    rain_total = np.zeros((args['nrows'],args['ncols']))

    for iters, out_date in enumerate(outputs['dates']):

        # assume to start that we are processing everything
        proc_list = copy.deepcopy([*args['vars'].keys()])

        pass_flag = False

        # delete anything on the database with the same run_name and date
        for bid in args['plotorder']:
            results = query(args['connector'], out_date, out_date,
                            args['run_name'], args['basins'], bid, 'swe_vol')

            if not results.empty:
                if not args['db_overwrite']:
                    if bid == args['plotorder'][0]:
                        logging.info(' Skipping outputs for {}, {}, '
                                     'database records exist...'.format(bid,
                                     out_date.strftime("%Y-%-m-%-d %H:00")))
                    else:
                        logging.debug(' Skipping outputs for {}, {}, '
                                     'database records exist...'.format(bid,
                                     out_date.strftime("%Y-%-m-%-d %H:00")))

                    # If database records exist we can skip all outputs except
                    # for density on the last day, if making the figure
                    pass_flag = True
                    flag = False
                    if out_date == outputs['dates'][-1] and args['density_figure']:
                        proc_list = ['density']
                    else:
                        proc_list = []

                else:
                    out = delete(args['connector'], args['basins'], out_date,
                                 out_date, bid, args['run_name'])
                    if out != []:
                        if bid == args['plotorder'][0]:
                            logging.info(out[0])
                        else:
                            logging.debug(out[0])

        # Initialize output dataframes for every day
        daily_outputs = {'swe_vol':dz.copy(),
                         'swe_avail':dz.copy(),
                         'swe_unavail':dz.copy(),
                         'swe_z':dz.copy(),
                         'swi_vol':dz.copy(),
                         'swi_z':dz.copy(),
                         'precip_vol':dz.copy(),
                         'precip_z':dz.copy(),
                         'depth':dz.copy(),
                         'density':dz.copy(),
                         'rain_z':dz.copy(),
                         'evap_z':dz.copy(),
                         'coldcont':dz.copy(),
                         'snow_line':pd.DataFrame(0, index = ['total'],
                                                  columns = masks.keys())}

        density = {}
        for name in masks:
            density[name] = {}

        # Get daily rain from hourly input data
        # Only run this processing if database records don't exist, or if
        # we are making the precip figure
        if not pass_flag or args['precip_depth_figure']:
            logging.debug(' Processing precip for {}'.format(
                         out_date.strftime("%Y-%-m-%-d %H:00")))
            flag, path, pre, rain = precip(rundirs_dict[outputs['time'][iters]],
                                           precip_path)

            if flag:
                precip_total = precip_total + pre
                rain_total = rain_total + rain
            else:
                logging.warning(' Expected to find {} but it is not a valid '
                           'file, precip will not be calculated or put on the '
                           'database, no precip figures will be made'.format(path))

        if args['inputs_flag']:
            mask_list = []
            for name in masks:
                mask_list.append(copy.deepcopy(masks[name]['mask']))

            variable = 'air_temp'
            methods = args['inputs_methods']
            percentiles = args['inputs_percentiles']
            location = args['connector']
            run_name = args['run_name']
            basins = args['basins']
            run_id = args['run_id']

            if os.path.splitext(location)[1] == '.db':
                db = 'sqlite'
            else:
                db = 'sql'

            sf = rundirs_dict[outputs['time'][iters]].replace('runs','data')
            sf = sf.replace('run','data') + '/smrfOutputs/'
            inputs = os.listdir(sf)

            df = get_existing_records(args['connector'], args['dbs'])
            df = df.set_index('date_time')
            df.sort_index(inplace=True)

            for input in inputs:
                input_path = os.path.join(sf,input)
                variable = os.path.splitext(input)[0]

                if variable in args['inputs_variables']:
                    for basin in args['inputs_basins']:

                        basin_id = int(basins[basin]['basin_id'])

                        dfs = df[((df['variable'] == variable) &
                                 (df['run_name'] == run_name) &
                                 (df['basin_id'] == basin_id))]
                        idx = dfs.index

                        if not idx.contains(out_date) or (idx.contains(out_date) and args['db_overwrite']):
                            if ((basin == args['inputs_basins'][0]) and
                                (variable == args['inputs_variables'][0])):
                                logging.info(' Processing inputs for {}, {}, '
                                             '{} '.format(variable, basin,
                                             out_date.strftime("%Y-%-m-%-d %H:00")))
                            else:
                                logging.debug(' Processing inputs for {}, {}, '
                                             '{} '.format(variable, basin,
                                             out_date.strftime("%Y-%-m-%-d %H:00")))

                            input_summary(input_path, variable, methods,
                                          percentiles, db, location, run_name,
                                          basin_id, run_id, masks[basin]['mask'])

                        if idx.contains(out_date) and not args['db_overwrite']:
                            if ((basin == args['inputs_basins'][0]) and
                                (variable == args['inputs_variables'][0])):
                                logging.info(' Skipping inputs for {}, {}, '
                                             '{}, database records exist...'
                                             ''.format(variable, basin,
                                             out_date.strftime("%Y-%-m-%-d %H:00")))
                            else:
                                logging.debug(' Skipping inputs for {}, {}, '
                                             '{}, database records exist...'
                                             ''.format(variable, basin,
                                             out_date.strftime("%Y-%-m-%-d %H:00")))

        swe = copy.deepcopy(outputs['swe_z'][iters])
        cold = copy.deepcopy(outputs['coldcont'][iters])

        # Loop over outputs (depths are copied, volumes are calculated)
        for k in proc_list:

            # Mask by subbasin
            for name in masks:
                if name == args['plotorder'][0]:
                    logging.info(' Processing {}, {}, {} '.format(k, name,
                                 rundirs_dict[outputs['time'][iters]].split('/')[-1]))
                else:
                    logging.debug(' Processing {}, {}, {} '.format(k, name,
                                 rundirs_dict[outputs['time'][iters]].split('/')[-1]))

                mask = copy.deepcopy(masks[name]['mask'])
                elevbin = ixd*mask

                snow_mask = swe > 0
                avail_mask = cold > cclimit
                unavail_mask = cold <= cclimit

                if k in raw_out:
                    o = copy.deepcopy(outputs[k][iters])

                # elevation band
                for n in np.arange(0,len(edges)):
                    b = edges[n]
                    elev_mask = elevbin == n

                    # list of masks
                    be = [mask, elev_mask]
                    ba = [mask, avail_mask]
                    bu = [mask, unavail_mask]
                    bes = [mask, elev_mask, snow_mask]
                    besa = [mask, elev_mask, snow_mask, avail_mask]
                    besu = [mask, elev_mask, snow_mask, unavail_mask]

                    if k == 'swe_z':
                        daily_outputs['swe_unavail'].loc[b,name] = \
                                    calculate(o, pixel, besu, 'sum','volume')
                        daily_outputs['swe_avail'].loc[b,name] = \
                                    calculate(o, pixel, besa, 'sum','volume')
                        daily_outputs['swe_vol'].loc[b,name] = \
                                    calculate(o, pixel, be, 'sum','volume')
                        daily_outputs['swe_z'].loc[b,name] = \
                                    calculate(o, pixel, be, 'mean','depth')

                    if k == 'swi_z':
                        daily_outputs[k].loc[b,name] = calculate(o,pixel,be,'mean','depth')
                        daily_outputs['swi_vol'].loc[b,name] = calculate(o,pixel,be,'sum','volume')

                    if k == 'depth':
                        daily_outputs[k].loc[b,name] = calculate(o, pixel, be, 'mean', 'snow_depth')

                    if k == 'evap_z':
                        daily_outputs[k].loc[b,name] = calculate(o, pixel, be, 'mean', 'depth')

                    if k == 'coldcont':
                        daily_outputs[k].loc[b,name] = calculate(o, pixel, bes, 'mean')

                    if k == 'density':
                        daily_outputs[k].loc[b,name] = calculate(o, pixel, bes, 'mean')

                        if out_date == outputs['dates'][-1]:
                            od = copy.deepcopy(o)
                            ml = [mask, elev_mask, snow_mask]
                            for m in ml:
                                m = m.astype('float')
                                m[m < 1] = np.nan
                                od = od * m

                            density[name][edges[n]] = copy.deepcopy(od)

                    if k == 'precip_z' and flag:
                        daily_outputs[k].loc[b,name] = calculate(pre, pixel, be, 'mean', 'depth')
                        daily_outputs['precip_vol'].loc[b,name] = calculate(pre, pixel, be, 'sum', 'volume')

                    if k == 'rain_z' and flag:
                        daily_outputs[k].loc[b,name] = calculate(rain, pixel, be, 'mean', 'depth')

                if k == 'evap_z':
                    daily_outputs[k].loc['total',name] = calculate(o, pixel, [mask, snow_mask], 'mean', 'depth')

                if k == 'coldcont':
                    daily_outputs[k].loc['total',name] = calculate(o, pixel, [mask, snow_mask], 'mean')

                if k == 'swe_z':
                    daily_outputs['swe_vol'].loc['total',name] = calculate(o, pixel, mask, 'sum','volume')
                    daily_outputs['swe_avail'].loc['total',name] = calculate(o, pixel, ba, 'sum','volume')
                    daily_outputs['swe_unavail'].loc['total',name] = calculate(o, pixel, bu, 'sum','volume')
                    daily_outputs[k].loc['total',name] = calculate(o, pixel, mask, 'mean','depth')
                    daily_outputs['snow_line'].loc['total',name] = snow_line(o, dem, mask, args['snow_limit'])

                if k == 'depth':
                    daily_outputs[k].loc['total',name] = calculate(o, pixel, mask, 'mean', 'snow_depth')

                if k == 'density':
                    daily_outputs[k].loc['total',name] = calculate(o, pixel, [mask, snow_mask], 'mean')

                if k == 'swi_z':
                    daily_outputs[k].loc['total',name] = calculate(o,pixel,mask,'mean','depth')
                    daily_outputs['swi_vol'].loc['total',name] = calculate(o,pixel,mask,'sum','volume')

                if k == 'precip_z' and flag:
                    daily_outputs[k].loc['total',name] = calculate(pre, pixel, mask, 'mean', 'depth')
                    daily_outputs['precip_vol'].loc['total',name] = calculate(pre, pixel, mask, 'sum', 'volume')

                if k == 'rain_z' and flag:
                    daily_outputs[k].loc['total',name] = calculate(rain, pixel, mask, 'mean', 'depth')

            df = daily_outputs[k].copy()
            df = df.round(decimals = 3)

            if not pass_flag:
                package(args['connector'], lbls, args['basins'], df, args['run_id'],
                        args['vid'], k, out_date, args['run_name'])

                # snow line
                if k == 'swe_z':
                    package(args['connector'], lbls, args['basins'], daily_outputs['snow_line'],
                            args['run_id'], args['vid'], 'snow_line', out_date, args['run_name'])

        hr = int(outputs['time'][iters])
        stamp = datetime.now().strftime("%Y-%-m-%-d %H:%M:%S")
        if not pass_flag:
            logging.info(' Completed {}, hours: {}, date: {}, at: {} UTC'.format(
                         rundirs_dict[outputs['time'][iters]].split('/')[-1],
                         str(hr - t), out_date.date().strftime("%Y-%-m-%-d"),
                         stamp))

        t = int(hr)

    return flag, log, precip_total, rain_total, density
