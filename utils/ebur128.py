import numpy as np
import soundfile as sf
from math import log10
from pyebur128 import (
    ChannelType, MeasurementMode, R128State,
    get_loudness_global, get_true_peak, get_loudness_momentary, get_loudness_range, get_loudness_shortterm
)

def get_single_loudness_integrated(filename):
    '''Open the WAV file and get the integrated loudness.'''
    with sf.SoundFile(filename) as wav:
        state = R128State(wav.channels, wav.samplerate, MeasurementMode.MODE_I)

        if wav.channels == 5:
            state.set_channel(0, ChannelType.LEFT)
            state.set_channel(1, ChannelType.RIGHT)
            state.set_channel(2, ChannelType.CENTER)
            state.set_channel(3, ChannelType.LEFT_SURROUND)
            state.set_channel(4, ChannelType.RIGHT_SURROUND)

        for sample in wav.read():
            if wav.channels == 1:
                sample = np.array([sample])
            state.add_frames(sample, 1)

    loudness = get_loudness_global(state)
    return loudness

def get_max_true_peak(filename):
    '''Open the WAV file and get the maximum true loudness peak.'''
    with sf.SoundFile(filename) as wav:
        state = R128State(wav.channels,
                          wav.samplerate,
                          MeasurementMode.MODE_TRUE_PEAK)

        if wav.channels == 5:
            state.set_channel(0, ChannelType.LEFT)
            state.set_channel(1, ChannelType.RIGHT)
            state.set_channel(2, ChannelType.CENTER)
            state.set_channel(3, ChannelType.LEFT_SURROUND)
            state.set_channel(4, ChannelType.RIGHT_SURROUND)

        for sample in wav.read():
            if wav.channels == 1:
                sample = np.array([sample])
            state.add_frames(sample, 1)

    max_true_peak = float('-inf')
    for channel in range(state.channels):
        true_peak = get_true_peak(state, channel)
        max_true_peak = max(true_peak, max_true_peak)
    del state

    return 20 * log10(max_true_peak)

def get_max_loudness_momentary(filename):
    '''Open the WAV file and get the loudness in momentary (400ms) chunks.'''
    with sf.SoundFile(filename) as wav:
        state = R128State(wav.channels,
                          wav.samplerate,
                          MeasurementMode.MODE_M)

        if wav.channels == 5:
            state.set_channel(0, ChannelType.LEFT)
            state.set_channel(1, ChannelType.RIGHT)
            state.set_channel(2, ChannelType.CENTER)
            state.set_channel(3, ChannelType.LEFT_SURROUND)
            state.set_channel(4, ChannelType.RIGHT_SURROUND)

        # 10 ms buffer / 100 Hz refresh rate as 10 Hz refresh rate fails on
        # several tests.
        max_momentary = float('-inf')
        total_frames_read = 0
        for block in wav.blocks(blocksize=int(wav.samplerate / 100)):
            frames_read = len(block)
            total_frames_read += frames_read

            for sample in block:
                if wav.channels == 1:
                    sample = np.array([sample])
                state.add_frames(sample, 1)

            # Invalid results before the first 400 ms.
            if total_frames_read >= 4 * wav.samplerate / 10:
                momentary = get_loudness_momentary(state)
                max_momentary = max(momentary, max_momentary)

    del state

    return max_momentary

def get_single_loudness_range(filename):
    '''Open the WAV file and get the loudness range.'''
    with sf.SoundFile(filename) as wav:
        state = R128State(wav.channels,
                          wav.samplerate,
                          MeasurementMode.MODE_LRA)

        if wav.channels == 5:
            state.set_channel(0, ChannelType.LEFT)
            state.set_channel(1, ChannelType.RIGHT)
            state.set_channel(2, ChannelType.CENTER)
            state.set_channel(3, ChannelType.LEFT_SURROUND)
            state.set_channel(4, ChannelType.RIGHT_SURROUND)

        for sample in wav.read():
            if wav.channels == 1:
                sample = np.array([sample])
            state.add_frames(sample, 1)

    loudness = get_loudness_range(state)
    del state

    return loudness

def get_max_loudness_shortterm(filename):
    '''Open the WAV file and get the loudness in short-term (3s) chunks.'''
    with sf.SoundFile(filename) as wav:
        state = R128State(wav.channels,
                          wav.samplerate,
                          MeasurementMode.MODE_S)

        if wav.channels == 5:
            state.set_channel(0, ChannelType.LEFT)
            state.set_channel(1, ChannelType.RIGHT)
            state.set_channel(2, ChannelType.CENTER)
            state.set_channel(3, ChannelType.LEFT_SURROUND)
            state.set_channel(4, ChannelType.RIGHT_SURROUND)

        # 10 ms buffer / 10 Hz refresh rate.
        max_shortterm = float('-inf')
        total_frames_read = 0
        for block in wav.blocks(blocksize=int(wav.samplerate / 10)):
            frames_read = len(block)
            total_frames_read += frames_read

            for sample in block:
                if wav.channels == 1:
                    sample = np.array([sample])
                state.add_frames(sample, 1)

            # Invalid results before the first 3 seconds.
            if total_frames_read >= 3 * wav.samplerate:
                shortterm = get_loudness_shortterm(state)
                max_shortterm = max(shortterm, max_shortterm)

    del state

    return max_shortterm