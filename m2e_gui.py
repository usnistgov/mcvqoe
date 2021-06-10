# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 08:52:09 2021

@author: MkZee
"""


import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fdl

from shared import LabeledControl
from shared import PADX
from shared import PADY
from shared import _SignalOverride
from tkinter.scrolledtext import ScrolledText
    
import time
import sys



class M2eFrame(tk.LabelFrame):
    """
    Gui to configure and run a M2E Latency Test
    
    strvars : StringVarDict
    loads and stores the values in the controls
    
    """
       
    
    def __init__(self, btnvars, text='Mouth-to-Ear Latency Test',
                 *args, **kwargs):
        #sets what controls will be in this frame
        controls = (
            test,
            audio_files,
            trials,
            ptt_wait,
            overplay,
            outdir,
            advanced
            )
        
        
        
        super().__init__(*args, text=text, **kwargs)
        #option functions will get and store their values in here
        self.btnvars = btnvars
        
        
        #initializes controls
        for row in range(len(controls)):
            controls[row](master=self, row=row)
        
        
        
            
            
class M2EAdvancedConfigGUI(tk.Toplevel):
    """Advanced options for the M2E test
    

    """    
    
    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        self.title('M2E Latency - Advanced')
        #sets the controls in this window
        controls = (
            BgNoise,
            AudioSettings,
            radioport,
            _advanced_submit
            )
        
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
        
            
        
        
        
        
        #------------------ Controls ----------------------



class test(LabeledControl):
    text = 'Location Type:'
    
    variable_arg = None # indicates the argument is positional
    MCtrl = ttk.OptionMenu
    MCtrlargs = ['', 'm2e_1loc', 'm2e_2loc_rx', 'm2e_2loc_tx']
    

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

    

class _advanced_submit(LabeledControl):
    
    #closes the advanced window
    MCtrl = None
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'OK'}
    
    def on_button(self):
        self.master.destroy()
    
    
# advanced groups
class BgNoise(tk.LabelFrame):
    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, *args, text='Background Noise', **kwargs)
        
        self.btnvars = master.btnvars
        
        controls = (bgnoise_file, bgnoise_volume)
        
        for row_ in range(len(controls)):
            controls[row_](master=self, row=row_)
        
        self.grid(column=0, row=row, padx=PADX, pady=PADY, columnspan=3,
                  sticky='WE')
        

class AudioSettings(tk.LabelFrame):
    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, *args, text='Audio Settings', **kwargs)
        
        self.btnvars = master.btnvars
        
        controls = (blocksize, buffersize)
        
        for row_ in range(len(controls)):
            controls[row_](master=self, row=row_)
        
        self.grid(column=0, row=row, padx=PADX, pady=PADY, columnspan=3,
                  sticky='WE')











def run(cnf, is_simulation):
    print(cnf,'\n', is_simulation)
    
     
    import m2e_class
    from mcvqoe.simulation.QoEsim import QoEsim
     
    o = m2e_class.M2E()
    
    cnf['audio_file'] = cnf['audio_files'].split(', ')[0]
    ToDo = '' # The above should change when we implement multiple audio files
    
    for k, v in cnf.items():
         if hasattr(o, k):
             setattr(o, k, v)
     
    o.param_check()
     
    # Get start time and date
    time_n_date = m2e_class.datetime.datetime.now().replace(microsecond=0)
    o.info['Tstart'] = time_n_date

    # Add test to info dictionary
    o.info['test'] = o.test
    
    
    
    if is_simulation:
        sim = QoEsim()
        def get_sim(*args, **kwargs):
            return sim
        
        #override these to simulate them
        m2e_class.RadioInterface = get_sim
        m2e_class.AudioPlayer = get_sim
    
    print('now')
    # Open RadioInterface object for testing
    o.ri = m2e_class.RadioInterface(o.radioport)
    print('you')
    # Fill 'Arguments' within info dictionary
    o.info.update(m2e_class.write_log.fill_log(o))


    m2e_class.test_info_gui.TestInfoGui.quit = lambda s=None : None
    # Gather pretest notes and M2E parameters
    o.info.update(m2e_class.test_info_gui.pretest(outdir=o.outdir))

    # Write pretest notes and info to tests.log
    m2e_class.write_log.pre(info=o.info)
    
    print('are')
    # Run chosen M2E test
    if (o.test == "m2e_1loc"):
        o.m2e_1loc()
    elif (o.test == "m2e_2loc_tx"):
        o.m2e_2loc_tx()
    elif (o.test == "m2e_2loc_rx"):
        o.m2e_2loc_rx()
    else:
        raise ValueError("\nIncorrect test type")
    
    # Gather posttest notes and write to log
    post_dict = m2e_class.test_info_gui.post_test()
    m2e_class.write_log.post(info=post_dict, outdir=o.outdir)
    
    
    print('done')
     
     
     
     
     
     
     
     
     
    return
"""
     # OLD CODE
     # redefining args, which will be passed to the test
     sys.argv = [sys.argv[0],
         '--testtype',     cnf['test'],
         '--audiofile',    cnf['audio_file'],
         '--trials',       cnf['trials'],
         '--pttwait',      cnf['ptt_wait'],
         '--blocksize',    cnf['blocksize'],
         '--buffersize',   cnf['buffersize'],
         '--overplay',     cnf['overplay'],
         '--outdir',       cnf['outdir']
         ]
     
     if cnf['radioport']:
         sys.argv.append('--radioport')
         sys.argv.append(cnf['radioport'])
        
     if cnf['bgnoise_file']:
         sys.argv.append('--bgnoisefile')
         sys.argv.append(cnf['bgnoise_file'])
         sys.argv.append('--bgnoisevolume')
         sys.argv.append(cnf['bgnoise_volume'])
     
     # overriding the ability to call signal.signal
     m2e_class.signal = _SignalOverride()
     
     m2e_class.main()
     
    """ 
     
     
     
     