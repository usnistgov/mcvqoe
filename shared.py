# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 11:03:39 2021

@author: MkZee
"""
import pdb
from os import path

import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as fdl

import loadandsave
from tk_threading import show_error, Abort_by_User


from mcvqoe.simulation.QoEsim import QoEsim
from mcvqoe import simulation

PADX = 10
PADY = 10

FONT_SIZE = 10


class ScrollableFrame(ttk.Frame):
    
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
    Base class for frames to configure and run a test
    
    PARAMETERS
    ----------
    
    btnvars : TkVarDict
        loads and stores the values in the controls
    
    
    
    ATTRIBUTES
    ----------
    
    text : str
        The caption of the frame
    
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
            
            
        
        
        
    def get_controls(self) -> iter:
        """subclasses should override this
        """



class SubCfgFrame(TestCfgFrame):
    """Makes a subframe for controls grouped together
    
    """
    text = ''
    
    def __init__(self, master, row, *args, **kwargs):
        
        
    
        super().__init__(master.btnvars, master, *args, **kwargs)
        
        
        self.grid(column=0, row=row, columnspan=4, sticky='NSEW',
                  padx=PADX, pady=PADY)
        
        master.controls.update(self.controls)

    

class AdvancedConfigGUI(tk.Toplevel):
    """A Toplevel window containing advanced options for the test
    

    """
    text = ''
    
    def __init__(self, master, btnvars, *args, **kwargs):
        
        
        super().__init__(master, *args, **kwargs)
        
        self.traces_ = []
        
        self.title(self.text)
        #sets the controls in this window
        controls = list(self.get_controls())
        controls.append(_advanced_submit)
        
        self.btnvars = btnvars
        
        #Sets window on top of other windows
        self.focus_force()
        self.grab_set()
        #self.attributes('-topmost', True)
        
        self.controls = master.controls
        #initializes controls
        for row in range(len(controls)):
            c = controls[row](master=self, row=row)
            
            self.controls[c.__class__.__name__] = c
            
        
        
        
        # return key closes window
        self.bind('<Return>', lambda *args : self.destroy())
        
        
        
        
        
            
    def get_controls(self):
        pass
    
    def destroy(self):
        super().destroy()
        
        for var, trace_id in self.traces_:
            var.trace_remove('write', trace_id)
                

        
    

class LabeledControl():
    """A one-row grid consisting of a label, control, and optional 2nd control
    
    Sub-classes should redefine any of the class variables, as well as the
        setup() method
    
    
    
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
        pass
    
    
    
    def __init__(self, master, row):
        self.master = master
        
        
        
    
        ttk.Label(master, text=self.text).grid(
            padx=self.padx, pady=self.pady, column=0, row=row, sticky='E')
        
        MCtrlkwargs = self.MCtrlkwargs.copy()
        MCtrlargs = self.MCtrlargs.copy()
        RCtrlkwargs = self.RCtrlkwargs.copy()
        
        
        
        # get tcl variable 
        if self.__class__.__name__ in master.btnvars:
            self.btnvar = master.btnvars[self.__class__.__name__]
        
            
        
        
        
        # help button
        if self.__class__.__doc__:
            HelpIcon(master, tooltext=self._get_help()).grid(
                column=1, row=row, padx=0, pady=self.pady, sticky='NW')
            
            
            
            
        self.setup()
        #some controls require more flexibility, so they don't use self.MCtrl
        if self.MCtrl:
            try:
                btnvar = self.btnvar
            except AttributeError:
                btnvar = None
            if btnvar is None:
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
        
        
        
    def on_button(self):
        pass
            


class HelpIcon(ttk.Button):
    """Shows the control's doc when you hover over or select the icon"""
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
        if not self.tw:
            return
        self.tw.destroy()
        self.tw = None
        
def _get_master(m, targets = (tk.Tk, tk.Toplevel)):
        
        while hasattr(m, 'master'):
            if isinstance(m, targets):
                return m
            m = m.master
        

class ToolTip(tk.Toplevel):
    
    def __init__(self, master, text, style='McvToolTip.TLabel'):
        super().__init__(master)
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










class LabeledNumber(LabeledControl):
    
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
    association = {}
    do_font_scaling = False
    MCtrl = _MultiChoice_Frame
    
    def __init__(self, *args, **kwargs):
        self.MCtrlkwargs = self.MCtrlkwargs.copy()
        self.MCtrlkwargs['association'] = self.association
        
        super().__init__(*args, **kwargs)



class LabeledCheckbox(LabeledControl):
    
    MCtrl = ttk.Checkbutton
    do_font_scaling = False
    variable_arg = 'variable'
    
    def __init__(self, *args, **kwargs):
        
        
        self.MCtrlkwargs = {'text': self.text}
        
        self.text = ''
        
        super().__init__(*args, **kwargs)



















#---------------------------controls------------------------------------------
















class audio_files(LabeledControl):
    """Audio files to use for testing.
    
    If left blank, all the files in "Audio Folder" are used. """
    
    text = 'Audio File(s):'
    RCtrl = ttk.Button
    RCtrlkwargs = {
        'text' : 'Browse...'
        }
    
    
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
            
            
    
            
            
class audio_path(LabeledControl):
    """The source folder containing the audio files."""
    
    
    text = 'Audio Folder:'
    MCtrl = ttk.Entry
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'Browse Entire Folder'}
    
    
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
            
            
            
            
            
class trials(LabeledControl):
    """Number of trials to use for test."""
    text = 'Number of Trials:'
       
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 1, 'to' : 2**15 - 1}
    
    
class outdir(LabeledControl):
    """Location to store all output files"""
    
    text='Output Folder:'
    
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'Browse...'}
    
    def on_button(self):
        dirp = fdl.askdirectory(parent=self.master)
        if dirp:
            dirp = path.normpath(dirp)
            self.btnvar.set(dirp)
            
            
    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        


class overplay(LabeledControl):
    """The number of seconds to play silence after the audio is complete.
    This allows for all of the audio to be recorded when there is delay
    in the system"""
    
    
    text='Overplay Time (sec):'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'increment':0.01, 'from_':0, 'to':2**15 -1}
    

class ptt_gap(LabeledControl):
    """Time to pause after completing one trial and starting the next."""

    text = 'Gap Between Trials:'
    
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
    
class SaveAudio(MultiChoice):
    
    text = 'Save Audio:'
    
    association = {'all_audio' : 'All audio',
                   'rx_only'   : 'Rx audio only',
                   'no_audio'  : 'No audio',
                   }
    



   
class RadioCheck(SubCfgFrame):
    text = 'Regular Radio Checks'
    
    def get_controls(self):
        return (
            _limited_trials,
            pause_trials,
            )

class _limited_trials(LabeledControl):
    """When disabled, sets the number of pause_trials to infinite"""
    
    
    MCtrl = ttk.Checkbutton
    do_font_scaling = False
    variable_arg = 'variable'
    
    def __init__(self, master, row, *args, **kwargs):
        self.MCtrlkwargs = {'text': 'Enable Radio Checks',}
                
        self.btnvar = tk.BooleanVar()
        
        super().__init__(master, row, *args, **kwargs)
        
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
        
        
        
    
        
class pause_trials(LabeledControl):
    """Number of trials to run before pausing to perform a radio check."""
    
    text = 'Trials between check:'
    
       
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 1, 'to' : 2**15 - 1}
    
    
    
    
class dev_dly(LabeledControl):
    """Delay in seconds of the audio path with no communication device
    present."""
    
    text = 'Device Delay:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.001}
    
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'Calibrate'}
    
    def on_button(self):
        self.master.btnvars['dev_dly'].set(68)
        
        
        
        


class time_expand(SubCfgFrame):
    text = 'Time Expand'
    
    
    
    def __init__(self, master, row, **kwargs):
        
        super().__init__(master, row, **kwargs)
    
    def get_controls(self):
        
        return (
            _time_expand_i,
            _time_expand_f,
            )

class _time_expand_i(LabeledControl):
    """Length of time, in seconds, of extra
    audio to send BEFORE the keyword to ABC_MRT16. Adding time protects
    against inaccurate M2E latency calculations and misaligned audio."""
    
    text = 'Expand Before:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
    
class _time_expand_f(LabeledControl):
    """Length of time, in seconds, of extra
    audio to send AFTER the keyword to ABC_MRT16. Adding time protects
    against inaccurate M2E latency calculations and misaligned audio."""
    
    text = 'Expand After:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}

    
    
class bgnoise_file(LabeledControl):
    """This is used to read in a noise file to be mixed with the
    test audio. Default is no background noise."""

    text = 'Noise File:'
    
    RCtrl = ttk.Button
    RCtrlkwargs = {'text' : 'Browse...'}
    
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

class ptt_wait(LabeledControl):
    """The amount of time to wait in seconds between pushing the
    push to talk button and starting playback. This allows time
    for access to be granted on the system."""

    text = 'PTT Wait Time (sec):'
    
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'increment' : 0.01, 'from_' : 0, 'to' : 2**15 - 1}

              
                                  






class advanced(LabeledControl):
    text = ''
    
    MCtrl = None
    RCtrl = ttk.Button       
    RCtrlkwargs = {'text': 'Advanced...'}
    toplevel = None
    
    no_value = True
    
    def on_button(self):
        self.toplevel(master=self.master, btnvars=self.master.btnvars)

    

class _advanced_submit(LabeledControl):
    
    #closes the advanced window
    MCtrl = None
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'OK'}
    
    def on_button(self):
        self.master.destroy()
    
    
# advanced groups

class BgNoise(SubCfgFrame):
    text = 'Background Noise'
    
    def get_controls(self):
        return (bgnoise_file,
                bgnoise_volume)

       


















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

#HARDWARE SETTINGS WINDOW
class HdwSettings(AdvancedConfigGUI):
    text = 'Hardware Settings'
    
    
    def get_controls(self):
        return (
            AudioSettings,
            overplay,
            radioport,
            )
    
    


class radioport(LabeledControl):
    """Port to use for radio interface. Defaults to the first
    port where a radio interface is detected"""
    
    text = 'Radio Port:'

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


        
        
        







class _SimPrototype(QoEsim, simulation.PBI):
    def __init__(self):
        QoEsim.__init__(self)
        simulation.PBI.__init__(self)


#SIMULATION SETTINGS WINDOW
class SimSettings(AdvancedConfigGUI):
    
    
    text = 'Simulation Settings'
    
    def get_controls(self):
        return (
            channel_tech,
            channel_rate,
            
            overplay,
            
            m2e_latency,
            access_delay,
            rec_snr,
            PTT_sig_freq,
            PTT_sig_aplitude,
            
            Probabilityizer,            
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
            rates = QoEsim().get_channel_techs()
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
            
            default, rates = QoEsim().get_channel_rates(chan_tech)
            
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
    
class PTT_sig_aplitude(LabeledControl):
    """Amplitude of the PTT signal from the play_record method."""
    text = 'PTT Signal Amplitude:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_':0, 'to' : 2**15-1, 'increment':0.1}






class Probabilityizer(SubCfgFrame):
    
    text = 'Probabilityizer'
    
    def __init__(self, master, *args, **kwargs):
        
        super().__init__(master, *args, **kwargs)
        
        btv = self.btnvars['_enable_PBI']
        trace_id = btv.trace_add('write',lambda *a,**k:self.update())
        
        # mark the trace for deletion, otherwise causes errors
        _get_master(self).traces_.append((btv, trace_id))
        
        self.update()
    def get_controls(self):
        return (
            _enable_PBI,
            P_a1,
            P_a2,
            P_r,
            interval,
            )
    
    def update(self):
        
        state = ('disabled', '!disabled')[self.btnvars['_enable_PBI'].get()]
        
        # disable other controls
        for ctrlname, ctrl in self.controls.items():
            if ctrlname == '_enable_PBI':
                continue
            
            ctrl.m_ctrl.configure(state=state)
        


class _enable_PBI(LabeledCheckbox):
    
    text = 'Enable P.B.I Impairments'
    
    


class P_a1(LabeledNumber):
    min_ = 0
    max_ = 1
    increment = 0.01
    text = 'P_a1:'

class P_a2(LabeledNumber):
    min_ = 0
    max_ = 1
    increment = 0.01
    text = 'P_a2:'

class P_r(LabeledNumber):
    min_ = 0
    max_ = 1
    increment = 0.01
    text = 'P_r:'

class interval(LabeledNumber):
    
    text = 'P_Interval:'
    
    





# ---------------------------------- Misc ------------------------------------



class SignalOverride():
    
    def sig_handler(self, *args, **kwargs):
        #override signal's ability to close the application
        
        raise Abort_by_User()
        
        
class InvalidParameter(ValueError):
    """Raised when a user fails to input a required parameter.
    """
    
    def __init__(self, parameter, param_loc=None, message=None, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        
        self.param_loc = param_loc
        self.parameter = parameter
        self.message = message
    

        
        
        
        
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

