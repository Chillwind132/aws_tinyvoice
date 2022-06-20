from amazon_transcribe.model import TranscriptEvent
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.client import TranscribeStreamingClient
import aiofile
import asyncio
import time
import boto3
import sounddevice as sd
import soundfile as sf
import numpy
import sys
import queue
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
import os
import queue
import threading

assert np


def callback(indata, frames, time, status):
    """
    This is called from a separate thread for each audio block
    """
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        # This handler can be implemented to handle transcriptions as needed.
        # Here's an example to get started.
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
       print("Starting thread 1")
       while True:
            time.sleep(0.5)
            print("Exiting " + self.name)
            if record_flag is True:

                time.sleep(1.5)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(basic_transcribe())
                loop.close()
            

            if stop_threads:
               return


if __name__ == "__main__":

    global stop_threads, record_flag
    record_flag = False
    stop_threads = True

    with open('rootkey.csv', 'r') as f:
        content = f.readlines()

    keys = {}
    for line in content:
        pair = line.strip().split('=')
        keys.update({pair[0]: pair[1]})

    AWS_ACCESS_KEY_ID = keys['AWSAccessKeyId']
    AWS_SECRET_KEY = keys['AWSSecretKey']


    thread1 = myThread(1, "Thread-1", 1)
    thread1.start()

    q = queue.Queue()
    
    filename = 'voice.wav'
    if os.path.isfile(filename):
        os.remove(filename)
    
    with sf.SoundFile(filename, mode='x', samplerate=16000, channels=1) as file:
        with sd.InputStream(samplerate=16000, channels=1, callback=callback):
            print('#' * 80)
            print('press Ctrl+C to stop the recording')
            print('#' * 80)
            while True:
                record_flag = True
                file.write(q.get())
    
    

    
    
    
    print('Done')



