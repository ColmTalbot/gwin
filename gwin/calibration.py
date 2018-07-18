# Copyright (C) 2018 Colm Talbot
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
""" Functions for adding calibration factors to waveform templates.
"""

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

    def map_to_adjust(self, strain, prefix='recalib_', **params):
        """Map an input dictionary of sampling parameters to the
        adjust_strain function by filtering the dictionary for the
        calibration parameters, then calling adjust_strain.

        Parameters
        ----------
        strain : FrequencySeries
            The strain to be recalibrated.
        prefix: str
            Prefix for calibration parameter names
        params : dict
            Dictionary of sampling parameters which includes
            calibration parameters.
        Return
        ------
        strain_adjusted : FrequencySeries
            The recalibrated strain.
        """

        self.params.update({key[len(prefix):]: params[key]
                            for key in params if key[:len(prefix)] == prefix})

        strain_adjusted = self.apply_calibration(strain)

        return strain_adjusted

    @classmethod
    def from_config(cls, cp, ifo, section):
        """Read a config file to get calibration options and transfer
        functions which will be used to intialize the model.

        Parameters
        ----------
        cp : WorkflowConfigParser
            An open config file.
        ifo : string
            The detector (H1, L1) for which the calibration model will
            be loaded.
        section : string
            The section name in the config file from which to retrieve
            the calibration options.
        Return
        ------
        instance
            An instance of the class.
        """
        all_params = dict(cp.items(section))
        params = {key[3:]: all_params[key] for key in all_params if ifo in key}
        params.pop('{}-name'.format(ifo))

        return cls(**params)


class CubicSpline(Recalibrate):

    name = 'cubic_spline'

    def __init__(self, minimum_frequency, maximum_frequency, n_points):
        """
        Cubic spline recalibration

        see https://dcc.ligo.org/DocDB/0116/T1400682/001/calnote.pdf

        This assumes the spline points follow
        np.logspace(np.log(minimum_frequency), np.log(maximum_frequency), n_points)

        Parameters
        ----------
        minimum_frequency: float
            minimum frequency of spline points
        maximum_frequency: float
            maximum frequency of spline points
        n_points: int
            number of spline points
        """
        Recalibrate.__init__(self)
        self.n_points = n_points
        self.spline_points = np.logspace(np.log(minimum_frequency), np.log(maximum_frequency), n_points)

    def apply_calibration(self, strain):
        amplitude_parameters = [self.params['amplitude_{}'.format(ii)] for ii in range(self.n_points)]
        amplitude_spline = UnivariateSpline(self.spline_points, amplitude_parameters)
        delta_amplitude = amplitude_spline(strain.sample_frequencies.numpy())

        phase_parameters = [self.params['phase_{}'.format(ii)] for ii in range(self.n_points)]
        phase_spline = UnivariateSpline(self.spline_points, phase_parameters)
        delta_phase = phase_spline(strain.sample_frequencies.numpy())

        strain_adjusted = strain * (1 + delta_amplitude) * (2 + 1j * delta_phase) / (2 - 1j * delta_phase)

        return strain_adjusted

