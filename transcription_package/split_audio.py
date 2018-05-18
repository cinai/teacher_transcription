from pydub import AudioSegment
import sys
from os.path import join, basename

def split_audio(file_path,seconds,output_folder):
    audio_file = AudioSegment.from_wav(file_path)
    duration_milli = len(audio_file)
    chunk_duration = int(seconds)*1000
    base_name =  basename(file_path)[:-4]
    print("-------")
    print("Separando archivo: ",base_name)
    print("Largo del archivo: ",duration_milli)
    t1 = 0
    count = 0
    while(t1 < duration_milli):
        count += 1
        t2 = t1 + chunk_duration
        if(t2 <= duration_milli):
            newAudio = audio_file[t1:t2]
        else:
            newAudio = audio_file[t1:]
        file_name = base_name+'-'+str(count)+'.wav'
        file_name = join(output_folder,file_name)
        newAudio.export(file_name,format = 'wav')
        t1 += chunk_duration

    print("Separado en "+str(count)+" archivos")

if __name__ == '__main__':
    file_path = sys.argv[1]
    seconds = sys.argv[2]
    output_path = sys.argv[3]
    split_audio(file_path,seconds,output_path)
