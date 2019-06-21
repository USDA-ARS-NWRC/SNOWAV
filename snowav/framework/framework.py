
import os
from sys import exit
from snowav.framework.read_config import read_config
from snowav.framework.process import process
from snowav.framework.parse import parse
from snowav.framework.figures import figures
from snowav.report.report import report
from snowav.database.database import check_fields,delete,run_metadata,write_csv

class snowav(object):

    def __init__(self, config_file = None, external_logger = None, awsm = None):
        '''
        Read config file, parse config options, process results, put results
        on database, make figures, and make pdf report.

        Args
        -----
        config_file : str
            snowav config file
        external_logger : object
            awsm logger
        awsm : class
            awsm class if being run in awsm

        '''

        # Get config options
        if awsm is None and os.path.isfile(config_file):
            self.config_file = config_file
            read_config(self)

        elif awsm is not None:
            self.config_file = awsm.filename
            read_config(self, awsm = awsm)

        else:
            raise Exception('No config instance passed, or config file does '
                            'not exist!')

        # parse config options
        parse(self)

        # put run metadata on database
        run_metadata(self, self.run_name)

        # process results
        self.pargs['run_id'] = self.run_id
        self.pargs['vid'] = self.vid
        flags, out, pre, rain, density = process(self.pargs)

        # gather process() outputs
        for log in out:
            self._logger.info(log)

        self.density = density
        self.rain_total = rain
        self.precip_total = pre

        if not flags['precip']:
            self.precip_depth_flag = False
            self.precip_validate_flag = False

        # figures for standard run
        figures(self)

        # Do additional processing and figures if forecast is supplied. Some
        # field will be overwritten during forecast processing
        if self.forecast_flag:
            self._logger.info(' Starting forecast processing...')

            run_metadata(self, self.for_run_name)

            self.pargs['run_id'] = self.run_id
            self.pargs['vid'] = self.vid
            flags, out, pre, rain, density = process(self.pargs)

            for log in out:
                self._logger.info(log)

            self.density = density
            self.rain_total = rain
            self.precip_total = pre

            # figures for forecast run
            figures(self)

        if self.report_flag:
            report(self)
