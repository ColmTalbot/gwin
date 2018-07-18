import numpy as np
from scipy.interpolate import UnivariateSpline
from pycbc.types import FrequencySeries


class Recalibrate(object):

    def __init__(self):
        self.params = dict()
        pass

    def apply_calibration(self, strain):
        """Apply calibration model

        This method should be overwritten by subclasses

        Parameters
        ----------
        strain: FrequencySeries
            The strain to be recalibrated.

        Returns
        -------
        strain_adjusted : FrequencySeries
            The recalibrated strain.
        """
        return strain

    def map_to_adjust(self, strain, **params):
        """Map an input dictionary of sampling parameters to the
        adjust_strain function by filtering the dictionary for the
        calibration parameters, then calling adjust_strain.

        Parameters
        ----------
        strain : FrequencySeries
                The strain to be recalibrated.
        params : dict
            Dictionary of sampling parameters which includes
            calibration parameters.
        Return
        ------
        strain_adjusted : FrequencySeries
            The recalibrated strain.
        """

        self.params.update({key[8:]: params[key] for key in params if key[:8] == 'recalib_'})

        strain_adjusted = self.apply_calibration(strain)

        return strain_adjusted


class CubicSpline(Recalibrate):

    name = 'cubic_spline'

    def __init__(self, minimum_frequency, maximum_frequency, n_points):
        self.params = dict()
        self.n_points = n_points
        self.spline_points = np.logspace(minimum_frequency, maximum_frequency, n_points)

    def apply_calibration(self, strain):
        amplitude_parameters = [self.params['amplitude_{}'.format(ii)] for ii in range(self.n_points)]
        amplitude_spline = UnivariateSpline(self.spline_points, amplitude_parameters)
        delta_amplitude = amplitude_spline(strain.get_sample_frequencies)

        phase_parameters = [self.params['phase_{}'.format(ii)] for ii in range(self.n_points)]
        phase_spline = UnivariateSpline(self.spline_points, phase_parameters)
        delta_phase = phase_spline(strain.get_sample_frequencies)

        strain_adjusted = strain * (1 + delta_amplitude) * (2 + 1j * delta_phase) / (2 - 1j * delta_phase)

        return strain_adjusted

