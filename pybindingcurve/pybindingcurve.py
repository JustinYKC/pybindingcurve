import numpy as np
import matplotlib.pyplot as plt
from pybindingcurve import *
import lmfit

pbc_plot_style = {
    'axis_label_size': 12,
    'axis_label_font': "DejaVu Sans",
    'title_size': 12,
    'title_font': "DejaVu Sans",
    #'figure_width': 9,
    #'figure_height': 9,
    'x_tick_label_font_size': 10,
    'y_tick_label_font_size': 10,
    'legend_font_size': 9,
    'dpi': 300,
    'x_axis_labelpad': None,
    'y_axis_labelpad': None,
    'title_labelpad': None,
    'fig_size':(5*1.2,4*1.2)
}




class _Curve:
    """Curve class, represents a binding curve

    Consists of X and Y coordinates, along with a name and boolean
    flag denoting that the curve is a traced, real physical solution.
    """

    def __init__(self, xcoords: np.array, ycoords: np.array, series_name: str = ""):
        """Curve constructor

        Called by PyBindingCurve

        """
        self.xcoords = xcoords
        self.ycoords = ycoords
        self.name = series_name


class BindingCurve():
    system=None
    curves = []
    fig = None
    axes = None
    plot_solution_colours = list(
        "krgbycmrgbycmrgby")+list(np.linspace(0.1, 0.9, 0.05))
    _min_x_axis = 0.0
    _max_x_axis = 0.0
    _min_y_axis = 0.0
    _max_y_axis = 0.0
    _num_added_traces = 0
    _last_known_changing_parameter="X"
    _last_known_readout="Y"
    
    def query(self, parameters, readout):
        if not self.system.analytical:
            return self.system.query(parameters, readout)
        else:
            print("Must supply a readout")
            return None

    def query(self, parameters):
        if self.system.analytical:
            return self.system.query(parameters)
        else:
            print("Must supply a readout")


    def _find_changing_parameters(self, params: dict):
        changing_list = []
        for p in params.keys():
            if type(params[p]) == np.ndarray or type(params[p]) == list:
                changing_list.append(p)
        if len(changing_list) == 0:
            return None
        else:
            return changing_list

    def __init__(self, binding_system):
        if type(binding_system) is str:
            binding_system=binding_system.lower()
            # 1:1
            if binding_system=="simple" or binding_system=="1:1":
                self.system=System_one_to_one_analytical_pl()
            # 1:1 kinetic - only used for testing purposes
            if binding_system=="simplekinetic" or binding_system=="simple kinetic" or binding_system=="1:1 kinetic" or binding_system=="1:1kinetic":
                self.system=System_one_to_one()
            # Homodimer formation
            if binding_system=="homodimer" or binding_system=="homodimer formation":
                self.system=System_homodimer_formation_analytical_pp()
            # Homodimer formation kinetic - only used for testing purposes
            if binding_system=="homodimerkinetic" or binding_system=="homodimer kinetic" or binding_system=="homodimerformationkinetic" or binding_system=="homodimer formation kinetic":
                self.system=System_homodimer_formation()

            # Competition
            if binding_system=="competition" or binding_system=="1:1:1":
                self.system=System_competition()
            # Competition
            if binding_system=="homodimerbreaking" or binding_system=="homodimer breaking":
                self.system=System_homodimer_breaking()
        else:
            if issubclass(binding_system, BindingSystem):
                self.system = binding_system()
        if self.system is None:
            print("Invalid system specified, try one of: [simple, homodimer, competition, homdimer breaking]")
            return None
    def _initialize_plot(self):
        if self.fig is None:
            self.fig, self.axes = plt.subplots(
                nrows=1, ncols=1, figsize=pbc_plot_style['fig_size'])
            self.axes.grid(True, which='both')
            self.axes.set_ylim(0, 1)
            plt.tight_layout(rect=(0.05,0.05,0.95,0.92))
   

    def add_curve(self, parameters, readout, curve_name=None):
        if self.system is None:
            print("No system defined, could not proceed")
            return None
        self._initialize_plot()
        changing_parameters = self._find_changing_parameters(parameters)
        if not len(changing_parameters) == 1:
            print("Must have 1 changing parameter, no curves added.")
            return
        y_values = None
        if not self.system.analytical:
            y_values=self.system.query(parameters, readout)
        else:
            y_values=self.system.query(parameters)
        self.curves.append(_Curve(parameters[changing_parameters[0]],y_values))
        self._last_known_changing_parameter=changing_parameters[0]
        self._last_known_readout = readout
        self._num_added_traces += 1
        if curve_name is None:
            curve_name = f"Curve {self._num_added_traces}"
        self.axes.plot(parameters[changing_parameters[0]], y_values,
                       self.plot_solution_colours[self._num_added_traces]+'-', label=curve_name, linewidth=2)
        self._max_x_axis = np.nanmax(
            [self._max_x_axis, parameters[changing_parameters[0]][-1]])
        self._min_x_axis = np.nanmin(
            [self._min_x_axis, parameters[changing_parameters[0]][0]])
        self._min_y_axis = np.nanmin(y_values)
        self._max_y_axis = np.nanmax([self._max_y_axis, np.nanmax(y_values)])

    def add_points_to_plot(self, xcoords, ycoords):
        """
        Add scatterpoints to a plot, useful to represent real measurement data

        Args:

            xcoords (np.ndarray or list): x-coordinates
            ycoords (np.ndarray or list): y-coordinates

        Returns:

            None
        """
        self._initialize_plot()
        self.axes.scatter(xcoords, ycoords)
        if isinstance(xcoords, np.ndarray) and isinstance(ycoords, np.ndarray):
            self._min_y_axis = min(self._min_y_axis, min(np.real(ycoords)))
            self._max_y_axis = max(self._max_y_axis, max(np.real(ycoords)))


    def show_plot(self, title: str="System simulation",xlabel: str=None,ylabel: str=None,min_x: float=None,max_x: float=None,min_y: float=None,max_y: float=None,log_x_axis: bool=False,log_y_axis: bool=False,pbc_plot_style: dict=pbc_plot_style,png_filename: str=None,svg_filename: str=None,show_legend: bool=True):
        """Show the PyBindingCurve plot

        Args:

            title (str):  The title of the plot (default = "System simulation")
            xlabel (str):  X-axis label (default = None)
            ylabel (str):  Y-axis label (default = None, causing label to be "Fraction")
            min_x (float): X-axis minimum (default = None)
            max_x (float): X-axis maximum (default = None)
            min_y (float): Y-axis minimum (default = None)
            max_y (float): Y-axis maximum (default = None)
            log_x_axis (bool): log scale on X-axis (default = False)
            log_y_axis (bool): log scale on Y-axis (default = False)
            ma_style (bool): apply MA styling, making plots appear like GraFit plots
            png_filename(str): file name/location where png will be written
            svg_filename(str): file name/location where svg will be written


        Returns:

            None
        """
        if not min_x is None:
            self._min_x_axis=min_x
        if not max_x is None:
            self._max_x_axis=max_x
        if not min_y is None:
            self._min_y_axis=min_y
        if not max_y is None:
            self._max_y_axis=max_y

        if max_y is None:
            self.axes.set_ylim(self._min_y_axis, self._max_y_axis*1.1)
        else:
            self.axes.set_ylim(self._min_y_axis, self._max_y_axis)
        self.axes.set_xlim(self._min_x_axis, self._max_x_axis)
        if log_x_axis:
            self.axes.set_xscale("log", nonposx='clip')
        if log_y_axis:
            self.axes.set_yscale("log", nonposx='clip')


        if xlabel is None:
            self.axes.set_xlabel("["+self._last_known_changing_parameter.upper()+"]", fontsize=pbc_plot_style['axis_label_size'],fontname=pbc_plot_style['axis_label_font'], labelpad=pbc_plot_style['x_axis_labelpad'])
        else:
            self.axes.set_xlabel(xlabel, fontsize=pbc_plot_style['axis_label_size'],fontname=pbc_plot_style['axis_label_font'], labelpad=pbc_plot_style['x_axis_labelpad'])
        
        if ylabel is None:
            self.axes.set_ylabel("["+self._last_known_readout.upper()+"]", fontsize=pbc_plot_style['axis_label_size'],fontname=pbc_plot_style['axis_label_font'], labelpad=pbc_plot_style['y_axis_labelpad'])
        else:
            self.axes.set_ylabel(ylabel, fontsize=pbc_plot_style['axis_label_size'],fontname=pbc_plot_style['axis_label_font'], labelpad=pbc_plot_style['y_axis_labelpad'])
        
        self.axes.set_title(
            title, fontsize=pbc_plot_style['title_size'], fontname=pbc_plot_style['title_font'], pad=pbc_plot_style['title_labelpad'])

        #plt.figure(num=1, figsize=(
        #    pbc_plot_style['figure_width'], pbc_plot_style['figure_height']), dpi=pbc_plot_style['dpi'], facecolor='w', edgecolor='k')
        if show_legend:
            self.axes.legend(prop={'size': pbc_plot_style['legend_font_size']})

        for tick in self.axes.xaxis.get_major_ticks():
            tick.label.set_fontsize(pbc_plot_style['x_tick_label_font_size'])
        for tick in self.axes.yaxis.get_major_ticks():
            tick.label.set_fontsize(pbc_plot_style['y_tick_label_font_size'])

        if png_filename is not None:
            plt.savefig(png_filename, dpi=pbc_plot_style['dpi'], metadata={
                        'Title': "pyBindingCurve plot"})
        if svg_filename is not None:
            plt.savefig(svg_filename, metadata={
                        'Title': "pyBindingCurve plot"})
        plt.show()

    def fit(self, system_parameters: dict, to_fit: dict, ycoords: np.array, x_parameter='P', y_parameter='PL', bounds: dict=None,):
        """Fit the parameters of a system to a set of data points

        Fit the system to a set of (usually) experimental datapoints.
        The fitted parameters are stored in the system_parameters dict
        which may be accessed after running this function.  It is
        possible to fit multiple parameters at once and define bounds
        for the parameters.  The function returns a dictionary of the
        accuracy of fitted parameters, which may be captured, or not.

        Args:

            system_parameters (dict):  Dictionary containing system
                parameters, will be used as arguments to the systems equations.
            to_fit: (dict): Dictionary containing system parameters to fit.
            xcoords: (np.array): X coordinates of data the system
                parameters should be fit to
            ycoords: (np.array): Y coordinates of data the system
                parameters should be fit to
            bounds: (dict): Dictionary of tuples, indexed by system parameters
                denoting the lower and upper bounds of a system parameter
                being fit (default = None)

        Returns:

            tuple(dict, dict)
                Tuple containing a dictionary of best fit systems parameters, then a dictionary containing the accuracy for fitted variables.
        """
        y_parameter=y_parameter.lower()
        system_parameters_copy=dict(system_parameters)
        # Check we have parameters to fit, and nothing is missing
        if(len(to_fit.keys()) == 0):
            print("Nothing to fit, insert parameters to fit into to_fit dictionary")
            return None
        missing=sorted(list(
            set(self.system.arguments) - set([*system_parameters_copy]+[*to_fit])))
        if(len(missing) > 0):
            print("Not all system parameters included in system_parameters or to_fit dictionaries, check all variables for the used equation are included")
            print("Missing variables are: ", missing)
            return None
        # Add parameters for lmfit, accounting for bounds
        if bounds == None:
            bounds={}
        params=lmfit.Parameters()
        for varname in to_fit.keys():
            bnd_min=-np.inf
            bnd_max=np.inf
            if varname in bounds.keys():
                bnd_min=bounds[varname][0]
                bnd_max=bounds[varname][1]
            params.add(
                varname, value=to_fit[varname], min=bnd_min, max=bnd_max)

        lmmini=lmfit.Minimizer(self._residual, params, fcn_args=(
            system_parameters_copy, to_fit, ycoords, y_parameter))
        result=lmmini.minimize()

        for k in system_parameters_copy.keys():
            if type(system_parameters_copy[k]) == lmfit.parameter.Parameter:
                system_parameters_copy[k]=system_parameters_copy[k].value

        return system_parameters_copy, dict((p, result.params[p].stderr) for p in result.params)

    def _residual(self, params, system_parameters: dict, to_fit: dict, y: np.array, readout):
        """Residual function for fitting parameters.

        Helper function for lm_fit, calculating residual remaining for probed system parameters.

        Args:

        system_parameters (dict): Dictionary containing system
                parameters, will be used as arguments to the systems equations.
        to_fit: (dict): Dictionary containing system parameters to fit.

        """
        for value in params:
            system_parameters[value]=params[value]
        if not self.system.analytical:
            return self.system.query(system_parameters,readout)-y
        else:
            return self.system.query(system_parameters)-y
