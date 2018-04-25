

import sys
import snowav

def run(config_file):

    # config_file = '/home/markrobertson/mrworkspace/code/SNOWAV/snowav/config/snowav_brb_wy2018.ini'
    snow = snowav.plotting.framework.SNOWAV(config_file)

    # Make all the calculations
    snow.process()

    # Plots
    snowav.plotting.accumulated.accumulated(snow)
    snowav.plotting.current_image.current_image(snow)
    snowav.plotting.state_by_elev.state_by_elev(snow)
    snowav.plotting.image_change.image_change(snow)
    snowav.plotting.basin_total.basin_total(snow)
    snowav.plotting.pixel_swe.pixel_swe(snow)
    snowav.plotting.density.density(snow)
    snowav.plotting.stn_validate.stn_validate(snow)

    # Generate report if desired
    print(snow.report_flag)
    if snow.report_flag:
        snowav.report.report.report(snow)

if __name__ == '__main__':
    config_file = sys.argv[1]
    run(config_file)