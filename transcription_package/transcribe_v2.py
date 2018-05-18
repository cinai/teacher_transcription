#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Cloud Speech API sample that demonstrates word time offsets.
Example usage:
    python transcribe_word_time_offsets.py resources/audio.raw
    python transcribe_word_time_offsets.py \
        gs://cloud-samples-tests/speech/vr.flac
"""

import argparse
import io
from os.path import isfile, join, basename, isdir
from os import mkdir
import os

def transcribe_file_with_word_time_offsets(speech_file,output_path):
    """Transcribe the given audio file synchronously and output the word time
    offsets."""
    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types
    client = speech.SpeechClient()

    with io.open(speech_file, 'rb') as audio_file:
        content = audio_file.read()

    audio = types.RecognitionAudio(content=content)
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code='es-CL',
        enable_word_time_offsets=True)

    response = client.recognize(config, audio)

    file_name = basename(speech_file)
    file_name = file_name[:-4]+'.txt'

    transcription_folder = join(output_path,'transcription')
    confidence_folder = join(output_path,'confidence')
    word_offset_folder = join(output_path,'word_offset')

    if not isdir(transcription_folder):
        mkdir(transcription_folder)
    if not isdir(confidence_folder):
        mkdir(confidence_folder)
    if not isdir(word_offset_folder):
        mkdir(word_offset_folder)

    transcription = open(join(output_path,'transcription',file_name),'w')
    confidence = open(join(output_path,'confidence',file_name),'w')
    word_offset = open(join(output_path,'word_offset',file_name),'w')

    for result in response.results:
        alternative = result.alternatives[0]
        transcription.write(alternative.transcript.encode('utf-8'))
        confidence.write(str(alternative.confidence))

        for word_info in alternative.words:
            word = word_info.word
            start_time = word_info.start_time
            end_time = word_info.end_time
            a_str = ",".join([word,str(start_time.seconds + start_time.nanos * 1e-9),str(end_time.seconds + end_time.nanos * 1e-9)]).encode('utf-8')+'\n'
            word_offset.write(a_str)

    transcription.close()
    confidence.close()
    word_offset.close()

def files(path):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            yield file

def transcribe_folder(name,output_path):
    for file in files(name):
        file_path = join(name,file)
        try:
            if(os.path.isfile(join(output_path,file[:-4]+'.txt'))):
                print('Ya esta')
                continue
        except Exception, e:
            print 'Error '+str(file)+': '+e
            continue
        transcribe_file_with_word_time_offsets(file_path,output_path)
    print("Done "+basename(name))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'path', help='File or GCS path for audio file to be recognized')
    parser.add_argument(
        'output_path', help='Folder in which save the .txt files')
    args = parser.parse_args()
    if isdir(args.path):
        transcribe_folder(args.path,args.output_path)
    else:
        transcribe_gcs(args.path,args.output_path)