import argparse
import time

from ruka_hand.control.hand import Hand
from ruka_hand.utils.trajectory import move_to_pos

parser = argparse.ArgumentParser(description="Teleop robot hands.")
parser.add_argument(
    "-ht",
    "--hand_type",
    type=str,
    help="Hand you'd like to teleoperate",
    default="right",
)
args = parser.parse_args()
hand = Hand(args.hand_type)
try:
    curr_pos = hand.read_pos()
    print(f"curr_pos: {curr_pos}, des_pos: {hand.tensioned_pos}")
    move_to_pos(curr_pos=curr_pos, des_pos=hand.tensioned_pos, hand=hand, traj_len=50)
    time.sleep(0.5)
finally:
    hand.close()
