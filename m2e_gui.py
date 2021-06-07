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
            controls[row](self, r=row)
        
   
 #button functions
    def choose_audio_file(self):
        fp = fdl.askopenfilename(parent=self,
                initialfile=self.btnvars['audio_file'].get(),
                filetypes=[('WAV files', '*.wav')])
        if fp:
            self.btnvars['audio_file'].set(fp)
    
    def choose_bgnoise_file(self):
        fp = fdl.askopenfilename(parent=self,
            initialfile=self.btnvars['bgnoise_file'].get(),
            filetypes=[('WAV files', '*.wav')])
        if fp:
            self.btnvars['bgnoise_file'].set(fp)
            
            
    def choose_outdir(self):
        dirp = fdl.askdirectory(parent=self)
        if dirp:
            self.btnvars['outdir'].set(dirp)
    
    def show_advanced(self):
        M2EAdvancedConfigGUI(btnvars=self.btnvars)
                        
      
            
            
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
        
            

#controls
def test(master, r):
    # Test Type
    c = ttk.Label(master, text='Test Type:')
    c.grid(column=0, row=r, sticky='E')
    
    ttk.OptionMenu(master, master.btnvars['test'],"",
                   'm2e_1loc', 'm2e_2loc_rx', 'm2e_2loc_tx').grid(
                       column=1, row=r, pady=master.pady, padx=master.padx)
    
def audio_file(master, r):
    # Audio File                
    ttk.Label(master, text='Audio File:').grid(column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['audio_file']).grid(
        column=1, row=r, pady=master.pady, padx=master.padx, sticky='W')
    
    ttk.Button(master, text='Browse...',
        command=master.choose_audio_file).grid(column=2, row=r, sticky='W')
    
def trials(master, r):
    # Number of trials
    ttk.Label(master, text='Number of Trials:').grid(
        column=0, row=r, sticky='E')
    
    ttk.Spinbox(master, textvariable=master.btnvars['trials'],
                from_=1, to=2**15 - 1).grid(
        column=1, row=r, padx=master.padx, pady=master.pady)
                    
def radioport(master, r):                    
    # Radio Port
    ttk.Label(master, text='Radio Port:').grid(column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['radioport']).grid(
                column=1, row=r, sticky='W',
                padx=master.padx, pady=master.pady)
    
def bgnoise_file(master, r):
    # bg noise File
    ttk.Label(master, text='Background Noise File:').grid(
        column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['bgnoise_file']).grid(
        column=1, row=r, sticky='W', padx=master.padx, pady=master.pady)
    
    ttk.Button(master, text='Browse...',
        command=master.choose_bgnoise_file).grid(column=2, row=r, sticky='W')
    
def bgnoise_volume(master, r):
    # bg noise volume
    ttk.Label(master, text='Background Noise Volume:').grid(
        column=0, row=r, sticky='E')
    
          
    txtvar = _bgnoise_volume_percentage()
    txtvar.set(master.btnvars['bgnoise_volume'].get())
    
    ttk.Label(master, textvariable=txtvar).grid(
        column=2, row=r, sticky='W')
    
    ttk.Scale(master, variable=master.btnvars['bgnoise_volume'],
        from_=0, to=1, command=txtvar.set).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')
            

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
            
def ptt_wait(master, r):                            
    # PTT Wait time
    ttk.Label(master, text='PTT Wait Time (sec):').grid(
        column=0, row=r, sticky='E')
    
    ttk.Spinbox(master, textvariable=master.btnvars['ptt_wait'], increment=0.01,
        from_=0, to=2**15-1).grid(column=1, row=r,
                    padx=master.padx, pady=master.pady, sticky='W')
                  
def blocksize(master, r):
    ttk.Label(master, text='Block Size:').grid(
        column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['blocksize']).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')
    

def buffersize(master, r):
    ttk.Label(master, text='Buffer Size:').grid(
        column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['buffersize']).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')

def overplay(master, r):
    ttk.Label(master, text='Overplay Time (sec):').grid(
        column=0, row=r, sticky='E')
    
    ttk.Spinbox(master, textvariable=master.btnvars['overplay'],
        increment=0.01, from_=0, to=2**15-1).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')
    
    
def outdir(master, r):
    ttk.Label(master, text='Output Folder:').grid(
        column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['outdir']).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')
    
    ttk.Button(master, text='Browse...', command=master.choose_outdir).grid(
        column=2, row=r, sticky='W')
    
    


def advanced(master, r):
    ttk.Button(master, text='Advanced...', command=master.show_advanced).grid(
        column=1, row=r, padx=master.padx, pady=master.pady, sticky='W')
    
def _advanced_submit(master, r):
    #closes the advanced window
    ttk.Button(master, text='OK', command=master.destroy).grid(
        column=2, row=r)