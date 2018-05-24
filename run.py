# -*- coding: utf-8 -*-
import shutil
import os
import sys
from os import listdir,mkdir,getcwd
from os.path import isfile, join, basename, isdir
import argparse
import subprocess
import multiprocessing 


'''
Esta rutina se encarga de ejecutar todo el proceso
de transcripcion: desde la division de audios, hasta
la union de los archivos transcritos. Permite transcribir
un solo archivo, o varios en paralelo. 

Los audios a transcribir se deben ubicar en la carpeta wav_files
por defecto. Se puede cambiar en el punto 1.

WARNING: wav_files debe contener carpetas con archivos, no
archivos sueltos.

Al correr esta rutina se debe entregar como argumento
un archivo o una carpeta, si se quiere transcribir un archivo
o la carpeta completa respectivamente.
'''

# VARIABLES

# 1. Define folders of files to transcribe 

root_path = getcwd()

transcription_package = join(root_path,'transcription_package') 
credentials_folder = join(root_path,'credentials') 

audio_folder = join(root_path,'wav_files') # wav files
splitted_folder = join(root_path,'splitted') # splitted wav files.
output_folder = join(root_path,'output') # txt files

# 2. Define credential

#   2.1 Select credential file

# other_credential_path = "json_key_file.json" # format example
roberto_credential_path = "SmartSpeech-38a19c8af6e0.json"
daniela_credential_path = "ASR_API-795e8133c62e.json"
catalina_credential_path = "API Project-f7708a52d278.json"

credential_path = join(credentials_folder,roberto_credential_path)

#   2.2 Set enviroment variable

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path


# AUXILIAR FUNCTIONS

def split_all(seconds,list_files,list_output_folders):
    split_script = join(transcription_package,'split_audio.py')
    for i,f in enumerate(list_files):
        output_path = list_output_folders[i]
        subprocess.call(['python',split_script,f,str(seconds),output_path])

def transcribe_folders(paths):
    folder_name,output_folder = paths
    transcribe_script = join(transcription_package,'transcribe_v2.py')
    subprocess.call(['python',transcribe_script,folder_name,output_folder])

def transcribe_all(list_folders,list_output_folders):
    # Run this with a pool of 5 agents having a chunksize of 3 until finished
    total_cpu = multiprocessing.cpu_count()-4
    pool = multiprocessing.Pool(processes=total_cpu)
    result = pool.map(transcribe_folders,zip(list_folders,list_output_folders))
    pool.terminate()

def make_summary(list_folders):
    empty = 0
    not_empty = 0
    not_empty_size_total = 0
    n_lines_per_file = []
    n_files_per_file = []
    for a_folder in list_folders:
        a_folder = a_folder[:-4]
        transcription_to_join =  join(output_folder,a_folder)
        transcription_splitted = join(transcription_to_join,'transcription')
        if len(listdir(transcription_to_join)) == 0:
            empty += 1
            continue
        else:
            not_empty += 1
        h,file_name = os.path.split(a_folder)
        file_path = join(transcription_to_join,file_name+'.txt')
        not_empty_size_total += os.path.getsize(file_path)
        merged_file = open(file_path,'r')
        n_lines = sum(1 for line in merged_file)
        n_files = len(os.listdir(transcription_splitted))
        n_files_per_file.append((file_name,n_files))
        n_lines_per_file.append((file_name,n_lines))
        merged_file.close()
    import time
    ts = int(time.time())
    output_file = open('summary_'+str(ts)+'.txt','w')
    output_file.write('Empty files: '+str(empty))
    output_file.write('\n')
    output_file.write('Not Empty files: '+str(not_empty))
    output_file.write('\n')
    output_file.write('Not Empty size: '+str(not_empty_size_total))
    output_file.write('\n')
    for i,a in enumerate(n_lines_per_file):
        a_file = a[0]
        n_lines = a[1]
        n_files = n_files_per_file[i][1]
        output_file.write(a_file+' n lineas: '+str(n_lines)+', n files: ' + str(n_files))
        output_file.write('\n')
    output_file.close()

def files(path):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            yield file

def join_transcription(a_folder):
    transcription_to_join =  join(output_folder,a_folder)
    transcription_splitted = join(transcription_to_join,'transcription')
    h,file_name = os.path.split(a_folder)
    merged_file = open(join(transcription_to_join,file_name+'.txt'),'w')
    files_names = os.listdir(transcription_splitted)
    n_files = max([int(f.split('-')[1].split('.')[0]) for f in files_names])
    #n_files = len(os.listdir(transcription_splitted))
    for i in range(n_files):
        file_i_name = join(transcription_splitted,file_name+'-'+str(i+1)+'.txt')
        try:
            file_i = open(file_i_name,'r')
            for line in file_i:
                merged_file.write(line)
            file_i.close()
        except:
            pass
        merged_file.write('\n')
    merged_file.close()

def join_all(list_folders):
    for f in list_folders:
        join_transcription(f[:-4])

# 0. Main

if __name__ == '__main__':
    # receive arguments (file or folder)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'path', help='File or GCS path for audio file to be recognized')
    args = parser.parse_args()
    folder_or_file = args.path
    list_folders = []

    # Capture output into a log file

    old_stdout = sys.stdout

    log_file = open("message.log","w")

    sys.stdout = log_file 
    # check if argument is folder or file
    if isfile(folder_or_file):
        list_files = [join(audio_folder,folder_or_file)]
        folder = folder_or_file.split('.')[0] # remove '.wav'
    else:
        # TODO: ADD RAISE IF FOLDER DOESNT EXIST
        list_files = []
        for f in listdir(join(audio_folder,folder_or_file)):
            file_path = join(audio_folder,folder_or_file,f)
            if isfile(file_path):
                list_files.append(file_path)    
                list_folders.append(join(folder_or_file,f))
            folder = folder_or_file

    # build folder to split audios
    save_folder = join(splitted_folder,folder)
    if not isdir(save_folder):
        mkdir(save_folder)
    list_splitted_folders = []
    for f in list_files:
        filename = basename(f).split('.')[0] # get only the file name and remove '.wav'
        folder_name = join(save_folder,filename)
        if not isdir(folder_name):
            mkdir(folder_name)
        list_splitted_folders.append(folder_name)
    
    # split audios, and save them in save_folders
    
    #split_all(15,list_files,list_splitted_folders) # into 15 seconds chunks

    # build folder to save the transcription
    save_folder = join(output_folder,folder)
    if not isdir(save_folder):
        mkdir(save_folder)
    list_output_folders = []
    for f in list_files:
        filename = basename(f).split('.')[0] # get only the file name and remove '.wav'
        folder_name = join(save_folder,filename)
        if not isdir(folder_name):
            mkdir(folder_name)
        list_output_folders.append(folder_name)
    # transcribir los archivos en ese folder
    transcribe_all(list_splitted_folders,list_output_folders)
    # unir los archivos
    join_all(list_folders)
    sys.stdout = old_stdout
    log_file.close()
    make_summary(list_folders)
    