from ConfigParser import ConfigParser
from pycbc.strain import models


def calibration_config_expander(input_file, output_file=None):
    """
    Take human readable calibration configuration options and produce gwin
    friendly version.

    Parameters
    ----------
    input_file: str
        Human friendly configuration file.
    output_file: str, optional
        GWIn friendly configuration file to save.

    Returns
    -------
    config: WorkflowConfigParser
        Expanded config parser.
    """
    config = ConfigParser()
    config.read(input_file)

    if not config.has_section('variable_params'):
        config.add_section('variable_params')

    calib_items = {key: value for key, value in config.items('calibration')}

    interferometer_names = list(set([key.split('_')[0]for key in calib_items]))

    for ifo in interferometer_names:
        calib_model = calib_items['{}_model'.format(ifo)]
        if calib_model not in models:
            raise(ValueError,
                  'Calibration model "{}" not implemented.'.format(calib_model))

        if calib_model == 'cubic_spline':
            n_points = int(calib_items['{}_n_points'.format(ifo)])
            sigmas = dict()
            means = dict()
            if '{}_calibration_envelope'.format(ifo) in calib_items:
                # FIXME: Allow reading of calibration envelope.
                # this needs a function that knows about the format of the file
                raise(RuntimeError,
                      'Reading calibration envelope not yet implemented.')

            else:
                if '{}_amplitude_sigma'.format(ifo) in calib_items:
                    sigmas['amplitude'] =\
                        [float(calib_items['{}_amplitude_sigma'.format(ifo)])]\
                        * n_points
                    means['amplitude'] = [0] * n_points
                if '{}_phase_sigma'.format(ifo) in calib_items:
                    sigmas['phase'] = \
                        [float(calib_items['{}_phase_sigma'.format(ifo)])] \
                        * n_points
                    means['phase'] = [0] * n_points

            for ii in range(n_points):
                for param in ['amplitude', 'phase']:
                    section = 'prior-recalib_{}_{}_{}'.format(param, ifo, ii)
                    config.set('variable_params', section, '')
                    if not config.has_section(section):
                        config.add_section(section)
                        config.set(section, 'name', 'gaussian')
                        config.set(section, section + '_mean', means[param][ii])
                        config.set(section, section + '_var',
                                   sigmas[param][ii]**2)

    if output_file is not None:
        with open(output_file, 'w') as ff:
            config.write(ff)

    return config
