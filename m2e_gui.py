# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 08:52:09 2021

@author: MkZee
"""

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fdl
    


class M2eFrame(tk.LabelFrame):
    """
    Gui to configure and run a M2E Latency Test
    
    strvars : StringVarDict
    loads and stores the values in the controls
    
    """
    # Setting the padding (distance between controls)
    pady = 10
    padx = 5
      
    
    def __init__(self, btnvars, text='Mouth-to-Ear Latency Test',
                 *args, **kwargs):
        #sets what controls will be in this frame
        controls = (
            test,
            audio_file,
            trials,
            bgnoise_file,
            bgnoise_volume,
            ptt_wait,
            overplay,
            outdir,
            advanced
            )
        
        
        
        super().__init__(*args, text=text, **kwargs)
        #option functions will get and store their values in here
        self.btnvars = btnvars
        
        
        #initialize controls
        for row in range(len(controls)):
            controls[row](self, row)
        
   
            
class M2EAdvancedConfigGUI(tk.Toplevel):
    """Advanced options for the M2E test
    

    """    
    
    padx=5
    pady=10
    def __init__(self, btnvars, *args, **kwargs):
        super().__init__()
        
        #sets the controls in this window
        controls = (
            radioport,
            blocksize,
            buffersize,
            _advanced_submit
            )
        
        self.btnvars = btnvars
        
        #Sets window on top of other windows
        self.attributes('-topmost', True)
        
        #initializes controls
        for row in range(len(controls)):
            controls[row](master=self, r=row)
        
            
        
        
        
        
        
        
        
        
        #------------------ Controls ----------------------
class LabeledControl():
    
    text = ''
    
    
    MCtrl = ttk.Entry
    MCtrlargs = []
    MCtrlkwargs = {}
    
    variable_arg = 'textvariable'
    
    #usually the browse button
    RCtrl = None
    RCtrlkwargs = {}
    
    padx = 5
    pady = 10
    
    def __init__(self, master, row):
        self.master = master
        
    
        ttk.Label(master, text=self.text).grid(
            column=0, row=row, sticky='E')
        
        MCtrlkwargs = self.MCtrlkwargs.copy()
        MCtrlargs = self.MCtrlargs.copy()
        RCtrlkwargs = self.RCtrlkwargs.copy()
        
        try:
            self.btnvar = master.btnvars[self.__class__.__name__]
        except KeyError:
            self.btnvar = None
            
            
        # some controls require the textvariable=... to be positional
        
        #some controls require more flexibility, so they don't use self.MCtrl
        if self.MCtrl:
            if self.variable_arg:
                MCtrlkwargs[self.variable_arg] = self.btnvar
            
            else:
                MCtrlargs.insert(0, self.btnvar)
                
            self.MCtrl(master, *MCtrlargs, **MCtrlkwargs).grid(
                column=1, row=row, padx=self.padx, pady=self.pady, sticky='WE')
        
        
        if self.RCtrl:
            #add command to button
            if self.RCtrl in (ttk.Button, tk.Button):
                RCtrlkwargs['command'] = self.on_button
            
            self.RCtrl(master, **RCtrlkwargs).grid(
                column=2, row=row, sticky='WE')
            
            
            
    def on_button(self):
        pass
            


class test(LabeledControl):
    text = 'Test Type:'
    
    variable_arg = None # indicates the argument is positional
    MCtrl = ttk.OptionMenu
    MCtrlargs = ['', 'm2e_1loc', 'm2e_2loc_rx', 'm2e_2loc_tx']
    
    
class audio_file(LabeledControl):
    
    def on_button(self):
        fp = fdl.askopenfilename(parent=self.master,
                initialfile=self.btnvar.get(),
                filetypes=[('WAV files', '*.wav')])
        if fp:
            self.btnvar.set(fp)
    
    
    text='Audio File:'
    RCtrl = ttk.Button
    RCtrlkwargs = {
        'text'   : 'Browse...'
        }
    
    
class trials(LabeledControl):
    text = 'Number of Trials:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 1, 'to' : 2**15 - 1}
    

class radioport(LabeledControl):
    text = 'Radio Port:'
    
    
    """
                    
def radioport2(master, r):                    
    # Radio Port
    ttk.Label(master, text='Radio Port:').grid(column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['radioport']).grid(
                column=1, row=r, sticky='W',
                padx=master.padx, pady=master.pady)
    
    """
    
class bgnoise_file(LabeledControl):
    text = 'Background Noise File:'
    
    RCtrl = ttk.Button
    RCtrlkwargs = {'text' : 'Browse...'}
    
    def on_button(self):
        fp = fdl.askopenfilename(parent=self.master,
            initialfile=self.btnvar.get(),
            filetypes=[('WAV files', '*.wav')])
        if fp:
            self.btnvar.set(fp)


class bgnoise_volume(LabeledControl):
    text = 'Background Noise Volume:'
    RCtrl = None
    MCtrl = None
    
    def __init__(self, master, r, *args, **kwargs):
        super().__init__(master, r, *args, **kwargs)
        txtvar = _bgnoise_volume_percentage()
        txtvar.set(self.btnvar.get())
    
        ttk.Label(master, textvariable=txtvar).grid(
            column=2, row=r, sticky='W')
    
        ttk.Scale(master, variable=self.btnvar,
            from_=0, to=1, command=txtvar.set).grid(
            column=1, row=r, padx=self.padx, pady=self.pady, sticky='WE')
    
          

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

"""
def ptt_wait2(master, r):                            
    # PTT Wait time
    ttk.Label(master, text='PTT Wait Time (sec):').grid(
        column=0, row=r, sticky='E')
    
    ttk.Spinbox(master, textvariable=master.btnvars['ptt_wait'], increment=0.01,
        from_=0, to=2**15-1).grid(column=1, row=r,
                    padx=master.padx, pady=master.pady, sticky='W')
"""                 
                                  
class blocksize(LabeledControl):
    text = 'Block Size:'
    

class buffersize(LabeledControl):
    text='Buffer Size:'
    
class overplay(LabeledControl):
    text='Overplay Time (sec):'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'increment':0.01, 'from_':0, 'to':2**15 -1}

class outdir(LabeledControl):
    text='Output Folder:'
    
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'Browse...'}
    
    def on_button(self):
        dirp = fdl.askdirectory(parent=self.master)
        if dirp:
            self.btnvar.set(dirp)

class advanced(LabeledControl):
    text = ''
    
    MCtrl = None
    RCtrl = ttk.Button       
    RCtrlkwargs = {'text': 'Advanced...'}
    
    def on_button(self):
        M2EAdvancedConfigGUI(btnvars=self.master.btnvars)
            
    
    
def blocksize2(master, r):
    ttk.Label(master, text='Block Size:').grid(
        column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['blocksize']).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')
    

def buffersize2(master, r):
    ttk.Label(master, text='Buffer Size:').grid(
        column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['buffersize']).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')

def overplay2(master, r):
    ttk.Label(master, text='Overplay Time (sec):').grid(
        column=0, row=r, sticky='E')
    
    ttk.Spinbox(master, textvariable=master.btnvars['overplay'],
        increment=0.01, from_=0, to=2**15-1).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')
    
    
def outdir2(master, r):
    ttk.Label(master, text='Output Folder:').grid(
        column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['outdir']).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')
    
    ttk.Button(master, text='Browse...', command=master.choose_outdir).grid(
        column=2, row=r, sticky='W')
    
    

class _advanced_submit(LabeledControl):
    
    #closes the advanced window
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'OK'}
    
    
    
    
    
