# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 11:03:39 2021

@author: MkZee
"""

import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as fdl

PADX = 10
PADY = 10

FONT_SIZE = 11

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
        
        
        
    def get_controls() -> iter:
        """subclasses should override this
        """



class SubCfgFrame(TestCfgFrame):
    """Makes a subframe for controls grouped together
    
    """
    text = ''
    
    def __init__(self, master, row, *args, **kwargs):
        super.__init__(self, master.btnvars, *args, **kwargs)
        
        self.grid(column=0, row=row, columnspan=3, sticky='NSEW',
                  padx=PADX, pady=PADY)



class AdvancedConfigGUI(tk.Toplevel):
    """Advanced options for the M2E test
    

    """    
    
    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        self.title('M2E Latency - Advanced')
        #sets the controls in this window
        controls = list(self.get_controls())
        controls.append(_advanced_submit)
        
        self.btnvars = btnvars
        
        #Sets window on top of other windows
        self.attributes('-topmost', True)
        
        #initializes controls
        for row in range(len(controls)):
            controls[row](master=self, row=row)
            
        
        
        
        # return key closes window
        self.bind('<Return>', lambda *args : self.destroy())
        
        #sets focus on the window
        self.focus_force()
        
            
    def get_controls():
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
            self.MCtrl(master, *MCtrlargs, **MCtrlkwargs).grid(
                column=1, row=row, padx=self.padx, pady=self.pady, sticky='WE')
        
        
        if self.RCtrl:
            #add command to button
            if self.RCtrl in (ttk.Button, tk.Button):
                RCtrlkwargs['command'] = self.on_button
            
            # initialize the control
            self.RCtrl(master, **RCtrlkwargs).grid(
                padx=self.padx, pady=self.pady, column=2, row=row, sticky='WE')
            
            
            
    def on_button(self):
        pass
            


#controls
class audio_files(LabeledControl):
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
    text = 'Number of Trials:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 1, 'to' : 2**15 - 1}
    
class outdir(LabeledControl):
    text='Output Folder:'
    
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'Browse...'}
    
    def on_button(self):
        dirp = fdl.askdirectory(parent=self.master)
        if dirp:
            self.btnvar.set(dirp)
            
            
    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        
        


class radioport(LabeledControl):
    text = 'Radio Port:'
    
    
class bgnoise_file(LabeledControl):
    text = 'Noise File:'
    
    RCtrl = ttk.Button
    RCtrlkwargs = {'text' : 'Browse...'}
    
    def on_button(self):
        fp = fdl.askopenfilename(parent=self.master,
            initialfile=self.btnvar.get(),
            filetypes=[('WAV files', '*.wav')])
        if fp:
            self.btnvar.set(fp)


class bgnoise_volume(LabeledControl):
    text = 'Volume:'
    RCtrl = None
    MCtrl = None
    # slider does not accept font size
    do_font_scaling = False    
    
    
    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, row, *args, **kwargs)
        self.txtvar = _bgnoise_volume_percentage()
        self.on_change()
        
        self.btnvar.trace_add('write', self.on_change)
    
        ttk.Label(master, textvariable=self.txtvar).grid(
            column=2, row=row, sticky='W')
    
        ttk.Scale(master, variable=self.btnvar,
            from_=0, to=1).grid(
            column=1, row=row, padx=self.padx, pady=self.pady, sticky='WE')
    
    def on_change(self, *args, **kwargs):
        #updates the percentage to match the value of the slider
        self.txtvar.set(self.btnvar.get())

class _bgnoise_volume_percentage(tk.StringVar):
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
            
        
class ptt_wait(LabeledControl):
    text = 'PTT Wait Time (sec):'
    
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'increment' : 0.01, 'from_' : 0, 'to' : 2**15 - 1}

              
                                  
class blocksize(LabeledControl):
    text = 'Block Size:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_':1, 'to':2**15 -1}
    

class buffersize(LabeledControl):
    text='Buffer Size:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_':1, 'to':2**15 -1}





class advanced(LabeledControl):
    text = ''
    
    MCtrl = None
    RCtrl = ttk.Button       
    RCtrlkwargs = {'text': 'Advanced...'}
    
    def on_button(self):
        #M2EAdvancedConfigGUI(btnvars=self.master.btnvars)
        pass

    

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











    
class Abort_by_User(BaseException):
    """Raised when user presses 'Abort test'
    
    Inherits from BaseException because it is not an error and therefore
    won't be treated as such
    """
    def __init__(self, *args, **kwargs):
        super().__init__('Test was aborted by the user', *args, **kwargs)