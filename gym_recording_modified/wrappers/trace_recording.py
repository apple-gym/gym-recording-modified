import os
import time
import json
import glob
import logging
import numpy as np
import gym
from gym import error
from gym.utils import closer
from gym_recording_modified.recording import TraceRecording
logger = logging.getLogger(__name__)

__all__ = ['TraceRecordingWrapper']


trace_record_closer = closer.Closer()

class TraceRecordingWrapper(gym.Wrapper):
    """

    A Wrapper that records a trace of every action, observation, and reward generated by an environment.
    For an episode of length N, this will consist of:
      actions [0..N]
      observations [0..N+1]. Including the initial observation from `env.reset()`
      rewards [0..N]

    Usage:

      from gym_recording.wrappers import TraceRecordingWrapper
      if args.record_trace:
        env = TraceRecordingWrapper(env, '/tmp/mytraces')

    Later you can load the recorded traces:

      import gym_recording.playback

      def episode_cb(observations, actions, rewards):
          ... do something the episode ...

      gym_recording.playback.scan_recorded_traces('/tmp/mytraces', episode_cb)

    For an episode of length N, episode_cb receives 3 numpy arrays:
      observations.shape = [N + 1, observation_dim]
      actions.shape = [N, action_dim]
      rewards.shape = [N]
    """
    def __init__(self, env, directory=None, batch_size=None, only_reward=False, preprocess_obs=None):
        """
        Create a TraceRecordingWrapper around env, writing into directory

        Parameters: 
           directory (str): path of the directory that will be used to save the recordings
           batch_size (int): the number of steps should be taken before saving the recordings
           only_reward (bool): if True only reward would be saved
        """

        super(TraceRecordingWrapper, self).__init__(env)
        
        trace_record_closer.register(self)

        self.recording = TraceRecording(directory, batch_size, only_reward)
        self.directory = self.recording.directory
        self.preprocess_obs = preprocess_obs if preprocess_obs is not None else lambda obs: obs

    def step(self, action):
        observation, reward, done, info = self.env.step(action)
        self.recording.add_step(action, self.preprocess_obs(observation), reward, info)
        if done:
            self.recording.end_episode()
        return observation, reward, done, info

    def reset(self):
        observation = self.env.reset()
        self.recording.add_reset(self.preprocess_obs(observation))
        return observation

    def close(self):
        """
        Flush any buffered data to disk and close. It should get called automatically at program exit time, but
        you can free up memory by calling it explicitly when you're done
        """
        if self.recording is not None:
            self.recording.close()
