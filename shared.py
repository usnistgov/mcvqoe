# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 11:03:39 2021

@author: MkZee
"""

import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as fdl

from mcvqoe.simulation.QoEsim import QoEsim

PADX = 10
PADY = 10

FONT_SIZE = 10
















class TestCfgFrame(ttk.LabelFrame):
    """
    Base class to configure and run a  Test
    
    btnvars : StringVarDict
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
        for row in range(len(controls)):
            controls[row](master=self, row=row)
        
        
        
    def get_controls(self) -> iter:
        """subclasses should override this
        """



class SubCfgFrame(TestCfgFrame):
    """Makes a subframe for controls grouped together
    
    """
    text = ''
    
    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master.btnvars, master, *args, **kwargs)
        
        self.grid(column=0, row=row, columnspan=3, sticky='NSEW',
                  padx=PADX, pady=PADY)



class AdvancedConfigGUI(tk.Toplevel):
    """Advanced options for the M2E test
    

    """
    text = ''
    
    def __init__(self, master, btnvars, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        
        self.title(self.text)
        #sets the controls in this window
        controls = list(self.get_controls())
        controls.append(_advanced_submit)
        
        self.btnvars = btnvars
        
        #Sets window on top of other windows
        self.focus_force()
        self.grab_set()
        #self.attributes('-topmost', True)
        
        #initializes controls
        for row in range(len(controls)):
            controls[row](master=self, row=row)
            
        
        
        
        # return key closes window
        self.bind('<Return>', lambda *args : self.destroy())
        
        
        
            
    def get_controls(self):
        pass
    


        
    

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
    
    help_ = None
    
    def setup(self):
        pass
    
    
    
    def __init__(self, master, row):
        self.master = master
        
        
        
    
        ttk.Label(master, text=self.text).grid(
            padx=self.padx, pady=self.pady, column=0, row=row, sticky='E')
        
        MCtrlkwargs = self.MCtrlkwargs.copy()
        MCtrlargs = self.MCtrlargs.copy()
        RCtrlkwargs = self.RCtrlkwargs.copy()
        
        try:
            self.btnvar = master.btnvars[self.__class__.__name__]
        except KeyError:
            self.btnvar = None
            
        
        
        
        # help button
        if self.__class__.__doc__:
            HelpIcon(master, tooltext=self.__class__.__doc__).grid(
                column=1, row=row, padx=0, pady=self.pady, sticky='NW')
            
            
            
            
        self.setup()
        #some controls require more flexibility, so they don't use self.MCtrl
        if self.MCtrl:
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
        rootx = self._get_master().winfo_rootx()
        
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
        
    def _get_master(self):
        m = self
        while hasattr(m, 'master'):
            m = m.master
            if isinstance(m, (tk.Tk, tk.Toplevel)):
                return m
        

class ToolTip(tk.Toplevel):
    
    def __init__(self, master, text):
        super().__init__(master)
        lf = ttk.Frame(self, style='McvToolTip.TFrame')
        lf.pack()
        
        ttk.Label(lf, text=text, style='McvToolTip.TLabel').pack(
            padx=PADX, pady=PADY)
        
        #removes window title-bar, taskbar icon, etc
        self.wm_overrideredirect(1)
        
        # temporarily hides window to prevent sudden movement
        self.withdraw()
        
        # solidifies the window's size to ensure correct placement on screen
        self.update_idletasks()
    
    def show(self):self.deiconify()


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
    
        ttk.Scale(master, variable=self.btnvar,
            from_=0, to=1).grid(
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
        
        
        #initialize
        for val, text in association.items():
            ttk.Radiobutton(self, variable=textvariable, value=val,
                text=text).pack(fill=tk.X)

class MultiChoice(LabeledControl):
    association = {}
    do_font_scaling = False
    MCtrl = _MultiChoice_Frame
    
    def __init__(self, *args, **kwargs):
        self.MCtrlkwargs = self.MCtrlkwargs.copy()
        self.MCtrlkwargs['association'] = self.association
        
        super().__init__(*args, **kwargs)



















#---------------------------controls------------------------------------------
















class audio_files(LabeledControl):
    """Audio files to use for test"""
    
    text = 'Audio File(s):'
    RCtrl = ttk.Button
    RCtrlkwargs = {
        'text' : 'Browse...'
        }
    
    
    
    
    
    def on_button(self):
        fp = fdl.askopenfilenames(parent=self.master,
                initialfile=self.btnvar.get(),
                filetypes=[('WAV files', '*.wav')])
        if fp:
            str_ = ', '
            self.btnvar.set(str_.join(fp))
            
            
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







class radioport(LabeledControl):
    """Port to use for radio interface. Defaults to the first
    port where a radio interface is detected"""
    
    text = 'Radio Port:'
    
    
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





class advanced(LabeledControl):
    text = ''
    
    MCtrl = None
    RCtrl = ttk.Button       
    RCtrlkwargs = {'text': 'Advanced...'}
    toplevel = None
    
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
class BgNoise(ttk.LabelFrame):
    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, *args, text='Background Noise', **kwargs)
        
        self.btnvars = master.btnvars
        
        controls = (bgnoise_file, bgnoise_volume)
        
        for row_ in range(len(controls)):
            controls[row_](master=self, row=row_)
        
        self.grid(column=0, row=row, padx=PADX, pady=PADY, columnspan=3,
                  sticky='WE')
        

class AudioSettings(ttk.LabelFrame):
    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, *args, text='Audio Settings', **kwargs)
        
        self.btnvars = master.btnvars
        
        controls = (blocksize, buffersize)
        
        for row_ in range(len(controls)):
            controls[row_](master=self, row=row_)
        
        self.grid(column=0, row=row, padx=PADX, pady=PADY, columnspan=3,
                  sticky='WE')

class TimeExpand(SubCfgFrame):
    text = 'Time Expand'
    
    def get_controls(self):
        return (
            _time_expand_i,
            _time_expand_f,
            )

















#------------------------ Global settings for hdw/simulation------------------



class HdwSettings(AdvancedConfigGUI):
    text = 'Hardware Settings'
    







class SimSettings(AdvancedConfigGUI):
    text = 'Simulation Settings'
    
    def get_controls(self):
        return (
            channel_tech,
            channel_rate,        
            )

class channel_tech(LabeledControl):
    

    
    def __init__(self, master, row):
        
        self.text = 'Channel Tech:'
        self.MCtrl = ttk.Menubutton
        self.do_font_scaling = False
        
        super().__init__(master, row)
        
        self.menu = tk.Menu(self.m_ctrl, tearoff=False)
        
        self.m_ctrl.configure(menu=self.menu)
        
        # get channel_techs to use as menu options
        for tech_ in QoEsim().get_channel_techs():
            self.menu.add_command(label=tech_,
                    command=tk._setit(self.btnvar, tech_))
        
        
        
    
class channel_rate(LabeledControl):
    
    
    def __init__(self, master, row):
        
        self.text = 'Channel Rate:'
        self.MCtrl = ttk.Menubutton
        
        self.do_font_scaling = False
        
        super().__init__(master, row)
        
        self.menu = tk.Menu(self.m_ctrl, tearoff=False)
        self.m_ctrl.configure(menu=self.menu)
        
        #track selection of channel_tech
        self.master.btnvars['channel_tech'].trace_add('write', self.update)
        
        #fill menu with options
        self.update()
        

    
    def update(self, *args, **kwargs):
        
        chan_tech = self.master.btnvars['channel_tech'].get()
        
        self.menu.delete(0, 'end')
        
        rates = QoEsim().get_channel_rates(chan_tech)
        for rate in rates:
                       
            
            #add a dropdown list option
            self.menu.add_command(label=repr(rate),
                        command=tk._setit(self.btnvar, repr(rate)))









# ------- Misc -------------



class SignalOverride():
    
    def sig_handler(self, *args, **kwargs):
        #override signal's ability to close the application
        
        raise Abort_by_User()
    
class Abort_by_User(BaseException):
    """Raised when user presses 'Abort test'
    
    Inherits from BaseException because it is not an error and therefore
    won't be treated as such
    """
    def __init__(self, *args, **kwargs):
        super().__init__('Test was aborted by the user', *args, **kwargs)