
import numpy as np
import pandas as pd
import copy
from datetime import datetime
from tablizer.tablizer import get_existing_records
from snowav.plotting.swi import swi
from snowav.plotting.basin_total import basin_total
from snowav.plotting.cold_content import cold_content
from snowav.plotting.compare_runs import compare_runs
from snowav.plotting.density import density
from snowav.plotting.flt_image_change import flt_image_change
from snowav.plotting.image_change import image_change
from snowav.plotting.precip_depth import precip_depth
from snowav.plotting.stn_validate import stn_validate
from snowav.plotting.swe_change import swe_change
from snowav.plotting.write_properties import write_properties
from snowav.plotting.swe_volume import swe_volume
from snowav.plotting.inputs import inputs
from snowav.inflow.inflow import inflow
from snowav.plotting.diagnostics import diagnostics
from snowav.plotting.plotlims import plotlims
from snowav.database.database import collect
from snowav.plotting.plotlims import plotlims as plotlims

def figures(self):
    '''
    Set up and call snowav figures. See CoreConfig.ini and README.md for more on
    config options and use.

    Notes:
    - swe_volume() must be called before cold_content() if you want to use
    the same ylims for each.

    '''

    args = {'report_start':self.report_start.date().strftime("%Y-%-m-%-d"),
            'report_date':self.report_date.date().strftime("%Y-%-m-%-d"),
            'print':self.print_args_dict,
            'run_name':self.run_name,
            'start_date':self.start_date,
            'end_date':self.end_date,
            'directory':self.directory,
            'figs_path':self.figs_path,
            'edges':self.edges,
            'plotorder':self.plotorder,
            'labels':self.labels,
            'lims':plotlims(self.plotorder),
            'masks':self.masks,
            'figsize':self.figsize,
            'dpi':self.dpi,
            'depthlbl':self.depthlbl,
            'vollbl':self.vollbl,
            'elevlbl':self.elevlbl,
            'dplcs':self.dplcs,
            'barcolors':self.barcolors,
            'xlims':self.xlims,
            'depth_clip':self.depth_clip,
            'percent_min':self.percent_min,
            'percent_max':self.percent_max,
            'basins':self.basins,
            'wy':self.wy,
            'flag':False,
            'flt_flag':self.flt_flag}

    if self.flt_flag:
        args['flight_dates'] = self.flight_diff_dates

    fig_names = {}
    connector = self.connector

    ##########################################################################
    #       For each figure, collect 2D array image, by-elevation            #
    #       DataFrame, and set any figure-specific args inputs               #
    ##########################################################################
    if self.flt_flag:
        args['depth_factor'] = self.depth_factor
        args['update_file'] = self.update_file
        args['update_numbers'] = self.update_numbers
        args['flight_outputs'] = self.flight_outputs
        args['pre_flight_outputs'] = self.pre_flight_outputs
        args['connector'] = connector

        self.flight_diff_fig_names, self.flight_delta_vol_df = flt_image_change(args, self._logger)

    if self.swi_flag:
        image = np.zeros_like(self.outputs['swi_z'][0])
        for n in range(self.ixs,self.ixe):
            image = image + self.outputs['swi_z'][n]*self.depth_factor

        df = collect(connector, args['plotorder'], args['basins'],
                     args['start_date'], args['end_date'], 'swi_vol',
                     args['run_name'], args['edges'], 'sum')

        args['df'] = df
        args['image'] = image
        args['title'] = 'Accumulated SWI\n{} to {}'.format(
                        self.start_date.date().strftime("%Y-%-m-%-d"),
                        self.end_date.date().strftime("%Y-%-m-%-d"))

        fig_names['swi'] = swi(args, self._logger)

    if self.image_change_flag:
        image = self.outputs['swe_z'][self.ixe] - self.outputs['swe_z'][self.ixs]

        start = collect(connector, args['plotorder'], args['basins'],
                        args['start_date'], args['start_date'],'swe_vol',
                        args['run_name'], args['edges'],'end')
        end = collect(connector, args['plotorder'], args['basins'],
                      args['start_date'], args['end_date'], 'swe_vol',
                      args['run_name'], args['edges'],'end')

        df = end - start

        args['df'] = df
        args['image'] = image*self.depth_factor
        args['title'] = 'Change in SWE Depth\n{} to {}'.format(
                        args['report_start'], args['report_date'])

        fig_names['image_change'] = image_change(args, self._logger)

    if self.swe_volume_flag:
        df = collect(connector, args['plotorder'], args['basins'],
                     args['start_date'], args['end_date'],'swe_vol',
                     args['run_name'], args['edges'],'end')

        image = self.outputs['swe_z'][self.ixe]*self.depth_factor

        args['df'] = df
        args['image'] = image
        args['title'] = 'SWE {}'.format(args['report_date'])

        fig_names['swe_volume'], args['ylims'] = swe_volume(args, self._logger)

    if self.cold_content_flag:
        df = collect(connector, args['plotorder'], args['basins'],
                     args['start_date'], args['end_date'], 'swe_unavail',
                     args['run_name'], args['edges'],'end')

        swe = self.outputs['swe_z'][self.ixe]
        image = self.outputs['coldcont'][self.ixe]*0.000001

        args['df'] = df
        args['swe'] = swe
        args['image'] = image
        args['title'] = 'Cold Content {}'.format(args['report_date'])

        fig_names['cold_content'] = cold_content(args, self._logger)

    if self.density_flag:
        image = self.outputs['density'][self.ixe]

        # self.density is assigned in process()
        args['density'] = self.density
        args['image'] = image
        args['title'] = 'Density {}'.format(args['report_date'])

        fig_names['density'] = density(args, self._logger)

    if self.basin_total_flag:
        wy_start = datetime(self.wy-1,10,1)
        swi_summary = collect(connector, args['plotorder'], args['basins'],
                              wy_start,args['end_date'],'swi_vol',
                              args['run_name'],'total','daily')
        df_swe = collect(connector, args['plotorder'], args['basins'],
                              wy_start,args['end_date'],'swe_vol',
                              args['run_name'],'total','daily')
        df_swi = swi_summary.cumsum()

        args['swi_summary'] = df_swi
        args['swe_summary'] = df_swe
        args['forecast_flag'] = self.forecast_flag
        args['flt_flag'] = self.flt_flag

        fig_names['basin_total'] = basin_total(args, self._logger)

    if self.precip_depth_flag:
        swi_image = np.zeros_like(self.outputs['swi_z'][0])
        for n in range(self.ixs,self.ixe):
            swi_image = swi_image + self.outputs['swi_z'][n]*self.depth_factor

        swi_df = collect(connector, args['plotorder'], args['basins'],
                         args['start_date'], args['end_date'], 'swi_z',
                         args['run_name'], args['edges'], 'sum')
        precip_df = collect(connector, args['plotorder'], args['basins'],
                            args['start_date'], args['end_date'], 'precip_z',
                            args['run_name'], args['edges'], 'sum')
        rain_df = collect(connector, args['plotorder'], args['basins'],
                          args['start_date'], args['end_date'], 'rain_z',
                          args['run_name'], args['edges'], 'sum')

        args['swi_image'] = swi_image
        args['precip_image'] = self.precip_total*self.depth_factor
        args['rain_image'] = self.rain_total*self.depth_factor
        args['swi_df'] = swi_df
        args['precip_df'] = precip_df
        args['rain_df'] = rain_df
        args['title'] = 'Depth of SWI, Precipitation, and Rain\n{} to {}'.format(
                        args['report_start'],args['report_date'])

        fig_names['precip_depth'] = precip_depth(args, self._logger)

    if self.diagnostics_flag:
        wy_start = datetime(self.wy-1,10,1)
        precip = collect(connector, args['plotorder'], args['basins'],
                         wy_start, args['end_date'], 'precip_z',
                         args['run_name'], args['edges'], 'daily')
        precip_per = collect(connector, args['plotorder'], args['basins'],
                         args['start_date'], args['end_date'], 'precip_z',
                         args['run_name'], args['edges'], 'daily')
        swe = collect(connector, args['plotorder'], args['basins'],
                         wy_start, args['end_date'], 'swe_z',
                         args['run_name'], args['edges'], 'daily')
        swe_per = collect(connector, args['plotorder'], args['basins'],
                         args['start_date'], args['end_date'], 'swe_z',
                         args['run_name'], args['edges'], 'daily')
        density = collect(connector, args['plotorder'], args['basins'],
                         wy_start, args['end_date'], 'density',
                         args['run_name'], args['edges'], 'daily')
        density_per = collect(connector, args['plotorder'], args['basins'],
                         args['start_date'], args['end_date'], 'density',
                         args['run_name'], args['edges'], 'daily')
        snow_line = collect(connector, args['plotorder'], args['basins'],
                         wy_start, args['end_date'], 'snow_line',
                         args['run_name'], args['edges'], 'daily')
        snow_line_per = collect(connector, args['plotorder'], args['basins'],
                         args['start_date'], args['end_date'], 'snow_line',
                         args['run_name'], args['edges'], 'daily')

        snow_line_per = snow_line_per.fillna(0)
        first_row = snow_line_per.iloc[[0]].values[0]
        snow_line_per = snow_line_per.apply(lambda row: row - first_row, axis=1)
        args['snow_line'] = snow_line
        args['snow_line_per'] = snow_line_per

        swe = swe.fillna(0)
        swe_per = swe_per.fillna(0)
        first_row = swe_per.iloc[[0]].values[0]
        swe_per = swe_per.apply(lambda row: row - first_row, axis=1)

        density = density.fillna(0)
        density_per = density_per.fillna(0)
        first_row = density_per.iloc[[0]].values[0]
        density_per = density_per.apply(lambda row: row - first_row, axis=1)

        precip = precip.fillna(0)
        precip_per = precip_per.fillna(0)
        precip = precip.cumsum()
        precip_per = precip_per.cumsum()
        first_row = precip_per.iloc[[0]].values[0]
        precip_per = precip_per.apply(lambda row: row - first_row, axis=1)

        if self.diag_basins is None:
            args['dbasins'] = copy.deepcopy(self.plotorder)
        else:
            args['dbasins'] = self.diag_basins

        args['precip'] = precip
        args['precip_per'] = precip_per
        args['swe'] = swe
        args['swe_per'] = swe_per
        args['density'] = density
        args['density_per'] = density_per
        args['elevlbl'] = self.elevlbl

        diagnostics(args, self._logger)

    if self.stn_validate_flag:
        args['dirs'] = self.all_dirs
        args['stns'] = self.val_stns
        args['lbls'] = self.val_lbls
        args['client'] = self.val_client
        args['factor'] = 25.4
        args['user'] = self.wxdb_user
        args['password'] = self.wxdb_password
        args['host'] = self.wxdb_host
        args['port'] = self.wxdb_port
        args['snow_x'] = self.snow_x
        args['snow_y'] = self.snow_y
        args['stns'] = self.val_stns
        args['nash_sut_flag'] = self.nash_sut_flag

        # could change these for precip, px = 0, 'em.nc'
        args['tbl'] = 'tbl_level1'
        args['var'] = 'snow_water_equiv'
        args['px'] = (1,1,1,0,0,0,-1,-1,-1)
        args['py'] = (1,0,-1,1,0,-1,1,0,-1)
        args['ncfile'] = 'snow.nc'

        fig_names['valid'], flag = stn_validate(args, self._logger)

        if not flag:
            self.stn_validate_flag = False

    if self.compare_runs_flag:
        args['variables'] = ['swe_vol','swi_vol']
        wy_start = datetime(self.wy-1,10,1)

        if self.flt_flag:
            args['flag'] = True
        else:
            args['flag'] = False

        dict = {}
        for var in args['variables']:
            dict[var] = {}
            for run in self.compare_run_names:
                df = collect(connector, args['plotorder'][0], args['basins'],
                             wy_start,args['end_date'],var,run,'total','daily')
                if var == 'swi_vol':
                    df = df.cumsum()

                dict[var][run] = df

        args['dict'] = dict

        compare_runs(args, self._logger)

    if self.inflow_flag:
        wy_start = datetime(self.wy-1,10,1)
        swi_summary = collect(connector, args['plotorder'], args['basins'],
                              wy_start,args['end_date'],'swi_vol',
                              args['run_name'],'total','daily')
        df_swi = swi_summary.cumsum()

        args['swi_summary'] = df_swi

        if self.inflow_data is None:
            raw = pd.read_csv(self.summary_csv, skiprows = 1,
                              parse_dates=[0], index_col = 0)
            args['inflow_summary'] = raw[self.basin_headings]

        else:
            args['inflow_summary'] = pd.read_csv(self.summary_csv,
                                                 parse_dates=[0], index_col = 0)

        args['inflow_headings'] = self.inflow_headings
        args['basin_headings'] = self.basin_headings

        inflow(args, self._logger)

    if self.write_properties is not None:
        args['connector'] = self.connector
        args['wy_start'] = datetime(self.wy-1,10,1)

        write_properties(args, self.write_properties)

    if self.inputs_fig_flag:
        # plots_inputs_variables
        df = get_existing_records(connector, 'sqlite')
        df = df.set_index('date_time')
        ivalue = {}
        y = {}

        for var in self.plots_inputs_variables:
            ivalue[var] = {}

            for basin in args['basins']:
                bid = args['basins'][basin]['basin_id']
                ivalue[var][basin] = {}

                for func in self.inputs_methods:

                    if 'percentile' in func:
                        nfunc = '{}_{}'.format(func,str(self.inputs_percentiles[0]))
                        ivalue[var][basin][nfunc] =  df[(df['function'] == nfunc) &
                                       (df['variable'] == var) &
                                       (df['basin_id'] == int(bid)) &
                                       (df['run_name'] == args['run_name'])]

                        nfunc = '{}_{}'.format(func,str(self.inputs_percentiles[1]))

                        ivalue[var][basin][nfunc] =  df[(df['function'] == nfunc) &
                                       (df['variable'] == var) &
                                       (df['basin_id'] == int(bid)) &
                                       (df['run_name'] == args['run_name'])]
                    else:
                        ivalue[var][basin][func] =  df[(df['function'] == func) &
                                       (df['variable'] == var) &
                                       (df['basin_id'] == int(bid)) &
                                       (df['run_name'] == args['run_name'])]

        # also get date_time
        args['inputs'] = ivalue
        args['inputs_methods'] = self.inputs_methods

        inputs(args, self._logger)

    if self.forecast_flag:
        print('Forecast figures in progress...')
        # if self.image_change_flag:
        #     image_change(self, forecast=self.for_run_name)
        #
        # if self.swi_flag:
        #
        #     if forecast is None:
        #         run_name = snow.run_name
        #         outputs = copy.deepcopy(snow.outputs)
        #         ixs = snow.ixs
        #         ixe = snow.ixe
        #         start_date = snow.start_date
        #         end_date = snow.end_date
        #         directory = snow.directory
        #         title = 'Accumulated SWI\n{} to {}'.format(
        #                                     snow.report_start.date().strftime("%Y-%-m-%-d"),
        #                                     snow.report_date.date().strftime("%Y-%-m-%-d"))
        #     swi(args)
        #
        # if self.swe_volume_flag:
        #     '''
        #         if day is not None:
        #             figs_path = day.figs_path
        #             name_append = 'day'
        #             date_stamp = day.date.strftime("%Y-%-m-%-d %H:%M") + ' (UTC)'
        #
        #     '''
        #
        #     args['directory'] = self.directory + '_forecast'
        #     args['run_name'] = self.for_run_name
        #     args['start_date'] = self.for_start_date
        #     args['end_date'] = self.for_end_date
        #     args['title'] = 'Forecast SWE \n {}'.format(self.for_end_date.date().strftime("%Y-%-m-%-d"))
        #
        #     swe = collect(self,args['plotorder'],args['start_date'],
        #                   args['end_date'],'swe_vol',args['run_name'],
        #                   args['edges'],'end')
        #
        #     image = self.for_outputs['swe_z'][self.for_ixe]*self.depth_factor
        #
        #     args['df'] = swe
        #     args['image'] = image
        #     args['title'] = 'SWE {}'.format(args['report_end'])
        #
        #     name, ylims = swe_volume(args, self._logger)
        #
        #     if self.basin_total_flag:
        #         '''
        #             for iter,d in enumerate(v['date_time'].values):
        #                 swe_summary.loc[d,bid] = v['value'].values[iter]
        #                 swi_summary.loc[d,bid] = v2['value'].values[iter]
        #
        #         swi_summary.sort_index(inplace=True)
        #
        #         # as a starting spot, add actual run
        #         swi_summary.iloc[0,:] = swi_summary.iloc[0,:] + swi_end_val.iloc[-1,:].values
        #         swi_summary = swi_summary.cumsum()
        #         '''
        #         # forecast True
        #         args['flag'] = True
        #
        #         basin_total(self, forecast=self.for_run_name)
        #
        #     if self.precip_depth_flag:
        #         precip_depth(self, forecast=self.for_run_name)

    self.fig_names = fig_names


def save_fig(fig, paths):
    '''
    Args
    ----------
    fig : object
        matplotlib figure object
    paths : list
        list of paths to save figure

    '''

    if type(paths) != list:
        paths = [paths]

    for path in paths:
        fig.savefig(path)
