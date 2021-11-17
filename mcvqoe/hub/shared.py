# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 11:03:39 2021

@author: MkZee
"""

from os import path

import importlib.resources
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as fdl
from PIL import Image, ImageTk

import mcvqoe.hub.loadandsave as loadandsave
from .tk_threading import show_error, Abort_by_User, InvalidParameter
from .tk_threading import SingletonWindow

from mcvqoe.simulation import QoEsim

PADX = 10
PADY = 10

FONT_SIZE = 10

#find MCV icon and add set as window icon
def add_mcv_icon(win):
    with importlib.resources.path('mcvqoe.hub','MCV-sm.ico') as icon:
        if icon:
            #set the title- and taskbar icon
            win.iconbitmap(icon)
        else:
            print('Could not find icon file')


class ScrollableFrame(ttk.Frame):
    """Used to add a scrollbar to frames. see MCVQoEGui.init_frames() for
    details on how to add a scrollbar to a frame.
    
    """
    
    def __init__(self, master, **kwargs):
        self.container = ttk.Frame(master)
        self.canvas = tk.Canvas(self.container)
        scrollbar = ttk.Scrollbar(
            self.container, orient='vertical', command=self.canvas.yview)
        
        super().__init__(self.canvas, **kwargs)
        
        self.bind(
                "<Configure>",
                self._on_resize
                )
        self.canvas.create_window((0, 0), window=self, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        
    def _on_resize(self, e):
        self.canvas.configure(
                    scrollregion=self.canvas.bbox("all")
                    )
    
    def pack(self, *args, **kwargs):
        self.container.pack(*args, **kwargs)
    
    def grid(self, *args, **kwargs):
        self.container.grid(*args, **kwargs)
    def place(self, *args, **kwargs):
        self.container.place(*args, **kwargs)
    def pack_forget(self):
        self.container.pack_forget()
    def grid_forget(self):
        self.container.grid_forget()
        
    def scroll(self, event):
        
        if (hasattr(event, 'num') and event.num == 5) or (hasattr(
                event, 'delta') and event.delta < 0):
            delta = -1
        else:
            delta = 1
        self.canvas.yview_scroll(-delta, 'units')












        
class TestCfgFrame(ttk.LabelFrame):

    """
    Base class for frames to configure and run a measurement.
    
    
    CLASS VARIABLES
    ---------------
    
    text : str
        The title of the frame
    
    
    PARAMETERS
    ----------
    
    btnvars : TkVarDict
        loads and stores the values in the controls
    
    
    """
    
    text = ''
    
       
    
    def __init__(self, btnvars, *args, **kwargs):
        
        kwargs['text'] = self.text
            
        super().__init__(*args, **kwargs)
        
        #option functions will get and store their values in here
        self.btnvars = btnvars
        
        
        #sets what controls will be in this frame
        controls = self.get_controls()
        
        #initializes controls
        self.controls = {}
        for row in range(len(controls)):
            c = controls[row](master=self, row=row)
            
            self.controls[c.__class__.__name__] = c
            
    def update_title(self, title):
        self.configure(text = title)        
        
        
        
    def get_controls(self) -> iter:
        """
        Called to acquire an ordered list of control classes to construct.
        
        Classes should be subclasses of LabeledControl
        
        Subclasses should override this.
        
        
        RETURNS
        -------
        control-list : iter
            a list of control classes that go into the frame, in the order they should
            appear
            
        """
        return tuple()



class SubCfgFrame(TestCfgFrame):
    """Base class to make a subframe for controls grouped together.
    
    It is designed to behave like a control in and of itself, and should be
    included in the get_controls() of its master.
    
    CLASS VARIABLES
    ---------------
    
    text : str
        the title of the frame
    
    """
    
    text = ''
    
    def __init__(self, master, row, *args, **kwargs):
        
        
    
        super().__init__(master.btnvars, master, *args, **kwargs)
        
        
        self.grid(column=0, row=row, columnspan=4, sticky='NSEW',
                  padx=PADX, pady=PADY)
        
        master.controls.update(self.controls)
        
        
        
    def get_controls(self) -> iter:
        """see TestCfgFrame.get_controls"""
        return tuple()
    

class AdvancedConfigGUI(tk.Toplevel, metaclass = SingletonWindow):
    """A Toplevel window containing advanced/other parameters.
    
    Used as a base class for all advanced windows, as well as
    hardware- and simulation-settings windows.
    
    ATTRIBUTES
    ----------
    
    text : str
        the title of the window

    """
    text = ''
    
    def __init__(self, master, btnvars, *args, **kwargs):
        
        
        super().__init__(master, *args, **kwargs)
        #hide the window
        self.withdraw()
        #as soon as possible (after app starts) show again
        self.after(0,self.deiconify)
        
        # keeps track of tcl variable traces for later destruction
        # this prevents some errors in the simulation settings window.
        self.traces_ = []
        
        # sets its title based on class variable 'text'
        self.title(self.text)
        
        #sets the controls in this window
        control_classes = list(self.get_controls())
        
        # include the OK button to close the window
        control_classes.append(_advanced_submit)
        
        self.btnvars = btnvars
        
        # take keyboard focus
        self.focus_force()
        
        add_mcv_icon(self)
        
        self.controls = master.controls
        #initializes controls
        for row in range(len(control_classes)):
            c = control_classes[row](master=self, row=row)
            
            # stores controls with their keys being their parameter names
            self.controls[c.__class__.__name__] = c
            
        
        
        
        # return key closes window
        self.bind('<Return>', lambda *args : self.destroy())
        
        
        
        
        
            
    def get_controls(self):
        pass
    
    def destroy(self):
        super().destroy()
        
        # remove tcl variable traces (prevents errors in simulation settings)
        for var, trace_id in self.traces_:
            var.trace_remove('write', trace_id)
                

class DescriptionBlock:        
    """
    A block of text to go with Labled controls.
    
    A block of text that is wordwraped that spans 3 grid rows
    """
    
    text = ''
    
    do_font_scaling = True
    
    MCtrl = ttk.Entry
    MCtrlargs = []
    MCtrlkwargs = {}
    
    #usually the browse button
    RCtrl = None
    RCtrlkwargs = {}
    
    padx = PADX
    pady = PADY
    
    no_value = False # if it has no associated instance variable in measure
    
    def __init__(self, master, row):
        self.master = master

        self.description = ttk.Label(master, text=self.text, wraplength=320)
        
        self.description.grid(
            padx=self.padx, pady=self.pady, column=0, columnspan=3, row=row, sticky='E')
        
    def destroy(self):

        #destroy all the things
        if hasattr(self,'description') and self.description is not None:
            #make sure widget exists
            if self.description.winfo_exists():
                self.description.grid_forget()
                self.description.destroy()
            #mark as destroyed
            self.description = None
            

class LabeledControl:
    """
    A row consisting of the following general template:
        
        MyParameter:   (?)     [value          ]     BUTTON
    
    NOTE: if you can, use one of the following base-classes instead of
    over-customizing this one:
        
        LabeledEntry
        LabeledNumber
        LabeledCheckbox
        LabeledSlider
        MultiChoice
        EntryWithButton
        advanced
    
    
    Subclasses should redefine any of the class variables, as well as the
        setup() method
        
    Subclasses should have their names be equal to the internal parameter name
    
    CLASS VARIABLES
    ---------------
    
    text : str
        a user-friendly name for the parameter
        
        
    do_font_scaling : bool
        whether the middle control has user-modifiable text that can be font-scaled
        
        set this to false for things like radiobuttons and checkboxes
        
        
    MCtrl : tkinter.ttk widget class
        the class of tkinter widget to use for the middle control
        
        recommended to use classes from the tkinter.ttk module for aesthetic reasons.
        
    MCtrlargs : list
        positional arguments to be passed to the MCtrl constructor
    
    MCtrlkwargs : dict
        kw arguments to be passed to the MCtrl constructor
        
    variable_arg : 'textvariable', 'variable'
        whether the control's value should be pulled from its text.
        
        change this to 'variable' for controls like sliders, checkboxes, radiobuttons, etc
        that don't have user-modifiable text
        
    
    RCtrl : tkinter.ttk widget class
        the right-most control (usually a button)
        
    RCtrlkwargs : dict
        the kwargs to be passed to the RCtrl constructor
    
    padx, pady : int
        the control's padding, in pixels
        
    no_value : bool
        set this to true for controls, such as the advanced button,
        that do not have a value to put into the measure class
    
    
    PARAMETERS  (handled internally)
    ----------
    master : 
        the window that this will be in
        
    row : int
        the row that the controls should be gridded in
        
    
    """
    text = ''
    
    do_font_scaling = True
    
    MCtrl = ttk.Entry
    MCtrlargs = []
    MCtrlkwargs = {}
    
    variable_arg = 'textvariable'
    
    #usually the browse button
    RCtrl = None
    RCtrlkwargs = {}
    
    padx = PADX
    pady = PADY
    
    no_value = False # if it has no associated instance variable in measure
    
    
    def setup(self):
        """additional code that can be run during initiation
        
        """
        pass
    
    
    
    def __init__(self, master, row):
        self.master = master

        self.l_ctrl = ttk.Label(master, text=self.text)
        
        self.l_ctrl.grid(
            padx=self.padx, pady=self.pady, column=0, row=row, sticky='E')
        
        MCtrlkwargs = self.MCtrlkwargs.copy()
        MCtrlargs = self.MCtrlargs.copy()
        RCtrlkwargs = self.RCtrlkwargs.copy()

        
        # get tcl variable 
        if self.__class__.__name__ in master.btnvars:
            self.btnvar = master.btnvars[self.__class__.__name__]
        
        # help button
        if self.__class__.__doc__:
            self.h_ctrl = HelpIcon(master, tooltext=self._get_help())
            self.h_ctrl.grid(
                column=1, row=row, padx=0, pady=self.pady, sticky='NW')

        self.setup()
        #some controls require more flexibility, so they don't use self.MCtrl
        if self.MCtrl:
            try:
                btnvar = self.btnvar
            except AttributeError:
                btnvar = None
                raise KeyError(f" The parameter '{self.__class__.__name__}' "+
                               f"from '{self.master.__class__.__name__}' "+
                               'is missing its default value. '+
                               "Make sure it is declared in 'control_list', "+
                               "and that it is an accepted type")
                
            if self.variable_arg:
                MCtrlkwargs[self.variable_arg] = self.btnvar
                
            else:
                MCtrlargs.insert(0, self.btnvar)
            
            if self.do_font_scaling:
                MCtrlkwargs['font'] = (FONT_SIZE,)
            
            # initialize the control
            self.m_ctrl = self.MCtrl(master, *MCtrlargs, **MCtrlkwargs)
            self.m_ctrl.grid(
                column=2, row=row, padx=self.padx, pady=self.pady, sticky='WE')
        
        # Right-most control
        if self.RCtrl:
            #add command to button
            if self.RCtrl in (ttk.Button, tk.Button):
                RCtrlkwargs['command'] = self.on_button
            
            # initialize the control
            self.r_ctrl = self.RCtrl(master, **RCtrlkwargs)
            
            self.r_ctrl.grid(
                padx=self.padx, pady=self.pady, column=3, row=row, sticky='WE')
            
            
    def _get_help(self):
        
        lst = []
        for line in self.__class__.__doc__.splitlines():
            lst.append(line.strip())
        
        return '\n'.join(lst)
        
    def destroy(self):

        #destroy all the things
        if hasattr(self,'l_ctrl') and self.l_ctrl is not None:
            #make sure window exists
            if self.l_ctrl.winfo_exists():
                self.l_ctrl.grid_forget()
                self.l_ctrl.destroy()
            self.l_ctrl = None

        if hasattr(self,'m_ctrl') and self.m_ctrl is not None:
            #make sure window exists
            if self.m_ctrl.winfo_exists():
                self.m_ctrl.grid_forget()
                self.m_ctrl.destroy()
            self.m_ctrl = None

        if hasattr(self,'r_ctrl') and self.r_ctrl is not None:
            #make sure window exists
            if self.r_ctrl.winfo_exists():
                self.r_ctrl.grid_forget()
                self.r_ctrl.destroy()
            self.r_ctrl = None

        if hasattr(self,'h_ctrl') and self.h_ctrl is not None:
            #make sure window exists
            if self.h_ctrl.winfo_exists():
                self.h_ctrl.grid_forget()
                self.h_ctrl.destroy()
            self.h_ctrl = None
        
    def on_button(self):
        """The function to run when the user presses the button on the right
        of the control.
        
        Subclasses should override this.

        """
        pass
            


class HelpIcon(ttk.Button):
    """
    Shows the control's __doc__ when you hover over or select this icon
    
    """
    def __init__(self, master, *args, tooltext, **kwargs):
        kwargs['text'] = '?'
        kwargs['style'] = 'McvHelpBtn.TLabel'
        super().__init__(master, *args, **kwargs)
        
        # bind hover and selection events
        self.bind('<Enter>', self.enter)
        self.bind('<FocusIn>', self.enter)
        self.bind('<Leave>', self.leave)
        self.bind('<FocusOut>', self.leave)
        
        self.tw = None
        self.tooltext = tooltext
        
    def enter(self, event):
        """
        shows the HELP tooltip

        Parameters
        ----------
        event : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if self.tw:
            return
        self.tw = ToolTip(self, self.tooltext)
        
        # get location of help icon
        x, y, cx, cy = self.bbox("insert")
        rootx = _get_master(self).winfo_rootx()
        
        # calculate location of tooltip
        x = x + self.winfo_rootx() - self.tw.winfo_width()
        y = y + cy + self.winfo_rooty() + 27
        
        #ensure tooltip does not fall off left edge of window
        if x < rootx + 20: x = rootx + 20
                
        # set position of tooltip
        self.tw.wm_geometry("+%d+%d" % (x, y))
        
        #show tooltip
        self.tw.show()
        
        
    def leave(self, event):
        """
        Hides the tooltip

        Parameters
        ----------
        event : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if not self.tw:
            return
        self.tw.destroy()
        self.tw = None
        
def _get_master(m, targets = (tk.Tk, tk.Toplevel)):
    """
    given a tkinter widget, goes up the chain of hierarchy until it finds
    a widget in targets, and returns that widget.
    
    Used to get a widget's parent window, or to get the tkinter main window
    

    Parameters
    ----------
    m : widget
        
    targets : tk classes
        The default is (tk.Tk, tk.Toplevel).

    Returns
    -------
    m : instance of targets
        

    """
    while hasattr(m, 'master'):
            if isinstance(m, targets):
                return m
            m = m.master
        

class ToolTip(tk.Toplevel):
    """
    A simple tool-tip window for showing help info about a parameter
    """
    def __init__(self, master, text, style='McvToolTip.TLabel'):
        super().__init__(master)
        
        try:
            # on windows, add alwaysontop
            self.attributes('-topmost',True)
        except: pass
        
        
        lf = ttk.Frame(self, style='McvToolTip.TFrame')
        lf.pack()
        
        ttk.Label(lf, text=text, style=style).pack(
            padx=PADX, pady=PADY)
        
        #removes window title-bar, taskbar icon, etc
        self.wm_overrideredirect(1)
        
        # temporarily hides window to prevent sudden movement
        self.withdraw()
        
        # solidifies the window's size to ensure correct placement on screen
        self.update_idletasks()
    
    def show(self):self.deiconify()



class LabeledEntry(LabeledControl):
    """
    A convenient text-entry control
    
    CLASS VARIABLES
    ---------------
    
    text : str
        a user-friendly name for the parameter
    
    """






class LabeledNumber(LabeledControl):
    """A convenient base class for parameters that should be a number.
    
    Sub-classes should set any of the following class variables for customization
    
    CLASS VARIABLES
    ---------------
    
    text : str
        the user-friendly name for the parameter
    
    min_ : number
        the minimum value (defaults to 0)
    max_ : number
        the maximum value (defaults to very large)
        
    increment : number
        how much the up- and down- buttons should change the value.
        this does NOT limit the resolution of the value
    
    
    """
    RCtrl = None
    
    MCtrl = ttk.Spinbox
    
    min_ = 0
    max_ = 2**15 - 1
    increment = 1
    
    def __init__(self, *args, **kwargs):
        
        self.MCtrlkwargs = {'increment':self.increment,
                                          'from_':self.min_,
                                          'to':self.max_}
        super().__init__(*args, **kwargs)


class LabeledSlider(LabeledControl):
    """A convenient base class for parameters that should be a percentage
    
    Base classes should not modify any of the class variables (except 'text');
    Use LabeledNumber for better resolution and range.
    
    CLASS VARIABLES
    ---------------
    
    text : str
        the user-friendly name for the parameter
    
    """
    
    RCtrl = None
    MCtrl = None
    # slider does not accept font size
    do_font_scaling = False    
    
    
    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, row, *args, **kwargs)
        self.txtvar = self._percentage()
        self.on_change()
        
        self.btnvar.trace_add('write', self.on_change)
    
        ttk.Label(master, textvariable=self.txtvar).grid(
            column=3, row=row, sticky='W')
    
        self.m_ctrl = ttk.Scale(master, variable=self.btnvar,
            from_=0, to=1)
        
        self.m_ctrl.grid(
            column=2, row=row, padx=self.padx, pady=self.pady, sticky='WE')
    
    def on_change(self, *args, **kwargs):
        #updates the percentage to match the value of the slider
        self.txtvar.set(self.btnvar.get())

    class _percentage(tk.StringVar):
        """Displays a percentage instead of a float
    
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        
        def set(self, value):
            v = float(value) * 100
            s = ''
        
            for char in str(v):
                if char == '.':
                    break
                s = f'{s}{char}'
        
                    
            super().set(f'{s}%')
            


class _MultiChoice_Frame(tk.Frame):
    def __init__(self, *args, association, textvariable, **kwargs):
        
        super().__init__(*args, **kwargs)
        self.controls = []
        
        #initialize
        for val, text in association.items():
            c = ttk.Radiobutton(self, variable=textvariable, value=val,
                text=text)
            
            c.pack(fill=tk.X)
            
            self.controls.append(c)
            
    def configure(self, *args, **kwargs):
        for ctrl in self.controls:
            ctrl.configure(*args, **kwargs)





class MultiChoice(LabeledControl):
    """ A base class for multiple-choice controls
    
    sub-classes should change any of the following class variables
    for customization
    
    CLASS VARIABLES
    ---------------
    
    text : str
        user-friendly name for the parameter
    
    association : dict
        associates the internal option with its user-friendly name. i.e.:
            
            {
            'm2e_1loc'   : '1 Location',
            'm2e_2loc_tx': '2 Location (transmit)',
            'm2e_2loc_rx': '2 Location (receive)'
            }
        
    
    
    """
    association = {}
    do_font_scaling = False
    MCtrl = _MultiChoice_Frame
    
    def __init__(self, *args, **kwargs):
        self.MCtrlkwargs = self.MCtrlkwargs.copy()
        self.MCtrlkwargs['association'] = self.association
        
        super().__init__(*args, **kwargs)



class LabeledCheckbox(LabeledControl):
    """
    Base class for parameters that are boolean
    
    sub-classes should not change any of the class variables (except 'text')
    
    CLASS VARIABLES
    ---------------
    
    text : str
        USE MIDDLE_TEXT INSTEAD
    
    middle_text : str
        user-friendly name for parameter
    
    """
    middle_text = ''
    
    MCtrl = ttk.Checkbutton
    do_font_scaling = False
    variable_arg = 'variable'
    
    def __init__(self, *args, **kwargs):
        
        
        self.MCtrlkwargs = {'text': self.middle_text}
        
        
        super().__init__(*args, **kwargs)



class EntryWithButton(LabeledControl):
    """A base-class for controls that have an entry alongside a button.
    
    Subclasses should override the on_button() method to determine the button's action.
    Within the method, the parameter's value can be interacted with using:
    
        current_value = self.btnvar.get()
        
        self.btnvar.set(new_value)
        
    the following class variables should be overridden for customization
    
    CLASS VARIABLES
    ---------------
    
    text : str
        user-friendly name for the parameter
        
    button_text : str
        text to go into the button
    
    
    """
    
    button_text = ''
    
    
    RCtrl = ttk.Button
    
    def on_button(self): pass
    
    def __init__(self, *args, **kwargs):
        
        self.RCtrlkwargs = self.RCtrlkwargs.copy()
        self.RCtrlkwargs['text'] = self.button_text
        super().__init__(*args, **kwargs)
        
        



class advanced(EntryWithButton):
    """Base class for singular-button 'advanced' controls.
    
    This could theoretically be sub-classed further for other single-button uses.
    
    Subclasses should modify the following class variables:
        
    CLASS VARIABLES
    ---------------
    
    text : str
        USE BUTTON_TEXT INSTEAD
    
    toplevel : type
        a subclass of tk.Toplevel that will be constructed when the button is pressed
        
    button_text : str
        the text inside the button
    
    
    """
    text = ''
    
    MCtrl = None
    
    button_text = 'Advanced...'
    
    toplevel = None
    
    no_value = True
    
    def on_button(self):
        self.toplevel(master=self.master, btnvars=self.master.btnvars)












#---------------------------controls------------------------------------------
















class audio_files(EntryWithButton):
    """Audio files to use for testing.
    
    If left blank, all the files in "Audio Folder" are used. """
    
    text = 'Audio File(s):'
    
    button_text = 'Browse...'
        
    
    
    def on_button(self):
        
        initpath = self.master.btnvars['audio_path'].get()
        if not initpath or not path.isdir(initpath):
            
            # load cached folder
            initpath = loadandsave.fdl_cache[
                f'{self.master.__class__.__name__}.audio_path']
        
        
        fp = fdl.askopenfilenames(parent=self.master,
                initialdir=initpath,
                filetypes=[('WAV files', '*.wav')])
        if fp:
            # normalize paths (prevents mixing of / and \ on windows)
            fp = [path.normpath(f) for f in fp]
            
            path_, files = format_audio_files('', fp)
            self.btnvar.set(files)
            self.master.btnvars['audio_path'].set(path_)
            
            # cache folder
            loadandsave.fdl_cache.put(
                f'{self.master.__class__.__name__}.audio_path',
                 path_,
                 )
            
            
    
            
            
class audio_path(EntryWithButton):
    """The source folder containing the audio files."""
    
    
    text = 'Audio Folder:'
    
    button_text = 'Browse Folder'
    
    
    def on_button(self):
        
        initpath = self.btnvar.get()
        if not initpath or not path.isdir(initpath):
            
            # load cached folder
            initpath = loadandsave.fdl_cache[
                f'{self.master.__class__.__name__}.audio_path']
        
        
        fp = fdl.askdirectory(initialdir = initpath)
        if fp:
            
            fp = path.normpath(fp)
            
            path_, files = format_audio_files(path_=fp)
            
            self.master.btnvars['audio_files'].set(files)
            
            self.btnvar.set(path_)
            
            loadandsave.fdl_cache.put(
                f'{self.master.__class__.__name__}.audio_path',
                path_,
                )


class Audio_Set(LabeledControl):
    """Default audio set to use for measurement, if applicable."""

    def __init__(self, master, row, *args, **kwargs):

        self.text = 'Audio Set:'
        self.MCtrl = ttk.Menubutton
        self.do_font_scaling = False

        super().__init__(master, row, *args, **kwargs)

        self.menu = tk.Menu(self.m_ctrl, tearoff=False)

        self.m_ctrl.configure(menu=self.menu)


class trials(LabeledNumber):
    """Number of trials to use for test."""
    
    text = 'Number of Trials:'
       
    min_ = 1
    
    
class outdir(EntryWithButton):
    """Location to store all output files"""
    
    text='Output Folder:'
    
    button_text = 'Browse...'
    
    def on_button(self):
        dirp = fdl.askdirectory(parent=self.master)
        if dirp:
            dirp = path.normpath(dirp)
            self.btnvar.set(dirp)
            
            
    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        


class overplay(LabeledNumber):
    """The number of seconds to play silence after the audio is complete.
    This allows for all of the audio to be recorded when there is delay
    in the system"""
    
    
    text='Overplay Time (sec):'
    
    increment = 0.01
    
    

class ptt_gap(LabeledNumber):
    """Time to pause after completing one trial and starting the next."""

    text = 'Gap Between Trials:'
    
    MCtrl = ttk.Spinbox
    
    increment = 0.01
    
    
class SaveAudio(MultiChoice):
    """Sets what recorded audio should be saved into the output folder.
    
    Set to 'Rx audio only' to only save received audio."""
    text = 'Save Audio:'
    
    association = {'all_audio' : 'All audio',
                   'rx_only'   : 'Rx audio only',
                   'no_audio'  : 'No audio',
                   }
    



# --------------------------- the following 3 are all for pause_trials--------
class RadioCheck(SubCfgFrame):
    
    text = 'Regular Radio Checks'
    
    def get_controls(self):
        return (
            _limited_trials,
            pause_trials,
            )

class _limited_trials(LabeledCheckbox):
    """When disabled, sets the number of pause_trials to infinite"""
    
    middle_text = 'Enable Radio Checks'
    
    
    def __init__(self, master, row, *args, **kwargs):
        
        # give itself an actual stored value
        self.btnvar = tk.BooleanVar()
        
        super().__init__(master, row, *args, **kwargs)
        
        # set a trace to change the value depending on 'pause_trials' parameter
        self.btnvar.trace_add('write', self.on_button)
        self.master.btnvars['pause_trials'].trace_add('write', self.update)
        self.update()
        
        
    def on_button(self, *args, **kwargs):
        if self.btnvar.get():
            val = self.previous
        else:
            val = 'inf'
            
        self.master.btnvars['pause_trials'].set(val)
    
    def update(self, *args, **kwargs):
        
        v = self.master.btnvars['pause_trials'].get()
        
        other = v != 'inf'
        this = self.btnvar.get()
        
        if other:
            self.previous = v
            
        if other != this:
            self.btnvar.set(other)
        
        
        
    
        
class pause_trials(LabeledNumber):
    """Number of trials to run before pausing to perform a radio check."""
    
    text = 'Trials between check:'
    
       
    min_ = 1
    
    
    
        

class time_expand(SubCfgFrame):
    text = 'Time Expand'
    
    
    
    def __init__(self, master, row, **kwargs):
        
        super().__init__(master, row, **kwargs)
    
    def get_controls(self):
        
        return (
            _time_expand_i,
            _time_expand_f,
            )

class _time_expand_i(LabeledNumber):
    """Length of time, in seconds, of extra
    audio to send BEFORE the keyword to ABC_MRT16. Adding time protects
    against inaccurate M2E latency calculations and misaligned audio."""
    
    text = 'Expand Before:'
    
    increment = 0.01
    
    
class _time_expand_f(LabeledNumber):
    """Length of time, in seconds, of extra
    audio to send AFTER the keyword to ABC_MRT16. Adding time protects
    against inaccurate M2E latency calculations and misaligned audio."""
    
    text = 'Expand After:'
    
    increment = 0.01

    
    
class bgnoise_file(EntryWithButton):
    """This is used to read in a noise file to be mixed with the
    test audio. Default is no background noise."""

    text = 'Noise File:'
    
    button_text = 'Browse...'
    
    def on_button(self):
        fp = fdl.askopenfilename(parent=self.master,
            initialfile=self.btnvar.get(),
            filetypes=[('WAV files', '*.wav')])
        if fp:
            self.btnvar.set(fp)



class bgnoise_volume(LabeledSlider):
    """Scale factor for background
    noise."""

    text = 'Volume:'

class ptt_wait(LabeledNumber):
    """The amount of time to wait, in seconds, between pushing the
    push to talk button and starting playback. This allows time
    for access to be granted on the system."""

    text = 'PTT Wait Time:'
    
    increment = 0.01

              
                                  








    

class _advanced_submit(advanced):
    
    #closes the advanced window
    
    button_text = 'OK'
    
    def on_button(self):
        self.master.destroy()
    
    
# advanced groups

class BgNoise(SubCfgFrame):
    text = 'Background Noise'
    
    def get_controls(self):
        return (bgnoise_file,
                bgnoise_volume)

       




# ----------------------- Device delay characterization -----------------------


class dev_dly(LabeledNumber):
    """Delay in seconds of the audio path with no communication device
    present."""
    
    text = 'Device Delay:'
    
    increment = 0.001
    
    # add button functionality too.
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'Calibrate'}
    

    def on_button(self):
        CharDevDly()



class CharDevDly(tk.Toplevel, metaclass = SingletonWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #hide the window
        self.withdraw()
        #as soon as possible (after app starts) show again
        self.after(0,self.deiconify)

        add_mcv_icon(self)
        
        self.title('Device Delay Characterization')
        
        ttk.Label(self, text=
"""It seems like you have not yet done a characterization test. A
characterization test is a Mouth-to-Ear test that is run with the audio
output directly fed into the input, as shown below.
""").pack(fill=tk.X, padx=10, pady=10)


        # open image
        max_width = 600
        max_height = 500

        canvas = tk.Canvas(self,width=max_width, height=max_height)
        
        with importlib.resources.path('mcvqoe.hub','dev_dly_char_example.png') as name:
            img = Image.open(name)

        img.thumbnail((max_width,max_height),resample=Image.LANCZOS, reducing_gap=None)

        canvas.crestimg = ImageTk.PhotoImage(img)
        canvas.create_image(
            max_width//2, max_height//2 + 10,
            image=canvas.crestimg
        )

        canvas.pack()

        ttk.Label(self, text='Once finished, enter the device delay below')

        ttk.Button(self, text='Continue', command = self.continue_btn
                   ).pack()

        self.finished = False
                   
    
    
    
    def continue_btn(self):
        
        _get_master(self, tk.Tk).selected_test.set('DevDlyCharFrame')
        self.destroy()




#------------------------ Global settings for hdw/simulation------------------

class _HdwPrototype:
    """Contains the default audioplayer settings.
    
    Settings must be drawn from here because the real audioplayer might throw a 
    RuntimeError on program load if the interface is not found.
    
    """
    radioport = ''
    blocksize=512
    buffersize=20
    overplay=1.0
    timecode_type='IRIGB_timecode'

#HARDWARE SETTINGS WINDOW
class HdwSettings(AdvancedConfigGUI):
    text = 'Hardware Settings'
    
    # used for _restore_defaults control
    prototype = _HdwPrototype
    
    def get_controls(self):
        return (
            AudioSettings,
            overplay,
            radioport,
            timecode_type,
            _restore_defaults,
            )
            
class radioport(LabeledControl):
    """Port to use for radio interface. Defaults to the first
    port where a radio interface is detected"""
    
    text = 'Radio Port:'
    
class timecode_type(LabeledControl):
    """type of timecode to use for two location tests"""

    text = 'Timecode Type:'
    MCtrl = ttk.Combobox
    MCtrlkwargs = {'values' : ('IRIGB_timecode','soft_timecode')}

class AudioSettings(SubCfgFrame):
    
    text = 'Audio Settings'
    
    def get_controls(self):
        return (blocksize, buffersize)
      
class blocksize(LabeledControl):
    """Block size for transmitting audio, must be a power of 2"""
    
    text = 'Block Size:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_':1, 'to':2**15 -1}
    

class buffersize(LabeledControl):
    """Number of blocks used for buffering audio"""
    
    text='Buffer Size:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_':1, 'to':2**15 -1}

class _restore_defaults(LabeledControl):
    
    
    MCtrl = None
    RCtrl = ttk.Button
    
    RCtrlkwargs = {'text' : 'Restore Defaults'}
    
    def on_button(self):
        """restores the default hardware/simulation settings.

        """
        
        from_obj = self.master.prototype()
        
        for k, tk_var in self.master.btnvars.items():
            
            if hasattr(from_obj, k):
                tk_var.set(getattr(from_obj, k))

class _SimPrototype(QoEsim):
    def __init__(self):
        QoEsim.__init__(self)
        
        self._impairment_plugin = ''

#SIMULATION SETTINGS WINDOW
class SimSettings(AdvancedConfigGUI):
    
    
    text = 'Simulation Settings'
    
    # used for _restore_defaults button
    prototype = _SimPrototype
    
    def get_controls(self):
        return (
            channel_tech,
            channel_rate,
            
            overplay,
            
            m2e_latency,
            access_delay,
            device_delay,
            rec_snr,
            PTT_sig_freq,
            PTT_sig_amplitude,
            
            ImpairmentsSelect,
            _restore_defaults,
            )

class channel_tech(LabeledControl):
    """Technology to use for the simulated channel. Channel technologies are
    handled by plugins. The only tech that is available by default is 'clean'."""

    def __init__(self, master, row, *args, **kwargs):
        
        self.text = 'Channel Tech:'
        self.MCtrl = ttk.Menubutton
        self.do_font_scaling = False
        
        super().__init__(master, row, *args, **kwargs)
        
        self.menu = tk.Menu(self.m_ctrl, tearoff=False)
        
        self.m_ctrl.configure(menu=self.menu)
        
        try:
            rates = QoEsim.get_channel_techs()
        except Exception as e:
            show_error(e)
        
        else:
            # get channel_techs to use as menu options
            for tech_ in rates:
                self.menu.add_command(label=tech_,
                        command=tk._setit(self.btnvar, tech_))

class channel_rate(LabeledControl):
    """Rate to simulate channel at. Each channel tech handles this differently.
    When set to None the default rate is used."""
    
    
    def __init__(self, master, row, *args, **kwargs):
        
        self.text = 'Channel Rate:'
        self.MCtrl = ttk.Menubutton
        
        self.do_font_scaling = False
        
        super().__init__(master, row, *args, **kwargs)
        
        self.menu = tk.Menu(self.m_ctrl, tearoff=False)
        self.m_ctrl.configure(menu=self.menu)
        
        #track selection of channel_tech
        id = self.master.btnvars['channel_tech'].trace_add('write', self.update)
        self.master.traces_.append((self.master.btnvars['channel_tech'], id))
    
        #fill menu with options
        self.update()
        

    
    def update(self, *args, **kwargs):
        failed = False
        try:
            chan_tech = self.master.btnvars['channel_tech'].get()
            
            self.menu.delete(0, 'end')
            
            default, rates = QoEsim.get_channel_rates(chan_tech)
            
            old = self.btnvar.get()
            if old not in rates:
                self.btnvar.set(default)
            
            for rate in rates:
                #add a dropdown list option
                self.menu.add_command(label=str(rate),
                            command=tk._setit(self.btnvar, str(rate)))
        except Exception as e:
            show_error(e)
            failed = True
        
        if failed:
            self.master.btnvars['channel_tech'].set('clean')

class m2e_latency(LabeledControl):
    """Simulated mouth to ear latency for the channel in seconds.
    
    Defaults to the minimum latency allowed by the channel tech."""
    
    text = 'Mouth-to-ear Latency:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_': 0, 'to': 2**15-1, 'increment':0.0001}
    
    
class access_delay(LabeledControl):
    """Delay between the time that the simulated push to talk button is pushed
    and when audio starts coming through the channel. If the 'ptt_delay'
    method is called before play_record is called, then the time given to
    'ptt_delay' is added to access_delay to get the time when access is
    granted. Otherwise access is granted 'access_delay' seconds after the
    clip starts."""
    
    text = 'Access Delay:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_': 0, 'to': 2**15-1, 'increment':0.001}

class device_delay(LabeledControl):
    """Simulated device delay in seconds."""
    
    text = 'Device Delay:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_': 0, 'to': 2**15-1, 'increment':0.0001}
    
class rec_snr(LabeledControl):
    """Signal to noise ratio for audio channel."""
    text = 'Channel SNR:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_': 0, 'to': 2**15-1, 'increment':1.0}
    

class PTT_sig_freq(LabeledControl):
    """Frequency of the PTT signal from the play_record method."""
    text = 'PTT Signal Frequency:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_':0, 'to' : 2**15-1, 'increment':0.1}
    
class PTT_sig_amplitude(LabeledControl):
    """Amplitude of the PTT signal from the play_record method."""
    text = 'PTT Signal Amplitude:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_':0, 'to' : 2**15-1, 'increment':0.1}

class ImpairmentsSelect(SubCfgFrame):
    
    text = 'Impairments'
    
    def __init__(self, master, *args, **kwargs):
        
        self.traces_ = []
        
        super().__init__(master, *args, **kwargs)

        
    def get_controls(self):
        return (
            PreImpairment,
            PreImpairmentSettings,
            ChannelImpairment,
            ChannelImpairmentSettings,
            PostImpairment,
            PostImpairmentSettings,
            )


class ChannelImpairment(LabeledControl):
    """Impairment to use on channel data."""
    
    
    def __init__(self, master, row, *args, **kwargs):
        
        self.text = 'Channel Impairment:'
        self.MCtrl = ttk.Menubutton
        
        self.do_font_scaling = False
        
        super().__init__(master, row, *args, **kwargs)
        
        self.menu = tk.Menu(self.m_ctrl, tearoff=False)
        self.m_ctrl.configure(menu=self.menu)
        
        #track selection of channel_tech
        id = self.master.master.btnvars['channel_tech'].trace_add('write', self.update)
        self.master.master.traces_.append((self.master.btnvars['channel_tech'], id))
    
        #fill menu with options
        self.update()
        
        
    def update(self, *args, **kwargs):
        failed = False
        try:
            chan_tech = self.master.master.btnvars['channel_tech'].get()

            self.menu.delete(0, 'end')
            
            if chan_tech == 'None':
                failed = True
            else:
                #get channel type
                chan_type = QoEsim().get_channel_type(chan_tech)

                #get list of impairments for the channel type
                impairments = QoEsim.get_impairment_names(chan_type)

                old = self.btnvar.get()
                if old not in impairments:
                    self.btnvar.set('None')
                
                #add None to the list
                self.menu.add_command(label='None',
                                      command=tk._setit(self.btnvar, 'None'))
                for i in impairments:
                    #add a dropdown list option
                    self.menu.add_command(label=i,
                                command=tk._setit(self.btnvar, i))
        except Exception as e:
            show_error(e)
            failed = True
        
        if failed:
            self.master.btnvars['channel_tech'].set('None')

class ImpairmentSettings(SubCfgFrame):    
    
    def __init__(self, master, row, *args, **kwargs):
        
        self.text = ''
        
        self.impairment=''
        
        self.row_num = row
        
        self.traces_ = []
        
        super().__init__(master, row, *args, **kwargs)
        
        #track selection of channel impairment
        id = self.master.btnvars[self.impairment_name].trace_add('write', self.update)
        self.master.traces_.append((self.master.btnvars[self.impairment_name], id))
        
        self.update()
        
    def get_controls(self):
        
        #empty list for controls
        controls = []
        
        if self.impairment and self.impairment != 'None':
            params = QoEsim.get_impairment_params(self.impairment)
            
            description = QoEsim.get_impairment_description(self.impairment)
            
            
            #get the name of this class
            cls_name = self.__class__.__name__
            
            descC = type(f'{cls_name}_Desc',(DescriptionBlock,),{
                                                        'text': description,
                                                      }
                        )
            
            #append description control to list
            controls.append(descC)
            
            for name,info in params.items():
                #create type name from class and parameter name
                type_name = f'{cls_name}_{name}'

                # check if a value exists
                if type_name not in self.master.btnvars:
                    #add default
                    self.master.btnvars.add_entry(type_name,info.value_type(info.default))

                if info.choice_type in ('range', 'positive'):

                    class_vals = {
                                    'min_' : info.min_val,
                                    'max_' : info.max_val,
                                    'increment' : info.interval,
                                    'text' : name,
                                 }
                    
                    if hasattr(info,'description'):
                        class_vals['__doc__'] = info.description
                    
                    #create a control class
                    cc = type(type_name,(LabeledNumber,),class_vals)
                    #add to list of controls
                    controls.append(cc)
                elif info.choice_type == 'file':

                    #function to run when browse is clicked
                    def brows_files(self):
                        fp = fdl.askopenfilename(parent=self.master,
                                filetypes=info.filetypes)
                        if fp:
                            # normalize paths (prevents mixing of / and \ on windows)
                            fp = path.normpath(fp)

                            self.btnvar.set(fp)

                    class_vals = {
                                    'on_button' : brows_files,
                                    'button_text' : 'Browse...',
                                    'text' : name,
                                 }

                    if hasattr(info,'description'):
                        class_vals['__doc__'] = info.description

                    #create a control class
                    cc = type(type_name,(EntryWithButton,),class_vals)
                    #add to list of controls
                    controls.append(cc)
                else:
                    print(f'unknown choice type {info.choice_type}')
            
        return tuple(controls)
        
    def update(self, *args, **kwargs):
        
        #update impairment name
        self.impairment = self.master.btnvars[self.impairment_name].get()
        
        cls_name = self.__class__.__name__

        for n,c in self.master.controls.items():
            if n.startswith(cls_name) and n != cls_name:
                c.destroy()

        #sets what controls will be in this frame
        control_classes = self.get_controls()
        
        #remove from grid and forget settings
        if self.impairment == 'None':
            self.grid_forget()
        else:
            #add back to grid
            self.grid(column=0, row=self.row_num, columnspan=4, sticky='NSEW',
                  padx=PADX, pady=PADY)
            self.set_name(self.impairment)
        
        #initializes controls
        controls = {}
        for row in range(len(control_classes)):
            c = control_classes[row](master=self, row=row)
            
            controls[c.__class__.__name__] = c
        
        self.master.controls = controls
    
    def set_name(self,impairment):
        if impairment:
            self.update_title(f'{impairment} Settings')
        #else:
        #    self.update_title('')

class ChannelImpairmentSettings(ImpairmentSettings):    
    
    def __init__(self, master, row, *args, **kwargs):
        
        self.impairment_name = 'ChannelImpairment'
        
        super().__init__(master, row, *args, **kwargs)

class PreImpairment(LabeledControl):
    """impairment to use before audio goes into the channel"""

    def __init__(self, master, row, *args, **kwargs):
        
        self.text = 'Pre Impairment :'
        self.MCtrl = ttk.Menubutton
        self.do_font_scaling = False
        
        super().__init__(master, row, *args, **kwargs)
        
        self.menu = tk.Menu(self.m_ctrl, tearoff=False)
        
        self.m_ctrl.configure(menu=self.menu)
        
        try:
            impairments = QoEsim.get_impairment_names('audio')
        except Exception as e:
            show_error(e)
        
        else:
            #add None to the list
            self.menu.add_command(label='None',
                                  command=tk._setit(self.btnvar, 'None'))
            # get channel_techs to use as menu options
            for i in impairments:
                self.menu.add_command(label=i,
                        command=tk._setit(self.btnvar, i))
                        
class PreImpairmentSettings(ImpairmentSettings):    
    
    def __init__(self, master, row, *args, **kwargs):
        
        self.impairment_name = 'PreImpairment'
        
        super().__init__(master, row, *args, **kwargs)

class PostImpairment(LabeledControl):
    """impairment to use after audio goes through the channel"""

    def __init__(self, master, row, *args, **kwargs):
        
        self.text = 'Post Impairment :'
        self.MCtrl = ttk.Menubutton
        self.do_font_scaling = False
        
        super().__init__(master, row, *args, **kwargs)
        
        self.menu = tk.Menu(self.m_ctrl, tearoff=False)
        
        self.m_ctrl.configure(menu=self.menu)
        
        try:
            impairments = QoEsim.get_impairment_names('audio')
        except Exception as e:
            show_error(e)
        
        else:
            #add None to the list
            self.menu.add_command(label='None',
                                  command=tk._setit(self.btnvar, 'None'))
            # get channel_techs to use as menu options
            for i in impairments:
                self.menu.add_command(label=i,
                        command=tk._setit(self.btnvar, i))

class PostImpairmentSettings(ImpairmentSettings):    
    
    def __init__(self, master, row, *args, **kwargs):
        
        self.impairment_name = 'PostImpairment'
        
        super().__init__(master, row, *args, **kwargs)


# ---------------------------------- Misc ------------------------------------

class SignalOverride():
    
    def sig_handler(self, *args, **kwargs):
        #override signal's ability to close the application
        
        raise Abort_by_User()
        
def format_audio_files(path_= '', files=[]):
    """
    

    Parameters
    ----------
    path_ : str, optional
        a path to append all files to. The default is ''.
    files : list of str, optional
        path to each file. The default is [].

    Returns
    -------
    newpath : str
        the absolute path containing all the files.
    newfiles : list of str
        the paths relative to newpath containing the files.

    """
    
    if not files:
        return path_, ['<entire audio folder>']
    
    if len(files) == 1:
        f = path.join(path_, files[0])
        
        if path.isfile(f):
        
            newpath, newfile = path.split(f)
            
            return newpath, [newfile]
        
        elif path.isdir(f):
            
            return f, ['<entire audio folder>']
        else:
            
            return '', []
    
    newpath = path.commonpath([path.join(path_, f) for f in files])
    
    newfiles = [path.relpath(f, newpath) for f in files]
    
    return newpath, newfiles
