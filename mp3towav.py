import os
import sys
import time
import numpy as np
from joblib import Parallel, delayed
import librosa
import soundfile as sf
import pandas as pd

from create_birds_dataset import BIRDSLIST, BANNEDIDS, LABELS_PATH, DATA_PATH_FILTERED, DATA_DIR, DATA_DIR_WAV


# To create training dataset
DATA_DIR_MP3 = DATA_DIR
FINAL_LABELS_PATH = f"{LABELS_PATH}/all_data.csv"

SR = 14000
BIRDS_DIR_LIST = os.listdir(DATA_DIR_MP3)


# Create directories for wav files
if not os.path.exists(DATA_DIR_WAV):
    os.makedirs(DATA_DIR_WAV)

for bird in BIRDS_DIR_LIST:
    data_dir_bird = f"{DATA_DIR_WAV}/{bird}"
    if not os.path.exists(data_dir_bird):
        os.makedirs(data_dir_bird)


def convert_mp3_to_wav(filename, birdName, sr):
    """
    Converts the mp3 file to wav, with a sample_rate = 14000Hz and a single channel.
    """
    bird_filename_mp3 = f"{DATA_DIR_MP3}/{birdName}/{filename}"
    bird_filename_wav = f"{DATA_DIR_WAV}/{birdName}/{filename[:-4]}.wav"

    if bird_filename_mp3[-4:] == '.mp3' and not os.path.isfile(bird_filename_wav):
        try:
            bird_array, _ = librosa.load(bird_filename_mp3, mono=True, sr=sr)
            sf.write(bird_filename_wav, bird_array, sr)
        except:
            unvalidList.append(bird_filename_mp3)


# Return unvalid files
unvalidList = []
def conversion_function(birdslist, sr, do_print=False):
    """
    Converts all of the mp3 files
    """
    for birdName in birdslist:
        bird_dir = f"{DATA_DIR_MP3}/{birdName}"
        birdsaudiolist = [f for f in os.listdir(bird_dir) if os.path.isfile(os.path.join(bird_dir, f))]

        # print(birdsaudiolist)
        
        if do_print: start_time = time.time(); print(f"Converting {len(birdsaudiolist)} audio files of {birdName}")
           
        Parallel(n_jobs=-1)(delayed(convert_mp3_to_wav)(birdaudio, birdName, sr,) 
                                       for birdaudio in birdsaudiolist)
        

        if do_print: print(f"Conversion duration: {time.time()-start_time}s\n")
        

def give_fname(row):
    """
    Get the path to the wav file for each row
    """
    birdName = row['birdName'].replace(" ", "_").lower()
    iD = row['iD']
    fname = f"{DATA_DIR_WAV}/{birdName}/{birdName}_{iD}.wav"

    return fname


def create_labels_df(birdslist, bannedids):
    """
    Create Labels dataset from {DATA_PATH_FILTERED}.
    """
    labels_df = pd.read_csv(DATA_PATH_FILTERED)

    NumBirdsList = [len(labels_df.loc[labels_df['birdName'] == bird]) for bird in birdslist]

    birds_df = pd.DataFrame(columns=['bird', 'label', 'numSamples'])
    birds_df['bird'] = birdslist
    birds_df['label'] = list(range(len(birdslist)))
    birds_df['numSamples'] = NumBirdsList

    labels_dict = {birds_df['bird'][i]: birds_df['label'][i] for i in range(len(birds_df))}

    # Replace iD by the path to the audio file
    labels_df['fname'] = labels_df.apply(lambda row: give_fname(row), axis=1)

    # Replace birdName by its label
    labels_df = labels_df.replace(labels_dict)
    labels_df = labels_df.rename(columns={'birdName': 'label'})

    # Keep fname, length and label columns
    labels_df = labels_df[['fname', 'iD', 'length', 'label']]
    labels_df = labels_df[~labels_df['iD'].isin(bannedids)]

    print("Labels Dataframe Shape:", labels_df.shape)

    # Save filtered df to csv
    labels_df.to_csv(FINAL_LABELS_PATH, index=False)




if __name__ == "__main__":

    ### Start the conversion from mp3 to wav ###
    conversion_function(BIRDS_DIR_LIST, SR, do_print=True)

    print("Unvalid files:", unvalidList)

    ### Create labels Dataset for training ###
    BirdsList = BIRDSLIST
    BannedIDs = BANNEDIDS
    create_labels_df(BirdsList, BannedIDs)