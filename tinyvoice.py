import aiofile
import asyncio
import time
import boto3
import sys
import tempfile
import numpy as np
import os
import queue
import threading
import sounddevice as sd
import soundfile as sf
from amazon_transcribe.model import TranscriptEvent
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.client import TranscribeStreamingClient
import msvcrt

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                print(alt.transcript)


async def basic_transcribe():
    client = TranscribeStreamingClient(region="us-east-2")
    # Start transcription to generate our async stream
    stream = await client.start_stream_transcription(
        language_code="en-US",
        media_sample_rate_hz=16000,
        media_encoding="pcm",
    )

    async def write_chunks():
        async with aiofile.AIOFile('voice.wav', 'rb') as afp:
            reader = aiofile.Reader(afp, chunk_size=1024 * 16)
            async for chunk in reader:
                time.sleep(0.5)
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
                
                if user_selection_stop == "2": # Stop the loop if app terminated by user 
                    loop = asyncio.get_running_loop()
                    loop.stop()
                    loop.close()
                   
        
        await stream.input_stream.end_stream()
    # Instantiate our handler and start processing events
    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(write_chunks(), handler.handle_events())


class myThread (threading.Thread): 
   def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter

   def run(self):
       print("Starting tinyvoice")
       while user_selection_stop != '2':
            
            time.sleep(1)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Transcribe voice data in chunks
            try:
                loop.run_until_complete(basic_transcribe())
                loop.close()
            except Exception as e:
                print("async terminated") 


class myThread_usr_sel (threading.Thread):
    def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
      
    def run(self):
        global user_selection_stop
        user_selection_stop = self.user_input_stop()
        
    def user_input_stop(self):
        key_stroke = ''
        while key_stroke != b'\x1b': # Terminate if "esc" pressed
            if msvcrt.kbhit():
                key_stroke = msvcrt.getch()
                if key_stroke == b'\x1b': 
                    self.selection_stop = '2'
                    print("Esc key pressed")
                else:
                    print(str(key_stroke).split("'")[1], "key pressed")
                
        
        return self.selection_stop
    
class main():
    def __init__(self):

        self.AWS_ACCESS_KEY_ID = ""
        self.AWS_SECRET_KEY = ""
        self.selection_start = '0'
        self.selection_stop = '0'

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

        global stop_threads, user_selection_stop
        
        stop_threads = True
        user_selection_stop ='' 
        
        
        
        if self.user_input_start() == '1':
            thread1 = myThread(1, "Thread-1", 1)
            thread1.start()
            
            
            filename = 'voice.wav'
            if os.path.isfile(filename):
                os.remove(filename)

            with sf.SoundFile(filename, mode='x', samplerate=16000, channels=1) as file: # Stream our voice data to voice.wav
                with sd.InputStream(samplerate=16000, channels=1, callback=callback):
                   
                    thread2 = myThread_usr_sel(1, "Thread-user_sel", 1) #Prompts user to stop app exec 
                    thread2.start()
                    
                    
                    while user_selection_stop != '2':
                        
                        file.write(q.get())
                        
                    thread1.join()
                    print ('terminated')
                    

    def user_input_start(self):
        self.selection_start = input(
            "Press 1 to start\n")
        while self.selection_start != '1':
            print('Invalid input')
            self.selection_start = input(
                "Press 1 to start\n")
        return self.selection_start

    
    
if __name__ == "__main__":
    
    q = queue.Queue()
    main()
    print('done')






