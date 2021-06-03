# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 08:52:09 2021

@author: MkZee
"""

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fdl
    

defaults = {    'audio_file'      : "test.wav",
                'bgnoise_file'    : "",
                'bgnoise_volume'  : 0.1,
                'blocksize'       : 512,
                'buffersize'      : 20,
                'fs'              : int(48e3),
                'info'            : {},
                'no_log'          : ['test', 'ri'],
                'outdir'          : "",
                'overplay'        : 1.0,
                'ptt_wait'        : 0.68,
                'radioport'       : "",
                'ri'              : None,
                'test'            : "m2e_1loc",
                'trials'          : 100
            }

class M2EConfigFrame(tk.Frame):
    """
    Gui to configure and run a M2E Latency Test
    
    strvars : StringVarDict
    loads and stores the values in the controls
    
    """
    # Setting the padding (distance between controls)
    pady = 10
    padx = 5
      
    
    def __init__(self, btnvars, *args, **kwargs):
        #sets what controls will be in this frame
        controls = (
            test,
            audio_file,
            trials,
            bgnoise_file,
            bgnoise_volume,
            ptt_wait
            )
        
        
        
        super().__init__(*args, **kwargs)
        #option functions will get and store their values in here
        self.btnvars = btnvars
        
        
        for row in range(len(controls)):
            controls[row](self, r=row)
        
   
 #button functions
    def choose_audio_file(self):
        fp = fdl.askopenfilename(parent=self,
                initialfile=self.config['audio_file'],
                title='Open File',
                filetypes=[('WAV files','*.wav')])
        if fp != None:
            self.btnvars['audio_file'].set(fp)
    
    def choose_bgnoise_file(self):
        pass
                        
      
            
            
class _M2EAdvancedConfigGUI(tk.Toplevel):
    """Advanced options for the M2E test
    

    """    
    def __init__(self, btnvars, *args, **kwargs):
        self.btnvars = btnvars
        
        
            

#controls
def test(master, r):
    # Test Type
    c = ttk.Label(master, text='Test Type:')
    c['font'] = master.font
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
    ttk.Label(master, text='Background Noise File').grid(
        column=0, row=r, sticky='E')
    
    ttk.Entry(master, textvariable=master.btnvars['bgnoise_file']).grid(
        column=1, row=r, sticky='W', padx=master.padx, pady=master.pady)
    
    ttk.Button(master, text='Browse...',
        command=master.choose_bgnoise_file).grid(column=2, row=r, sticky='W')
    
def bgnoise_volume(master, r):    
    # bg noise volume
    ttk.Label(master, text='Background Noise Volume').grid(
        column=0, row=r, sticky='E')
    
    ttk.Spinbox(master, textvariable=master.btnvars['bgnoise_volume'], increment=0.01,
        from_=0, to=5).grid(column=1, row=r, sticky='W',
                            padx=master.padx, pady=master.pady)
                            
def ptt_wait(master, r):                            
    # PTT Wait time
    ttk.Label(master, text='PTT Wait Time (seconds)').grid(
        column=0, row=r, sticky='E')
    
    ttk.Spinbox(master, textvariable=master.btnvars['ptt_wait'], increment=0.01,
        from_=0, to=2**15-1).grid(column=1, row=r,
                    padx=master.padx, pady=master.pady, sticky='W')
                  
def blocksize(master, r):
    ttk.Label(master, text='Block Size').grid(
        column=0, row=r, sticky='E')
    
    c = ttk.Entry(master, text='Block Size')
    c['font'] = master.font
    c.grid(column=1)
    
                                  
 
    

        
if __name__ == '__main__':
    wn = tk.Tk()
    lb = M2EConfigFrame(, master=wn)
    lb.pack()
    