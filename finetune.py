import os
import torch
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import LabelEncoder
import torchaudio


class BirdSegmentDataset(Dataset):
    def __init__(self, csv_file, audio_dir, transform=None):
        self.annotations = pd.read_csv(csv_file)
        self.audio_dir = audio_dir
        self.transform = transform
        self.label_encoder = LabelEncoder()
        self.annotations['label'] = self.label_encoder.fit_transform(self.annotations['Common Name'])

    def __len__(self):
        return len(self.annotations)


    def __getitem__(self, idx):
        filename = self.annotations.iloc[idx, 0]
        print(f"Processing file: {filename}")
        if not filename.endswith('.mp3'):
            filename += '.mp3'

        if '_alarmcall_' in filename:
            audio_path = os.path.normpath(os.path.join(f'{self.audio_dir}/alarmcall', filename))
            print(f"Loading audio file: {audio_path}")
            waveform, sample_rate = torchaudio.load(audio_path)
            label = self.annotations.iloc[idx, 1]
        elif '_call_' in filename:
            audio_path = os.path.normpath(os.path.join(f'{self.audio_dir}/call', filename))
            print(f"Loading audio file: {audio_path}")
            waveform, sample_rate = torchaudio.load(audio_path)
            label = self.annotations.iloc[idx, 1]
        elif '_beggingcall_' in filename:
            audio_path = os.path.normpath(os.path.join(f'{self.audio_dir}/beggingcall', filename))
            print(f"Loading audio file: {audio_path}")
            waveform, sample_rate = torchaudio.load(audio_path)
            label = self.annotations.iloc[idx, 1]
        elif '_song_' in filename:
            audio_path = os.path.normpath(os.path.join(f'{self.audio_dir}/song', filename))
            print(f"Loading audio file: {audio_path}")
            waveform, sample_rate = torchaudio.load(audio_path)
            label = self.annotations.iloc[idx, 1]
        else:
            raise ValueError(f"Unknown file type for {filename}")

        if self.transform:
            waveform = self.transform(waveform)

        return waveform, label


def main():
    bird = "Blaumeise"
    # Load dataset
    csv_file = f'Files/{bird}/data.csv'
    audio_dir = f'Files/{bird}'
    dataset = BirdSegmentDataset(csv_file, audio_dir)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
main()
