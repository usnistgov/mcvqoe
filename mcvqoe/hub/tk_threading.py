# -*- coding: utf-8 -*-
"""
Created on Mon Aug  9 14:51:59 2021

@author: MkZee
"""

import datetime
import sys
import functools
import threading
from threading import Thread
import time
import traceback
import tkinter as tk
import os.path

from .common import save_dir


def in_thread(thread, wait=True, except_ = None):
    """A function decorator to ensure that a function runs in the given thread.
    
    Has no effect whenever the function is called from the same thread it is set
    to be in.
    
    thread: one of 'GuiThread', 'MainThread'
        the thread to run the function in
        
    wait : bool
        whether to wait for the function to return in the other thread.
        if this is False, it may return None if called from a different thread.
        
    except_:
        an exception or tuple of exceptions which will be passed to the caller
        if raised by the function. (as if used in an except clause).
        Has no effect if wait is False
    
    Example:
        
        @in_thread('MainThread')
        def my_mainthread_func(*args, **kwargs):
            print('Hello from the main thread!')
        
    """
    
    exceptions = except_
    
    # convert exceptions to catch nothing if they are not applicable
    if not wait or exceptions is None:
        exceptions = tuple()
        
    
    
    if thread not in ('MainThread', 'GuiThread'):
        raise ValueError(f'Thread {thread} does not exist')
        
    def decorator(func):
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            
            
                
            
            if thread == threading.current_thread().getName():
                # we are already in that thread!!
                # run the function as normal
                return func(*args, **kwargs)
            
            switch_obj = _dec_return(func, args, kwargs, exceptions)
            
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
    def __init__(self, func, args, kwargs, exceptions):
        
        self.func = func
        self.finished = False
        self.args = args
        self.kwargs = kwargs
        
        self.exc = None
        self.return_val = None
        self.exceptions = exceptions

    def callbacker(self):
        try:
            self.return_val = self.func(*self.args, **self.kwargs)
            
        except self.exceptions as e:
            self.exc = e
            
        except BaseException as e:
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
        
        # register callback for error handling in gui-thread
        self.win.report_callback_exception = lambda typ, exc, trace: show_error(exc)
        
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
            except Exception as e:
                #don't crash in case of error
                show_error(e)
                
        
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
        
        
class SingletonWindow(type):
    # no idea how tf this works by the way
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        
        if cls not in cls._instances or not cls._instances[cls].winfo_exists():
            
            cls._instances[cls] = super(SingletonWindow, cls).__call__(*args, **kwargs)
        else:
            cls._instances[cls].focus_force()
            cls._instances[cls].bell()
        return cls._instances[cls]

@in_thread('GuiThread')
def _show_error(err_name, msg):
    tk.messagebox.showerror(err_name, msg)

def show_error(exc=None, err_func=None):

    err_time = datetime.datetime.now()

    #dir for traceback.log file
    base_fold = save_dir
    #full path to log file
    err_log = os.path.join(base_fold,'traceback.log')

    try:
        #get traceback info in a string
        tb_str = traceback.format_exc()
        #make sure directory exists
        os.makedirs(base_fold, exist_ok=True)

        with open(err_log, 'at') as f:
            #write Heading for start of traceback
            f.write(f'##Error Encountered on {err_time.strftime("%c")}:\n')
            #write traceback
            f.write(tb_str)
            #add an extra newline for seperation
            f.write('\n')
    except (OSError, IOError):
        print('Unable to write traceback.log')

    traceback.print_exc()
    
    if exc is None:
        exc = sys.exc_info()[1]
    if isinstance(exc, tuple):
        exc = exc[1]
        
    if not exc:
        #no error
        return
    
    if isinstance(exc, InvalidParameter) and err_func is None:
        main.win.show_invalid_parameter(exc)
    else:
        err_name, msg = format_error(exc)

        if err_func:
            err_func(err_name, msg)
        else:
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


class InvalidParameter(ValueError):
    """Raised when a user fails to input a required parameter.
    """
    
    def __init__(self, parameter, message=None, *args, **kwargs):
        
        super().__init__(f'{parameter}: {message}', *args, **kwargs)
        
        self.parameter = parameter
        self.message = message
    
    
class Abort_by_User(BaseException):
    """Raised when user presses 'Abort test'
    
    Inherits from BaseException because it is not an error and therefore
    won't be treated as such
    """
    def __init__(self, *args, **kwargs):
        super().__init__('Measurement aborted by user', *args, **kwargs)
        
        
