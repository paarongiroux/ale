from glob import glob
import os

import numpy as np
import pvl
import spiceypy as spice

from ale import config
from ale.base import Driver
from ale.base.data_naif import NaifSpice
from ale.base.data_isis import IsisSpice
from ale.base.label_pds3 import Pds3Label
from ale.base.label_isis import IsisLabel
from ale.base.type_distortion import RadialDistortion
from ale.base.type_sensor import LineScanner


class MroCtxIsisLabelIsisSpiceDriver(Driver, IsisSpice, LineScanner, RadialDistortion):

    @property
    def instrument_id(self):
        """
        Returns an instrument id for uniquely identifying the instrument, but often
        also used to be piped into Spice Kernels to acquire IKIDs. Therefore they
        the same ID the Spice expects in bods2c calls.

        Returns
        -------
        : str
          instrument id
        """
        return "N/A"

    @property
    def spacecraft_id(self):
        """
        Returns
        -------
        : int
          Naif ID code for the spacecraft
        """
        return "N/A"

    @property
    def ikid(self):
        """
        Returns
        -------
        : int
          Naif ID code for the instrument
        """
        return int(self.label["IsisCube"]["Kernels"]["NaifFrameCode"])

    @property
    def line_exposure_duration(self):
        """
        Returns
        -------
        : float
          Line exposure duration in seconds
        """
        return self.label["IsisCube"]["Instrument"]["LineExposureDuration"].value * 0.001 # Scale to seconds


class MroCtxIsisLabelNaifSpiceDriver(IsisLabel, NaifSpice, LineScanner, RadialDistortion, Driver):
    """
    Driver for reading CTX ISIS labels.
    """

    @property
    def metakernel(self):
        """
        Returns latest instrument metakernels

        Returns
        -------
        : string
          Path to latest metakernel file
        """
        metakernel_dir = config.mro
        mks = sorted(glob(os.path.join(metakernel_dir,'*.tm')))
        if not hasattr(self, '_metakernel'):
            self._metakernel = None
            for mk in mks:
                if str(self.utc_start_time.year) in os.path.basename(mk):
                    self._metakernel = mk
        return self._metakernel

    @property
    def instrument_id(self):
        """
        Returns an instrument id for uniquely identifying the instrument, but often
        also used to be piped into Spice Kernels to acquire IKIDs. Therefore they
        the same ID the Spice expects in bods2c calls.
        Expects instrument_id to be defined in the IsisLabel mixin. This should be
        a string of the form 'CTX'

        Returns
        -------
        : str
          instrument id
        """
        id_lookup = {
        "CTX" : "MRO_CTX"
        }
        return id_lookup[super().instrument_id]

    @property
    def sensor_name(self):
        """
        ISIS doesn't propergate this to the ingested cube label, so hard-code it.
        """
        return "CONTEXT CAMERA"

    @property
    def ephemeris_start_time(self):
        """
        Returns the ephemeris start time of the image.
        Expects spacecraft_id to be defined. This should be the integer
        Naif ID code for the spacecraft.

        Returns
        -------
        : float
          ephemeris start time of the image
        """
        if not hasattr(self, '_ephemeris_start_time'):
            sclock = self.label['IsisCube']['Instrument']['SpacecraftClockCount']
            self._ephemeris_start_time = spice.scs2e(self.spacecraft_id, sclock)
        return self._ephemeris_start_time

    @property
    def ephemeris_stop_time(self):
        """
        ISIS doesn't preserve the spacecraft stop count that we can use to get
        the ephemeris stop time of the image, so compute the epehemris stop time
        from the start time and the exposure duration.
        """
        return self.ephemeris_start_time + self.exposure_duration * self.image_lines

    @property
    def spacecraft_name(self):
        """
        Returns the spacecraft name used in various Spice calls to acquire
        ephemeris data.
        Expects the platform_name to be defined. This should be a string of
        the form 'Mars_Reconnaissance_Orbiter'

        Returns
        -------
        : str
          spacecraft name
        """
        name_lookup = {
            'Mars_Reconnaissance_Orbiter': 'MRO'
        }
        return name_lookup[super().platform_name]

    @property
    def detector_start_line(self):
        """
        Returns
        -------
        : int
          The starting detector line of the image
        """
        return 1

    @property
    def detector_start_sample(self):
        """
        Returns
        -------
        : int
          The starting detector sample of the image
        """
        return self.label['IsisCube']['Instrument']['SampleFirstPixel']

    @property
    def sensor_model_version(self):
        """
        Returns
        -------
        : int
          ISIS sensor model version
        """
        return 1

class MroCtxPds3LabelNaifSpiceDriver(Pds3Label, NaifSpice, LineScanner, RadialDistortion, Driver):
    """
    Driver for reading CTX PDS3 labels. Requires a Spice mixin to acquire addtional
    ephemeris and instrument data located exclusively in spice kernels.
    """

    @property
    def metakernel(self):
        """
        Returns latest instrument metakernels

        Returns
        -------
        : string
          Path to latest metakernel file
        """
        metakernel_dir = config.mro
        mks = sorted(glob(os.path.join(metakernel_dir,'*.tm')))
        if not hasattr(self, '_metakernel'):
            self._metakernel = None
            for mk in mks:
                if str(self.utc_start_time.year) in os.path.basename(mk):
                    self._metakernel = mk
        return self._metakernel

    @property
    def instrument_id(self):
        """
        Returns an instrument id for uniquely identifying the instrument, but often
        also used to be piped into Spice Kernels to acquire IKIDs. Therefore they
        the same ID the Spice expects in bods2c calls.
        Expects instrument_id to be defined in the Pds3Label mixin. This should
        be a string of the form 'CONTEXT CAMERA' or 'CTX'

        Returns
        -------
        : str
          instrument id
        """
        id_lookup = {
            'CONTEXT CAMERA':'MRO_CTX',
            'CTX':'MRO_CTX'
        }

        return id_lookup[super().instrument_id]

    @property
    def spacecraft_name(self):
        """
        Returns the spacecraft name used in various Spice calls to acquire
        ephemeris data.
        Expects spacecraft_name to be defined. This should be a string of the form
        'MARS_RECONNAISSANCE_ORBITER'

        Returns
        -------
        : str
          spacecraft name
        """
        name_lookup = {
            'MARS_RECONNAISSANCE_ORBITER': 'MRO'
        }
        return name_lookup[super().spacecraft_name]

    @property
    def detector_start_line(self):
        """
        Returns
        -------
        : int
          Starting detector line for the image
        """
        return 1

    @property
    def detector_start_sample(self):
        """
        Returns
        -------
        : int
          Starting detector sample for the image
        """
        return self.label.get('SAMPLE_FIRST_PIXEL', 0)

    @property
    def sensor_model_version(self):
        """
        Returns
        -------
        : int
          ISIS sensor model version
        """
        return 1
