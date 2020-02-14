import emg3d
import empymod
import numpy as np
import ipywidgets as widgets
import scipy.interpolate as si
import matplotlib.pyplot as plt
from IPython.display import display
from scipy.signal import find_peaks

# Define all errors we want to catch with the variable-checks and setting of
# default values. This is not perfect, but better than 'except Exception'.
VariableCatch = (LookupError, AttributeError, ValueError, TypeError, NameError)


# Interactive Frequency Selection

class InteractiveFrequency(emg3d.utils.Fourier):
    """App to create required frequencies for Fourier Transform."""

    def __init__(self, src_z, rec_z, depth, res, time, signal=0, ab=11,
                 aniso=None, **kwargs):
        """App to create required frequencies for Fourier Transform.

        No thorough input checks are carried out. Rubbish in, rubbish out.

        See empymod.model.dipole for details regarding the modelling.


        Parameters
        ----------
        src_z, rec_z : floats
            Source and receiver depths and offset. The source is located at
            src=(0, 0, src_z), the receiver at rec=(off, 0, rec_z).

        depth : list
            Absolute layer interfaces z (m); #depth = #res - 1
            (excluding +/- infinity).

        res : array_like
            Horizontal resistivities rho_h (Ohm.m); #res = #depth + 1.

        time : array_like
            Times t (s).

        signal : {0, 1, -1}, optional
            Source signal, default is 0:
                - -1 : Switch-off time-domain response
                - 0 : Impulse time-domain response
                - +1 : Switch-on time-domain response

        ab : int, optional
            Source-receiver configuration, defaults to 11. (See
            empymod.model.dipole for all possibilities.)

        aniso : array_like, optional
            Anisotropies lambda = sqrt(rho_v/rho_h) (-); #aniso = #res.
            Defaults to ones.

        ft : {'sin', 'cos'}, optional
            Flag to choose either the Sine or Cosine Digital Linear Filter
            method.  Defaults to 'sin'.
            If signal is < 0, it is set to cosine. If signal > 0, it is set to
            sine. Both can be used for signal = 0.

        ftarg : dict or list, optional
            [fftfilt, pts_per_dec]:

            - fftfilt: string of filter name in ``empymod.filters`` or the
                       filter method itself. (Default:
                       ``empymod.filters.key_201_CosSin_2012()``)
            - pts_per_dec: points per decade; (default: 4)
                - If 0: Standard DLF.
                - If < 0: Lagged Convolution DLF.
                - If > 0: Splined DLF

            The values can be provided as dict with the keywords, or as list.
            However, if provided as list, you have to follow the order given
            above.

        **kwargs : Optional parameters:

            - ``fmin`` : float
              Initial minimum frequency. Default is 1e-3.

            - ``fmax`` : float
              Initial maximum frequency. Default is 1e1.

            - ``off`` : float
              Initial offset. Default is 500.

            - ``ft`` : str {'sin', 'cos', 'fftlog'}
              Initial Fourier transform method. Default is 'sin'.

            - ``ftarg`` : dict
              Initial Fourier transform arguments corresponding to ``ft``.
              Default is None.

            - ``pts_per_dec`` : int
              Initial points per decade. Default is 5.

            - ``linlog`` : str {'linear', 'log'}
              Initial display scaling. Default is 'linear'.

            - ``xtfact`` : float
              Factor for linear x-dimension: t_max = xtfact*offset/1000.

            - ``verb`` : int
              Verbosity. Only for debugging purposes.

        """
        # Get initial values or set to default.
        fmin = kwargs.pop('fmin', 1e-3)
        fmax = kwargs.pop('fmax', 1e1)
        off = kwargs.pop('off', 5000)
        ft = kwargs.pop('ft', 'sin')
        ftarg = kwargs.pop('ftarg', None)
        self.pts_per_dec = kwargs.pop('pts_per_dec', 5)
        self.linlog = kwargs.pop('linlog', 'linear')
        self.xtfact = kwargs.pop('xtfact', 1)
        self.verb = kwargs.pop('verb', 1)

        # Ensure no kwargs left.
        if kwargs:
            raise TypeError('Unexpected **kwargs: %r' % kwargs)

        # Collect model from input.
        self.model = {
            'src': [0, 0, src_z],
            'rec': [off, 0, rec_z],
            'depth': depth,
            'res': res,
            'aniso': aniso,
            'ab': ab,
            'verb': self.verb,
        }

        # Initiate a Fourier instance.
        super().__init__(time, fmin, fmax, signal, ft, ftarg, verb=self.verb)

        # Create the figure.
        self.initiate_figure()

    def initiate_figure(self):
        """Create the figure."""

        # Create figure and all axes
        fig = plt.figure(f"Interactive frequency selection for the Fourier "
                         f"Transform.", figsize=(9, 4))
        plt.subplots_adjust(hspace=0.03, wspace=0.04, bottom=0.15, top=0.9)
        # plt.tight_layout(rect=[0, 0, 1, 0.95])  # Leave space for suptitle.
        ax1 = plt.subplot2grid((3, 2), (0, 0), rowspan=2)
        plt.grid('on', alpha=0.4)
        ax2 = plt.subplot2grid((3, 2), (0, 1), rowspan=2)
        plt.grid('on', alpha=0.4)
        ax3 = plt.subplot2grid((3, 2), (2, 0))
        plt.grid('on', alpha=0.4)
        ax4 = plt.subplot2grid((3, 2), (2, 1))
        plt.grid('on', alpha=0.4)

        # Synchronize x-axis, switch upper labels off
        ax1.get_shared_x_axes().join(ax1, ax3)
        ax2.get_shared_x_axes().join(ax2, ax4)
        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.setp(ax2.get_xticklabels(), visible=False)

        # Move labels of t-domain to the right
        ax2.yaxis.set_ticks_position('right')
        ax4.yaxis.set_ticks_position('right')

        # Set fixed limits
        ax1.set_xscale('log')
        ax3.set_yscale('log')
        ax3.set_yscale('log')
        ax3.set_ylim([0.007, 141])
        ax3.set_yticks([0.01, 0.1, 1, 10, 100])
        ax3.set_yticklabels(('0.01', '0.1', '1', '10', '100'))
        ax4.set_yscale('log')
        ax4.set_yscale('log')
        ax4.set_ylim([0.007, 141])
        ax4.set_yticks([0.01, 0.1, 1, 10, 100])
        ax4.set_yticklabels(('0.01', '0.1', '1', '10', '100'))

        # Labels etc
        ax1.set_ylabel('Amplitude (V/m)')
        ax3.set_ylabel('Rel. Error (%)')
        ax3.set_xlabel('Frequency (Hz)')
        ax4.set_xlabel('Time (s)')
        ax3.axhline(1, c='k')
        ax4.axhline(1, c='k')

        # Add instances
        self.fig = fig
        self.axs = [ax1, ax2, ax3, ax4]

        # Plot initial base model
        self.update_ftfilt(self.ftarg)
        self.plot_base_model()

        # Initiate the widgets
        self.create_widget()

    def reim(self, inp):
        """Return real or imaginary part as a function of signal."""
        if self.signal < 0:
            return inp.real
        else:
            return inp.imag

    def create_widget(self):
        """Create widgets and their layout."""

        # Offset slider.
        off = widgets.interactive(
            self.update_off,
            off=widgets.IntSlider(
                min=500,
                max=10000,
                description='Offset (m)',
                value=self.model['rec'][0],
                step=250,
                continuous_update=False,
                style={'description_width': '60px'},
                layout={'width': '260px'},
            ),
        )

        # Pts/dec slider.
        pts_per_dec = widgets.interactive(
            self.update_pts_per_dec,
            pts_per_dec=widgets.IntSlider(
                min=1,
                max=10,
                description='pts/dec',
                value=self.pts_per_dec,
                step=1,
                continuous_update=False,
                style={'description_width': '60px'},
                layout={'width': '260px'},
            ),
        )

        # Linear/logarithmic selection.
        linlog = widgets.interactive(
            self.update_linlog,
            linlog=widgets.ToggleButtons(
                value=self.linlog,
                options=['linear', 'log'],
                description='Display',
                style={'description_width': '60px', 'button_width': '100px'},
            ),
        )

        # Frequency-range slider.
        freq_range = widgets.interactive(
            self.update_freq_range,
            freq_range=widgets.FloatRangeSlider(
                value=[np.log10(self.fmin), np.log10(self.fmax)],
                description='f-range',
                min=-4,
                max=3,
                step=0.1,
                continuous_update=False,
                style={'description_width': '60px'},
                layout={'width': '260px'},
            ),
        )

        # Signal selection (-1, 0, 1).
        signal = widgets.interactive(
            self.update_signal,
            signal=widgets.ToggleButtons(
                value=self.signal,
                options=[-1, 0, 1],
                description='Signal',
                style={'description_width': '60px', 'button_width': '65px'},
            ),
        )

        # Fourier transform method selection.
        def _get_init():
            """Return initial choice of Fourier Transform."""
            if self.ft == 'fftlog':
                return self.ft
            else:
                return self.ftarg[0].savename

        ftfilt = widgets.interactive(
            self.update_ftfilt,
            ftfilt=widgets.Dropdown(
                options=['fftlog', 'key_81_CosSin_2009',
                         'key_241_CosSin_2009', 'key_601_CosSin_2009',
                         'key_101_CosSin_2012', 'key_201_CosSin_2012'],
                description='Fourier',
                value=_get_init(),  # Initial value
                style={'description_width': '60px'},
                layout={'width': 'max-content'},
            ),
        )

        # Group them together.
        t1col1 = widgets.VBox(children=[pts_per_dec, freq_range],
                              layout={'width': '310px'})
        t1col2 = widgets.VBox(children=[off, ftfilt],
                              layout={'width': '310px'})
        t1col3 = widgets.VBox(children=[signal, linlog],
                              layout={'width': '310px'})

        # Group them together.
        display(widgets.HBox(children=[t1col1, t1col2, t1col3]))

    # Plotting and calculation routines.
    def clear_handle(self, handles):
        """Clear `handles` from figure."""
        for hndl in handles:
            if hasattr(self, 'h_'+hndl):
                getattr(self, 'h_'+hndl).remove()

    def adjust_lim(self):
        """Adjust axes limits."""

        # Adjust y-limits f-domain
        if self.linlog == 'linear':
            self.axs[0].set_ylim([1.1*min(self.reim(self.f_dense)),
                                  1.5*max(self.reim(self.f_dense))])
        else:
            self.axs[0].set_ylim([5*min(self.reim(self.f_dense)),
                                  5*max(self.reim(self.f_dense))])

        # Adjust x-limits f-domain
        self.axs[0].set_xlim([min(self.freq_req), max(self.freq_req)])

        # Adjust y-limits t-domain
        if self.linlog == 'linear':
            self.axs[1].set_ylim(
                    [min(-max(self.t_base)/20, 0.9*min(self.t_base)),
                     max(-min(self.t_base)/20, 1.1*max(self.t_base))])
        else:
            self.axs[1].set_ylim([10**(np.log10(max(self.t_base))-5),
                                  1.5*max(self.t_base)])

        # Adjust x-limits t-domain
        if self.linlog == 'linear':
            if self.signal == 0:
                self.axs[1].set_xlim(
                        [0, self.xtfact*self.model['rec'][0]/1000])
            else:
                self.axs[1].set_xlim([0, max(self.time)])
        else:
            self.axs[1].set_xlim([min(self.time), max(self.time)])

    def print_suptitle(self):
        """Update suptitle."""
        plt.suptitle(
            f"Offset = {np.squeeze(self.model['rec'][0])/1000} km;    "
            f"No. freq. coarse: {self.freq_calc.size};    No. freq. full: "
            f"{self.freq_req.size}  ({self.freq_req.min():.1e} $-$ "
            f"{self.freq_req.max():.1e} Hz)")

    def plot_base_model(self):
        """Update smooth, 'correct' model."""

        # Calculate responses
        self.f_dense = empymod.dipole(freqtime=self.freq_dense, **self.model)
        self.t_base = empymod.dipole(
            freqtime=self.time, signal=self.signal, **self.model)

        # Clear existing handles
        self.clear_handle(['f_base', 't_base'])

        # Plot new result
        self.h_f_base, = self.axs[0].plot(
                self.freq_dense, self.reim(self.f_dense), 'C3')
        self.h_t_base, = self.axs[1].plot(self.time, self.t_base, 'C3')

        self.adjust_lim()

    def plot_coarse_model(self):
        """Update coarse model."""

        # Calculate the f-responses for required and the calculation range.
        f_req = empymod.dipole(freqtime=self.freq_req, **self.model)
        f_calc = empymod.dipole(freqtime=self.freq_calc, **self.model)

        # Interpolate from calculated to required frequencies and transform.
        f_int = self.interpolate(f_calc)
        t_int = self.freq2time(f_calc, self.model['rec'][0])

        # Calculate the errors.
        f_error = np.clip(100*abs((self.reim(f_int)-self.reim(f_req)) /
                                  self.reim(f_req)), 0.01, 100)
        t_error = np.clip(100*abs((t_int-self.t_base)/self.t_base), 0.01, 100)

        # Clear existing handles
        self.clear_handle(['f_int', 't_int', 'f_inti', 'f_inte', 't_inte'])

        # Plot frequency-domain result
        self.h_f_inti, = self.axs[0].plot(
                self.freq_req, self.reim(f_int), 'k.', ms=4)
        self.h_f_int, = self.axs[0].plot(
                self.freq_calc, self.reim(f_calc), 'C0.', ms=8)
        self.h_f_inte, = self.axs[2].plot(self.freq_req, f_error, 'k.')

        # Plot time-domain result
        self.h_t_int, = self.axs[1].plot(self.time, t_int, 'k--')
        self.h_t_inte, = self.axs[3].plot(self.time, t_error, 'k.')

        # Update suptitle
        self.print_suptitle()

    # Interactive routines
    def update_off(self, off):
        """Offset-slider"""

        # Update model
        self.model['rec'] = [off, self.model['rec'][1], self.model['rec'][2]]

        # Redraw models
        self.plot_base_model()
        self.plot_coarse_model()

    def update_pts_per_dec(self, pts_per_dec):
        """pts_per_dec-slider."""

        # Store pts_per_dec.
        self.pts_per_dec = pts_per_dec

        # Redraw through update_ftfilt.
        self.update_ftfilt(self.ftarg)

    def update_freq_range(self, freq_range):
        """Freq-range slider."""

        # Update values
        self.fmin = 10**freq_range[0]
        self.fmax = 10**freq_range[1]

        # Redraw models
        self.plot_coarse_model()

    def update_ftfilt(self, ftfilt):
        """Ftfilt dropdown."""

        # Check if FFTLog or DLF; git DLF filter.
        if isinstance(ftfilt, str):
            fftlog = ftfilt == 'fftlog'
        else:
            if hasattr(ftfilt[0], 'savename'):
                fftlog = False
                ftfilt = ftfilt[0].savename
            else:
                fftlog = True

        # Update Fourier arguments.
        if fftlog:
            self.fourier_arguments('fftlog', {'pts_per_dec': self.pts_per_dec})
            self.freq_inp = None

        else:
            # Calculate input frequency from min to max with pts_per_dec.
            lmin = np.log10(self.freq_req.min())
            lmax = np.log10(self.freq_req.max())
            self.freq_inp = np.logspace(
                    lmin, lmax, int(self.pts_per_dec*np.ceil(lmax-lmin)))

            self.fourier_arguments(
                    'sin', {'fftfilt': ftfilt, 'pts_per_dec': -1})

        # Dense frequencies for comparison reasons
        self.freq_dense = np.logspace(np.log10(self.freq_req.min()),
                                      np.log10(self.freq_req.max()), 301)

        # Redraw models
        self.plot_base_model()
        self.plot_coarse_model()

    def update_linlog(self, linlog):
        """Adjust x- and y-scaling of both frequency- and time-domain."""

        # Store linlog
        self.linlog = linlog

        # f-domain: x-axis always log; y-axis linear or symlog.
        if linlog == 'log':
            sym_dec = 10  # Number of decades to show on symlog
            lty = int(max(np.log10(abs(self.reim(self.f_dense))))-sym_dec)
            self.axs[0].set_yscale('symlog', linthreshy=10**lty, linscaley=0.7)

            # Remove the zero line becouse of the overlapping ticklabels.
            nticks = len(self.axs[0].get_yticks())//2
            iticks = np.arange(nticks)
            iticks = np.r_[iticks, iticks+nticks+1]
            self.axs[0].set_yticks(self.axs[0].get_yticks()[iticks])

        else:
            self.axs[0].set_yscale(linlog)

        # t-domain: either linear or loglog
        self.axs[1].set_yscale(linlog)
        self.axs[1].set_xscale(linlog)

        # Adjust limits
        self.adjust_lim()

    def update_signal(self, signal):
        """Use signal."""

        # Store signal.
        self.signal = signal

        # Redraw through update_ftfilt.
        self.update_ftfilt(self.ftarg)


# Routines for the Adaptive Frequency Selection

def get_new_freq(freq, field, rtol, req_freq=None, full_output=False):
    r"""Returns next frequency to calculate.

    The field of a frequency is considered stable when it fulfills the
    following requirement:

    .. math::
        \frac{\Im(E_x - E_x^\rm{int})}{\max|E_x|} < rtol .

    The adaptive algorithm has two steps:

    1. As long as the field at the lowest frequency does not fulfill the
       criteria, more frequencies are added at lower frequencies, half a
       log10-decade at a time.
    2. Once the field at the lowest frequency fulfills the criteria, it moves
       towards higher frequencies, adding frequencies if it is not stable (a)
       midway (log10-scale) to the next frequency, or (b) half a log10-decade,
       if the last frequency was reached.

    Only the imaginary field is considered in the interpolation. For the
    interpolation, three frequencies are added, 1e-100, 1e4, and 1e100 Hz, all
    with a field of 0 V/m. The interpolation is carried out with piecewise
    cubic Hermite interpolation (pchip).

    Parameters
    ----------
    freq : ndarray
        Current frequencies. Initially there must be at least two frequencies.

    field : ndarray
        E-field corresponding to current frequencies.

    rtol : float
        Tolerance, to decide if the field is stable around a given frequency.

    req_freq : ndarray
        Frequencies of a pre-calculated model for comparison in the plots. If
        provided, a dashed line with the extent of req_freq and the current
        interpolation is shown.

    full_output : bool
        If True, returns the data from the evaluation.


    Returns
    -------
    new_freq : float
        New frequency to be calculated. If ``full_output=True``, it is a
        tuple, where the first entry is new_freq.

    """

    # Pre-allocate array for interpolated field.
    i_field = np.zeros_like(field)

    # Loop over frequencies.
    for i in range(freq.size):

        # Create temporary arrays without this frequency/field.
        # (Adding 0-fields at 1e-100, 1e4, and 1e100 Hz.)
        if max(freq) < 1e4:
            tmp_f = np.r_[1e-100, freq[np.arange(freq.size) != i], 1e4, 1e100]
            tmp_s = np.r_[0, field[np.arange(field.size) != i], 0, 0]
        else:
            tmp_f = np.r_[1e-100, freq[np.arange(freq.size) != i], 1e100]
            tmp_s = np.r_[0, field[np.arange(field.size) != i], 0]

        # Now interpolate at left-out frequency.
        i_field[i] = 1j*si.pchip_interpolate(tmp_f, tmp_s.imag, freq[i])

        # Calculate complete interpol. if required frequency-range is provided.
        if req_freq is not None:
            if max(freq) < 1e4:
                tmp_f2 = np.r_[1e-100, freq, 1e4, 1e100]
                tmp_s2 = np.r_[0, field, 0, 0]
            else:
                tmp_f2 = np.r_[1e-100, freq, 1e100]
                tmp_s2 = np.r_[0, field, 0]
            i_field2 = 1j*si.pchip_interpolate(tmp_f2, tmp_s2.imag, req_freq)

    # Calculate the error as a fct of max(|E_x|).
    error = np.abs((i_field.imag-field.imag)/max(np.abs(field)))

    # Check error; if any bigger than rtol, get a new frequency.
    ierr = np.arange(freq.size)[error > rtol]
    new_freq = np.array([])
    if len(ierr) > 0:

        # Calculate log10-freqs and differences between freqs.
        lfreq = np.log10(freq)
        diff = np.diff(lfreq)

        # Add new frequency depending on location in array.
        if error[0] > rtol:
            # If first frequency is not stable, subtract 1/2 decade.
            new_lfreq = lfreq[ierr[0]] - 0.5
        elif error[-1] > rtol and len(ierr) == 1:
            # If last frequency is not stable, add 1/2 decade.
            new_lfreq = lfreq[ierr[0]] + 0.5
        else:
            # If not first and not last, create new halfway to next frequency.
            new_lfreq = lfreq[ierr[0]] + diff[ierr[0]]/2

        # Back from log10.
        new_freq = 10**np.array([new_lfreq])

    # Return new frequencies
    if full_output:
        if req_freq is not None:
            return (new_freq, i_field, error, ierr, i_field2)
        else:
            return (new_freq, i_field, error, ierr)
    else:
        return new_freq


def design_freq_range(time, model, rtol, signal, freq_range, xlim_freq=None,
                      ylim_freq=None, xlim_lin=None, ylim_lin=None,
                      xlim_log=None, ylim_log=None, pause=0.1):
    """GUI to design required frequencies for Fourier transform."""

    # Get required frequencies for provided time and ft, verbose.
    time, req_freq, ft, ftarg = empymod.utils.check_time(
        time=time, signal=signal, ft=model.get('ft', 'sin'),
        ftarg=model.get('ftarg', 0), verb=3
    )
    req_freq, ri = np.unique(req_freq, return_inverse=True)

    # Use empymod-utilities to print frequency range.
    mod = empymod.utils.check_model(
            [], 1, None, None, None, None, None, False, 0)
    _ = empymod.utils.check_frequency(req_freq, *mod[1:-1], 3)

    # Calculate "good" f- and t-domain field.
    fine_model = model.copy()
    for key in ['ht', 'htarg', 'ft', 'ftarg']:
        if key in fine_model:
            del fine_model[key]
    fine_model['ht'] = 'fht'
    fine_model['htarg'] = {'pts_per_dec': -1}
    fine_model['ft'] = 'sin'
    fine_model['ftarg'] = {'pts_per_dec': -1}
    sfEM = empymod.dipole(freqtime=req_freq, **fine_model)
    stEM = empymod.dipole(freqtime=time, signal=signal, **fine_model)

    # Define initial frequencies.
    if isinstance(freq_range, tuple):
        new_freq = np.logspace(*freq_range)
    elif isinstance(freq_range, np.ndarray):
        new_freq = freq_range
    else:
        p, _ = find_peaks(np.abs(sfEM.imag))
        # Get first n peaks.
        new_freq = req_freq[p[:freq_range]]
        # Add midpoints, plus one before.
        lfreq = np.log10(new_freq)
        new_freq = 10**np.unique(np.r_[lfreq, lfreq[:-1]+np.diff(lfreq),
                                       lfreq[0]-np.diff(lfreq[:2])])

    # Start figure and print current number of frequencies.
    fig, axs = plt.subplots(2, 3, figsize=(9, 8))
    fig.h_sup = plt.suptitle(f"Number of frequencies: --.", y=1, fontsize=14)

    # Subplot 1: Actual signals.
    axs[0, 0].set_title(r'Im($E_x$)')
    axs[0, 0].set_xlabel('Frequency (Hz)')
    axs[0, 0].set_ylabel(r'$E_x$ (V/m)')
    axs[0, 0].set_xscale('log')
    axs[0, 0].get_shared_x_axes().join(axs[0, 0], axs[1, 0])
    if xlim_freq is not None:
        axs[0, 0].set_xlim(xlim_freq)
    else:
        axs[0, 0].set_xlim([min(req_freq), max(req_freq)])
    if ylim_freq is not None:
        axs[0, 0].set_ylim(ylim_freq)
    axs[0, 0].plot(req_freq, sfEM.imag, 'k')

    # Subplot 2: Error.
    axs[1, 0].set_title(r'$|\Im(E_x-E^{\rm{int}}_x)/\max|E_x||$')
    axs[1, 0].set_xlabel('Frequency (Hz)')
    axs[1, 0].set_ylabel('Relative error (%)')
    axs[1, 0].axhline(100*rtol, c='k')  # Tolerance of error-level.
    axs[1, 0].set_yscale('log')
    axs[1, 0].set_xscale('log')
    axs[1, 0].set_ylim([1e-2, 1e2])

    # Subplot 3: Linear t-domain model.
    axs[0, 1].set_xlabel('Time (s)')
    axs[0, 1].get_shared_x_axes().join(axs[0, 1], axs[1, 1])
    if xlim_lin is not None:
        axs[0, 1].set_xlim(xlim_lin)
    else:
        axs[0, 1].set_xlim([min(time), max(time)])
    if ylim_lin is not None:
        axs[0, 1].set_ylim(ylim_lin)
    else:
        axs[0, 1].set_ylim(
                [min(-max(stEM)/20, 0.9*min(stEM)),
                 max(-min(stEM)/20, 1.1*max(stEM))])
    axs[0, 1].plot(time, stEM, 'k-', lw=1)

    # Subplot 4: Error linear t-domain model.
    axs[1, 1].set_title('Error')
    axs[1, 1].set_xlabel('Time (s)')
    axs[1, 1].axhline(100*rtol, c='k')
    axs[1, 1].set_yscale('log')
    axs[1, 1].set_ylim([1e-2, 1e2])

    # Subplot 5: Logarithmic t-domain model.
    axs[0, 2].set_xlabel('Time (s)')
    axs[0, 2].set_xscale('log')
    axs[0, 2].set_yscale('log')
    axs[0, 2].get_shared_x_axes().join(axs[0, 2], axs[1, 2])
    if xlim_log is not None:
        axs[0, 2].set_xlim(xlim_log)
    else:
        axs[0, 2].set_xlim([min(time), max(time)])
    if ylim_log is not None:
        axs[0, 2].set_ylim(ylim_log)
    axs[0, 2].plot(time, stEM, 'k-', lw=1)

    # Subplot 6: Error logarithmic t-domain model.
    axs[1, 2].set_title('Error')
    axs[1, 2].set_xlabel('Time (s)')
    axs[1, 2].axhline(100*rtol, c='k')
    axs[1, 2].set_yscale('log')
    axs[1, 2].set_xscale('log')
    axs[1, 2].set_ylim([1e-2, 1e2])

    plt.tight_layout()
    fig.canvas.draw()
    plt.pause(pause)

    # Pre-allocate arrays.
    freq = np.array([], dtype=float)
    fEM = np.array([], dtype=complex)

    # Loop until satisfied.
    while len(new_freq) > 0:

        # Calculate fEM for new frequencies.
        new_fEM = empymod.dipole(freqtime=new_freq, **model)

        # Combine existing and new frequencies and fEM.
        freq, ai = np.unique(np.r_[freq, new_freq], return_index=True)
        fEM = np.r_[fEM, new_fEM][ai]

        # Check if more frequencies are required.
        out = get_new_freq(freq, fEM, rtol, req_freq, True)
        new_freq = out[0]

        # Calculate corresponding time-domain signal.

        # 1. Interpolation to required frequencies
        #    Slightly different for real and imaginary parts.

        # 3-point ramp from last frequency, step-size is diff. btw last two
        # freqs.
        lfreq = np.log10(freq)
        freq_ramp = 10**(np.ones(3)*lfreq[-1] +
                         np.arange(1, 4)*np.diff(lfreq[-2:]))
        fEM_ramp = np.array([0.75, 0.5, 0.25])*fEM[-1]

        # Imag: Add ramp and also 0-fields at +/-1e-100.
        itmp_f = np.r_[1e-100, freq, freq_ramp, 1e100]
        itmp_s = np.r_[0, fEM.imag, fEM_ramp.imag, 0]
        isfEM = si.pchip_interpolate(itmp_f, itmp_s, req_freq)

        # Real: Add ramp and also 0-fields at +1e-100 (not at -1e-100).
        rtmp_f = np.r_[freq, freq_ramp, 1e100]
        rtmp_s = np.r_[fEM.real, fEM_ramp.real, 0]
        rsfEM = si.pchip_interpolate(rtmp_f, rtmp_s, req_freq)

        # Combine
        sfEM = rsfEM + 1j*isfEM

        # Re-arrange req_freq and sfEM if ri is provided.
        if ri is not None:
            req_freq = req_freq[ri]
            sfEM = sfEM[ri]

        # 2. Carry out the actual Fourier transform.
        #    (without checking for QWE convergence.)
        tEM, _ = empymod.model.tem(
                sfEM[:, None], model['rec'][0], freq=req_freq, time=time,
                signal=signal, ft=ft, ftarg=ftarg)

        # Reshape and return
        nrec, nsrc = 1, 1
        tEM = np.squeeze(tEM.reshape((-1, nrec, nsrc), order='F'))

        # Clean up old lines before updating plots.
        names = ['tlin', 'tlog', 'elin', 'elog', 'if2', 'err', 'erd', 'err1',
                 'erd1']
        for name in names:
            if hasattr(fig, 'h_'+name):
                getattr(fig, 'h_'+name).remove()

        # Adjust number of frequencies.
        fig.h_sup = plt.suptitle(f"Number of frequencies: {freq.size}.",
                                 y=1, fontsize=14)

        # Plot the interpolated points.
        error_bars = [fEM.imag-out[1].imag, fEM.imag*0]
        fig.h_err = axs[0, 0].errorbar(
                freq, fEM.imag, yerr=error_bars, fmt='.', ms=8, color='k',
                ecolor='C0', label='Calc. points')

        # Plot the error.
        fig.h_erd, = axs[1, 0].plot(freq, 100*out[2], 'C0o', ms=6)

        # Make frequency under consideration blue.
        ierr = out[3]
        if len(ierr) > 0:
            iierr = ierr[0]
            fig.h_err1, = axs[0, 0].plot(freq[iierr], out[1][iierr].imag,
                                         'bo', ms=6)
            fig.h_erd1, = axs[1, 0].plot(freq[iierr], 100*out[2][iierr],
                                         'bo', ms=6)

        # Plot complete interpolation.
        fig.h_if2, = axs[0, 0].plot(req_freq, out[4].imag, 'C0--')

        # Plot current time domain result and error.
        fig.h_tlin, = axs[0, 1].plot(time, tEM, 'C0-')
        fig.h_tlog, = axs[0, 2].plot(time, tEM, 'C0-')
        fig.h_elin, = axs[1, 1].plot(time, 100*abs((tEM-stEM)/stEM), 'r--')
        fig.h_elog, = axs[1, 2].plot(time, 100*abs((tEM-stEM)/stEM), 'r--')

        plt.tight_layout()
        fig.canvas.draw()
        plt.pause(pause)

    # Return time-domain signal (correspond to provided times); also
    # return used frequencies and corresponding signal.
    return tEM, freq, fEM
