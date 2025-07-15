import numpy as np
from reward_buffer import DiscountedUCBRewardBuffer
import sys

# Modified Agent class methods to use Discounted UCB


def create_discounted_ucb_agent(agent_class):
    """
    Modify the Agent class to use Discounted UCB.
    This function should be applied to your Agent class.
    """
    
    original_init = agent_class.__init__
    
    def new_init(self, design_dir, platflorm, verilog_file="", work_dir="../temp", 
                 output_verilog="final.v", use_discounted_ucb=True, gamma=0.95, c=2.0):
        """
        Modified init to optionally use Discounted UCB.
        
        Additional Args:
            use_discounted_ucb (bool): Whether to use Discounted UCB instead of original buffer
            gamma (float): Discount factor for Discounted UCB
            c (float): Exploration parameter for Discounted UCB
        """
        # Call original init
        original_init(self, design_dir, platflorm, verilog_file, work_dir, output_verilog)
        
        # Replace reward buffer if using Discounted UCB
        if use_discounted_ucb:
            reward_buffer_size = 4 * self.operator.num_operators
            self.reward_buffer = DiscountedUCBRewardBuffer(
                num_action=self.operator.num_operators,
                reward_buffer_size=reward_buffer_size,
                gamma=gamma,
                c=c
            )
            self.use_discounted_ucb = True
        else:
            self.use_discounted_ucb = False
    
    def new_get_next_operator(self, rand: bool = False):
        """
        Modified operator selection using Discounted UCB.
        """
        if rand:
            return random.randint(0, self.operator.num_operators - 1)
        
        if hasattr(self, 'use_discounted_ucb') and self.use_discounted_ucb:
            # Use Discounted UCB scores
            ucb_scores = self.reward_buffer.get_action_score()
            
            # Handle infinity values (unvisited actions)
            if np.any(np.isinf(ucb_scores)):
                # Return first unvisited action
                return np.where(np.isinf(ucb_scores))[0][0]
            
            # Return action with highest UCB score
            best_operator = np.argmax(ucb_scores)
            print(f"Selected operator {best_operator} with UCB score {ucb_scores[best_operator]:.4f}")
            return best_operator
        else:
            # Use original method
            action_score = self.reward_buffer.get_action_score()
            best_operator = np.argmax(action_score)
            return best_operator
    
    def new_run(self):
        """
        Modified run method with better logging for Discounted UCB.
        """
        self.global_placement()
        self.record_design()
        
        while not self.terminate():
            # Get the next operator
            action = self.get_next_operator()
            if action is None:
                print("No more operators available.")
                sys.stdout.flush()
                break
            
            print(f"\n=== Iteration {self.iteration} ===")
            print(f"Selected action: {action}")
            
            # Perform the operation
            self.operate(action)
            
            # Get the score after the operation
            action_seq = self.reward_buffer.get_action_trials()
            action_seq = [str(i) for i in action_seq]
            design_name = self.design_name + "_" + "".join(action_seq)
            score = self.get_score(design_name)
            
            if score < self.best_score:
                print(f"New best score: {score:.4f} (previous: {self.best_score:.4f})")
                self.best_score = score
                self.write_verilog(self.output_verilog)
            
            if score is None:
                raise Exception("Failed to get score after operation.")
            
            self.update_reward(action, score)
            
            # Print statistics if using Discounted UCB
            if hasattr(self, 'use_discounted_ucb') and self.use_discounted_ucb:
                stats = self.reward_buffer.get_statistics()
                print("\nOperator Statistics:")
                for op_idx, stat in stats.items():
                    print(f"  Operator {op_idx}: avg_reward={stat['avg_discounted_reward']:.4f}, "
                          f"selections={stat['total_selections']}")
            
            print(f"=== End Iteration {self.iteration} ===\n")
            sys.stdout.flush()
        
        self.detail_placement()
        self.global_routing()
        self.repair_design()
        self.repair_timing()
        
        # Final evaluation
        self.design.evalTclString("exit")
    
    # Apply modifications
    agent_class.__init__ = new_init
    agent_class.get_next_operator = new_get_next_operator
    agent_class.run = new_run
    
    return agent_class


# Example usage
if __name__ == "__main__":
    import argparse
    from pathlib import Path
    
    # Import your Agent class here
    from agent import Agent
    
    # Apply Discounted UCB modifications
    Agent = create_discounted_ucb_agent(Agent)
    
    # Now you can use the Agent with Discounted UCB
    
    parser = argparse.ArgumentParser(description="Run agent with Discounted UCB")
    parser.add_argument("--design_name", type=str, default="ac97_top")
    parser.add_argument("--output_verilog", type=str, default="final.v")
    parser.add_argument("--use_ducb", action="store_true", help="Use Discounted UCB")
    parser.add_argument("--gamma", type=float, default=0.8, help="Discount factor")
    parser.add_argument("--c", type=float, default=2.0, help="Exploration parameter")
    
    args = parser.parse_args()
    
    design_base = Path("/app/MLCAD25-Contest-Scripts-Benchmarks/designs")
    platform = "/app/MLCAD25-Contest-Scripts-Benchmarks/platform"
    temp_dir = "/app/MLCAD25-Contest-Scripts-Benchmarks/src/MLCAD_infrastructure/temp"
    
    agent = Agent(
        design_dir=design_base/args.design_name,
        platflorm=platform,
        work_dir=temp_dir,
        output_verilog=args.output_verilog,
        use_discounted_ucb=args.use_ducb,
        gamma=args.gamma,
        c=args.c
    )
    
    agent.run()
    os._exit(0)  # Ensure clean exit
    