import argparse
import time

from ruka_hand.control.hand import Hand
from ruka_hand.utils.trajectory import move_to_pos

parser = argparse.ArgumentParser(description="Move the RUKA hand to its curled limit.")
parser.add_argument(
    "-ht",
    "--hand_type",
    type=str,
    choices=["right", "left"],
    help="Hand to move.",
    default="right",
)
parser.add_argument(
    "--traj-len",
    type=int,
    default=80,
    help="Number of interpolation steps for the motion.",
)
parser.add_argument(
    "--sleep-time",
    type=float,
    default=0.015,
    help="Delay between interpolation steps in seconds.",
)
parser.add_argument(
    "--hold",
    action="store_true",
    help="Keep torque enabled after curling until Ctrl-C.",
)
args = parser.parse_args()

hand = Hand(args.hand_type)
try:
    curr_pos = hand.read_pos()
    print(f"curr_pos: {curr_pos}, des_pos: {hand.curled_bound}")
    move_to_pos(
        curr_pos=curr_pos,
        des_pos=hand.curled_bound,
        hand=hand,
        traj_len=args.traj_len,
        sleep_time=args.sleep_time,
    )
    if args.hold:
        print("Holding fist with torque enabled. Press Ctrl-C to release.")
        while True:
            time.sleep(1)
    else:
        time.sleep(0.5)
finally:
    hand.close()
