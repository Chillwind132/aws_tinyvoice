import aiofile
import asyncio
import time
import sys
import numpy as np
import os
import queue
import threading
import sounddevice as sd
import soundfile as sf
import msvcrt
import time
import cProfile
import pstats
import subprocess
from amazon_transcribe.model import TranscriptEvent
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.client import TranscribeStreamingClient
from colorama import Fore, Back, Style
from colorama import init
import webbrowser


SAMPLERATE = 16000
VOICE_DATA = 'voice.wav'

class main():
    def __init__(self):

        self.AWS_ACCESS_KEY_ID = ""
        self.AWS_SECRET_KEY = ""
        self.selection_start = ""
        self.selection_stop = ""

        self.main()

    def auth(self):
        with open('rootkey.csv', 'r') as f:
            content = f.readlines()

        keys = {}
        for line in content:
            pair = line.strip().split('=')
            keys.update({pair[0]: pair[1]})

        self.AWS_ACCESS_KEY_ID = keys['AWSAccessKeyId']
        self.AWS_SECRET_KEY = keys['AWSSecretKey']

    def main(self):

        self.auth()

        global stop_threads, start_listen_flag, action_flag
        action_flag = '0'
        stop_threads = False
        start_listen_flag = False

        print(Fore.GREEN + "Starting tinyvoice" + Style.RESET_ALL)

        if os.path.isfile(VOICE_DATA):
            os.remove(VOICE_DATA)

        thread1 = myThread(1, "Thread-1", 1)
        thread1.start()

        if self.user_input_start() == '1':

            start_listen_flag = True

            print(Fore.GREEN + "Listening..." + Style.RESET_ALL)
            
            
            
            thread_voice_listener = myThread_voice_listener(1, "voice_listener", 1)
            thread_voice_listener.start()
            
            thread1.join()
            thread_voice_listener.join()
            
            
    def user_input_start(self):
        self.selection_start = input(
            "Press 1 to start\n")
        while self.selection_start != '1':
                print('Invalid input')
                self.selection_start = input(
                    "Press 1 to start\n")
        return self.selection_start
    

class myThread (threading.Thread): 
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        
        while stop_threads is not True:
                
                time.sleep(0.5)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                ####
                
                ###
                # Transcribe voice data in chunks
                try:
                    loop.run_until_complete(self.basic_transcribe())
                    loop.close()
                    
                except FileNotFoundError:
                    
                    while os.path.isfile(VOICE_DATA) is not True:
                        pass
                    
                except Exception as e:
                    print(Fore.RED + "tinyvoice terminated" + Style.RESET_ALL)
                    print(e)

    async def basic_transcribe(self):
        
        start_time = time.time()
        
        client = TranscribeStreamingClient(region="us-east-2")
        # Start transcription to generate our async stream
        #Preload the thread to this point to speed up processing#
        while start_listen_flag is False:
            pass
        stream = await client.start_stream_transcription(
            language_code="en-US",
            media_sample_rate_hz=SAMPLERATE,
            media_encoding="pcm",
        )

        async def write_chunks():
            
            
            async with aiofile.AIOFile('voice.wav', 'rb') as afp:
                
                reader = aiofile.Reader(afp, chunk_size=1024 * 25)
                async for chunk in reader:
                    
                    print("--- %s seconds ---" % (time.time() - start_time))
                    
                    time.sleep(0.5)

                    await stream.input_stream.send_audio_event(audio_chunk=chunk)

                    if stop_threads is True:  # Stop async loop if stop_threads = True
                        loop = asyncio.get_running_loop()
                        loop.stop()
                        loop.close()

            await stream.input_stream.end_stream()
        # Instantiate our handler and start processing events
        handler = MyEventHandler(stream.output_stream)
        await asyncio.gather(write_chunks(), handler.handle_events())


class myThread_voice_listener (threading.Thread):
    def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
      
    def run(self):
        # Stream our voice data to voice.wav
        
        
        while True:
            with sf.SoundFile(VOICE_DATA, mode='x', samplerate=SAMPLERATE, channels=1) as file:
                with sd.InputStream(samplerate=SAMPLERATE, channels=1, callback=callback):

                    # Prompts user to stop app exec in a seperate thread
                    thread2 = myThread_usr_sel(1, "Thread-user_sel", 1)
                    thread2.start()

                    while stop_threads is not True: # LOOP CHECK
                        
                        file.write(q.get())
                        
                        #if action_flag == '1':
                            #file.close()
                            
        
                    

class myThread_usr_sel (threading.Thread):
    def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter

    def run(self):
        global stop_threads, start_listen_flag
        stop_threads = self.user_input_stop()

    def user_input_stop(self):
        key_stroke = ''
        print(Fore.RED + "Use 'ESC' button to quit" + Style.RESET_ALL)
        while key_stroke != b'\x1b':  # Terminate if "esc" pressed
            if msvcrt.kbhit():
                key_stroke = msvcrt.getch()
                if key_stroke == b'\x1b':
                    self.selection_stop = True
                    print("Esc key pressed")
                else:
                    print(str(key_stroke).split("'")[1], "key pressed")

        return self.selection_stop
    

class MyEventHandler(TranscriptResultStreamHandler):
    
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                print(alt.transcript)
                
                if alt.transcript.strip() == 'Open Google chrome':
                    print(Fore.YELLOW + 'ACTION' + Style.RESET_ALL)
                    #self.reset_loop()
                    
    def reset_loop(self):
        
        global action_flag
        action_flag = '1'
                        
               
                    
class Queue(queue.Queue):
  '''
  A custom queue subclass that provides a :meth:`clear` method.
  '''

  def clear(self):
    '''
    Clears all items from the queue.
    '''
    
    with self.mutex:
      unfinished = self.unfinished_tasks - len(self.queue)
      if unfinished <= 0:
        if unfinished < 0:
          raise ValueError('task_done() called too many times')
        self.all_tasks_done.notify_all()
      self.unfinished_tasks = unfinished
      self.queue.clear()
      self.not_full.notify_all()                    
                  
                

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())
    
if __name__ == "__main__":
    

    
    init()
    q = queue.Queue()
    main()
    
   
    
    print('done')






