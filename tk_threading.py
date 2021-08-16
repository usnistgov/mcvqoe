# -*- coding: utf-8 -*-
"""
Created on Mon Aug  9 14:51:59 2021

@author: MkZee
"""

import sys
import functools
import threading
from threading import Thread
import time
import traceback
import tkinter as tk



def in_thread(thread, wait=True, do_exceptions = False):
    """A function decorator to ensure that a function runs in the given thread.
    
    thread: can be {'GuiThread', 'MainThread'}
        the thread to run the function in
    wait:
        whether to wait for the function to return in the other thread
        if this is false, it may or may not return None.
        
    exceptions:
        whether to pass exceptions to the caller.
        wait must be set to True
    
    Example:
        
        @in_thread('MainThread')
        def my_mainthread_func(*args, **kwargs):
            print('Hello from the main thread!')
        
    """
    if thread not in ('MainThread', 'GuiThread'):
        raise ValueError(f'Thread {thread} does not exist')
        
    def decorator(func):
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            
            
                
            
            if thread == threading.current_thread().getName():
                # we are already in that thread!!
                return func(*args, **kwargs)
            
            switch_obj = _dec_return(func, args, kwargs, do_exceptions)
            
            if thread == 'MainThread':
                main.callback(switch_obj.callbacker)
            elif thread == 'GuiThread':
                main.gui_thread.callback(switch_obj.callbacker)
            
            
            if wait:
                # wait until function is finished if applicable
                while not switch_obj.finished:
                    if thread == 'MainThread':
                        # keep the gui responsive
                        main.win.update_idletasks()
                        
                    time.sleep(0.1)
                    
                if switch_obj.exc is not None:
                    raise switch_obj.exc
                    
                return switch_obj.return_val
                
            
        return wrapper
    return decorator

class _dec_return:
    def __init__(self, func, args, kwargs, do_exceptions):
        
        self.func = func
        self.finished = False
        self.args = args
        self.kwargs = kwargs
        
        self.exc = None
        self.return_val = None
        self.do_exceptions = do_exceptions

    def callbacker(self):
        try:
            self.return_val = self.func(*self.args, **self.kwargs)
        except BaseException as e:
            if self.do_exceptions:
                self.exc = e
            else:
                traceback.print_exc()
                show_error(e)
            
        self.finished = True
        
        

class GuiThread(Thread):
   
    def callback(self, function):
        """Calls a function in the GUIThread
        

        Parameters
        ----------
        function : callable
        
        """
        self._callbacks.insert(0, function)
    
     
    def __init__(self, win_class=tk.Tk):
        super().__init__()
        
        self.setName('GuiThread')
        self.setDaemon(True)
        self._callbacks = []
        self.win_class = win_class
        self.win = None
        
    
    
    def run(self):
        
        # construct window
        self.win = self.win_class()
        
        self.win.after(100, self._main_loop_ext)
        self.win.mainloop()

    def _main_loop_ext(self):
        
        try:
            #grab a function
            f = self._callbacks.pop()
        except IndexError:pass
        else:
            try:
                f()
            except:
                #don't crash in case of error
                traceback.print_exc()
                
        
        #run this function again
        self.win.after(100, self._main_loop_ext)
    
    @in_thread('GuiThread')
    def stop(self):
        if self.win is not None:
            self.win.destroy()
        
        
        
        

class Main():
    def __init__(self, win_class=tk.Tk):
        global main
        main = self
        self._break = False
        self._callbacks = []
        self.is_running = False
        self.last_error = None

        # constructs gui in new thread
        self.gui_thread = GuiThread(win_class)
        self.gui_thread.start()
        
        while self.gui_thread.win is None:
            time.sleep(0.01)
        
        self.win = self.gui_thread.win
        
        
        


    
    def callback(self, function):
        """Calls a function in the main thread.
        

        Parameters
        ----------
        function : callable
            

        Returns
        -------
        None.

        """
        self._callbacks.insert(0, function)
        
        
        
    def main_loop(self):
        while True:
            if self._break:
                self.is_running = False
                self.gui_thread.join()
                return
            try:
                try:
                    f = self._callbacks.pop()
                except IndexError:
                    #if no callbacks to be called
                    self.is_running = False
                    time.sleep(0.2)
                else:
                    self.is_running = True
                    f()
                
                
                
                
            except Abort_by_User:pass
                
            except SystemExit:
                break
                
            except KeyboardInterrupt:pass
                
                    
            except Exception as e:
                
                # prints exception without exiting main thread
                show_error(e)
        
        
        
        #thread is ending
        self.is_running = False
        
        
        self.gui_thread.join()
        return
        
          

    def stop(self):
        self._break = True
        
        








def show_error(exc=None):
    
    
    traceback.print_exc()
    
    if exc is None:
        exc = sys.exc_info()[1]
    if isinstance(exc, tuple):
        exc = exc[1]
        
    if not exc:
        #no error
        return
    
    print(exc)
    
    err_name, msg = format_error(exc)
    
    _show_error(err_name, msg)
    

def format_error(exc):
    msg = str(exc)
    err_name = exc.__class__.__name__
    
    
    if not msg and isinstance(exc, Exception):
        if 'error' in err_name.lower():
            descriptor = ''
        else:
            descriptor = ' error'
        if err_name[0].lower() in 'aeiou':
            article = 'An'
        else:
            article = 'A'
            
        msg = f'{article} "{err_name}"{descriptor} occurred.'
        
        
        err_name = 'Error'
    elif isinstance(exc, Abort_by_User):
        err_name = 'Measurement Stopped'
        msg = 'Aborted by user.'
    
        
    return err_name, msg
    
    
    
@in_thread('GuiThread')
def _show_error(err_name, msg):
    tk.messagebox.showerror(err_name, msg)
    
    
    
    
    
class Abort_by_User(BaseException):
    """Raised when user presses 'Abort test'
    
    Inherits from BaseException because it is not an error and therefore
    won't be treated as such
    """
    def __init__(self, *args, **kwargs):
        super().__init__('Measurement aborted by user', *args, **kwargs)
        
        
