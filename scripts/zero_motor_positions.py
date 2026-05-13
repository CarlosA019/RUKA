import argparse
import sys
import time

from ruka_hand.utils.constants import USB_PORTS
from ruka_hand.utils.control_table.control_table import (
    ADDR_HOMING_OFFSET,
    ADDR_PRESENT_POSITION,
    LEN_PRESENT_POSITION,
    LEN__HOMING_OFFSET,
)
from ruka_hand.utils.dynamixel_util import DynamixelClient, unsigned_to_signed


DEFAULT_MOTORS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


def parse_int_list(value):
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def read_signed(client, motors, address, size):
    values = client.sync_read(motors, address, size)
    return [unsigned_to_signed(value, size) for value in values]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Set Dynamixel homing offsets so the current motor positions read as "
            "a chosen target, usually zero."
        )
    )
    parser.add_argument(
        "-ht",
        "--hand-type",
        default="right",
        choices=["left", "right"],
        help="Hand port to use from ruka_hand.utils.constants.USB_PORTS.",
    )
    parser.add_argument(
        "-m",
        "--motors",
        type=parse_int_list,
        default=DEFAULT_MOTORS,
        help="Comma-separated motor IDs to zero.",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=0,
        help="Position value the selected motors should read after offsetting.",
    )
    parser.add_argument(
        "--positions",
        type=parse_int_list,
        help=(
            "Optional comma-separated present positions to use instead of reading "
            "the motors. Must match --motors length."
        ),
    )
    parser.add_argument(
        "--max-adjust",
        type=int,
        default=10000,
        help="Refuse offset changes larger than this many ticks.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write homing offsets. Without this, only prints the plan.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    motors = args.motors

    if args.positions is not None and len(args.positions) != len(motors):
        raise ValueError("--positions length must match --motors length")

    client = DynamixelClient(motors, USB_PORTS[args.hand_type])
    client.connect()

    try:
        present = args.positions
        if present is not None:
            present = [
                unsigned_to_signed(value, LEN_PRESENT_POSITION) for value in present
            ]
        if present is None:
            present = read_signed(
                client, motors, ADDR_PRESENT_POSITION, LEN_PRESENT_POSITION
            )
        homing = read_signed(client, motors, ADDR_HOMING_OFFSET, LEN__HOMING_OFFSET)

        # reported_position = raw_position + homing_offset, so subtract the
        # current reported error from each homing offset.
        new_homing = [
            int(current_offset - (current_position - args.target))
            for current_offset, current_position in zip(homing, present)
        ]
        adjustments = [
            new_offset - current_offset
            for new_offset, current_offset in zip(new_homing, homing)
        ]

        print("Motor zeroing plan:")
        print("id | present | homing_offset | adjustment | new_homing_offset")
        for motor_id, pos, offset, adjustment, new_offset in zip(
            motors, present, homing, adjustments, new_homing
        ):
            print(
                f"{motor_id:>2} | {pos:>7} | {offset:>13} | "
                f"{adjustment:>10} | {new_offset:>17}"
            )

        too_large = [
            (motor_id, adjustment)
            for motor_id, adjustment in zip(motors, adjustments)
            if abs(adjustment) > args.max_adjust
        ]
        if too_large:
            print("\nRefusing to write; offset adjustment is too large:")
            for motor_id, adjustment in too_large:
                print(f"  motor {motor_id}: {adjustment}")
            print("Increase --max-adjust only after checking the mechanical setup.")
            return 2

        if not args.apply:
            print("\nDry run only. Re-run with --apply to write these offsets.")
            return 0

        print("\nDisabling torque and writing homing offsets...")
        client.set_torque_enabled(False, retries=0)
        time.sleep(0.1)
        client.sync_write(motors, new_homing, ADDR_HOMING_OFFSET, LEN__HOMING_OFFSET)
        time.sleep(0.1)

        updated = read_signed(client, motors, ADDR_HOMING_OFFSET, LEN__HOMING_OFFSET)
        print("Updated homing offsets:", updated)
        print("Power-cycle or re-enable torque before normal control.")
        return 0
    finally:
        client.disconnect()


if __name__ == "__main__":
    sys.exit(main())
