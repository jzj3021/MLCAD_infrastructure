import numpy as np
import math
import sys
import random
import time
import os

class Reward_buffer:
	def __init__(self, num_action: int, reward_buffer_size=32, trade_off_para: int = 0.1,  initial_value: np.array = None):
		"""
		Initialize the Reward_buffer with a specified size.
		Args:
		reward_buffer_size (int): The size of the reward buffer.
		initial_value (np.array): Optional initial values for the reward buffer.
		"""
		self.reward_buffer = np.zeros(reward_buffer_size, dtype=float)
		self.reward_buffer_size = reward_buffer_size
		self.visited_num = np.zeros(num_action, dtype=int)
		self.action_trials = -1 * np.ones(reward_buffer_size, dtype=int)
		self.num_actions = num_action
		self.pos = 0			# Current position in the buffer, starts at 0
		self.num_visited = 0	# Number of visited actions, starts at 0
		self.first_score = 0.0	# Last score, starts at 0

		# The trade-off between exploration and exploitation
		self.trade_off_para = trade_off_para
		random.seed(time.time_ns())
		if initial_value is not None:
			"""
			Randomly initialize the reward buffer with values between 0 and 1 if initial value is not given
			"""
			for i in range(self.reward_buffer_size):
				self.reward_buffer[i] = random.uniform(0, 1)

	def update_reward(self, action: int, score: float):
		"""
		Add a new reward and action to the buffer.
		If the buffer is full, it rolls the buffer and overwrites the oldest entry.
		Args:
			reward (float): The reward value to add.
			action (int): The action index corresponding to the reward.
		"""
		if action < 0 or action >= self.num_actions:
			raise IndexError("Action index out of bounds for the number of actions.")
		if self.pos == 0:
			reward = 0
			self.first_score = score
		else:
			reward = self.first_score - score
		if self.pos == self.reward_buffer_size:
			self.reward_buffer = np.roll(self.reward_buffer, -1)
			self.visited_num = np.roll(self.visited_num, -1)
			self.action_trials = np.roll(self.action_trials, -1)

			self.pos = self.reward_buffer_size
		else:
			self.pos += 1

		self.reward_buffer[self.pos - 1] = reward
		sys.stdout.flush()
		self.visited_num[action] += 1
		self.action_trials[self.pos - 1] = action
	
	def get_visited_num(self, index: int):
		"""
		Get the number of visits for the specified index.
		Args:
			index (int): The index to retrieve from the visited_num array.
		Returns:
			int: The number of visits for the specified index.
		"""
		if index < 0 or index >= self.reward_buffer_size:
			raise IndexError("Index out of bounds for visited_num array.")
		return self.visited_num[index]

	def get_action_trials(self):
		"""
		Get the action trials array.
		Returns:
			np.array: The action trials array.
		"""
		return self.action_trials[:self.pos]
	
	def get_reward_buffer(self):
		"""
		Get the current reward buffer.
		Returns:
			np.array: The current reward buffer.
		"""
		return self.reward_buffer
	
	def size(self):
		"""
		Get the size of the reward buffer.
		Returns:
			int: The size of the reward buffer.
		"""
		return self.reward_buffer_size
	
	def get_pos(self):
		"""
		Get the current position in the reward buffer.
		Returns:
			int: The current position in the reward buffer.
		"""
		return self.pos
	
	def num_visited(self):
		"""
		Get the number of visited actions.
		Returns:
			int: The number of visited actions.
		"""
		return self.num_visited
	
	def reset(self):
		"""
		Reset the reward buffer and visited_num array to their initial state.
		"""
		self.reward_buffer = np.zeros(self.reward_buffer_size)
		self.visited_num = np.zeros(self.reward_buffer_size)

	def argsort(self):
		"""
		Sort the reward buffer and return the indices of the sorted elements.
		Returns:
			np.array: Indices of the sorted elements in the reward buffer.
		"""
		temp_buffer = self.reward_buffer[:self.pos]
		return np.argsort(temp_buffer)

	def get_action_score(self):
		"""
		Get the current score of each action. If buffer is empty, return an array of zeros.
		Returns:
			ndarray: The score of each action in the reward buffer. Action 1 is at the first index, etc..
		"""
		if self.pos == 0:
			return np.zeros(self.num_actions)
		
		temp = self.argsort()
		print("Current sorted indices:", temp)
		cnt = 0
		action_space = np.zeros(self.num_actions)
		for i in temp:
			temp_score = self.reward_buffer_size - cnt
			action_space[self.action_trials[i]] += temp_score
			cnt += 1
		
		action_space = action_space / ((self.reward_buffer_size + 1) / 2.0 * self.reward_buffer_size)

		cnt = 0
		print("Current visited numbers:", self.visited_num)
		print("Current action space:", action_space)
		print("Current reward buffer:", self.reward_buffer)
		print("Current action trials:", self.action_trials)
		for i in action_space:
			action_space[cnt] = (1 - self.trade_off_para) * i + self.trade_off_para * math.sqrt(2 * math.log(self.reward_buffer_size) / (self.visited_num[cnt] + 0.1)) 
			print(f"Reward for action = {(1 - self.trade_off_para) * i}, Exploration = {self.trade_off_para * math.sqrt(2 * math.log(self.reward_buffer_size) / (self.visited_num[cnt] + 0.1))}")
			cnt += 1
		sys.stdout.flush()
		return action_space

class DiscountedUCBRewardBuffer:
    """
    Reward buffer using Discounted UCB algorithm for non-stationary rewards.
    Replaces the original Reward_buffer class.
    """
    def __init__(self, num_action: int, reward_buffer_size=32, gamma=0.95, c=2.0, initial_value=None):
        """
        Initialize the Discounted UCB Reward Buffer.
        
        Args:
            num_action (int): Number of available actions/operators
            reward_buffer_size (int): Size of the reward buffer
            gamma (float): Discount factor (0 < gamma <= 1)
            c (float): Exploration parameter for UCB
            initial_value: Optional initial values (not used in Discounted UCB)
        """
        self.num_actions = num_action
        self.reward_buffer_size = reward_buffer_size
        self.gamma = gamma
        self.c = c
        
        # Discounted UCB specific tracking
        self.discounted_rewards = np.zeros(num_action, dtype=float)
        self.discounted_counts = np.zeros(num_action, dtype=float)
        
        # Compatibility with original interface
        self.reward_buffer = np.zeros(reward_buffer_size, dtype=float)
        self.action_trials = -1 * np.ones(reward_buffer_size, dtype=int)
        self.visited_num = np.zeros(num_action, dtype=int)
        self.pos = 0
        self.first_score = 0.0
        
        # Total steps for UCB calculation
        self.total_steps = 0
        
        # History tracking for analysis
        self.reward_history = [[] for _ in range(num_action)]
        
        random.seed(time.time_ns())
    
    def update_reward(self, action: int, score: float):
        """
        Update the reward buffer with Discounted UCB logic.
        
        Args:
            action (int): The action/operator index
            score (float): The score after applying the action
        """
        if action < 0 or action >= self.num_actions:
            raise IndexError("Action index out of bounds for the number of actions.")
        
        # Calculate reward as improvement (lower score is better)
        if self.pos == 0:
            reward = 0
            self.first_score = score
        else:
            reward = self.first_score - score  # Positive reward for improvement
        
        # Apply discount to all previous statistics
        self.discounted_rewards *= self.gamma
        self.discounted_counts *= self.gamma
        
        # Add new observation
        self.discounted_rewards[action] += reward
        self.discounted_counts[action] += 1
        
        # Update compatibility tracking
        if self.pos < self.reward_buffer_size:
            self.reward_buffer[self.pos] = reward
            self.action_trials[self.pos] = action
            self.pos += 1
        else:
            # Roll buffer if full
            self.reward_buffer = np.roll(self.reward_buffer, -1)
            self.action_trials = np.roll(self.action_trials, -1)
            self.reward_buffer[-1] = reward
            self.action_trials[-1] = action
        
        self.visited_num[action] += 1
        self.total_steps += 1
        self.reward_history[action].append(reward)
        
        # Debug output
        print(f"Action {action}: reward={reward:.4f}, score={score:.4f}")
        print(f"Discounted stats - rewards: {self.discounted_rewards}")
        print(f"Discounted stats - counts: {self.discounted_counts}")
        sys.stdout.flush()
    
    def get_action_score(self):
        """
        Get UCB scores for each action using Discounted UCB.
        
        Returns:
            np.array: UCB scores for each action
        """
        ucb_scores = np.zeros(self.num_actions)
        
        # For the first num_actions steps, ensure each action is tried once
        if self.total_steps < self.num_actions:
            # Return high score for unvisited actions
            for i in range(self.num_actions):
                if self.visited_num[i] == 0:
                    ucb_scores[i] = float('inf')
                    return ucb_scores
        
        # Calculate UCB values for each action
        for action in range(self.num_actions):
            if self.discounted_counts[action] > 0:
                # Average discounted reward
                avg_reward = self.discounted_rewards[action] / self.discounted_counts[action]
                
                # Confidence bonus using discounted counts
                effective_n = self.discounted_counts[action]
                confidence_bonus = self.c * np.sqrt(2 * np.log(self.total_steps + 1) / effective_n)
                
                ucb_scores[action] = avg_reward + confidence_bonus
                
                print(f"Action {action}: avg_reward={avg_reward:.4f}, "
                      f"confidence={confidence_bonus:.4f}, UCB={ucb_scores[action]:.4f}")
            else:
                # If never pulled (shouldn't happen after initialization)
                ucb_scores[action] = float('inf')
        
        sys.stdout.flush()
        return ucb_scores
    
    def get_statistics(self):
        """Get current statistics for all actions."""
        stats = {}
        for action in range(self.num_actions):
            if self.discounted_counts[action] > 0:
                avg_reward = self.discounted_rewards[action] / self.discounted_counts[action]
            else:
                avg_reward = 0.0
            
            stats[action] = {
                'avg_discounted_reward': avg_reward,
                'discounted_count': self.discounted_counts[action],
                'total_selections': self.visited_num[action],
                'recent_rewards': self.reward_history[action][-5:] if self.reward_history[action] else []
            }
        return stats
    
    # Compatibility methods with original interface
    def get_visited_num(self, index: int):
        """Get the number of visits for the specified index."""
        if index < 0 or index >= self.num_actions:
            raise IndexError("Index out of bounds for visited_num array.")
        return self.visited_num[index]
    
    def get_action_trials(self):
        """Get the action trials array."""
        return self.action_trials[:self.pos]
    
    def get_reward_buffer(self):
        """Get the current reward buffer."""
        return self.reward_buffer[:self.pos]
    
    def size(self):
        """Get the size of the reward buffer."""
        return self.reward_buffer_size
    
    def get_pos(self):
        """Get the current position in the reward buffer."""
        return self.pos
    
    def reset(self):
        """Reset the buffer to initial state."""
        self.discounted_rewards = np.zeros(self.num_actions, dtype=float)
        self.discounted_counts = np.zeros(self.num_actions, dtype=float)
        self.reward_buffer = np.zeros(self.reward_buffer_size, dtype=float)
        self.action_trials = -1 * np.ones(self.reward_buffer_size, dtype=int)
        self.visited_num = np.zeros(self.num_actions, dtype=int)
        self.pos = 0
        self.total_steps = 0
        self.reward_history = [[] for _ in range(self.num_actions)]
    
    def argsort(self):
        """Sort the reward buffer and return indices."""
        temp_buffer = self.reward_buffer[:self.pos]
        return np.argsort(temp_buffer)
